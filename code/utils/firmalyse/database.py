# This file is responsible for handling the data.
# It does include several query and insertion functions for accessing the
# database. The fist argument of each function must be an instance of the
# Connection class listed below. It is possible to get a multiprocessing.Event
# object for certain tables (see __table_change_events). Each event is going
# to be activated on every write to its corresponding table. This allows the
# gui to recognize if it needs to update.
import configparser
import json
import multiprocessing as mp

from pymysql import connect, err

from utils.firmalyse import datastructures

config = configparser.ConfigParser()
config.read("/etc/corsica/config.ini")

# Database constants (keys) for settings table
CONFIG_FIRMWARE_DIR = "/opt/data/images"
CONFIG_RESUlT_DIR = "/opt/data/unpacked"
CONFIG_TMP_DIR = "/tmp/ram_disk"
CONFIG_TMP_SIZE = 805306368
CONFIG_BAT_TIMEOUT = 3600

LOG_ERROR = 'Error'
LOG_DEBUG = 'Debug'
LOG_INFO = 'Info'


class Connection(object):
    """Each operation on the database is done through a Connection object. It
     also provides direct access to the settings table
    """

    def __init__(self, host=config['mysql']['host'], user=config['mysql']['user'],
                 password=config['mysql']['password'], db=config['mysql']['database']):
        self.__mysql = connect(host, user, password, db, charset='utf8')
        self.__mysql.apilevel = "2.0"
        self.__mysql.threadsafety = 3
        self.__mysql.paramstyle = "format"
        self.__l = mp.Lock()
        self.query('SET innodb_lock_wait_timeout = 1000')

    def get_connection(self):
        return self.__mysql

    def query(self, query, data=None):
        self.__l.acquire()

        def execute():
            cursor = self.__mysql.cursor()
            if data is None:
                cursor.execute((query))
            else:
                cursor.execute((query), data)
            self.commit()
            return cursor

        try:
            return execute()
        except err.OperationalError:
            # In case there is an OperationalError, try to reconnect and
            # retry the query. PyMySQL might raise this exception if a
            # connection is open for too long time.
            self.__mysql.close()
            self.__init__(self.__mysql.host, self.__mysql.user,
                          self.__mysql.password, self.__mysql.db)
            return execute()

        finally:
            try:
                self.__l.release()
            except ValueError:
                pass

    def commit(self):
        self.__mysql.commit()

    def close(self):
        self.__mysql.close()


def get_ram_disk_obj():
    size = CONFIG_TMP_SIZE
    path = CONFIG_TMP_DIR
    if not size:
        raise EnvironmentError("Ramdisk size not set in database")
    return datastructures.RamDisk(path, size)


def get_bat_cfg_obj(dbcon):
    return datastructures.BatConfig(dbcon)


def inc_fw_state(dbcon, id, p=None):
    if p:
        q = 'UPDATE `firmware_meta` SET `processed` = %s WHERE`id`=%s'
        dbcon.query(q, (p, id))
        return p
    else:
        q = 'UPDATE `firmware_meta` SET `processed` = `processed` + 16.7 ' \
            'WHERE  `id`=%s'
        dbcon.query(q, id)
        return 16.7


def clear_fw_state(dbcon, id):
    q = 'UPDATE `firmware_meta` SET `processed` = 0 WHERE  `id` = %s'
    d = dbcon.query(q, id).fetchone()
    return d


def get_fw_obj(dbcon, image_id):
    db_row = get_firmware(dbcon, image_id)
    return datastructures.Firmware(CONFIG_FIRMWARE_DIR, CONFIG_RESUlT_DIR, *db_row)


def get_bat_result_obj(dbcon, image_id):
    db_row = get_firmware(dbcon, image_id)
    return datastructures.BatResultTar(CONFIG_FIRMWARE_DIR, CONFIG_RESUlT_DIR, *db_row)


def log_error(dbcon, job, message, extra_data: dict):
    query = 'INSERT INTO `settings_logs` (`kind`, `job`, `message`,`json`) ' \
            'VALUES ( %s, %s, %s, %s)'
    data = (LOG_ERROR, job, message[:150], json.dumps(extra_data)[:2 ** 16])
    d = dbcon.query(query, data).lastrowid
    return d


