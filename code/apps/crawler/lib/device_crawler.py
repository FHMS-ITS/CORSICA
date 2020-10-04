#!/usr/bin/env python3

import json
import os
import traceback
import uuid
import docker
from shutil import rmtree
from builtins import len, str, FileExistsError, Exception

from urllib.parse import urlparse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from database.models.crawler import TestDevice, CrawlerTarget
from utils.Parallelizer import Parallelizer
from utils.constants import *
from utils.docker import build_docker
from utils.log import _info, _warning, _error
from utils.firmalyse.backend import LoadingImage, ScanningImages


class DeviceCrawler:
    def __init__(self, db_engine, path, depth=5, crawler_uuid=str(uuid.uuid1())):
        _info("corsica.crawler", "DeviceCrawler initiated with (path: {}, depth: {} )".format(path, depth))
        self.fw_id = 1
        self.firmwares = []
        self.db_engine = db_engine
        self.crawler_uuid = crawler_uuid
        self.depth = depth
        self.unpack_dir = '/opt/data/unpacked'
        self.path_crawler = "{}/{}".format(path, crawler_uuid)
        self.__create_path()
        self.thread_count = 10

        self.docker_client = docker.from_env()
        build_docker("corsica-crawler", os.path.dirname(os.path.realpath(__file__)))

    def crawl_threaded(self, targets):
        _info("corsica.crawler", "Start crawling {} urls".format(len(targets)))
        target_ids = []
        for target in targets:
            target_ids.append(target.id)
        Parallelizer(self.crawl, self.thread_count).work(target_ids)
        self.__cleanup()

    def crawl(self, target_id):
        """
        Create firmware object and crawl firmware url
        :param target_id: target to crawl
        :return:
        """
        session = sessionmaker(bind=self.db_engine)()
        target = session.query(CrawlerTarget).filter_by(id=target_id).first()
        target_urls = json.loads(target.url)
        _info("corsica.crawler", "Processing {}".format(target_urls[0]))

        file_path = self.__download(target)
        if target.status < 0:
            _warning("corsica.crawler", "File Path for {} was empty".format(target_urls[0]))
            return
        fw_id, fw_hash = LoadingImage(file_path, vendor=target.vendor, device=target.device_name)
        target.fw_id = fw_id
        target.fw_hash = fw_hash
        target.status = CRAWL_STAT_FIRM_CREATED
        session.commit()
        if fw_id == -1:
            _warning("corsica.crawler", "Device from {} already in database with hash {}".format(target_urls[0], fw_hash))
        else:
            _info("corsica.crawler", "Scanning {} with id {}".format(target_urls[0], target.fw_id))
            try:
                ScanningImages(fw_id)
                os.system("cd {}/{}; tar xfz *.tar.gz".format(self.unpack_dir, fw_id))
            except Exception as e:
                _error("corsica.crawler", "Scanning {target_url} with id {target_fw_id} failed: {exception}".format(
                    target_url=target_urls[0], target_fw_id=target.fw_id, exception=e))
                _error('corsica.crawler', '{}'.format(traceback.format_exc()))
                target.status = CRAWL_STAT_ERR_EMPTY_RES
                session.commit()
                return
        target.status = CRAWL_STAT_FINISHED
        test_devices = target_urls
        if len(target_urls) > 1:
            test_devices = target_urls[1:]

        for url in test_devices:
            port = 80
            uri = urlparse(url)
            if not uri.hostname:
                uri = urlparse("//{}".format(url))

            if uri.scheme == "https":
                port = 443
            if uri.port:
                port = uri.port

            try:
                session.add(TestDevice(fw_id=target.fw_id, address=uri.hostname, port=port))
                session.commit()
            except IntegrityError:
                session.rollback()
                _warning("corsica.crawler", "Device {} for fw_id {} already exists".format(url, target.fw_id))

        session.commit()

        _info("corsica.crawler", "Finished Device {}".format(target_urls[0]))
        return {}

    def __download(self, target):
        target_urls = json.loads(target.url)
        uid = str(uuid.uuid1()).split("-")[0]
        uri = urlparse(target_urls[0], "http")
        if uri.netloc == "":
            uri = urlparse("//{}".format(target_urls[0]), "http")

        path = "{}/{}/".format(self.path_crawler, uid)
        _info("corsica.crawler", "Starting with path {}".format(path))
        c = self.docker_client.containers.create(image="corsica-crawler:latest",
                                                 name="crawler_{}".format(uid),
                                                 volumes={path: {"bind": "/crawler", "mode": "rw"}},
                                                 command="{uri.hostname} {uri.scheme}://{uri.netloc}/".format(uri=uri)
                                                 )
        _info("corsica.crawler", "Starting Container crawler_{}".format(uid))
        c.start()

        try:
            c.wait()
            target.status = CRAWL_STAT_CRAWL_SUCCESS
        except Exception as e:
            _warning("corsica.crawler", "Killed Container crawler_{} after timeout with error {}".format(uid, str(e)))
            target.status = CRAWL_STAT_ERR_TIMEOUT
            c.kill()

        c.remove()

        _info("corsica.crawler", "Destroyed Container crawler_{}".format(uid))
        return "{}/result.tar".format(path)

    def __create_path(self):
        try:
            _info("corsica.crawler", "Creating path {}".format(self.path_crawler))
            os.makedirs(self.path_crawler)
        except FileExistsError as e:
            _info("corsica.crawler", "Skipping creation of path {}: {}".format(self.path_crawler, e))

    def __cleanup(self):
        _info("corsica.crawler", "Cleaning up directory {}".format(self.path_crawler))
        # rmtree("{}/".format(self.path_crawler))
