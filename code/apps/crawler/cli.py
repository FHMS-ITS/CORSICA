#!/usr/bin/env python3

import json
from urllib.parse import urlparse

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from database.models.core import JobQueue
from database.models.firmalyse import FirmwareMeta
from utils.log import _info, _error, _warning
from database.models.crawler import CrawlerTarget, TestDevice
from beautifultable import BeautifulTable
from utils.constants import LANG


def add_target(session, args):
    if None in [args.target, args.vendor, args.device_name] and not args.json_file:
        _error("corsica.crawler", "Missing required argument: -t TARGET -v VENDOR -n DEVICE_NAME")
        return
    if args.json_file:
        data = json.load(open(args.json_file))
        for elem in data:
            crawler_target = CrawlerTarget(url=elem['ip_address'],
                                           status=0,
                                           vendor=elem['vendor'],
                                           device_name=elem['device_name']
                                           )

            session.add(crawler_target)
        _info("corsica.crawler", "Added {} Devices".format(len(data)))
        session.commit()
    else:
        crawler_target = CrawlerTarget(url=json.dumps([args.target]),
                                       status=0,
                                       vendor=args.vendor,
                                       device_name=args.device_name
                                       )

        session.add(crawler_target)
        session.commit()
        _info("corsica.crawler", "Device (Target: {}) was created".format(crawler_target.url))

    job = JobQueue()
    job.service = "crawler"
    job.action = "run"
    job.in_data = "{}"
    session.add(job)
    session.commit()


def add_test_device(session, args):
    if None in [args.test_devices, args.fw_id]:
        _error("corsica.crawler", "Missing required argument: -f FW_ID -d TEST_DEVICES")
        return

    if not session.query(FirmwareMeta).filter_by(id=args.fw_id).count():
        _error("corsica.crawler", "No Crawler for Firmware ID {}".format(args.fw_id))
        return
    device_count = 0
    for device in args.test_devices:
        port = 80
        uri = urlparse(device)
        if not uri.hostname:
            uri = urlparse("//{}".format(device))

        if uri.scheme == "https":
            port = 443
        if uri.port:
            port = uri.port

        try:
            session.add(TestDevice(fw_id=args.fw_id, address=uri.hostname, port=port))
            session.commit()
            device_count += 1
        except IntegrityError:
            session.rollback()
            _warning("corsica.crawler", "Device {} for fw_id {} already exists".format(device, args.fw_id))

    _info("corsica.crawler", "Added {} devices to testdevices".format(device_count))


def show_devices(session, args):
    table = BeautifulTable(max_width=100)
    table.column_headers = ["ID", "Status", "FW_ID", "Vendor", "Name", "URL"]
    for target in session.query(CrawlerTarget).all():
        table.append_row(
            [target.id, LANG["CRAWLER"]["STATUS"][target.status], target.fw_id, target.vendor, target.device_name,
             target.url])
    print(table)


def run(config, engine, args):
    session = sessionmaker(bind=engine)()
    actions = {"add": add_target, "show": show_devices, "testdevice": add_test_device}

    if args.action in actions:
        actions[args.action](session, args)
    else:
        print("No action defined")
