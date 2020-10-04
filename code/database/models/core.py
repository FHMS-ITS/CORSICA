import datetime
import json

from sqlalchemy import Column, Integer, String, DateTime, Text, text
from sqlalchemy.dialects.mysql import LONGTEXT

from database.base import Base


class JobQueue(Base):
    __tablename__ = 'job_queue'

    id = Column(Integer, primary_key=True)
    service = Column(String(250), nullable=False, default="")
    action = Column(String(250), nullable=False, default="")
    creation = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(Integer, nullable=False, default=0)
    in_data = Column(LONGTEXT, nullable=False, default="{}")
    out_data = Column(LONGTEXT, nullable=False, default="{}")
    log = Column(LONGTEXT, default="")

    def __repr__(self):
        return '<JobQueue {job.id}: {job.service} {job.creation} {job.status}>'.format(job=self)


class JavaScriptValue(Base):
    __tablename__ = 'javascript_values'

    id = Column(Integer, primary_key=True)
    created = Column(DateTime, default=datetime.datetime.utcnow)
    group_id = Column(String(250), nullable=False, default="")
    name = Column(String(250), nullable=False, default="")
    value = Column(LONGTEXT, nullable=False, default="")
    compressed = Column(Integer, nullable=False, server_default="0")

    def __repr__(self):
        return '<JavaScriptValue {jsv.id}: {jsv.name} {jsv.group_id}>'.format(jsv=self)
