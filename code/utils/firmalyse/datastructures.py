# This file contains some classes, that are used by the database module as
# return types. This encapsulates the actual database scheme from its usage.
# The job module mainly operates on object out of this module.

import configparser
import io
import json
import multiprocessing as mp
import os
import pickle
import re
import tarfile
import tempfile
import time
import uuid
from shutil import rmtree
from subprocess import run, PIPE, Popen, TimeoutExpired

from utils.firmalyse import database as db


class BatConfig(object):
    def __init__(self, source):
        if type(source) is db.Connection:
            cfg_str = open("/etc/corsica/bat.conf").read()
            if cfg_str == "":
                raise ValueError('Database does not contain any bat config')
            self._config = configparser.RawConfigParser()
            self._config.read_string(cfg_str)
            self._connection = source
        elif type(source) is str:
            if not os.path.isfile(source):
                ValueError('Invalid path to bat config file')
            self._config = configparser.RawConfigParser()
            self._config.read(source)
            self._connection = None

    def dump_file(self, directory):
        config_file = os.path.join(directory, "bat-scan.config")
        with open(config_file, 'w') as f:
            self._config.write(f)
        return config_file

    def set_temp(self, path):
        self._config['batconfig']['temporary_unpackdirectory'] = path
        self._config['batconfig']['unpackdirectory'] = path

    def __str__(self):
        output = io.StringIO()
        self._config.write(output)
        return output.getvalue()

    @property
    def config(self):
        return self._config

    def test(self):
        a = []
        for section in self._config.sections():
            b = [section]
            for option in list(self._config[section]):
                b.append([option, str(self._config[section][option])])
            a.append(b)
        return a


class Firmware(object):
    def __init__(self, source_root, unpack_root, imageid, created, imgname,
                 vendor, version, device, size, hash, processed):
        self._img_id = imageid
        self._created = created
        self._img_name = imgname
        self._vendor = vendor
        self._version = version
        self._device = device
        self._size = size
        self._hash = hash
        self._processed = processed

        self._source_dir = os.path.join(source_root, str(imageid))
        self._unpack_dir = os.path.join(unpack_root, str(imageid))

    def __str__(self):
        return self.get_absolute_path

    @property
    def id(self):
        return self._img_id

    @property
    def hash(self):
        return self._hash

    @property
    def name(self):
        return self._img_name

    @property
    def size(self):
        return self._size

    @property
    def get_absolute_path(self):
        return os.path.join(self._source_dir, self._img_name)

    @property
    def get_source_dir(self):
        return self._source_dir

    @property
    def unpack_dir(self):
        if not os.path.exists(self._unpack_dir):
            os.makedirs(self._unpack_dir)
        return self._unpack_dir

    def inc_processed(self, dbcon):
        if self._processed < 100:
            self._processed += db.inc_fw_state(dbcon, self._img_id)


