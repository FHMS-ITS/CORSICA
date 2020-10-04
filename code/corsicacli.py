#!/usr/bin/env python3
import configparser
import argparse
import logging
import os
import sys
import warnings

import pymysql
from sqlalchemy import create_engine

from database.models.crawler import *
from database.models.firmalyse import *
from database.models.generator.memory import *
from database.models.generator.persistant import *
from database.models.core import *

from database.base import Base
from utils import log
from apps.crawler.cli import run as crawler_cli_run
from apps.generator.cli import run as generator_cli_run
from apps.fingerprinter.cli import run as fingerprinter_cli_run
# from apps.testsuite.cli import run as testsuite_cli_run
from apps.shodan.cli import run as shodan_cli_run


def init_crawler_parser(parser_obj):
    crawler_parser = parser_obj.add_parser('crawler')
    crawler_parser.add_argument('action', choices=['add', 'show', 'testdevice'], help='Action: Crawl target')
    crawler_parser.set_defaults(func=crawler_cli_run)

    group_add = crawler_parser.add_argument_group('New crawler target [add]')
    group_add.add_argument('-t', '--target', dest='target', help='Target URL')
    group_add.add_argument('-v', '--vendor', dest='vendor', help='Vendor')
    group_add.add_argument('-n', '--devicename', dest='device_name', help='Device Name')
    group_add.add_argument('-j', '--json_file', dest='json_file', help='JSON-File Input')

    group_test_device = crawler_parser.add_argument_group('Add Testdevices [testdevice]')
    group_test_device.add_argument('-f', '--fw_id', dest='fw_id', help='Firmware_id')
    group_test_device.add_argument('-d', dest='test_devices', action='append', help='Test Devices')


def init_import_parser(parser_obj):
    import_parser = parser_obj.add_parser('import')
    import_parser.add_argument('action', choices=['insert', 'devices'], help='Action')
    group_add = import_parser.add_argument_group('Shodan Query')
    group_add.add_argument('-q', '--query', dest='query', help='Query')
    group_add.add_argument('-c', '--count', dest='count', help='Count')
    import_parser.set_defaults(func=shodan_cli_run)


def init_generator_parser(parser_obj):
    generator_parser = parser_obj.add_parser('generator')
    generator_parser.add_argument('action', choices=['all', 'extract', 'generate', 'version_generator'], help='Action')
    generator_parser.set_defaults(func=generator_cli_run)

def init_fingerprinter_parser(parser_obj):
    generator_parser = parser_obj.add_parser('fingerprinter')
    generator_parser.add_argument('action', choices=['calculate_plugins'], help='Action')
    generator_parser.set_defaults(func=fingerprinter_cli_run)

def init_testsuite_parser(parser_obj):
    test_suite_parser = parser_obj.add_parser('testsuite')
    test_suite_parser.add_argument('action', choices=['create', 'run'], help='Action')
    # test_suite_parser.set_defaults(func=testsuite_cli_run)


parser = argparse.ArgumentParser(prog='PROG')
subparsers = parser.add_subparsers(help='sub-command help')

init_import_parser(subparsers)
init_crawler_parser(subparsers)
init_generator_parser(subparsers)
init_fingerprinter_parser(subparsers)
init_testsuite_parser(subparsers)

config = configparser.ConfigParser()
config.read('/etc/corsica/config.ini')

log.init_logging(logging._nameToLevel[config['logging']['level']], config['logging']['log_path'])
logging.getLogger('docker.utils.config').setLevel(logging.ERROR)

warnings.filterwarnings('ignore', category=pymysql.Warning)

try:
    os.makedirs(config['common']['tmp_directory'])
except FileExistsError:
    pass
except Exception as e:
    print('Error creating the temporary directory at {} with exception {}'.format(config['common']['tmp_directory'], e))
    sys.exit(1)

db_conn_str = 'mysql+pymysql://{user}:{password}@{host}:{port}/{database}'.format(**config['mysql'])
engine = create_engine(db_conn_str, pool_recycle=60)
Base.metadata.create_all(engine)
args = parser.parse_args()
if 'func' not in args:
    parser.print_help()
else:
    args.func(config, engine, args)
