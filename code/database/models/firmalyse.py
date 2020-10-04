from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Table, Text, BigInteger, text
from sqlalchemy.orm import relationship

from database.base import Base

metadata = Base.metadata


class Architecture(Base):
    __tablename__ = 'architectures'

    id = Column(Integer, primary_key=True)
    arch = Column(String(64), nullable=False)
    optional = Column(String(256), nullable=False, server_default=text("'None'"))


class FileExtension(Base):
    __tablename__ = 'file_extension'

    id = Column(Integer, primary_key=True)
    extension = Column(String(20), nullable=False, unique=True)


class FileLib(Base):
    __tablename__ = 'file_libs'

    id = Column(Integer, primary_key=True)
    libid = Column(ForeignKey('libs.id'), nullable=False, index=True)
    fileid = Column(ForeignKey('file_meta.id'), nullable=False, index=True)

    file_meta = relationship('FileMeta')
    lib = relationship('Lib')


class FileMagic(Base):
    __tablename__ = 'file_magic'

    id = Column(Integer, primary_key=True)
    magic = Column(String(255), nullable=False)


class FileMeta(Base):
    __tablename__ = 'file_meta'

    id = Column(Integer, primary_key=True)
    firmware = Column(ForeignKey('firmware_meta.id'), nullable=False, index=True)
    magic = Column(ForeignKey('file_magic.id'), nullable=False, index=True)
    size = Column(BigInteger, nullable=False)
    filename = Column(String(255), nullable=False)
    hash_sum = Column(String(64), nullable=False)
    real_path = Column(String(512), nullable=False)
    root_path = Column(String(255), nullable=False)

    firmware_meta = relationship('FirmwareMeta')
    file_magic = relationship('FileMagic')

    def __repr__(self):
        return '<File {} (FW {}): {}>'.format(self.id, self.firmware, self.filename)


class FileMetaGeneric(Base):
    __tablename__ = 'file_meta_generic'

    id = Column(Integer, primary_key=True)
    fileid = Column(ForeignKey('file_meta.id'), nullable=False, index=True)
    kind = Column(String(64), nullable=False)
    info = Column(String(512), nullable=False)

    file_meta = relationship('FileMeta')


class FileSymbol(Base):
    __tablename__ = 'file_symbols'

    id = Column(Integer, primary_key=True)
    fileid = Column(ForeignKey('file_meta.id'), nullable=False, index=True)
    symbol = Column(String(128), nullable=False)

    file_meta = relationship('FileMeta')


class FileTag(Base):
    __tablename__ = 'file_tags'

    id = Column(Integer, primary_key=True)
    tagid = Column(ForeignKey('tags.id'), nullable=False, index=True)
    fileid = Column(ForeignKey('file_meta.id'), nullable=False, index=True)

    file_meta = relationship('FileMeta')
    tag = relationship('Tag')


class FirmwareArchitecture(Base):
    __tablename__ = 'firmware_architectures'

    id = Column(Integer, primary_key=True)
    archid = Column(ForeignKey('architectures.id'), nullable=False, index=True)
    firmwareid = Column(ForeignKey('firmware_meta.id'), nullable=False, index=True)

    architecture = relationship('Architecture')
    firmware_meta = relationship('FirmwareMeta')


class FirmwareMeta(Base):
    __tablename__ = 'firmware_meta'

    id = Column(Integer, primary_key=True)
    created = Column(DateTime, nullable=False, server_default=text("current_timestamp()"))
    filename = Column(String(250), nullable=False)
    vendor = Column(String(250), nullable=False)
    version = Column(String(250), nullable=False)
    devicename = Column(String(250), nullable=False)
    size = Column(Integer, nullable=False)
    hash_sum = Column(String(150), nullable=False)
    processed = Column(Integer, server_default=text("0"))


class Lib(Base):
    __tablename__ = 'libs'

    id = Column(Integer, primary_key=True)
    libname = Column(String(128), nullable=False)
    description = Column(String(256), nullable=False, server_default=text("'None'"))


class SettingsLog(Base):
    __tablename__ = 'settings_logs'

    id = Column(Integer, primary_key=True)
    time = Column(DateTime, nullable=False, server_default=text("current_timestamp()"))
    kind = Column(String(16), nullable=False)
    job = Column(String(64), nullable=False)
    message = Column(String(150), nullable=False)
    json = Column(Text, nullable=False)


class Tag(Base):
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True)
    tag = Column(String(64), nullable=False)
    description = Column(String(256), nullable=False, server_default=text("'None'"))
