import json
from sqlalchemy.orm import sessionmaker

from apps.generator.manager.MgrFingerprintCreation import MgrFingerprintCreation
from apps.generator.manager.MgrWebRootExtraction import MgrWebRootExtraction
from apps.testsuite.testsuites.core import create
from database.models.test_suite import TSRemoteResult

from utils.log import _info, _error
from utils.selenium import SeleniumTester
from utils.utils import clear_tmp_dir


class RemoteTestSuite:
    def __init__(self, config, db_engine, args):
        self.script_path = '/srv/dev/corsica/apps/web/selenium/test_suite/remote/scripts'
        self.data_path = '{}/test_suite/remote/data/'.format(config['common']['tmp_directory'])
        self.args = args
        self.config = config
        self.db_engine = db_engine
        clear_tmp_dir(self.config, self.data_path)

    def prepare(self, execute_generation=False):

        mgr_fingerprint_creation = MgrFingerprintCreation(self.config, self.db_engine, self.args,
                                                          js_result_path=self.data_path)
        if execute_generation:
            mgr_web_root_extraction = MgrWebRootExtraction(self.config, self.db_engine, self.args)
            mgr_web_root_extraction.work()
            mgr_fingerprint_creation.work()

        else:
            mgr_fingerprint_creation.export_to_js(self.data_path)

        create(self.config, self.db_engine, self.args, self.data_path)

    def run_test(self, browser, test_ids=None):
        db_session = sessionmaker(bind=self.db_engine)()
        if test_ids is None:
            test_ids = []
        results = {}
        selenium = SeleniumTester(script_path=self.script_path, data_path=self.data_path)
        _info('corsica.tests.sel', 'Starting test suite run for {}'.format(browser))
        try:
            selenium.start_container(browser)
            for id in test_ids:
                try:
                    result = json.loads(selenium.execute(browser, file='index.html#{}'.format(id)))
                    db_session.add(TSRemoteResult(fw_id=id, browser=browser, result=json.dumps(result)))
                    db_session.commit()
                except (json.decoder.JSONDecodeError, KeyError, Exception) as e:
                    _error('corsica.fpgen.dae',
                           'Test run for ID {} in browser {} failed: {}'.format(id, browser, type(e).__name__, e))
                    db_session.add(TSRemoteResult(fw_id=id, browser=browser, result=json.dumps({})))
                    db_session.commit()
        finally:
            selenium.stop_container(browser)
        db_session.close()
        return results