def log_debug(dbcon, job, message, extra_data: dict):
    query = 'INSERT INTO `settings_logs` (`kind`, `job`, `message`,`json`) ' \
            'VALUES ( %s, %s, %s, %s)'
    data = (LOG_DEBUG, job, message[:150], json.dumps(extra_data)[:2 ** 16])
    d = dbcon.query(query, data).lastrowid
    return d


def insert_firmware(dbcon, filename, vendor, version, device_name, size,
                    hash_sum):
    q = 'INSERT INTO `firmware_meta` (`filename`, `vendor`,`version`, ' \
        '`devicename`, `size`, `hash_sum`)' \
        ' VALUES ( %s, %s, %s, %s, %s, %s)'
    data = (filename, vendor, version, device_name, size, hash_sum)
    d = dbcon.query(q, data).lastrowid
    return d


def get_firmware(dbcon, id=None):
    if not id:
        q = "SELECT * FROM `firmware_meta`"
        return dbcon.query(q).fetchall()
    else:
        q = 'SELECT * FROM `firmware_meta` WHERE `id`=%s'
        return dbcon.query(q, id).fetchone()


def check_duplicate_hash(dbcon, hash_sum):
    query = 'SELECT `id` FROM `firmware_meta` WHERE `hash_sum` = %s'
    return dbcon.query(query, hash_sum).fetchone()


def get_logs(dbcon):
    query = 'SELECT * FROM `settings_logs`'
    return dbcon.query(query).fetchall()


def get_set_file_magic(dbcon, magic):
    select = 'SELECT `id` FROM `file_magic` WHERE `magic` = %s'
    id_magic = dbcon.query(select, [magic]).fetchone()
    if id_magic:
        return id_magic[0]
    inset = 'INSERT INTO `file_magic` (`magic`) VALUES (%s)'
    return dbcon.query(inset, [magic]).lastrowid


def insert_file(dbcon, fid, magic, size, filename, hash_sum, real_path,
                root_path):
    query = "INSERT INTO `file_meta` (`firmware`, `magic`, `size`," \
            "`filename`, `hash_sum`,`real_path`, `root_path`)" \
            " VALUES (%s, %s, %s, %s, %s, %s, %s)"
    data = [fid, magic, size, filename, hash_sum, real_path, root_path]
    d = dbcon.query(query, data).lastrowid
    return d


def get_set_architectures(dbcon, arch):
    select = 'SELECT `id` FROM `architectures` WHERE `arch` = %s'
    arch_id = dbcon.query(select, [arch]).fetchone()
    if arch_id:
        return arch_id[0]
    inset = 'INSERT INTO `architectures` (`arch`) VALUES (%s)'
    return dbcon.query(inset, [arch]).lastrowid


def set_firmware_arch(dbcon, firmware_id, arch):
    arch_id = get_set_architectures(dbcon, arch)
    inset = 'INSERT INTO `firmware_architectures` (`archid`, `firmwareid`) ' \
            'VALUES (%s, %s)'
    return dbcon.query(inset, [arch_id, firmware_id]).lastrowid


def set_file_symbols_may(dbcon, table_rows):
    inset = 'INSERT INTO `file_symbols` (`fileid`, `symbol`) VALUES (%s, %s)'
    dbcon.get_connection().cursor().executemany(inset, table_rows)
    dbcon.commit()


def get_set_lib(dbcon, libname):
    select = 'SELECT `id` FROM `libs` WHERE `libname` = %s'
    tag_id = dbcon.query(select, [libname]).fetchone()
    if tag_id:
        return tag_id[0]
    inset = 'INSERT INTO `libs` (`libname`) VALUES (%s)'
    return dbcon.query(inset, [libname]).lastrowid


def get_lib_cache(dbcon):
    select = 'SELECT `id`, `libname` FROM `libs`'
    return {s[1]: s[0] for s in dbcon.query(select)}


def set_file_libs_many(dbcon, table_rows):
    inset = 'INSERT INTO `file_libs` (`libid`, `fileid`) VALUES (%s, %s)'
    dbcon.get_connection().cursor().executemany(inset, table_rows)
    dbcon.commit()


