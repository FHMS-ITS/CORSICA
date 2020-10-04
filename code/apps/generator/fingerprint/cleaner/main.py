from sqlalchemy import update, bindparam, select, func
from sqlalchemy.orm import sessionmaker

from apps.generator.fingerprint.cleaner.selenium import SeleniumCleaner
from database.models.generator.memory import MemFpFileFingerprint, MemWebRootFiles
from utils.log import _info


class FingerprintCleaner:
    def __init__(self, config, db_engine, args):
        self.args = args
        self.config = config
        self.db_engine = db_engine

        self.file_blacklist = ['public_msg.js', '%unpack-%']

        self.hash_blacklist = []
        for elem in open("/srv/corsica/apps/generator/fingerprint/cleaner/hash_blacklist","r"):
            if elem:
                self.hash_blacklist.append(elem.strip())

        self.value_blacklist = ['0px', '0']
#        self.hash_blacklist = ['2d76f4bebb93b732631b36e540955fab5e727eb5d7e94fe14828f406cf0d820d',
#                               '3bad5d259351fbd1e1cd3deb4d44d91ae8c153ba27881c0466936645275914b1','7c7c12c7c106d523c1c3ff6916cc29384837ccf1716479715ac0f198a0f8973b','936edf8e3044720acf0046c106c0b61a34e0cbc032d8bd94b53b2320583a9a3d']
        self.web_path_blacklist = ['%/wp-content/%']

    def clean(self):

        _info("corsica.fpgen.cln", "Run blacklist cleaner")
        self.__clean_by_blacklist()
        _info("corsica.fpgen.cln", "Run duplicated cleaner")
        self.__clean_duplicated("s")
        self.__clean_duplicated("i")
        _info("corsica.fpgen.cln", "Run selenium cleaner")
        self.__clean_by_selenium()
        _info("corsica.fpgen.cln", "Run no-fingerprint cleaner")
        self.__clean_without_fingerprint()


    def __clean_duplicated(self, type):
        db_session = sessionmaker(bind=self.db_engine)()
        to_del = []
        stmt = select([MemFpFileFingerprint.fp_hash, func.count(MemFpFileFingerprint.hash)]).where(MemFpFileFingerprint.fingerprint.like('%"t": "{}"%'.format(type))).group_by(MemFpFileFingerprint.fp_hash)
        for data in db_session.execute(stmt).fetchall():
            if data[1] > 1:
                stmt = update(MemFpFileFingerprint).values(deleted=1, cleaned=1).where(MemFpFileFingerprint.fp_hash == data[0])
            else:
                stmt = update(MemFpFileFingerprint).values(deleted=0, cleaned=1).where(MemFpFileFingerprint.fp_hash == data[0])
            db_session.execute(stmt)

        db_session.commit()
        _info("corsica.fpgen.cln", to_del)

    def __clean_by_blacklist(self):
        db_session = sessionmaker(bind=self.db_engine)()
        # Delete Files standing on a blacklist defined above
        for file in self.file_blacklist:
            stmt = update(MemWebRootFiles) \
                .values(deleted=1) \
                .where(MemWebRootFiles.filename.like(file))

            db_session.execute(stmt)
        db_session.commit()

        for value in self.value_blacklist:
            stmt = update(MemFpFileFingerprint) \
                .values(deleted=1, cleaned=1) \
                .where(MemFpFileFingerprint.fingerprint.like('%"sv": "0"%'))
            db_session.execute(stmt)
        db_session.commit()

        for file_hash in self.hash_blacklist:
            stmt = update(MemWebRootFiles) \
                .values(deleted=1) \
                .where(MemWebRootFiles.hash == file_hash)
            db_session.execute(stmt)
            stmt = update(MemFpFileFingerprint) \
                .values(deleted=1, cleaned=1) \
                .where(MemFpFileFingerprint.hash == file_hash)
            db_session.execute(stmt)
        db_session.commit()

        for path in self.web_path_blacklist:
            stmt = update(MemWebRootFiles) \
                .values(deleted=1) \
                .where(MemWebRootFiles.web_path.like(path))

            db_session.execute(stmt)
        db_session.commit()

        stmt = update(MemFpFileFingerprint) \
            .values(deleted=1, cleaned=1) \
            .where(MemFpFileFingerprint.fingerprint == '{}')
        db_session.execute(stmt)
        db_session.commit()
        db_session.close()

    def __clean_by_selenium(self):
        c_css = SeleniumCleaner(self.config, self.db_engine, self.args, 'css')
        c_css.clean()
        c_js = SeleniumCleaner(self.config, self.db_engine, self.args, 'js')
        c_js.clean()

    def __clean_without_fingerprint(self):
        db_session = sessionmaker(bind=self.db_engine)()
        fingerprints = [x.hash for x in
                        db_session.query(MemFpFileFingerprint.hash).distinct().filter_by(deleted=0).all()]
        files = [x[0] for x in db_session.query(MemWebRootFiles.hash).filter_by(deleted=0).all()]
        to_delete = []
        for file_hash in files:
            if file_hash not in fingerprints:
                to_delete.append(file_hash)

        if len(to_delete) > 0:
            stmt = update(MemWebRootFiles).values(deleted=1).where(MemWebRootFiles.hash == bindparam('file_hash'))
            db_session.execute(stmt, [{'file_hash': file_hash} for file_hash in list(set(to_delete))])
            db_session.commit()
        db_session.close()
