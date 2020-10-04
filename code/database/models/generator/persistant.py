from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint, Boolean
from sqlalchemy.orm import relationship

from database.base import Base


class WebRoots(Base):
    __tablename__ = 'corsica_web_roots'

    id = Column(Integer, primary_key=True)
    firmware = Column(ForeignKey('firmware_meta.id'), nullable=False, index=True)
    hash_web_root = Column(String(255), nullable=False)
    path_web_root = Column(String(255), nullable=False)
    path_web_root_real = Column(String(512), nullable=False)

    firmware_meta = relationship('FirmwareMeta')
    __table_args__ = (UniqueConstraint('firmware', 'hash_web_root', name='_unique_entries'),)

    def __repr__(self):
        return '<WebRoot {elem.id}: {elem.firmware} {elem.path_web_root}>'.format(elem=self)


class WebRootFiles(Base):
    __tablename__ = 'corsica_web_root_files'

    id = Column(Integer, primary_key=True)
    firmware = Column(ForeignKey('firmware_meta.id'), nullable=False, index=True)
    file_id = Column(ForeignKey('file_meta.id'), nullable=False, index=True)
    hash = Column(String(255), nullable=False)
    # web_root = Column(ForeignKey('corsica_web_roots.id', onupdate="SET NULL", ondelete="SET NULL"), index=True)
    web_root = Column(Integer, nullable=False)
    filename = Column(String(255), nullable=False)
    local_path = Column(String(512), nullable=False)
    web_path = Column(String(255), nullable=False)
    web_full_path = Column(String(255), nullable=False)
    deleted = Column(Boolean(), default=False)

    firmware_meta = relationship('FirmwareMeta')
    file_meta = relationship('FileMeta')
    # corsica_web_roots = relationship('WebRoots')

    __table_args__ = (UniqueConstraint('firmware', 'file_id', name='_unique_entries'),)

    def __repr__(self):
        return '<WebRootFile {elem.id}: {elem.firmware} {elem.web_path}>'.format(elem=self)


class WebPathCount(Base):
    __tablename__ = 'corsica_web_path_count'

    id = Column(Integer, primary_key=True)
    web_full_path = Column(String(255), nullable=False)
    hash = Column(String(255), nullable=False)
    count = Column(Integer(), nullable=False)

    def __repr__(self):
        return '<WebPathCount {elem.id}: {elem.web_full_path} {elem.count}>'.format(elem=self)


class FpFileFingerprint(Base):
    __tablename__ = 'corsica_fp_file_fingerprint'
    __table_args__ = (UniqueConstraint('hash', 'fingerprint', name='_unique_entries'),)

    id = Column(Integer, primary_key=True)
    hash = Column(String(500), nullable=False)
    fingerprint = Column(String(500), nullable=False)
    fp_hash = Column(String(70), nullable=False)
    cleaned = Column(Integer, server_default="0")
    duplicated = Column(Integer, server_default="0")
    deleted = Column(Integer, nullable=False, server_default="0")

    def __repr__(self):
        return '<FileFingerprint {elem.id}: {elem.fingerprint}>'.format(elem=self)


class FpFileFingerprintError(Base):
    __tablename__ = 'corsica_fp_file_fingerprint_error'

    id = Column(Integer, primary_key=True)
    hash = Column(String(500), nullable=False, unique=True)
    file = Column(String(500), nullable=False)
    error = Column(String(500), nullable=False)

    def __repr__(self):
        return '<FileFingerprintError {elem.id}: {elem.file} {elem.error}>'.format(elem=self)


class FpPart(Base):
    __tablename__ = 'corsica_fp_parts'

    id = Column(Integer, primary_key=True)
    web_root = Column(Integer, nullable=False)
    firm_id = Column(Integer, nullable=False)
    web_root_file_id = Column(Integer, nullable=False)
    web_full_path = Column(String(500), nullable=False)
    hash = Column(String(500), nullable=False)

    def __repr__(self):
        return '<FingerprintPart {elem.id}: {elem.hash}>'.format(elem=self)
