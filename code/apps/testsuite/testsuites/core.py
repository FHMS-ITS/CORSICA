import json

from sqlalchemy.orm import sessionmaker
from database.models.crawler import TestDevice
from database.models.generator.memory import MemWebRoots
import pymysql
import warnings

from utils.log import _info
from utils.utils import jsv_save_javascript_value

warnings.filterwarnings('ignore', category=pymysql.Warning)


def create(config, db_engine, args, result_path):
    db_session = sessionmaker(bind=db_engine)()
    test_devices = db_session.query(TestDevice).all()
    res_list = {}
    for device in test_devices:
        str_dev = "{dev.scheme}{dev.address}:{dev.port}".format(dev=device)
        if device.fw_id in res_list:
            res_list[device.fw_id].append(str_dev)
        else:
            res_list[device.fw_id] = [str_dev]

    firm_web_roots = {}
    web_roots = db_session.query(MemWebRoots).all()
    for web_root in web_roots:
        if web_root.firmware in firm_web_roots:
            firm_web_roots[web_root.firmware].append(web_root.id)
        else:
            firm_web_roots[web_root.firmware] = [web_root.id]

    jsv_save_javascript_value(db_session, 'devices', json.dumps(res_list))
    jsv_save_javascript_value(db_session, 'firm_web_roots', json.dumps(firm_web_roots))
    f = open("{}/devices.js".format(result_path), "w")
    f.write("devices = {}\n\n".format(json.dumps(res_list)))
    f.write("firm_web_roots = {}\n\n".format(json.dumps(firm_web_roots)))
    f.close()
    db_session.close()
