import json
import uuid
from json import JSONDecodeError

from sqlalchemy.orm import sessionmaker

from apps.generator.fingerprint.generators.fine_fingerprint_generator import FineFingerprintGenerator
from apps.generator.fingerprint.generators.tree_generator import TreeGenerator
from database.models.generator.memory import MemFpFileFingerprint, MemWebRoots
from utils.log import _info

from apps.generator.fingerprint.cleaner.main import FingerprintCleaner
from apps.generator.fingerprint.generators.file_fingerprint_generator import FileFingerprintGenerator
from utils.utils import jsv_save_javascript_value, jsv_get_latest_javascript_value


class MgrTreeGenerator:
    def __init__(self, config, db_engine, args):
        self.args = args
        self.config = config
        self.db_engine = db_engine
        self.uid = str(uuid.uuid1()).split("-")[0]

    def work(self):
        used_files = []
        _info("corsica.fpgen.fpc", "Running Tree Generation")
        tree_generator = TreeGenerator(self.config, self.db_engine, self.args, self.uid)
        tree_generator.run()
        used_files += tree_generator.used_files

        _info("corsica.fpgen.fpc", "Running Fine Fingerprint Generation")
        used_files += FineFingerprintGenerator(self.config, self.db_engine, self.args, self.uid).run()

        _info("corsica.fpgen.fpc", "Saving file fingerprints")
        self.__save_additional_js_values(used_files)

    def __save_additional_js_values(self, used_files):
        db_session = sessionmaker(bind=self.db_engine)()
        file_fingerprints = {}

        for file_hash in list(set(used_files)):
            fingerprints = db_session.query(MemFpFileFingerprint.fingerprint).filter_by(hash=file_hash) \
                .filter_by(deleted=0).filter_by(cleaned=1).all()

            file_fingerprints[file_hash] = []
            if len(fingerprints) > 0:
                file_fingerprints[file_hash] = []
                for elem in fingerprints:
                    try:
                        file_fingerprints[file_hash].append(json.loads(elem.fingerprint))
                    except JSONDecodeError:
                        pass

        web_roots_to_firmware = {}
        for elem in db_session.query(MemWebRoots).all():
            web_roots_to_firmware[elem.id] = elem.firmware
        jsv_save_javascript_value(db_session, 'file_fingerprints', json.dumps(file_fingerprints), self.uid)
        jsv_save_javascript_value(db_session, 'web_roots_to_firmware', json.dumps(web_roots_to_firmware), self.uid)
        db_session.close()
