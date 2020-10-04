#!/usr/bin/env python3
import json
import os
import urllib
import uuid
from multiprocessing import Process, Queue

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from builtins import KeyboardInterrupt, SystemExit
from apps.crawler.lib.device_crawler import DeviceCrawler
from database.models.crawler import CrawlerTarget, ShodanQuery, ShodanDevice
from database.base import Base
from utils.constants import CRAWL_STAT_IN_PROGRESS
from utils.constants import JOB_STATUS_SUCCESS, JOB_STATUS_STARTED, JOB_STATUS_ERROR, JOB_STATUS_WARNING
from utils.firmalyse.backend import ScanningImages, LoadingImage
from utils.log import _info, log_to_var, _error, get_log_content, _exception, _warning
from shodan import Shodan

used_loggers = ['corsica.crawler', 'corsica.crawl.dae']


file_queue = Queue()


def crawl(config, db_engine, args, job_data):
    session = sessionmaker(bind=db_engine)()
    result = {'status': -1, 'out_data': '{}'}
    targets = session.query(CrawlerTarget).filter_by(status=0)
    if targets.count() > 0:
        targets = targets.all()
        for target in targets:
            target.status = CRAWL_STAT_IN_PROGRESS
            session.commit()
        crawler = DeviceCrawler(db_engine, "{}/crawler/".format(config['common']['tmp_directory']), 3)
        crawler.crawl_threaded(targets)
        result['status'] = JOB_STATUS_SUCCESS
    else:
        result['status'] = JOB_STATUS_WARNING
        result['out_data'] = "{'error':'No Target Available'}"
    session.commit()
    return result


def get_shodan_devices(config, db_engine, args, job_data):
    api = Shodan(config['shodan']['api_key'])
    session = sessionmaker(bind=db_engine)()

    queries = session.query(ShodanQuery).filter_by(status=0)

    for q in queries:
        result = api.search(q.query)
        _info("corsica.crawl.sho", "Got {} results for query {}".format(len(result['matches']), q.id))
        devices = []
        for service in result['matches']:
            device = ShodanDevice(query_id=q.id,
                                  address=service["ip_str"],
                                  port=service["port"],
                                  information=json.dumps(service))
            try:
                session.add(device)
                session.commit()
                devices.append(device)
            except IntegrityError:
                session.rollback()

        for device in devices:
            crawler_target = CrawlerTarget(vendor="Shodan Query {}".format(q.id),
                                           device_name="{device.address}:{device.port}".format(device=device),
                                           url=json.dumps(
                                               ["http://{device.address}:{device.port}".format(device=device)]))
            session.add(crawler_target)
            session.commit()
        q.status = 1
        session.add(q)
        session.commit()


def get_file_from_url(config, db_engine, args, job_data):
    if 'url' in job_data:
        file_path = '/tmp/{}.tar.gz'.format(str(uuid.uuid1()))
        urllib.request.urlretrieve(job_data['url'], file_path)
        add_file_to_system(file_path, '/opt/data/unpacked', job_data['vendor'], job_data['device_name'],
                           job_data['version'])

def add_file_to_system(file_path, unpack_dir, vendor, device_name, version):
    fw_id, fw_hash = LoadingImage(file_path, vendor=vendor, device=device_name, version=version)
    if fw_id == -1:
        _warning("corsica.crawler", "Device from {} already in database with hash {}".format(file_path, fw_hash))
    else:
        file_queue.put([fw_id, file_path, unpack_dir])


def _worker(thread_nr):
    while True:
        fw_id, file_path, unpack_dir = file_queue.get()
        _info("corsica.crawler", "Thread {}: Scanning {} with id {}".format(thread_nr, file_path, fw_id))
        try:
            ScanningImages(fw_id)
            os.system("cd {}/{}; tar xfz *.tar.gz".format(unpack_dir, fw_id))
        except Exception as e:
            _error("corsica.crawler",
        "Scanning {target_url} with id {target_fw_id} failed: {exception}".format(target_url=file_path,
                                                                 target_fw_id=fw_id,
                                                                 exception=e))

def run(config, job_queue, args):
    db_conn_str = 'mysql+pymysql://{user}:{password}@{host}:{port}/{database}'.format(**config['mysql'])
    db_engine = create_engine(db_conn_str)
    Base.metadata.create_all(db_engine)

    _info("corsica.crawl.dae", "Daemon started")
    string_io = log_to_var(used_loggers)

    actions = {"crawl": crawl, "shodan": get_shodan_devices, "get_file_from_url": get_file_from_url}
    thread_count = 5
    _info("corsica.fpgen.par", "Starting {} threads".format(thread_count))
    for thread_nr in range(0, thread_count):
        p = Process(target=_worker, args=(thread_nr,))
        p.start()


    while True:
        db_engine = create_engine(db_conn_str)
        session = sessionmaker(bind=db_engine)()
        try:
            job = job_queue.get()
            job.status = JOB_STATUS_STARTED
            session.add(job)
            session.commit()
            try:
                job_data = json.loads(job.in_data)
                _info('corsica.fpgen.dae', 'Starting Job {} for action {}'.format(job.id, job.action))
                result = actions[job.action](config, db_engine, args, job_data)
                if not result:
                    result = {'status': JOB_STATUS_SUCCESS, 'out_data': '{}'}
                job.out_data = json.dumps(result['out_data'])
                job.status = result['status']
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