def set_file_lib(dbcon, libs):  # file_id, libname):
    lib_cache_f = get_lib_cache(dbcon)
    to_inset = []
    for file_id, libname in libs:
        if libname in lib_cache_f:
            lib_id = lib_cache_f[libname]
        else:
            lib_id = get_set_lib(dbcon, libname)
            lib_cache_f[libname] = lib_id
        to_inset.append((lib_id, file_id))
    set_file_libs_many(dbcon, to_inset)


def get_set_tag(dbcon, tag):
    select = 'SELECT `id` FROM `tags` WHERE `tag` = %s'
    tag_id = dbcon.query(select, [tag]).fetchone()
    if tag_id:
        return tag_id[0]
    inset = 'INSERT INTO `tags` (`tag`) VALUES (%s)'
    return dbcon.query(inset, [tag]).lastrowid


def get_tag_cache(dbcon):
    select = 'SELECT `id`, `tag` FROM `tags`'
    return {s[1]: s[0] for s in dbcon.query(select).fetchall()}


def set_file_tags_many(dbcon, table_rows):
    inset = 'INSERT INTO `file_tags` (`tagid`, `fileid`) VALUES (%s, %s)'
    dbcon.get_connection().cursor().executemany(inset, table_rows)
    dbcon.commit()


def set_file_tag(dbcon, tags):
    tag_cache = get_tag_cache(dbcon)
    to_inset = []
    for file_id, tag in tags:
        if tag in tag_cache:
            tag_id = tag_cache[tag]
        else:
            tag_id = get_set_tag(dbcon, tag)
            tag_cache[tag] = tag_id
        to_inset.append((tag_id, file_id))
    set_file_tags_many(dbcon, to_inset)


def set_file_meta_generic(dbcon, generic_reports):
    i = 'INSERT INTO `file_meta_generic` (`fileid`, `kind`, `info`) ' \
        'VALUES (%s, %s, %s)'
    dbcon.get_connection().cursor().executemany(i, generic_reports)
    dbcon.commit()


def get_file_list_obj(dbcon, firmware_id, unpack_root, set__optional=False,
                      magic_as_string=True):
    sf = 'SELECT * FROM `file_meta` WHERE `firmware` = %s'
    st = 'SELECT tag FROM file_tags INNER JOIN tags ON file_tags.tagid = ' \
         'tags.id WHERE   file_tags.fileid =  %s'
    sl = 'SELECT libname FROM file_libs INNER JOIN libs ON file_libs.libid = ' \
         'libs.id WHERE   file_libs.fileid =  %s'
    ss = 'SELECT DISTINCT symbol FROM file_symbols WHERE fileid =%s'
    smg = 'SELECT kind, info FROM file_meta_generic WHERE fileid =%s'
    smagic = 'SELECT magic FROM file_magic WHERE id =%s'

    files = dbcon.query(sf, [firmware_id]).fetchall()
    file_objects = []
    if not files:
        raise ValueError('There are not files for this firmware')
    for row in files:

        # Use the magic string instead of its id
        if magic_as_string:
            row = list(row)
            row[2] = dbcon.query(smagic, [row[2]]).fetchone()[0]

        firmware_file = datastructures.FirmwareFile(*row, unpack_root)

        tags = [t[0] for t in dbcon.query(st, [firmware_file.id]).fetchall()]
        firmware_file.set_tags(tags)

        if not set__optional:
            file_objects.append(firmware_file)
            continue

        libs = [t[0] for t in dbcon.query(sl, [firmware_file.id]).fetchall()]
        firmware_file.set_libs(libs)

        syms = [t[0] for t in dbcon.query(ss, [firmware_file.id]).fetchall()]
        firmware_file.set_symbols(syms)

        mg = [{t[0]: t[1]} for t in
              dbcon.query(smg, [firmware_file.id]).fetchall()]
        firmware_file.set_meta_generic(mg)

        file_objects.append(firmware_file)

    return file_objects


def get_unpacked_firmware_obj(dbcon, firmware_id, set__optional=False):
    db_row = get_firmware(dbcon, firmware_id)
    file_list = get_file_list_obj(dbcon, firmware_id, CONFIG_RESUlT_DIR,
                                  set__optional)
    fw_args = [CONFIG_FIRMWARE_DIR, CONFIG_RESUlT_DIR] + list(db_row)
    return datastructures.UnpackedFirmware(file_list, fw_args)
