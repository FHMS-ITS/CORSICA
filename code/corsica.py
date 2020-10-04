#!/usr/bin/env python3

import configparser
import os

import sys

import logging
from time import sleep

from sqlalchemy import create_engine, event, exc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from apps.crawler import daemon as crawler_daemon
from apps.generator import daemon as generator_daemon
from apps.testsuite import daemon as testsuite_daemon
from apps.fingerprinter import daemon as fingerprinter_daemon
from apps.web import daemon as web_daemon
from database.models.crawler import *
from database.models.firmalyse import *
from database.models.generator.memory import *
from database.models.generator.persistant import *

from database.models.core import *
from database.models.fingerprinter import *

from utils import log
from multiprocessing import Process, Queue

from utils.constants import JOB_STATUS_CREATED
from utils.log import _info, _error, _debug

import pymysql
import warnings

warnings.filterwarnings('ignore', category=pymysql.Warning)

config = configparser.ConfigParser()
config.read("/etc/corsica/config.ini")

db_conn_str = 'mysql+pymysql://{user}:{password}@{host}:{port}/{database}'.format(**config['mysql'])
engine = create_engine(db_conn_str, pool_recycle=60)
Base.metadata.create_all(engine)

log_path = "{log_path}".format(log_path=config['logging']['log_path'])
log.init_logging(logging._nameToLevel[config['logging']['level']], log_path)

services = {'crawler': crawler_daemon, 'generator': generator_daemon, 'test_suite': testsuite_daemon,
            'fingerprinter': fingerprinter_daemon}

processes = {}
job_queues = {}

try:
    for service in services:
        job_queues[service] = Queue()
        processes[service] = Process(target=services[service].run, args=(config, job_queues[service], None))
        _info('corsica.daemon', 'Starting {}'.format(service))
        processes[service].start()

    while True:
        engine = create_engine(db_conn_str, pool_timeout=20, pool_recycle=299, pool_pre_ping=True)
        session = sessionmaker(bind=engine)()
        job_queue_objects = session.query(JobQueue).filter_by(status=0)
        if job_queue_objects.count() > 0:
            jobs = job_queue_objects.all()
            for job in jobs:
                if job.service in services:
                    job.status = JOB_STATUS_CREATED
                    session.commit()
                    job_queues[job.service].put(job)
                else:
                    _error('corsica.daemon', 'Failed to add Job to Queue. Service {} not found'.format(job.service))
                    job.status = -1
                    job.save()
        else:
            session.commit()
            sleep(5)

except (KeyboardInterrupt, SystemExit):
    sys.exit()
