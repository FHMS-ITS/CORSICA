from apps.testsuite.actions import run_local_testsuite

import pymysql
import warnings

from apps.testsuite.testsuites.core import create

warnings.filterwarnings('ignore', category=pymysql.Warning)


def create_test_suite(config, db_engine, args):
    create(config, db_engine, args, config['generator']['js_result_path'])


def run(config, db_engine, args):
    actions = {"create": create_test_suite, "run": run_local_testsuite}

    if args.action in actions:
        actions[args.action](config, db_engine, args)

    else:
        print("No action defined")
