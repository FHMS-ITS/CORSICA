import datetime
from sqlalchemy import Column, Integer, String, DateTime, UniqueConstraint, Text
from sqlalchemy.dialects.mysql import LONGTEXT

from database.base import Base


class CrawlerTarget(Base):
    __tablename__ = 'corsica_crawler_targets'

    id = Column(Integer, primary_key=True)
    status = Column(Integer, nullable=False, default=0)
    creation = Column(DateTime, default=datetime.datetime.utcnow)
    fw_id = Column(Integer, default=-1)
    fw_hash = Column(String(250), nullable=False, default="")
    url = Column(String(250), nullable=False)
    vendor = Column(String(250), nullable=False)
    device_name = Column(String(250), nullable=False)

    __table_args__ = (UniqueConstraint('url', name='_unique_entries'),)

    def __repr__(self):
        return '<TestDevice {dev.id}: {dev.vendor} {dev.device_name}>'.format(dev=self)


class TestDevice(Base):
    __tablename__ = 'corsica_test_devices'

    id = Column(Integer, primary_key=True)
    fw_id = Column(Integer, nullable=False)
    scheme = Column(String(250), nullable=False, server_default="http://")
    address = Column(String(250), nullable=False)
    port = Column(Integer, nullable=False, default=80)

    __table_args__ = (UniqueConstraint('fw_id', 'address', 'port', name='_unique_entries'),)

    def __repr__(self):
        return '<TestDevice {dev.id}: {dev.fw_id} {dev.address}:{dev.port}>'.format(dev=self)


class ShodanQuery(Base):
    __tablename__ = 'shodan_queries'

    id = Column(Integer, primary_key=True)
    status = Column(Integer, nullable=False, default=0)
    query = Column(String(250), nullable=False)

    __table_args__ = (UniqueConstraint('query', name='_unique_entries'),)

    def __repr__(self):
        return '<ShodanQuery {query.id}: {query.test_case_id} {query.query}>'.format(query=self)


class ShodanDevice(Base):
    __tablename__ = 'shodan_devices'

    id = Column(Integer, primary_key=True)
    query_id = Column(Integer, nullable=False)
    address = Column(String(250), nullable=False)
    port = Column(Integer, nullable=False)
    information = Column(LONGTEXT, nullable=False)

    __table_args__ = (UniqueConstraint('address', 'port', name='_unique_entries'),)

    def __repr__(self):
        return '<ShodanDevice {dev.id}: {dev.address}:{dev.port}; Query:  {dev.query_id}>'.format(dev=self)
