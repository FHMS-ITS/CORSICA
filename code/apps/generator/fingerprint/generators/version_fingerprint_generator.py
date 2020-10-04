import json

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from database.models.firmalyse import FirmwareMeta
from database.models.generator.memory import MemWebRoots, MemWebRootFiles, MemWebPathCount, MemFpFileFingerprint
from utils.log import _error, _exception
from utils.utils import jsv_save_javascript_value


# ToDo: Add Used Files
class VersionFingerprintGenerator:
    def __init__(self, config, db_engine, args):
        self.args = args
        self.config = config
        self.db_engine = db_engine
        self.thread_count = int(self.config['generator']['thread_count'])

    def run(self):
        db_session = sessionmaker(bind=self.db_engine)()
        firmware = db_session.execute(select([FirmwareMeta.id, FirmwareMeta.vendor, FirmwareMeta.devicename, FirmwareMeta.version]).order_by(FirmwareMeta.vendor, FirmwareMeta.devicename)).fetchall()
        plugins = {}
        used_files = []
        fingerprints = {}
        for firm in firmware:
            if firm.vendor in plugins:
                if firm.devicename in plugins[firm.vendor]:
                    plugins[firm.vendor][firm.devicename].append(firm)
                else:
                    plugins[firm.vendor][firm.devicename] = [firm]
            else:
                plugins[firm.vendor] = {firm.devicename: [firm]}

        for vendor in plugins:
            fingerprints[vendor] = {}
            for plugin in plugins[vendor]:
                res = self.__generate_fingerprint_for_plugin(db_session, plugins[vendor][plugin])
                fingerprints[vendor][plugin] = res[0]
                used_files += res[1]

        print(fingerprints)
        return used_files

    def __generate_fingerprint_for_plugin(self, db_session, versions):
        used_files = []
        res = {}
        for version in versions:
            web_root = db_session.execute(select([MemWebRoots.id]).where(MemWebRoots.firmware == version['id'])).first()

            stmt = select([MemWebRootFiles, MemWebPathCount.count.label('count')]) \
                .where(MemWebRootFiles.deleted == 0) \
                .where(MemWebRootFiles.web_root == web_root.id) \
                .where(MemWebPathCount.hash == MemWebRootFiles.hash) \
                .where(MemWebPathCount.web_full_path == MemWebRootFiles.web_full_path).order_by('count')
            files = db_session.execute(stmt).fetchall()

            stmt = select([MemFpFileFingerprint.fingerprint]).where(MemFpFileFingerprint.hash == files[0].hash)
            file_type = ""
            try:
                file_type = json.loads(db_session.execute(stmt).first()[0])['t']
            except Exception as e:
                _error("corsica.fpgen.fpc", "Error: {}".format(db_session.execute(stmt).first()[0]))
                _exception("corsica.fpgen.fpc", e)

            res[web_root.id] = [{'path': file.web_full_path, 'type': file_type, 'hash': file.hash} for file in
                                   files[:3 if len(files) >= 3 else len(files)]]

            used_files += [file.hash for file in files[:3 if len(files) >= 3 else len(files)]]


        return res, used_files

