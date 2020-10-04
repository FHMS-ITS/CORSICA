# This module contains functions for the actual analysis and
# general purpose functions for maintaining database and other
# cpu demanding tasks. The Scheduler class can be used to process
# the functions in parallel.
import atexit
import hashlib
import shutil
import signal
import os
import time
import traceback
from subprocess import Popen, TimeoutExpired, PIPE

import utils.firmalyse.database as db

shared_dbcon = db.Connection()


def is_ramdisk_mounted(path):
    path = str(path)
    with open('/proc/mounts', 'r') as f:
        for m in f.read().split('\n'):
            if path in m:
                return m[5:]


def mount_ramdisk(pw, path, size):
    cmd = 'mount -t tmpfs -o size=%sM none %s &> /dev/null' % (size, path)

    if is_ramdisk_mounted(path):
        if not umount_ramdisk(pw, path):
            return
    try:
        os.makedirs(path)
    except FileExistsError:
        pass

    time.sleep(0.1)
    os.system('{} &> /dev/null'.format(cmd))
    # Ditry haack to unmount the ramdsik atexit
    atexit.register(umount_ramdisk, pw, path)

    time.sleep(0.1)
    return is_ramdisk_mounted(path)


def umount_ramdisk(pw, path):
    cmd = 'umount %s' % path
    # TODO: Check exceptions for os.system()
    os.system('{} &> /dev/null'.format(cmd))
    return not is_ramdisk_mounted(path)


# ToDo: YES
def ScanningImages(iids):
    """Invokes BAT, static and dynamic analysis on a list of image ids
    :param iids: list of primary keys inside the database for all
    images to be processed
    :return: None
    """
    # if not is_ramdisk_mounted(db.CONFIG_TMP_DIR):
    #    mount_ramdisk("abc", db.CONFIG_TMP_DIR, 4096)

    if type(iids) is int:
        iids = [iids]

    le = lambda m, err, t: db.log_error(
        shared_dbcon, 'ScanningImages', m,
        {'iid': iid, 'e': str(err), 'trace': t})

    got_exception = None

    for iid in iids:
        # In case of an Exception finish the loop and raise it later
        try:
            Unpacking(iid)
            FetchingBatResults(iid)
            fw_obj = db.get_unpacked_firmware_obj(shared_dbcon, iid)
            WritingFiles(fw_obj)
        except Exception as e:
            got_exception = e
            t = traceback.format_exc()
            le('Caught Exception', e, t)

    if got_exception:
        raise got_exception


# ToDo: YES
def LoadingImages(file_list):
    for path, unique, vendor, device, version in file_list:
        LoadingImage(path, unique, vendor, device, version)


# ToDo: YES
def LoadingImage(path, unique=True, vendor='unknown', device='unknown',
                 version='unknown'):
    """Take a firmware image from the filesystem marked by path, calculate
    information like hash sum and size and insert its information into the
    database. The image itself will be copied to the firmware_root directory
    :param path: the path to the firmware image
    :param vendor: the vendor name for this image
    :param device: the name of the device
    :param unique: skip this image, if it is already present in the database
    :param version: the version of the firmware
    :return: None
    """
    j = (path, vendor, device, unique, version)
    ld = lambda m: db.log_debug(shared_dbcon, 'LoadingImage', m, j)

    if not os.path.isfile(path):
        ld("Invalid path to firmware")
        raise ValueError("Invalid path to firmware")

    filename = os.path.basename(path)

    for c in ['(', ')', '"', ' ']:
        filename = filename.replace(c, '_')

    with open(path, 'rb') as f:
        hash = hashlib.sha256(f.read()).hexdigest()

    if unique and db.check_duplicate_hash(shared_dbcon, hash_sum=hash):
        return -1, hash

    size = os.path.getsize(path)
    id = db.insert_firmware(shared_dbcon, filename, vendor, version, device,
                            size, hash)
    if not id:
        ld("Database has returned None on insert")
        raise EnvironmentError("database has returned None on insert")

    destination = os.path.join(db.CONFIG_FIRMWARE_DIR, str(id))
    try:
        os.makedirs(destination)
    except PermissionError:
        ld("Can't write to " + '"' + db.CONFIG_FIRMWARE_DIR + '"')
        raise
    shutil.copyfile(path, os.path.join(destination, filename))
    return id, hash


