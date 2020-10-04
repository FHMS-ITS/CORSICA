#!/usr/bin/env python3
# Python webcrawler using wget
# Used to collect accessible files for a given IP
# Variable starting point for crawling (defaults to /)
# Follow links, image tags, style directives as long as they stay on the same web page
import json
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from builtins import KeyboardInterrupt, SystemExit

from apps.generator.fingerprint.generators.version_fingerprint_generator import VersionFingerprintGenerator
from apps.generator.manager.MgrFingerprintCreation import MgrFingerprintCreation
from apps.generator.manager.MgrWebRootExtraction import MgrWebRootExtraction
from apps.generator.manager.MgrTreeGenerator import MgrTreeGenerator

from database.base import Base
from utils.constants import JOB_STATUS_SUCCESS, JOB_STATUS_STARTED, JOB_STATUS_ERROR
from utils.log import _info, log_to_var, _error, get_log_content, _exception

used_loggers = ['corsica.fpgen.dae', 'corsica.fpgen.wre', 'corsica.fpgen.fpc', 'corsica.fpgen.cln', 'selenium']


def run_extraction(config, db_engine, args):
    mgr_web_root_extraction = MgrWebRootExtraction(config, db_engine, args)
    mgr_web_root_extraction.work()


# ToDo: Refactoring
def run_generation(config, db_engine, args):
    mgr_fingerprint_creation = MgrFingerprintCreation(config, db_engine, args)
    mgr_fingerprint_creation.work()

def run_tree(config, db_engine, args):
    mgr_tree_generator = MgrTreeGenerator(config, db_engine, args)
    mgr_tree_generator.work()

def run_version_generation(config, db_engine, args):
    mgr_version_fingerprint_creation = VersionFingerprintGenerator(config, db_engine, args)
    mgr_version_fingerprint_creation.run()

def run_without_tree(config, db_engine, args):
    run_extraction(config, db_engine, args)
    copy_dbs(db_engine, 'mem', 'corsica')
    run_generation(config, db_engine, args)

def run_all(config, db_engine, args):
    run_without_tree(db_engine, 'mem', 'corsica')
    copy_dbs(db_engine, 'mem', 'corsica')
    run_tree(config, db_engine, args)

def copy_dbs(db_engine, src, dst):
    _info("corsica.fpgen.dae", "Copy Database from {src} to {dst}".format(src=src, dst=dst))
    dbs = ['fp_file_fingerprint',
           'fp_file_fingerprint_error',
           'fp_parts',
           'web_path_count',
           'web_roots',
           'web_root_files',
           ]

    for db in dbs:
        db_engine.execute("TRUNCATE TABLE {dst}_{db};".format(db=db, src=src, dst=dst))
        db_engine.execute("INSERT {dst}_{db} SELECT * FROM {src}_{db};".format(db=db, src=src, dst=dst))


def run(config, job_queue, args):
    db_conn_str = 'mysql+pymysql://{user}:{password}@{host}:{port}/{database}'.format(**config['mysql'])
    db_engine = create_engine(db_conn_str, pool_recycle=60)
    Base.metadata.create_all(db_engine)

    _info("corsica.fpgen.dae", "Daemon started")
    actions = {"all": run_all, "all_no_tree":run_without_tree, "extract": run_extraction, "generate": run_generation, "tree": run_tree, "version_generator": run_version_generation}
    string_io = log_to_var(used_loggers)

    # ToDo: Add Exceptions for different Error Cases
    while True:
        db_engine = create_engine(db_conn_str, pool_timeout=20, pool_recycle=299, pool_pre_ping=True)
        session = sessionmaker(bind=db_engine)()
        try:
            job = job_queue.get()
            job.status = JOB_STATUS_STARTED
            session.add(job)
            session.commit()
            try:
                job_data = json.loads(job.in_data)
                _info('corsica.fpgen.dae', 'Starting Job {} for action {}'.format(job.id, job.action))

                copy_dbs(db_engine, 'corsica', 'mem')
                result = actions[job.action](config, db_engine, args)
                if not result:
                    result = []
                job.out_data = json.dumps(result)
                copy_dbs(db_engine, 'mem', 'corsica')
                job.status = JOB_STATUS_SUCCESS
            except (json.decoder.JSONDecodeError, KeyError, Exception) as e:
                _error('corsica.fpgen.dae', 'Job {} failed. {}: {}'.format(job.id, type(e).__name__, e))
                _exception('corsica.fpgen.dae', e)
                job.status = JOB_STATUS_ERROR

            _info('corsica.fpgen.dae',
                  'Finished Job {} for action {} with status {}'.format(job.id, job.action, job.status))
            log_contents = get_log_content(string_io)
            job.log = log_contents
            session.add(job)
            session.commit()

        except (KeyboardInterrupt, SystemExit):
            raise
