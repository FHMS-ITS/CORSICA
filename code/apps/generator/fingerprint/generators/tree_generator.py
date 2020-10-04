import json
import operator
from sqlalchemy import select, func, desc
from sqlalchemy.orm import sessionmaker
from apps.generator.lib.node import Node
from database.models.generator.memory import MemWebRootFiles, MemFpFileFingerprint
from utils.log import _info, _debug, _error
from utils.utils import jsv_save_javascript_value


class TreeGenerator:
    def __init__(self, config, db_engine, args, uid):
        self.args = args
        self.uid = uid
        self.config = config
        self.db_engine = db_engine
        self.used_files = []
        self.thread_count = int(self.config['generator']['thread_count'])

    def run(self):
        db_session = sessionmaker(bind=self.db_engine)()
        result = db_session.execute(
            select([MemWebRootFiles.web_root]).distinct().where(MemWebRootFiles.deleted == 0)).fetchall()
        root_node = Node(webroots=[x[0] for x in result])

        if len(root_node.webroots) > 0:
            self.__process_node(root_node, db_session)

        _info("corsica.fpgen.fpc", "Saving Tree values to database")
        jsv_save_javascript_value(db_session, 'tree', json.dumps(root_node.to_dict()), self.uid)
        jsv_save_javascript_value(db_session, 'used_files', json.dumps(self.used_files), self.uid)
        db_session.close()
        return root_node

    def __process_node(self, node, db_session, iteration=0, paths_in_tree=None):
        _info('test', node)
        if paths_in_tree is None:
            paths_in_tree = []

        stmt = select([func.count(MemWebRootFiles.web_full_path).label('path_count'), MemWebRootFiles.web_full_path]) \
            .where(MemWebRootFiles.deleted == 0) \
            .where(MemWebRootFiles.web_root.in_(node.webroots)) \
            .group_by(MemWebRootFiles.web_full_path) \
            .order_by(desc('path_count'))
        result = db_session.execute(stmt).fetchall()

        # Find new path to separate left and right subtree
        paths = {}
        for r in result:
            stmt = select([func.count(MemWebRootFiles.id).label('del_count')]).where(
                MemWebRootFiles.deleted == 1).where(MemWebRootFiles.web_full_path == r.web_full_path)
            if db_session.execute(stmt).first()[0] > 0:
                continue
            if r.web_full_path.lower() not in paths_in_tree:
                paths[r.web_full_path] = r.path_count

        if len(paths) == 0:
            return

        desired = int(len(node.webroots) / 2)

        # Get all path elements greater or equal to desired and sort result dict by value
        # Example result: [('/shared_2_4.css', 2), ('/closely_1_4.css', 2), ('/shared_1_3.css', 2)]
        # ToDo: Baumqualität hängt von der Sortierung der Elemente mti gleicher Anzahl ab. Ggf durch probieren aller Möglichkeiten
        # ToDo: dont use a path where one file is deteled

        desired_files = dict((k, v) for k, v in paths.items() if v >= desired)
        desired_files = sorted(desired_files.items(), key=operator.itemgetter(1))
        if len(desired_files) < 1:
            desired_files = sorted(paths.items(), key=operator.itemgetter(1))

        node.path = desired_files[0][0]

        paths_in_tree.append(node.path.lower())

        stmt = select([MemWebRootFiles.web_full_path, MemWebRootFiles.hash]) \
            .where(MemWebRootFiles.web_full_path == node.path).where(MemWebRootFiles.deleted == 0)

        files = db_session.execute(stmt).fetchall()

        stmt = select([MemFpFileFingerprint.fingerprint]).where(MemFpFileFingerprint.hash == files[0][1])
        try:
            node.file_type = json.loads(db_session.execute(stmt).first()[0])['t']
        except:
            _error("corsica.fpgen.fpc", "Error: {}".format(db_session.execute(stmt).first()[0]))

        node.files = list(set([file.hash for file in files]))
        self.used_files += node.files

        # Get all remaining files that have this web_full_path
        stmt = select([MemWebRootFiles.web_root, MemWebRootFiles.web_full_path]).distinct() \
            .where(MemWebRootFiles.web_root.in_(node.webroots)) \
            .where(MemWebRootFiles.web_full_path.like(node.path))

        result = db_session.execute(stmt).fetchall()

        webroots_with_next_path = [x.web_root for x in result if node.path == x.web_full_path]
        webroots_without_next_path = [x for x in node.webroots if x not in webroots_with_next_path]
        _debug("corsica.fpgen.fpc", "{}".format(node.path))
        _debug("corsica.fpgen.fpc", "YES {}".format(webroots_with_next_path))
        _debug("corsica.fpgen.fpc", "NO {}".format(webroots_without_next_path))
        iteration += 1
        if len(webroots_with_next_path) > 0 and len(webroots_without_next_path) > 0:
            node.left = Node(webroots=webroots_with_next_path)
            self.__process_node(node.left, db_session, iteration, paths_in_tree=paths_in_tree)

            node.right = Node(webroots=webroots_without_next_path)
            self.__process_node(node.right, db_session, iteration, paths_in_tree=paths_in_tree)
        else:
            node.path = ""
            node.fingerprints = []

        return
