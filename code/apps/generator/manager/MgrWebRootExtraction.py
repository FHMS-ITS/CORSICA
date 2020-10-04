import os

from sqlalchemy import update, func, or_, insert, delete, select
from sqlalchemy.orm import sessionmaker

from database.models.firmalyse import FirmwareMeta, FileMeta
from database.models.generator.memory import MemWebRoots, MemWebRootFiles, MemWebPathCount
from utils.log import _info

from utils.Parallelizer import Parallelizer


class MgrWebRootExtraction:
    def __init__(self, config, db_engine, args):
        self.config = config
        self.db_engine = db_engine

        self.unpack_dir = "/opt/data/unpacked/"

        self.args = args
        # self.web_root_names = ['%%/www%%', '%%/html%%', '%%/htdocs%%', '%%/web%%', '%%/wordpress%%']
        # self.web_root_names = ['%%/www%%', '%%/wordpress%%', '%%/drupal-%%', '%%/typo3_src%%']
        self.relevant_files = ['%%.js', '%%.css', '%%.jpg', '%%.png', '%%.bmp', '%%.gif', '%%.ico']
        self.avm_special_files = ['avme', '1und1', 'freenet', 'otwo', 'ewetel', 'jquery', 'kopfbalken',
                                  'browser.js']  # ToDo: Browser.js dirty hack wei location href gesetzt wird.
        self.thread_count = int(self.config['generator']['thread_count'])

    def work(self):
        db_session = sessionmaker(bind=self.db_engine)()
        _info("corsica.fpgen.wre", "Set Device Names")
        self.__set_device_names(db_session)

        _info("corsica.fpgen.wre", "Extract possible WebRoots and save them to the Database")

        self.__save_web_roots(db_session)

        _info("corsica.fpgen.wre", "Get all relevant files from WebRoots")
        web_roots = db_session.query(MemWebRoots).all()
        Parallelizer(self.__get_relevant_files, self.thread_count, self.config).work(web_roots)

        _info("corsica.fpgen.wre", "Fill Web path counting Table")
        self.__fill_counting_table(db_session)

        _info("corsica.fpgen.wre", "Delete empty WebRoots")

        self.__clean_web_roots(db_session)

        _info("corsica.fpgen.wre", "Finished extracting")
        db_session.close()

    def __set_device_names(self, db_session):
        stmt = update(FirmwareMeta) \
            .where(FirmwareMeta.devicename == 'Unknown') \
            .values(devicename=FirmwareMeta.filename)
        db_session.execute(stmt)

        for ext in ['zip', 'image', 'bin', 'img', 'tar.gz', 'rar']:
            stmt = update(FirmwareMeta) \
                .where(FirmwareMeta.devicename.like('%{}'.format(ext))) \
                .values(devicename=func.replace(FirmwareMeta.devicename, '.{}'.format(ext), ""))
            db_session.execute(stmt)

        db_session.commit()

    def __get_relevant_files(self, web_root, db_session):
        stmt = db_session.query(FileMeta) \
            .filter(FileMeta.firmware == web_root.firmware) \
            .filter(or_(
            FileMeta.real_path == '/{}'.format(web_root.path_web_root),
            FileMeta.real_path.like('/{}/%'.format(web_root.path_web_root))
        )
        )
        if web_root.firmware == 513:
            _info("corsica.fpgen.wre", stmt)
        filters = []
        for elem in self.relevant_files:
            filters.append(FileMeta.filename.like(elem))
        stmt = stmt.filter(or_(*filters))

        files = stmt.all()

        if web_root.firmware == 513:
            _info("corsica.fpgen.wre", len(files))
        for file in files:
            if any(s in file.filename for s in self.avm_special_files):
                continue
            local_path = '{}{}'.format(self.get_firmware_path(web_root.firmware), file.real_path)
            web_path = '{}/'.format(file.real_path.replace(web_root.path_web_root, "")).replace("//", "/")

            stmt = insert(MemWebRootFiles).prefix_with("IGNORE")
            stmt = stmt.values(firmware=web_root.firmware,
                               file_id=file.id,
                               web_root=web_root.id,
                               hash=file.hash_sum,
                               filename=file.filename,
                               local_path=local_path,
                               web_path=web_path,
                               web_full_path='{}/{}'.format(
                                   web_path,
                                   file.filename
                               ).replace("//", "/"),
                               )
            db_session.execute(stmt)
        db_session.commit()

    def __fill_counting_table(self, db_session):
        db_session.query(MemWebPathCount).delete()
        db_session.commit()
        select_stmt = select([MemWebRootFiles.web_full_path, MemWebRootFiles.hash, func.count().label('count')]) \
            .group_by(MemWebRootFiles.hash, MemWebRootFiles.web_full_path)
        stmt = insert(MemWebPathCount).from_select(['web_full_path', 'hash', 'count'], select_stmt)
        db_session.execute(stmt)
        db_session.commit()

    def get_firmware_path(self, firmware_id, trailing_slash=False):
        path = os.path.abspath("{}/{}".format(self.unpack_dir, firmware_id))
        return path if not trailing_slash else '{}/'.format(path)

    def __save_web_roots(self, db_session):
        for firmware in db_session.query(FirmwareMeta).all():
            for file in db_session.query(FileMeta).filter(FileMeta.firmware == firmware.id).all():
                if file.root_path != "Unknown" and len(file.root_path.split("/")) == 2:
                    path_web_root = "{}".format(file.real_path)[1:].replace("/administrator", "")
                    path_web_root_real = "{}/{}".format(self.get_firmware_path(firmware.id), path_web_root)
                    stmt = insert(MemWebRoots).prefix_with("IGNORE")
                    stmt = stmt.values(firmware=firmware.id,
                                       hash_web_root=func.md5(path_web_root),
                                       path_web_root=path_web_root,
                                       path_web_root_real=path_web_root_real
                                       )
                    db_session.execute(stmt)
                    break

    def __clean_web_roots(self, db_session):
        stmt = select([MemWebRootFiles.web_root]).distinct().where(MemWebRootFiles.deleted == 0)
        file_web_roots = [x[0] for x in db_session.execute(stmt).fetchall()]

        web_roots = db_session.query(MemWebRoots)
        for web_root in web_roots:
            if web_root.id not in file_web_roots:
                db_session.query(MemWebRoots).filter(MemWebRoots.id == web_root.id).delete()
        db_session.commit()
