from apps.testsuite.testsuites.local import LocalTestSuite
from apps.testsuite.testsuites.remote import RemoteTestSuite

import pymysql
import warnings

from utils.log import _info

warnings.filterwarnings('ignore', category=pymysql.Warning)


def run_local_testsuite(config, db_engine, args):
    local_test_suite = LocalTestSuite(config, db_engine, args)
    local_test_suite.prepare()
    results = local_test_suite.run_test('chrome')
    res = {'successful': [], 'not_distinct': [], 'unsuccessful': set()}
    average_requests = {'successful': [0, 0], 'unsuccessful': [0, 0]}

    for elem in results['true']:
        res['successful'].append(elem['web_root'])
        average_requests['successful'][0] += elem['request_count']
        average_requests['successful'][1] += 1

    for elem in results['false']:
        if elem['web_root'] in res['successful']:
            res['not_distinct'].append(elem['web_root'])
            res['successful'].remove(elem['web_root'])
            continue
        res['unsuccessful'].add(elem['web_root'])
        average_requests['unsuccessful'][0] += elem['request_count']
        average_requests['unsuccessful'][1] += 1

    res['not_distinct'] = list(set(res['not_distinct']))
    _info('corsica.tests.erg', 'Successful: {}. Average requests {}'.format(len(res['successful']),
                                                                          average_requests['successful'][0] /
                                                                          average_requests['successful'][1]))
    _info('corsica.tests.erg', 'Not Distinct: {}.'.format(len(res['not_distinct'])))
    _info('corsica.tests.erg', 'Unsuccessful: {}. Average requests {}. Web Roots: {}'.format(len(res['unsuccessful']),
                                                                                           average_requests[
                                                                                               'unsuccessful'][0] /
                                                                                           average_requests[
                                                                                               'unsuccessful'][1],
                                                                                           res['unsuccessful']))


def run_single_remote_testsuite(config, db_engine, args):
    test_suite = RemoteTestSuite(config, db_engine, args)
    test_suite.prepare()
    if args['browser'] in ['chrome', 'firefox']:
        result = test_suite.run_test(args['browser'], args['test_ids'])
    else:
        raise Exception("Browser {} not supported".format(args['browser']))
    return result


def run_complete_remote_testsuite(config, db_engine, args):
    pass
