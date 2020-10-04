import json
import os

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from database.models.generator.memory import MemWebRoots, MemWebRootFiles, MemWebPathCount, MemFpFileFingerprint
from utils.log import _error, _info
from utils.utils import jsv_save_javascript_value


# ToDo: Add Used Files
class FineFingerprintGenerator:
    def __init__(self, config, db_engine, args, uid):
        self.args = args
        self.uid = uid
        self.config = config
        self.db_engine = db_engine
        self.thread_count = int(self.config['generator']['thread_count'])

    def run(self):
        db_session = sessionmaker(bind=self.db_engine)()
        web_roots = db_session.execute(select([MemWebRoots.id])).fetchall()
        result = {}
        used_files = []
        for web_root in web_roots:
            stmt = select([MemWebRootFiles, MemWebPathCount.count.label('count')]) \
                .where(MemWebRootFiles.deleted == 0) \
                .where(MemWebRootFiles.web_root == web_root.id) \
                .where(MemWebPathCount.hash == MemWebRootFiles.hash) \
                .where(MemWebPathCount.web_full_path == MemWebRootFiles.web_full_path).order_by('count')
            files = db_session.execute(stmt).fetchall()
            extension = os.path.splitext(files[0][5])[1] # Get File Extension
            if extension == ".css":
                file_type = "c"
            elif extension == ".js":
                file_type = "j"
            else:
                file_type="i"

            result[web_root.id] = [{'path': file.web_full_path, 'type': file_type, 'hash': file.hash} for file in
                                   files[:3 if len(files) >= 3 else len(files)]]
            used_files += [file.hash for file in files[:3 if len(files) >= 3 else len(files)]]
        jsv_save_javascript_value(db_session, 'fine_fingerprinting_files', json.dumps(result), self.uid)

        db_session.close()
        return used_files
