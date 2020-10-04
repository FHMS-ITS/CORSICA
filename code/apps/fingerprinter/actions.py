import json
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from apps.fingerprinter.fingerprinter.real import Fingerprinter
from apps.fingerprinter.fingerprinter.docker import Fingerprinter as Docker_Fingerprinter

import pymysql
import warnings

from database.models.firmalyse import FirmwareMeta
from database.models.generator.persistant import WebRoots, WebRootFiles, FpFileFingerprint
from utils.Parallelizer import Parallelizer
from utils.log import _info

warnings.filterwarnings('ignore', category=pymysql.Warning)


def run_fingerprinter(config, db_engine, args):
    fingerprinter = Fingerprinter(config, db_engine, args)
    fingerprinter.prepare(False)
    allowed_browsers = [x.strip() for x in config['common']['allowed_browsers'].split(",")]
    result = {}
    browser = None
    if 'browser' in args:
        if args['browser'] in allowed_browsers:
            browser = args['browser']
        else:
            raise Exception("Browser {} not supported".format(args['browser']))

    if browser:
        result[browser] = fingerprinter.run(args['browser'], args['urls'] if 'urls' in args else [])
    else:
        for browser in allowed_browsers:
            result[browser] = fingerprinter.run(browser, args['urls'] if 'urls' in args else [])
    return result



def run_docker_fingerprinter(config, db_engine, args):
    fingerprinter = Docker_Fingerprinter(config, db_engine, args)
    fingerprinter.prepare(False)
    allowed_browsers = [x.strip() for x in config['common']['allowed_browsers'].split(",")]
    result = {}
    browser = None
    if 'browser' in args:
        if args['browser'] in allowed_browsers:
            browser = args['browser']
        else:
            raise Exception("Browser {} not supported".format(args['browser']))

    if browser:
        result[browser] = fingerprinter.run(args['browser'], args['ids'] if 'ids' in args else [])
    else:
        for browser in allowed_browsers:
            result[browser] = fingerprinter.run(browser, args['ids'] if 'ids' in args else [])
    return result




def run_plugins(config, db_engine, args):
    result = {}
    db_session = sessionmaker(bind=db_engine)()
    plugins = [x[0] for x in db_session.execute(select([FirmwareMeta.devicename]).distinct())]
    _info("corsica.fprin.dae", "Starting plugin process for {} Plugins".format(len(plugins)))
    res = Parallelizer(__worker_plugins, int(config['generator']['thread_count']), config).work(plugins)
    _info("corsica.fprin.dae", "Workers returned with {} Elements".format(len(res)))
    for elem in res:
        result[elem['plugin']] = elem['result']
    _info("corsica.fprin.dae", "Getting a Result of {} Plugins".format(len(result)))
    json.dump(result, open("/tmp/corsica/plugins.json", "w"))

def __worker_plugins(plugin, db_session):
    res = {}
    stmt = select([WebRoots.id]).where(WebRoots.id == FirmwareMeta.id).where(FirmwareMeta.devicename==plugin)
    web_roots = [x[0] for x in db_session.execute(stmt)]
    fingerprints = {}
    for web_root in web_roots:
        stmt = select([FpFileFingerprint.fp_hash.label("fp_hash")]) \
            .where(WebRootFiles.web_root == web_root) \
            .where(FpFileFingerprint.deleted == 0)\
            .where(FpFileFingerprint.hash == WebRootFiles.hash)
        fingerprints[web_root] = [x[0] for x in db_session.execute(stmt).fetchall()]

    for web_root in fingerprints:
        res[web_root] = {}
        for x in [x for x in fingerprints.keys() if x != web_root]:
            res[web_root][x] = [y for y in fingerprints[web_root] if y not in fingerprints[x]]
    return {'plugin': plugin, 'result': res}

