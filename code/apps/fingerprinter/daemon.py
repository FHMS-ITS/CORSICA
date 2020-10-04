#!/usr/bin/env python3
# Python webcrawler using wget
# Used to collect accessible files for a given IP
# Variable starting point for crawling (defaults to /)
# Follow links, image tags, style directives as long as they stay on the same web page
import json
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy import create_engine
from builtins import KeyboardInterrupt, SystemExit

from apps.fingerprinter.actions import run_fingerprinter, run_docker_fingerprinter
from apps.fingerprinter.actions import run_plugins

from database.base import Base
from utils.constants import JOB_STATUS_SUCCESS, JOB_STATUS_STARTED, JOB_STATUS_ERROR
from utils.log import _info, log_to_var, _error, get_log_content, _exception

used_loggers = ['corsica.fprin.dae', 'corsica.fprin.erg', 'corsica.fpgen.wre', 'corsica.fpgen.fpc', 'corsica.fpgen.cln',
                'corsica.fprin.sel']


from sqlalchemy import exc
from sqlalchemy import event
from sqlalchemy.pool import Pool

@event.listens_for(Pool, "checkout")
def ping_connection(dbapi_connection, connection_record, connection_proxy):
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("SELECT 1")
    except:
        raise exc.DisconnectionError()
    cursor.close()

def run(config, job_queue, args):
    db_conn_str = 'mysql+pymysql://{user}:{password}@{host}:{port}/{database}'.format(**config['mysql'])
    db_engine = create_engine(db_conn_str, pool_timeout=20, pool_recycle=299, pool_pre_ping=True)
    Base.metadata.create_all(db_engine)

    _info("corsica.fprin.dae", "Daemon started")
    actions = {"run": run_fingerprinter, "calculate_plugins": run_plugins, "run_docker_fingerprinter": run_docker_fingerprinter}
    stringio = log_to_var(used_loggers)


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
                _info('corsica.tests.dae', 'Starting Job {} for action {}'.format(job.id, job.action))
                result = actions[job.action](config, db_engine, job_data)
                if not result:
                    result = []
                job.out_data = json.dumps(result)
                job.status = JOB_STATUS_SUCCESS
                session.add(job)
                session.commit()
            except (json.decoder.JSONDecodeError, KeyError, Exception) as e:
                _error('corsica.tests.dae', 'Job {} failed. {}: {}'.format(job.id, type(e).__name__, e))
                _exception('corsica.tests.dae', e)
                job.status = JOB_STATUS_ERROR
            _info('corsica.tests.dae',
                  'Finished Job {} for action {} with status {}'.format(job.id, job.action, job.status))
            log_contents = get_log_content(stringio)
            job.log = log_contents

            session.add(job)
            session.commit()

        except (KeyboardInterrupt, SystemExit):
            raise
        session.close()