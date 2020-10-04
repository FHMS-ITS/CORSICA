# Firmware files can be saved in a firmalyse-compatible file structure (firmware dump, .tar)
# Contains folders titled with the firmware id and a file metadata.json
# metadata.json contains metainfo on the firmware/crawled device

# Example for individual entry in metadata.json:
# "10": {
# "id": 10,
# "devicename": "C1",
# "filename": "C1.zip",
# "size": 13230419,
# "version": "2.x.2.43",
# "vendor": "Foscam",
# "hash_sum": "6d83527bac41aa174162279c3a746c7212ca85f2b0141704dea6afd329951237"
# }

import os
import tarfile
import json
import tempfile
import shutil
from utils.log import _info


class Firmware:
    def __init__(self, fw_id, url, filename="", version="", devicename="", size="", hash_sum="", vendor=""):
        self.fw_id = fw_id
        self.url = url

        # Metadata
        if filename:
            self.filename = filename
        else:
            self.filename = url
        self.version = version
        self.devicename = devicename
        self.size = size
        self.hash_sum = hash_sum
        self.vendor = vendor

    def get_metadata(self):
        """
        Create metadata-entry for this firmware
        :return: file contents
        """

        return (self.fw_id, {
            'filename': self.filename,
            'version': self.version,
            'devicename': self.devicename,
            'size': self.size,
            'hash_sum': self.hash_sum,
            'id': self.fw_id,
            'vendor': self.vendor
        })

    @staticmethod
    def create_tarfile(src_path, dest_path, metadata):
        """
        Create tarfile that can be imported into firmalyse
        :param src_path: src path for all firmwares
        :param dest_path: destination path for fw_tarfile.tar
        :param metadata: metadata for each firmware
        :return:
        """
        _info("corsica.firmware", "Creating tar file from {}".format(src_path))
        dest_filename = dest_path + "/fw_tarfile.tar"
        result = {}
        META_FILE = "metadata.json"

        with tarfile.open(dest_filename, "w") as tar:
            for fw in metadata:
                fw_id = fw[0]
                result[str(fw_id)] = fw[1]
                source_dir = os.path.join(src_path, str(fw_id))
                tar.add(source_dir, arcname=os.path.basename(source_dir))

            tmpdir = tempfile.mkdtemp()
            meta_file = os.path.join(tmpdir, META_FILE)
            with open(meta_file, 'w') as mf:
                json.dump(result, mf)
            tar.add(meta_file, arcname=META_FILE)
            shutil.rmtree(tmpdir)
        _info("corsica.firmware", "Creating tar file successful")
