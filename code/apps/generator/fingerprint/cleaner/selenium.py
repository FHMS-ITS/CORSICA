import json
import pathlib
import shutil
import docker

from sqlalchemy import select, update
from sqlalchemy.orm import sessionmaker

from utils.log import _info
from utils.selenium import SeleniumTester
from utils.utils import clear_tmp_dir

from database.models.generator.memory import MemFpFileFingerprint, MemWebRootFiles


class SeleniumCleaner:
    def __init__(self, config, db_engine, args, type):
        self.config = config
        self.db_engine = db_engine

        self.type = type

        self.docker_client = docker.from_env()

        self.cleaner_path = "{}/cleaner/{}/".format(config['common']['tmp_directory'], self.type)
        self.cleaner_data_path = "{}/data/".format(self.cleaner_path)

        self.browser = ["chrome"]  # ["chrome", "firefox"]

        clear_tmp_dir(self.config, "cleaner/{}/".format(self.type))
        clear_tmp_dir(self.config, "cleaner/{}/scripts".format(self.type))
        clear_tmp_dir(self.config, "cleaner/{}/data".format(self.type))
        clear_tmp_dir(self.config, "cleaner/{}/data/files".format(self.type))

    def clean(self):
        db_session = sessionmaker(bind=self.db_engine)()
        _info("corsica.fpgen.cln", "Preparing cleaner data for type {}".format(self.type))
        fingerprints = self.__generate_cleaner_data()
        if not fingerprints:
            _info("corsica.fpgen.cln", "No Fingerprints to clean for type {}".format(self.type))
            return
        fingerprints_to_clean = []
        selenium = SeleniumTester(script_path='/srv/dev/corsica/apps/web/selenium/cleaner/{}/scripts'.format(self.type),
                                  data_path=self.cleaner_data_path)
        for browser in self.browser:
            _info("corsica.fpgen.cln", "Starting clean test for type {} with browser {}".format(self.type, browser))
            num = 0
            result = json.loads(selenium.run(browser, timeout=1160, show_errors=False))
            for hash_value in result:
                num += len(result[hash_value])
                fingerprints_to_clean += result[hash_value]
            _info("corsica.fpgen.cln",
                  "Added {} fingerprints to clean list for type {} from browser {}".format(num, self.type, browser))

        fingerprints_to_clean = list(set(fingerprints_to_clean))
        _info("corsica.fpgen.cln",
              "Deleting {} fingerprints from selenium {} cleaner".format(len(fingerprints_to_clean), self.type))
        stmt = update(MemFpFileFingerprint).values(deleted=1).where(MemFpFileFingerprint.id.in_(fingerprints_to_clean))
        db_session.execute(stmt)
        stmt = update(MemFpFileFingerprint).values(cleaned=1).where(MemFpFileFingerprint.id.in_(fingerprints))
        db_session.execute(stmt)
        db_session.close()

    def __generate_cleaner_data(self):
        db_session = sessionmaker(bind=self.db_engine)()
        results = {}
        files = {}

        # Extract all fingerprints from database that are based on $type and are not deleted
        stmt = select([MemFpFileFingerprint.id, MemFpFileFingerprint.hash, MemFpFileFingerprint.fingerprint]) \
            .where(
            MemFpFileFingerprint.fingerprint.like('%"t": "{}"%'.format({'css': 'c', 'js': 'j', 'img': 'i'}[self.type]))) \
            .where(MemFpFileFingerprint.deleted == 0) \
            .where(MemFpFileFingerprint.cleaned == 0)

        fingerprints = db_session.execute(stmt).fetchall()
        if len(fingerprints) == 0:
            return False
        # Save these fingerprint into an array with the hash as key

        for element in fingerprints:
            info = {"id": element.id, "fingerprint": element.fingerprint}
            if element.hash in results:
                results[element.hash].append(info)
            else:
                results[element.hash] = [info]

        # Copy the first file in database for each hash to the directory {CSS_TARGET_PATH}/data/files/{hash}.css

        for hash_value in results:
            stmt = select([MemWebRootFiles.local_path, MemWebRootFiles.filename]) \
                .where(MemWebRootFiles.hash == hash_value).limit(1)
            web_root_file = db_session.execute(stmt).fetchone()

            file_path = "{f.local_path}/{f.filename}".format(f=web_root_file)
            shutil.copyfile(file_path,
                            "{}/files/{}{}".format(self.cleaner_data_path, hash_value, pathlib.Path(file_path).suffix))
            files[hash_value] = '{}{}'.format(hash_value, pathlib.Path(file_path).suffix)

        _info("corsica.fpgen.cln",
              "Testing {} fingerprints from selenium {} cleaner".format(len(fingerprints), self.type))
        # Writing the testdata into javascript file {CSS_TARGET_PATH}/data/data.js
        f = open("{}/data.js".format(self.cleaner_data_path), "w")
        f.write("data = {};\n".format(json.dumps(results)))
        f.write("files = {};\n".format(json.dumps(files)))
        f.close()
        db_session.close()
        return [elem.id for elem in fingerprints]
