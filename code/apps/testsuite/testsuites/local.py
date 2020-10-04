import json
import os
import shutil

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from apps.generator.manager.MgrFingerprintCreation import MgrFingerprintCreation
from apps.generator.manager.MgrWebRootExtraction import MgrWebRootExtraction
from database.models.generator.memory import MemWebRoots
from utils.log import _info
from utils.selenium import SeleniumTester
from utils.utils import clear_tmp_dir


class LocalTestSuite:
    def __init__(self, config, db_engine, args):
        self.script_path = '/srv/dev/corsica/apps/web/selenium/test_suite/local/scripts'
        self.data_path = '{}/test_suite/local/data/'.format(config['common']['tmp_directory'])
        self.args = args
        self.config = config
        self.db_engine = db_engine

        clear_tmp_dir(self.config, self.data_path)
        clear_tmp_dir(self.config, '{}/files/'.format(self.data_path))

    def prepare(self, execute_generation=False):
        db_session = sessionmaker(bind=self.db_engine)()
        stmt = select([MemWebRoots.id, MemWebRoots.path_web_root_real])
        web_roots = db_session.execute(stmt).fetchall()
        _info('corsica.tests.pre', 'Copying files to data dir')
        for web_root in web_roots:
            shutil.copytree(web_root.path_web_root_real, '{}/files/{}/'.format(self.data_path, web_root.id))
        os.system('chmod -R u+rwX,go+rX,go-w {}/files'.format(self.data_path))

        mgr_fingerprint_creation = MgrFingerprintCreation(self.config, self.db_engine, self.args,
                                                          js_result_path=self.data_path)
        if execute_generation:
            mgr_web_root_extraction = MgrWebRootExtraction(self.config, self.db_engine, self.args)
            mgr_web_root_extraction.work()
            mgr_fingerprint_creation.work()
        else:
            mgr_fingerprint_creation.export_to_js(self.data_path)
        db_session.close()

    def run_test(self, browser):
        selenium = SeleniumTester(script_path=self.script_path, data_path=self.data_path)
        _info('corsica.tests.sel', 'Starting test suite run for {}'.format(browser))
        return json.loads(selenium.run(browser))
