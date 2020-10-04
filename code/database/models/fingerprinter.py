import datetime
from sqlalchemy import Column, Integer, String, DateTime, UniqueConstraint, Text
from sqlalchemy.dialects.mysql import LONGTEXT

from database.base import Base


class FingerprinterEntry(Base):
    __tablename__ = 'corsica_fingerprinter'

    id = Column(Integer, primary_key=True)
    status = Column(Integer, nullable=False, default=0)
    creation = Column(DateTime, default=datetime.datetime.utcnow)
    browser = Column(String(250), nullable=False, default="")
    url = Column(String(250), nullable=False, default="")
    result = Column(LONGTEXT, nullable=False, default="")

    def __repr__(self):
        return '<Fingerprinter {fingerprinter.id}: {fingerprinter.status} {fingerprinter.url}: {fingerprinter.result}>'.format(
            fingerprinter=self)
