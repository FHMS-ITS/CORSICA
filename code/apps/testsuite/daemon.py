import json
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from builtins import KeyboardInterrupt, SystemExit

from apps.generator.manager.MgrFingerprintCreation import MgrFingerprintCreation
from apps.generator.manager.MgrWebRootExtraction import MgrWebRootExtraction
from apps.testsuite.actions import run_local_testsuite, run_complete_remote_testsuite, run_single_remote_testsuite

from database.base import Base
from utils.constants import JOB_STATUS_SUCCESS, JOB_STATUS_STARTED, JOB_STATUS_ERROR
from utils.log import _info, log_to_var, _error, get_log_content, _exception

used_loggers = ['corsica.tests.dae', 'corsica.tests.erg', 'corsica.fpgen.wre', 'corsica.fpgen.fpc', 'corsica.fpgen.cln']


def run(config, job_queue, args):
    db_conn_str = 'mysql+pymysql://{user}:{password}@{host}:{port}/{database}'.format(**config['mysql'])
    db_engine = create_engine(db_conn_str, pool_recycle=60)
    Base.metadata.create_all(db_engine)
    session = sessionmaker(bind=db_engine)()

    _info("corsica.tests.dae", "Daemon started")
    actions = {"local": run_local_testsuite, "remote_single": run_single_remote_testsuite,
               "remote_complete": run_complete_remote_testsuite}
    stringio = log_to_var(used_loggers)

    while True:
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
