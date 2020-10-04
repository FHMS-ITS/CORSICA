import datetime
from sqlalchemy import Column, Integer, DateTime, Text, String

from database.base import Base


class TSRemoteResult(Base):
    __tablename__ = 'ts_remote_results'

    id = Column(Integer, primary_key=True)
    fw_id = Column(Integer, nullable=False)
    browser = Column(String(250), nullable=False)
    date = Column(DateTime, default=datetime.datetime.utcnow)
    result = Column(Text, nullable=False)