class BatResultTar(Firmware):
    def __init__(self, source_root, unpack_root, image_id, created,
                 img_name, vendor, version, device, size, hash, processed):
        Firmware.__init__(self, source_root, unpack_root, image_id, created,
                          img_name, vendor, version, device, size, hash,
                          processed)

    @property
    def unpacked_size(self):
        return os.path.getsize(self.get_bat_tar())

    def get_bat_tar(self):
        tar_file = os.path.join(self._unpack_dir, self._img_name + '.tar.gz')
        if not os.path.isfile(tar_file):
            raise EnvironmentError(
                "Can't load bat results, tarfile does not exists")
        return tar_file

    def dump_tar_element(self, element, dir):
        with tarfile.open(self.get_bat_tar(), "r:gz") as tar:
            tar.extract(element, path=dir)
        return os.path.join(dir, element)

    def dump_tar_subdir(self, subdir, dir):
        with tarfile.open(self.get_bat_tar()) as tar:
            members = [m for m in tar.getmembers() if m.name.startswith(subdir)]
            def is_within_directory(directory, target):
                
                abs_directory = os.path.abspath(directory)
                abs_target = os.path.abspath(target)
            
                prefix = os.path.commonprefix([abs_directory, abs_target])
                
                return prefix == abs_directory
            
            def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
            
                for member in tar.getmembers():
                    member_path = os.path.join(path, member.name)
                    if not is_within_directory(path, member_path):
                        raise Exception("Attempted Path Traversal in Tar File")
            
                tar.extractall(path, members, numeric_owner=numeric_owner) 
                
            
            safe_extract(tar, members=members, path=dir)
        return [os.path.join(dir, m.name) for m in members]

    def dump_scan_data_json(self, dir):
        return self.dump_tar_element('scandata.json', dir)

    def dump_file_reports(self, dir):
        return self.dump_tar_subdir("filereports/", dir)

    def get_detailed_file_reports(self, temp_dir):
        reports = {}
        # TODO it may be more efficient to to dump only the needed report
        for report_path in self.dump_file_reports(temp_dir):
            hash_in_filename = os.path.basename(report_path)[:64]

            # Open and read the specific file report
            with open(report_path, 'rb') as f:
                r = pickle.load(f, encoding="utf8", errors="ignore")
                reports[hash_in_filename] = r
        return reports

    def get_file_list(self, temp_dir):
        file_list = []
        max_int = (2 ** 32) / 2 - 1

        img_name_encoded = self.name.encode("utf-8")
        try:
            general_report_json_file = self.dump_scan_data_json(temp_dir)
        except:
            raise ValueError("I'm actually not unpacked")

        with open(general_report_json_file, "rb") as pf:
            general_reports = json.loads(pf.read().decode("utf-8"))

        detailed_reports = self.get_detailed_file_reports(temp_dir)

        for f_report in general_reports:
            bf = BatFileEntry(temp_dir, f_report)

            # The old db uses int, where size is limited to (2 ** 32)/2 -1
            # (2.1 GiB). The new db scheme used bigint and fixes this.
            #
            # However it is likely that big files are caused by a bug of bat.
            # In one 100 miB image, Bat extracts a 3.1 GiB file. The image
            # may include files that are highly compressed like filesystem
            # dumps where free space was overwritten with /dev/zero.
            if bf.get_size() > max_int:
                continue

            # The firmware image itself is an extracted file within the bat
            # result. Do not insert is as file because it is already present in
            # the firmware_meta table
            if bf.get_name() == img_name_encoded:
                continue

            file_list.append(bf)

            if bf.get_hash() not in detailed_reports:
                continue

            # For symlinks we do not have detailed scan reports
            if bf.is_symlink():
                continue

            mdr = detailed_reports[bf.get_hash()]
            bf.set_file_report(mdr)

        return file_list


