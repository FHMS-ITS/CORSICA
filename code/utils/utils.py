import base64
import os
import shutil
import sys
import zlib

from sqlalchemy import select

from database.models.core import JavaScriptValue
from utils.log import _info, _warning, _error




def clear_tmp_dir(config, directory):
    if not directory.startswith("/"):
        directory = '{}/{}'.format(config['common']['tmp_directory'], directory)
    try:
        shutil.rmtree(directory)
    except FileNotFoundError:
        pass

    try:
        os.makedirs(directory)
    except FileExistsError:
        pass


def chunks(lst, chnk_size):
    for i in range(0, len(lst), chnk_size):
        yield lst[i:i+chnk_size]

def get_main_script_path():
    return os.path.abspath(os.path.dirname(sys.argv[0]))


# ToDo: Pfade anpassen, da aus dem Docker raus aber auf dem Host-System
def convert_path_to_absolute_if_relative(path):
    if not path.startswith("/"):
        path = '{}/{}'.format(get_main_script_path(), path)
    return path


def jsv_get_latest_javascript_value_by_group(db_session, name):
    jsv = db_session.execute(select([JavaScriptValue.value]).where(JavaScriptValue.name == name).order_by(
        JavaScriptValue.created.desc())).first()[0]
    return jsv


def jsv_get_latest_javascript_value(db_session, name):
    jsv = db_session.execute(select([JavaScriptValue.value]).where(JavaScriptValue.name == name).order_by(
        JavaScriptValue.created.desc())).first()[0]
    return jsv


def jsv_save_javascript_value(db_session, name, value, group_id=""):
    jsv = JavaScriptValue(name=name, value=value, group_id=group_id, compressed=False)
    db_session.add(jsv)
    db_session.commit()


def add_file_to_system(file_path, unpack_dir, vendor, device_name, version):
    from utils.firmalyse.backend import LoadingImage, ScanningImages
    fw_id, fw_hash = LoadingImage(file_path, vendor=vendor, device=device_name, version=version)
    ret = {"fw_id": fw_id, "fw_hash": fw_hash}
    if fw_id == -1:
        _warning("corsica.crawler", "Device from {} already in database with hash {}".format(file_path, fw_hash))
    else:
        _info("corsica.crawler", "Scanning {} with id {}".format(file_path, ret['fw_id']))
        try:
            ScanningImages(fw_id)
            os.system("cd {}/{}; tar xfz *.tar.gz".format(unpack_dir, fw_id))
        except Exception as e:
            _error("corsica.crawler",
                   "Scanning {target_url} with id {target_fw_id} failed: {exception}".format(target_url=file_path,
                                                                                             target_fw_id=ret['fw_id'],
                                                                                             exception=e))
            return
