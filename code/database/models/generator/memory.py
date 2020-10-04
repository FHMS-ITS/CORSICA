from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint, Boolean
from sqlalchemy.orm import relationship

from database.base import Base


class MemWebRoots(Base):
    __tablename__ = 'mem_web_roots'

    id = Column(Integer, primary_key=True)
    firmware = Column(ForeignKey('firmware_meta.id'), nullable=False, index=True)
    hash_web_root = Column(String(255), nullable=False)
    path_web_root = Column(String(255), nullable=False)
    path_web_root_real = Column(String(512), nullable=False)

    firmware_meta = relationship('FirmwareMeta')
    __table_args__ = (UniqueConstraint('firmware', 'hash_web_root', name='_unique_entries'), {'mysql_engine': 'Memory'})

    def __repr__(self):
        return '<WebRoot {elem.id}: {elem.firmware} {elem.path_web_root}>'.format(elem=self)


class MemWebRootFiles(Base):
    __tablename__ = 'mem_web_root_files'

    id = Column(Integer, primary_key=True)
    firmware = Column(ForeignKey('firmware_meta.id'), nullable=False, index=True)
    file_id = Column(ForeignKey('file_meta.id'), nullable=False, index=True)
    hash = Column(String(255), nullable=False)
    # web_root = Column(ForeignKey('mem_web_roots.id', onupdate="SET NULL", ondelete="SET NULL"), index=True)
    web_root = Column(Integer, nullable=False)
    filename = Column(String(255), nullable=False)
    local_path = Column(String(512), nullable=False)
    web_path = Column(String(255), nullable=False)
    web_full_path = Column(String(255), nullable=False)
    deleted = Column(Boolean(), default=False)

    firmware_meta = relationship('FirmwareMeta')
    file_meta = relationship('FileMeta')
    # mem_web_roots = relationship('MemWebRoots')

    __table_args__ = (UniqueConstraint('firmware', 'file_id', name='_unique_entries'), {'mysql_engine': 'Memory'})

    def __repr__(self):
        return '<WebRootFile {elem.id}: {elem.firmware} {elem.web_path} {elem.filename}>'.format(elem=self)


class MemWebPathCount(Base):
    __tablename__ = 'mem_web_path_count'
    __table_args__ = {'mysql_engine': 'Memory'}

    id = Column(Integer, primary_key=True)
    web_full_path = Column(String(255), nullable=False)
    hash = Column(String(255), nullable=False)
    count = Column(Integer(), nullable=False)

    def __repr__(self):
        return '<WebPathCount {elem.id}: {elem.web_full_path} {elem.count}>'.format(elem=self)


class MemFpFileFingerprint(Base):
    __tablename__ = 'mem_fp_file_fingerprint'
    __table_args__ = (UniqueConstraint('hash', 'fingerprint', name='_unique_entries'), {'mysql_engine': 'Memory'})

    id = Column(Integer, primary_key=True)
    hash = Column(String(500), nullable=False)
    fingerprint = Column(String(500), nullable=False)
    fp_hash = Column(String(70), nullable=False)
    cleaned = Column(Integer, server_default="0")
    duplicated = Column(Integer, server_default="0")
    deleted = Column(Integer, nullable=False, server_default="0")

    def __repr__(self):
        return '{elem.fingerprint}'.format(elem=self)


class MemFpFileFingerprintError(Base):
    __tablename__ = 'mem_fp_file_fingerprint_error'
    __table_args__ = {'mysql_engine': 'Memory'}

    id = Column(Integer, primary_key=True)
    hash = Column(String(500), nullable=False, unique=True)
    file = Column(String(500), nullable=False)
    error = Column(String(500), nullable=False)

    def __repr__(self):
        return '<FileFingerprintError {elem.id}: {elem.file} {elem.error}>'.format(elem=self)


class MemFpPart(Base):
    __tablename__ = 'mem_fp_parts'
    __table_args__ = {'mysql_engine': 'Memory'}

    id = Column(Integer, primary_key=True)
    web_root = Column(Integer, nullable=False)
    firm_id = Column(Integer, nullable=False)
    web_root_file_id = Column(Integer, nullable=False)
    web_full_path = Column(String(500), nullable=False)
    hash = Column(String(500), nullable=False)

    def __repr__(self):
        return '<FingerprintPart {elem.id}: {elem.hash}>'.format(elem=self)