class BatFileEntry(object):
    def __init__(self, temp_dir, f_report, ):
        self.f_report = f_report
        self.temp_dir = temp_dir

    def is_symlink(self):
        return 'symlink' in self.get_tags()

    def set_file_report(self, specific_report):
        if 'tags' in specific_report:
            del specific_report['tags']
        self.f_report.update(specific_report)

    def get_real_path(self, max_len=512, default='Unknown'):
        k = 'realpath'
        f = self.f_report
        rp = f[k] if k in f and f[k] else default
        # Strip off the first part of the path. So convert it from:
        # "/opt/firmalyse/tmp/tmpa8a195bh/tmpoB2ssq/data/WC4250_15...."
        # to "/data/WC4250_15...."
        # which is the relative path inside the BAT output tar file.
        rp = rp[len(self.temp_dir) + 10:]
        rp = rp.encode("utf8", "ignore")
        return default if len(rp) > max_len else rp

    def get_size(self, default=-1):
        k = 'size'
        f = self.f_report
        return f[k] if k in f and f[k] else default

    def get_tags(self, max_len=64, default=[]):
        k = 'tags'
        f = self.f_report
        tg = f[k] if k in f and f[k] else default
        return default if len(tg) > max_len else tg

    def get_name(self, max_len=255, default='Unknown'):
        k = 'name'
        f = self.f_report
        n = f[k] if k in f and f[k] else default
        n = n.encode("utf8", "ignore")
        return default if len(n) > max_len else n

    def get_root(self, max_len=255, default='Unknown'):
        k = 'path'
        f = self.f_report
        ro = f[k] if k in f and f[k] else default
        ro = ro.encode("utf8", "ignore")
        return default if len(ro) > max_len else ro

    def get_magic(self, max_len=255, default='Unknown'):
        k = 'magic'
        f = self.f_report
        m = f[k] if k in f and f[k] else default
        return default if len(m) > max_len else m

    def get_hash(self, max_len=64, default='symlink'):
        k = 'checksum'
        f = self.f_report
        h = f[k] if k in f and f[k] else default
        return default if len(h) > max_len else h

    def get_architecture(self, max_len=64, default='Unknown'):
        k = 'architecture'
        f = self.f_report
        return f[k] if k in f and f[k] and len(f[k]) < max_len else default

    def get_func_symbols(self, max_len=128, default=[]):
        k1 = 'identifier'
        k2 = 'functionnames'
        f = self.f_report
        syms = f[k1][k2] if k1 in f and k2 in f[k1] and f[k1][k2] else default
        return [s for s in syms if len(s) < max_len]

    def get_libs(self, max_len=128, default=[]):
        k = 'libs'
        f = self.f_report
        libs = f[k] if k in f and f[k] else default
        libs + [l.encode('utf-8', errors="ignore") for l in libs]
        return [default if len(s) > max_len else s for s in libs]

    def get_meta_generic(self, max_len=512, ):
        not_rest = ['libs', 'identifier', 'architecture', 'tags', 'checksum',
                    'name', 'path', 'realpath', 'size', 'magic', 'sha256',
                    'checksumtype', 'scans', 'md5', 'sha1', 'duplicates',
                    'relativename']
        f = self.f_report
        # TODO .decode("utf-8", "ignore")
        rest = [[k, str(f[k]).encode("utf8", "ignore")[:max_len]] for k in
                f.keys()
                if k not in not_rest]
        return rest


class FirmwareFile(object):
    def __init__(self, fid, firmware_id, magic, size, filename, hash, real_path,
                 __root_path, unpack_root):
        self._id = fid
        self._firmware_id = firmware_id
        self._unpack_dir = os.path.join(unpack_root, str(self._firmware_id))

        self._magic = magic
        self._size = size
        self._filename = filename
        self._hash = hash
        self._real_path = real_path

        self._dir_in_root = __root_path if __root_path[
                                               0] == '/' else '/' + __root_path

        self._tags = []
        self._libs = []
        self._symbols = []
        self._meta_generic = []

    @property
    def magic(self):
        return self._magic

    def set_symbolic_link(self):
        if not self.is_symlink:
            return

        if type(self.magic) is not str:
            # TODO(hannes) Es kann vorkommen, dass self.magic die id
            # der file_magic table ist... Testen!
            raise RuntimeError('type of magic is not str')

        hit = re.search('(?<=symbolic\slink\sto\s).*', self.magic)
        if not hit:
            return

        name = hit.group(0).strip()
        if name[0] is '/':  # Link to absolute path
            l_src = os.path.join(self.unpack_dir, name[1:])
        else:  # Link to relative path
            l_src = os.path.join(self.unpack_dir, self._dir_in_root[1:], name)

        l_dest = self.path_in_result_root
        try:
            if not os.path.isdir(os.path.dirname(l_dest)):
                os.makedirs(os.path.dirname(l_dest))

            os.symlink(l_src, l_dest)
        except (FileNotFoundError, FileExistsError, NotADirectoryError) as e:
            # A FileExistsError may often happen. If an image has different
            # partitions, with two directors having equal names ( like /etc on
            # partition 1 and /etc on partition 2), we merge them to one
            # directory. Hence symlinks from 1/etc/foo -> 2/etc/baa wont work
            # sys.stderr.write(str(e) + '\n')
            pass

    @property
    def id(self):
        return self._id

    @property
    def hash(self):
        return self._hash

    @property
    def is_symlink(self):
        return 'symlink' in self.tags

    @property
    def name(self):
        return self._filename

    @property
    def tags(self):
        return self._tags

    @property
    def size(self):
        return self._size

    @property
    def relative_path(self):
        p = os.path.join(self._dir_in_root, self._filename)
        if p[0] is '/':
            return p[1:]
        return p

    @property
    def unpack_dir(self):
        return self._unpack_dir

    @property
    def path_in_result_root(self):
        return os.path.join(self._unpack_dir, self.relative_path)

    @property
    def path_in_tar(self):
        return os.path.join(self._real_path, self._filename)[1:]

    def set_tags(self, tags):
        self._tags = tags

    def set_libs(self, libs):
        self._libs = libs

    def set_symbols(self, symbols):
        self._symbols = symbols

    def set_meta_generic(self, meta_generic):
        self._meta_generic = meta_generic

    def match_filename(self, compiled_regex):
        if re.match(compiled_regex, self._filename):
            return True
        return False


