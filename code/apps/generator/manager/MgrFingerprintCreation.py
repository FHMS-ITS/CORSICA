import uuid
from utils.log import _info

from apps.generator.fingerprint.cleaner.main import FingerprintCleaner
from apps.generator.fingerprint.generators.file_fingerprint_generator import FileFingerprintGenerator


class MgrFingerprintCreation:
    def __init__(self, config, db_engine, args):
        self.args = args
        self.config = config
        self.db_engine = db_engine
        self.uid = str(uuid.uuid1()).split("-")[0]

    def work(self):
        _info("corsica.fpgen.fpc", "Creating File Fingerprints")
        FileFingerprintGenerator(self.config, self.db_engine, self.args).run()

        _info("corsica.fpgen.fpc", "Cleaning Fingerprints")
        FingerprintCleaner(self.config, self.db_engine, self.args).clean()