# ToDo: !!!!
def Unpacking(iid):
    """Executes BAT on the firmware images. All necessary information
    will be fetched from the database. It then calls BAT using a ramdisk, and
    saves the result in the unpack directory once BAT is done.
    This function does not read BAT's results or submit something to the
    database. This is done in FetchingBatResults, to minimize the utilisation of
    the ramdisk.
    :param iid: The id of the firmware image to be processed
    :return: None
    """
    # Get the stuff out of the database
    ramdisk = db.get_ram_disk_obj()
    timeout = db.CONFIG_BAT_TIMEOUT
    fw_image = db.get_fw_obj(shared_dbcon, iid)
    bat_conf = db.get_bat_cfg_obj(shared_dbcon)

    ld = lambda m, j: db.log_debug(shared_dbcon, 'Unpacking', m, j)

    # Create a temporary directory on the ramdisk
    with ramdisk.request_dir(expected_size=fw_image.size * 6) as tmp:
        # Dump BAT's config file to the ramdisk. We set the tempdir value in
        # its config to this dir to say bat that it has to use this directory.
        bat_conf.set_temp(tmp)
        cfg_path = bat_conf.dump_file(tmp)
        cmd = 'bat-scan -d %s -c %s -u %s' % \
              (fw_image.get_source_dir, cfg_path, fw_image.unpack_dir)

        start = time.time()
        with Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE,
                   preexec_fn=os.setsid) as p:
            # BAT does not terminate on some images. Hence it will be
            # terminated after a timeout
            try:
                stdout, stderr = p.communicate(timeout=timeout)
            except TimeoutExpired:
                # send signal to the process group to ensure that child are
                # killed as well
                os.killpg(p.pid, signal.SIGINT)
                p.kill()
                ld("BAT timeout after {:.2f}s".format(time.time() - start),
                   {'iid': iid})
                # Raise anyways to allow the scheduler to recognize the
                # exception
                raise

    if stderr and (len(stderr) is not 0 or p.returncode is not 0):
        ld("BAT returned errors",
           {'returncode': str(p.returncode), 'stderr': str(stderr),
            'stdout': str(stdout)})

        if not os.listdir(fw_image.unpack_dir):
            return
    fw_image.inc_processed(shared_dbcon)


# ToDo: !!!!
def FetchingBatResults(iid):
    """Once bat has successfully processed a firmware image, it saves an archive
    called scandata.tar.gz to the unpack directory. This function reads
    this tar file and submits its content database.
    Due to performance, this is (like the execution of bat) done on the ramdisk.
    :param iid: The id of the firmware image to be processed
    :return: None
    """
    # Use an own db connection for speed
    own_dbcon = db.Connection()
    # Fetch the bat result for this firmware image identified by iid
    f = db.get_bat_result_obj(own_dbcon, iid)

    ramdisk = db.get_ram_disk_obj()
    ld = lambda m, j: db.log_debug(shared_dbcon, 'FetchingBatResults', m, j)

    # We do extract the the results from the scandata.tar.gz on a ramdisk. We
    # acquire on this ramdisk three time the size of the scandata.tar.gz.
    # ramdisk.request_dir will block until the requested size is available.
    with ramdisk.request_dir(expected_size=f.unpacked_size * 3) as tmp:
        try:
            file_list = f.get_file_list(tmp)
        except ValueError as e:
            # Just return if the image is not unpacked
            ld('No result present', {'iid': iid, 'e': str(e)})
            own_dbcon.close()
            return

    image_arch = {}
    tags_to_inset = []
    libs_to_insert = []
    symbols_to_insert = []
    generic_to_insert = []

    # Iterate over the list of file and inset the corresponding information
    for bf in file_list:
        # Insert magic string to get its primary key
        mid = db.get_set_file_magic(own_dbcon, bf.get_magic())

        # Insert the stuff into the file_meta table
        f_id = db.insert_file(own_dbcon, iid, mid, bf.get_size(),
                              bf.get_name(), bf.get_hash(),
                              bf.get_real_path(), bf.get_root())

        # Count the occurrence of architectures
        arch = bf.get_architecture(max_len=64, default=False)
        if arch:
            if arch not in image_arch:
                image_arch[arch] = 1
            else:
                image_arch[arch] += 1

        for t in bf.get_tags():
            tags_to_inset.append((f_id, t))
        for sym in bf.get_func_symbols():
            symbols_to_insert.append((f_id, sym))
        for lib in bf.get_libs():
            libs_to_insert.append((f_id, lib))
        for gen in bf.get_meta_generic():
            generic_to_insert.append(([f_id] + gen))

    if image_arch:
        arch = max(image_arch, key=lambda k: image_arch[k])
        db.set_firmware_arch(own_dbcon, iid, arch)

    # Insert as many as possible at once for speed
    db.set_file_tag(own_dbcon, tags_to_inset)
    db.set_file_lib(own_dbcon, libs_to_insert)
    db.set_file_symbols_may(own_dbcon, symbols_to_insert)
    db.set_file_meta_generic(own_dbcon, generic_to_insert)

    # Signalize that one processing step is done for this firmware image
    f.inc_processed(own_dbcon)
    own_dbcon.close()


# !
def WritingFiles(fw_obj):
    """Write to data from a bat result to the unpack directory and recreates the
    directory structure
    :param fw_obj: Unpacked firmware object for the image
    :return: None
    """
    ramdisk = db.get_ram_disk_obj()
    with ramdisk.request_dir(expected_size=fw_obj.unpacked_size * 3) as tmp:
        fw_obj.save_root_to_unpack_dir(tmp)
    fw_obj.inc_processed(shared_dbcon)