class UnpackedFirmware(BatResultTar):
    def __init__(self, file_list, fw_args):
        BatResultTar.__init__(self, *fw_args)
        self._file_list = file_list

    def dump_files(self, dir):
        return self.dump_tar_subdir("data/", dir)

    def get_file_content_by_filename(self, regex):
        hits = []
        got_error = False
        crex = re.compile(regex)
        for f in self._file_list:
            if not f.match_filename(crex):
                continue
            try:
                with open(f.path_in_result_root, 'rb') as of:
                    c = of.read().decode('utf-8', 'ignore')
            except Exception as e:
                got_error = e
                continue
            hits.append({'fileid': f.id, 'regex': regex, 'content': c})
        return hits, got_error

    def get_files_by_tag(self, tag_list):
        result = []
        for f in self._file_list:
            for t in tag_list:
                if t in f.tags:
                    result.append(f)
        return result

    def get_file_size_by_fileid(self, fileid):
        for f in self._file_list:
            if fileid == f.id:
                return f.size

    def dump_file_tmp(self, file_ids, temp_dir):
        if not isinstance(file_ids, list):
            file_ids = [file_ids]
        ps = []
        for f in self._file_list:
            if f.id in file_ids:
                path_tar = self.dump_tar_element(f.path_in_tar, temp_dir)
                ps.append(path_tar)
        return ps

    def save_root_to_unpack_dir(self, temp_dir):
        import shutil
        dumped = self.dump_files(temp_dir)
        skip = [self.name]

        to_link = []

        for f in self._file_list:
            if f.is_symlink:
                to_link.append(f)
                continue

            source_p = os.path.join(temp_dir, f.path_in_tar)
            if source_p not in dumped or os.path.basename(source_p) in skip:
                continue

            path_in_fs = os.path.join(self.unpack_dir, f.relative_path)
            try:
                os.makedirs(os.path.dirname(path_in_fs), exist_ok=True)
                shutil.copy(source_p, path_in_fs)
            except Exception as e:
                # Just in case there is something ....
                # sys.stderr.write(str(e) + '\n')
                pass

        for f in to_link:
            f.set_symbolic_link()

    def dump_files_to_target(self, file_ids, temp_dir, target_dir):
        if not isinstance(file_ids, list):
            file_ids = [file_ids]

        import shutil
        dumped = self.dump_files(temp_dir)

        for f in self._file_list:
            source_p = os.path.join(temp_dir, f.path_in_tar)
            if f.id in file_ids and source_p in dumped:
                path_in_filesystem = \
                    os.path.join(target_dir, str(self._img_id), f.relative_path)
                os.makedirs(os.path.dirname(path_in_filesystem), exist_ok=True)
                shutil.move(source_p, path_in_filesystem)

    def get_file_content_by_content(self, regex_list, regex_list_der):
        """
        Search for given regex in extracted files.
        :param regex_list: list of regex and associated label
        :param regex_list_der: list of regex for DER encoded strings
               (checked for valid DER encoding using openssl ans1parse)
               Note: 3rd and 4th byte are used as length bytes!
        :return:
        """
        if not isinstance(regex_list, list) and \
                not isinstance(regex_list, tuple):
            raise ValueError('regex_list must be list or tuple')
        if not isinstance(regex_list_der, list) and \
                not isinstance(regex_list_der, tuple):
            raise ValueError('regex_list_der must be list or tuple')

        hits = []
        got_error = False

        skip_tags = ['graphics', 'compressed', 'swf']

        for f in self._file_list:
            if [True for s in skip_tags if s in f.tags]:
                continue
            try:
                with open(f.path_in_result_root, 'rb') as of:
                    content_bytes = of.read()
                    content = content_bytes.decode('ascii', 'ignore')
            except Exception as e:
                got_error = e
                continue

            for label, rex in regex_list:
                # TODO? Note: this line uses about 1/10th of the CPU time for a given image
                for m in rex.finditer(content, re.IGNORECASE):
                    hits += [
                        {'fileid': f.id, 'label': label, 'offset': m.start(), 'len': m.end(), 'content': m.group(0)}]

        return hits, got_error

    def has_root_dir(self, dbcon):
        roots = db.get_root_dirs(dbcon, self.id)
        for rd in ['bin', 'lib']:
            if rd not in roots:
                return False
        return True


