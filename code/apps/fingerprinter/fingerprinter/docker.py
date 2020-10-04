import time
import uuid

import docker
from docker.errors import APIError

from apps.generator.manager.MgrFingerprintCreation import MgrFingerprintCreation
from apps.generator.manager.MgrWebRootExtraction import MgrWebRootExtraction
from database.models.firmalyse import FirmwareMeta
from database.models.generator.persistant import WebRoots
from database.models.test_suite import TSRemoteResult
from utils.docker import pull_image, get_images_tags

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
        _info('corsica.fprin.sel', 'IDs{}'.format(ids))
        query = db_session.query(FirmwareMeta).filter(FirmwareMeta.id.in_(ids))

        firmwares = query.all()
        _info('corsica.fprin.sel', 'Firmwares{}'.format(firmwares))
        if len(firmwares) == 0:
            _info('corsica.fprin.sel', 'No devices to fingerprint for {}'.format(browser))
            return results

        selenium = SeleniumTester(script_path=self.script_path, data_path=self.data_path)
        try:
            selenium.start_container(browser)
            uid = str(uuid.uuid1()).split("-")[0]
            container_db = docker.from_env().containers.create(
                image='{}:{}'.format("mariadb", "latest"),
                name="fp_db_{}".format(uid),
                environment={"MYSQL_ROOT_PASSWORD": "test", "MYSQL_USER": "test", "MYSQL_PASSWORD":"test", "MYSQL_DATABASE": "test"},
                network='corsica-network',
            )
            container_db.start()
            time.sleep(5)
            for firmware in firmwares:
                container = None
                try:
                    container = self.prepare_docker(firmware,container_db)
                    _info('corsica.fprin.sel', 'Started container {}'.format(container.name))

                    if container:
                        time.sleep(5)
                        container_data = docker.APIClient().inspect_container(container.name)
                        ip_address = container_data['NetworkSettings']['Networks']['corsica-network']['IPAddress']
                        result = json.loads(
                            selenium.execute(browser, file='index.html#http://{}'.format(ip_address), show_errors=True))

                        _info('corsica.fprin.dae', 'Result: {}'.format(result))
                        result_data = {'true': [], 'false': [], 'device_status': {'online': [firmware.id], 'offline': [0]}}
                        web_roots = [x.id for x in db_session.query(WebRoots).filter(WebRoots.firmware == firmware.id).all()]

                        for x in result['web_roots']:
                            if x in web_roots:
                                result_data['true'].append(x)
                            else:
                                result_data['false'].append(x)

                        db_session.add(TSRemoteResult(fw_id=firmware.id, browser=browser, result=json.dumps(result_data)))
                        db_session.commit()
                    else:
                        _error('corsica.fprin.dae',
                           'Kein Image gefunden für {}:{}'.format(firmware.device_name, firmware.version))
                except (json.decoder.JSONDecodeError, KeyError, Exception) as e:
                    _error('corsica.fprin.dae',
                           'Fingerprinting for browser {} failed: {} {}'.format(browser, type(e).__name__, e))
                finally:
                    if container:
                        try:
                            container.kill()
                            #container.remove()
                        except APIError as e:
                            _error('corsica.fprin.dae', 'Container {} not running anymore: {}'.format(type(e).__name__, e))

        finally:
            selenium.stop_container(browser)

        db_session.close()
        return results

    def prepare_docker(self, firmware, container_db):
        container_data = docker.APIClient().inspect_container(container_db.name)
        db_ip_address = container_data['NetworkSettings']['Networks']['corsica-network']['IPAddress']
        _info('corsica.fprin.sel', 'DB Container IP: {}'.format(db_ip_address))
        image = firmware.vendor.lower()
        version = firmware.version

        pull_image(image.lower().strip(),version.strip())

        uid = str(uuid.uuid1()).split("-")[0]

        container = docker.from_env().containers.create(
            image='{}:{}'.format(image,version),
            name="fingerprinter_{}".format(uid),
            environment={"WORDPRESS_DB_HOST":db_ip_address, "MYSQL_PORT_3306_TCP":db_ip_address, "WORDPRESS_DB_PASSWORD":"test"},
            network='corsica-network',
        )
        container.start()
        return container
