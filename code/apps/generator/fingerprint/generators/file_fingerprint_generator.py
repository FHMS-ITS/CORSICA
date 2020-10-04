import hashlib
import json
import pathlib
import shutil
import uuid

from sqlalchemy.orm import sessionmaker

from utils.Parallelizer import Parallelizer
from apps.generator.fingerprint.extractors.css_extractor import CssFingerprintExtractor
from apps.generator.fingerprint.extractors.javascript_extractor import JavaScriptFingerprintExtractor
from apps.generator.fingerprint.extractors.image_extractor import ImageFingerprintExtractor
from utils.exceptions import NoFingerprintFoundException, EmptyFileException
from utils.log import _info
from database.models.generator.memory import MemWebRootFiles, MemFpFileFingerprintError, MemFpFileFingerprint
from sqlalchemy import select, insert

from utils.selenium import SeleniumTester
from utils.utils import clear_tmp_dir, chunks

"""
File Fingerprints minified

t: type
# CSS
ct: css_type
et: elem_type
en: elem_name
sa: style_attrib
sv: style_value
# JS
f: func
v: var
# IMG
w: width
h: heigt
"""


class FileFingerprintGenerator:
    def __init__(self, config, db_engine, args):
        self.args = args
        self.config = config
        self.db_engine = db_engine

        self.thread_count = int(self.config['generator']['thread_count'])

    def run(self):
        db_session = sessionmaker(bind=self.db_engine)()
        db_session.query(MemFpFileFingerprintError).delete()
        db_session.commit()
        _info("corsica.fpgen.fpc", "Getting Web Root Files without Fingerprints")

        all_files = db_session.query(MemWebRootFiles).filter_by(deleted=0).all()

        fingerprinted_files = [x.hash for x in
                               db_session.execute(select([MemFpFileFingerprint.hash]).distinct())]

        files = []
        for f in all_files:
            if f.hash not in fingerprinted_files:
                files.append(f)

        _info("corsica.fpgen.fpc", "Start Fingerprint Generation for %s Files" % (len(files)))
        Parallelizer(self.__worker, self.thread_count, self.config).work(files)

        dbs = ['fp_file_fingerprint',
               'fp_file_fingerprint_error',
               'fp_parts',
               'web_path_count',
               'web_roots',
               'web_root_files',
               ]

        for db in dbs:
            self.db_engine.execute("TRUNCATE TABLE corsica_{db};".format(db=db))
            self.db_engine.execute("INSERT corsica_{db} SELECT * FROM mem_{db};".format(db=db))

        _info("corsica.fpgen.fpc", "Start Selenium JS File Fingerprint Generation")

        #all_files = db_session.query(MemWebRootFiles).filter_by(deleted=0).all()
        js_files = [file for file in files if ".js" in file.filename]
        chunked_files = list(chunks(js_files, 25))

        Parallelizer(self.__selenium_js_file_fp_generator, self.thread_count*2, self.config).work(chunked_files)
        self.__selenium_js_file_fp_generator(None)#[file for file in files if ".js" in file.filename])
        db_session.close()

    def __selenium_js_file_fp_generator(self, files, db_session):
        uid = str(uuid.uuid1())
        _info("corsica.fpgen.fpc", "Files: {}".format(len(files)))
        if not files:
            return

        selenium_generator_data_path ="{}/js_fp_gen/{}/data/".format(self.config['common']['tmp_directory'], uid)
        clear_tmp_dir(self.config, "js_fp_gen/{}/data/".format(uid))
        clear_tmp_dir(self.config, "js_fp_gen/{}/data/files".format(uid))
        for file in files:
            stmt = select([MemWebRootFiles.local_path, MemWebRootFiles.filename]) \
                .where(MemWebRootFiles.hash == file.hash).limit(1)
            web_root_file = db_session.execute(stmt).fetchone()

            file_path = "{f.local_path}/{f.filename}".format(f=web_root_file)
            shutil.copyfile(file_path,
                            "{}/files/{}.js".format(selenium_generator_data_path, file.hash))

        # Writing the testdata into javascript file data/data.js
        f = open("{}/data.js".format(selenium_generator_data_path), "w")
        f.write("hashes = {};\n".format(json.dumps([file.hash for file in files])))
        f.close()

        selenium = SeleniumTester(script_path='/srv/dev/corsica/apps/web/selenium/generator/scripts',
                                  data_path=selenium_generator_data_path)
        _info("corsica.fpgen.fpc", "Starting JS strings generation")
        result = json.loads(selenium.run("chrome", timeout=600, show_errors=False))

        for hash_value in result:
            fp_string = json.dumps({'t': 's', 'h': result[hash_value]})
            h = hashlib.new('md5')
            h.update(fp_string.encode('utf-8'))

            stmt = insert(MemFpFileFingerprint).prefix_with("IGNORE") \
                .values(hash=hash_value, fingerprint=fp_string, fp_hash=h.hexdigest())
            db_session.execute(stmt)
        db_session.commit()

        #_info("corsica.fpgen.fpc", result)
        db_session.close()

    def __worker(self, file, db_session):
        fingerprint = None
        if ".js" in file.filename:
            extractor = JavaScriptFingerprintExtractor
        elif ".css" in file.filename:
            extractor = CssFingerprintExtractor
        else:
            extractor = ImageFingerprintExtractor

        if extractor:
            error = None
            try:
                fingerprint = extractor.create_fingerprint(file)
            except NoFingerprintFoundException:
                error = "NoFingerprintFound"
            except IOError as e:
                error = str(e)
            except EmptyFileException:
                error = "EmptyFile: %s " % file
            except Exception as e:
                error = str(e)

            if error:
                stmt = insert(MemFpFileFingerprintError).prefix_with("IGNORE") \
                    .values(hash=file.hash, error=str(error), file="{f.local_path}/{f.filename}".format(f=file))
                db_session.execute(stmt)
                db_session.commit()
                return -1

        if fingerprint is not None:
            if not isinstance(fingerprint, list):
                fingerprint = [fingerprint]

            for fp in fingerprint:
                fp_string = json.dumps(fp)
                h = hashlib.new('md5')
                h.update(fp_string.encode('utf-8'))

                stmt = insert(MemFpFileFingerprint).prefix_with("IGNORE") \
                    .values(hash=file.hash, fingerprint=fp_string, fp_hash=h.hexdigest())
                db_session.execute(stmt)
            db_session.commit()
        return file.filename