globalLock = mp.Lock()
globalAllocated = mp.Value('i', 0)


class RamDisk(object):
    class RamdiskDir(tempfile.TemporaryDirectory):
        def __init__(self, dir, request, total_allocated):
            self.__request = request
            self.__total_requested = total_allocated
            tempfile.TemporaryDirectory.__init__(self, dir=dir)

        def __exit__(self, exc, value, tb):
            self.cleanup()
            self.__total_requested.value -= self.__request

    def __init__(self, path, max_size):
        self.__l = globalLock
        self.__path = path

        # the maximum allowed sized is max_size - 100 MiB
        self.__max_size = max_size - 100 * 1024 * 1024
        self.__total_requested = globalAllocated

    def __space_left(self, required):
        return abs(self.__max_size - self.__total_requested.value) > required

    def request_dir(self, expected_size):
        self.__l.acquire()
        if expected_size >= self.__max_size:
            self.__l.release()
            raise ValueError("Ramdisk too small for images!")

        while not self.__space_left(expected_size):
            time.sleep(5)

        self.__total_requested.value += expected_size
        self.__l.release()
        return RamDisk.RamdiskDir(self.__path, expected_size,
                                  self.__total_requested)


# Deps docker.io
# sudo usermod -aG docker ubuntu
# sudo usermod -aG docker $(echo $USER)
class DockerImage(object):
    """ Creates and runs a docker image, which commands can be sent to using exec
    """
    Docker_file = """
    FROM nfnty/arch-mini
    MAINTAINER Johannes Hessling; j.hessling@fh-muenster.de
    RUN pacman --noconfirm -Syu
    RUN pacman --noconfirm -S qemu-arch-extra
    RUN pacman --noconfirm -Sc
    """

    def __init__(self, docker_img, mount_dir):
        # Get a unique name for the docker image
        # A new image will be created for each scanned firmware, but not for each process
        self.mount_dir = mount_dir
        self.img = "fhms/vext-" + str(uuid.uuid4()).split('-')[0]
        self.container_id = None
        self.init_image(docker_img)
        self.init_container()

    def init_image(self, dimg=None):
        default_img = 'fhms/vext-default'

        for i in DockerImage.__get_docker_images():
            if default_img == i['repo']:
                run(['docker', 'tag', default_img, self.img])
                return

        # If we have a a docker images given via cli, use it.:
        if dimg and os.path.isfile(dimg):
            with open(dimg, 'rb') as dump:
                p = Popen(['docker', 'load'], stdin=PIPE)
                p.communicate(input=dump.read())
            run(['docker', 'tag', default_img, self.img])
            return

        # If not, build it.
        tmp = tempfile.mkdtemp()
        # Write docker file to local dir and build the image...
        with open(tmp + "/Dockerfile", "w") as f:
            f.write(DockerImage.Docker_file)

        ro_run = ['docker', 'build', '--force-rm', '-t=' + self.img, tmp]
        out = run(ro_run, stderr=PIPE, stdout=PIPE)
        if out.returncode is not 0:
            raise RuntimeError('Cant build docker image :' +
                               out.stderr.decode("utf8", "ignore"))

        run(['docker', 'tag', self.img, default_img])
        rmtree(tmp)

    def init_container(self):
        """
        Run the created image (image is kept running and container_id is stored in self.container_id)
        """

        # Run as -dt for detached and pseudo-tty
        # Use -v to allow for data access in mount_dir
        # append "tail -f /dev/null" so container keeps running
        cmd = 'docker run -dt -v {self.mount_dir}:{self.mount_dir}:ro {self.img} tail -f /dev/null'.format(self=self)
        # docker returns the container id
        with Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE, preexec_fn=os.setsid) as p:
            try:
                stdout, stderr = [o.decode("utf-8", "ignore") for o in
                                  p.communicate(timeout=4)]
                self.container_id = stdout.strip()
                # print("Image ID: " + self.img)
                # print("Container ID: " + self.container_id)
            except TimeoutExpired:
                # os.killpg(p.pid, signal.SIGINT)
                # FIXME: Better timeout values
                return None

    def docker_rm_zombies(self):
        # Some docker containers may run into an endless loop.
        # To deal with this, call docker kill on each container
        containers = DockerImage.__get_docker_containers()
        for cid in containers:
            if cid['img_id'] == self.img:
                run(['docker', 'rm', '-f', cid['cont_id']], stdout=PIPE)

    @staticmethod
    def __get_docker_images():
        out = run(['docker', 'images', '--format', "{{.ID}} {{.Repository}}"],
                  stdout=PIPE).stdout.decode("utf8", "ignore").strip()
        if not out:
            return []
        return [{'repo': r.split(' ')[1], 'img_id': r.split(' ')[0]} for
                r in out.split('\n')]

    @staticmethod
    def __get_docker_containers():
        out = run(['docker', 'ps', '-a', '--format', "{{.ID}} {{.Image}}"],
                  stdout=PIPE).stdout.decode("utf8", "ignore").strip()
        if not out:
            return []
        return [{'cont_id': r.split(' ')[0], 'img_id': r.split(' ')[1]
                 } for r in out.split('\n')]

    def __del__(self):
        self.docker_rm_zombies()
        run(['docker', 'rmi', '-f', self.img], stdout=PIPE)

    def run(self, mount, cmd, timeout=15):
        c = "docker exec {self.container_id} /bin/bash -c '{cmd}'".format(self=self, cmd=cmd)
        # print(c)

        # When not prepending "exec", docker exec will be run as a child of a shell and can therefore not be killed
        with Popen("exec " + c, shell=True, stdout=PIPE, stderr=PIPE, preexec_fn=os.setsid) as p:
            try:
                stdout, stderr = [o.decode("utf-8", "ignore") for o in p.communicate(timeout=timeout)]
                # print(stdout)
                # print(stderr)
            except TimeoutExpired:
                # Kill process, because this is not done automatically when p.communicate is used
                # See: https://docs.python.org/3/library/subprocess.html#subprocess.Popen.communicate
                # print("Killing docker exec for container " + self.container_id)
                p.kill()
                stdout, stderr = [o.decode("utf-8", "ignore") for o in p.communicate()]
                return stdout, stderr

            # FIXME: Verify container is still alive

        return stdout, stderr
