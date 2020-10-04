from apps.generator.manager.MgrFingerprintCreation import MgrFingerprintCreation
from apps.generator.manager.MgrWebRootExtraction import MgrWebRootExtraction

from utils.log import _error
from utils.selenium import SeleniumTester
from utils.utils import clear_tmp_dir, jsv_get_latest_javascript_value
import json

from sqlalchemy.orm import sessionmaker
from database.models.fingerprinter import FingerprinterEntry
import pymysql
import warnings

from utils.log import _info

warnings.filterwarnings('ignore', category=pymysql.Warning)


class Fingerprinter:
    def __init__(self, config, db_engine, args):
        self.script_path = '/srv/dev/corsica/apps/web/selenium/fingerprinter/scripts'
        self.data_path = '{}/fingerprinter/data/'.format(config['common']['tmp_directory'])
        self.args = args
        self.config = config
        self.db_engine = db_engine

        clear_tmp_dir(self.config, self.data_path)

    def prepare(self, execute_generation=False):
        db_session = sessionmaker(bind=self.db_engine)()
        mgr_fingerprint_creation = MgrFingerprintCreation(self.config, self.db_engine, self.args)
        if execute_generation:
            mgr_web_root_extraction = MgrWebRootExtraction(self.config, self.db_engine, self.args)
            mgr_web_root_extraction.work()
            mgr_fingerprint_creation.work()

        _info('corsica.tests.prepare', 'Exporting JavaScript')
        tree = jsv_get_latest_javascript_value(db_session, 'tree')
        file_fingerprints = jsv_get_latest_javascript_value(db_session, 'file_fingerprints')
        fine_fingerprinting_files = jsv_get_latest_javascript_value(db_session, 'fine_fingerprinting_files')
        f = open("{}/data.js".format(self.data_path), "w")
        f.write("tree = {};\n\n".format(tree))
        f.write("file_fingerprints = {};\n\n".format(file_fingerprints))
        f.write("fine_fingerprinting_files = {};\n\n".format(fine_fingerprinting_files))
        f.close()
        db_session.close()

    def run(self, browser, ids=None):
        if ids is None:
            ids = []
        db_session = sessionmaker(bind=self.db_engine)()
        results = {}

        query = db_session.query(FingerprinterEntry).filter(FingerprinterEntry.status == 0).filter(
            FingerprinterEntry.browser == browser)
        if ids:
            query = query.filter(FingerprinterEntry.id.in_(ids))

        devices = query.all()
        if len(devices) == 0:
            _info('corsica.fprin.sel', 'No devices to fingerprint for {}'.format(browser))
            return results

        selenium = SeleniumTester(script_path=self.script_path, data_path=self.data_path)
        _info('corsica.fprin.sel', 'Starting fingerprinter for {} with {} devices'.format(browser, len(devices)))
        try:
            selenium.start_container(browser)
            for device in devices:
                try:
                    device.status = 1
                    db_session.add(device)
                    db_session.commit()
                    result = json.loads(
                        selenium.execute(browser, file='index.html#{}'.format(device.url), show_errors=False))
                    device.result = json.dumps(result)
                    device.status = 5
                    db_session.add(device)
                    db_session.commit()
                except (json.decoder.JSONDecodeError, KeyError, Exception) as e:
                    _error('corsica.fpgen.dae',
                           'Fingerprinting for browser {} failed: {} {}'.format(browser, type(e).__name__, e))
                    device.status = -1
                    db_session.add(device)
                    db_session.commit()
        finally:
            selenium.stop_container(browser)

        db_session.close()
        return results
