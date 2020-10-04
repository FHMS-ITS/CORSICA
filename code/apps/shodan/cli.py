#!/usr/bin/env python3

import json

from shodan import Shodan
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from database.models.crawler import ShodanQuery, ShodanDevice


def run(config, db_engine, args):
    actions = {"insert": insert_query, "devices": get_devices}

    if args.action in actions:
        session = sessionmaker(bind=db_engine)()
        actions[args.action](config, session, args)
    else:
        print("No action defined")


def insert_query(config, session, args):
    pass


def get_devices(config, session, args):
    api = Shodan(config['shodan']['api_key'])

    queries = session.query(ShodanQuery).filter_by(test_case_id=1)

    for q in queries:
        device_count = session.query(ShodanDevice).filter_by(query_id=q.id).count()
        if not device_count:
            result = api.search(q.query)
            print(len(result['matches']))

            for service in result['matches']:
                device = ShodanDevice(query_id=q.id,
                                      address=service["ip_str"],
                                      port=service["port"],
                                      information=json.dumps(service))
                try:
                    session.add(device)
                    session.commit()
                except IntegrityError:
                    session.rollback()

        else:
            print("Devices for query {} were already added".format(q.id))
