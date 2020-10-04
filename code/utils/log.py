import io
import logging
from datetime import datetime
import os


def init_logging(log_level, log_path=""):
    logging.basicConfig(level=log_level, format='%(asctime)s %(name)-15s %(levelname)-8s %(message)s',
                        datefmt='%d.%m.%Y %H:%M')

    logging.getLogger("requests.packages.urllib3").setLevel(logging.ERROR)
    logging.getLogger("docker.auth").setLevel(logging.ERROR)
    logging.getLogger('docker.utils.config').setLevel(logging.ERROR)
    logging.getLogger('urllib3.connectionpool').setLevel(logging.ERROR)
    logging.getLogger('selenium.webdriver.remote.remote_connection').setLevel(logging.ERROR)

    logging.getLogger("PIL").setLevel(logging.ERROR)

    if log_path:
        if not os.path.exists(log_path):
            os.makedirs(log_path)

        filename = "corsica_daemon_{}.log".format(datetime.now().strftime("%Y%m%d_%H%M%S"))
        fh = logging.FileHandler("{}/{}".format(log_path, filename), 'w')
        fh.setLevel(log_level)

        if os.path.islink("{}/corsica_daemon.log".format(log_path)):
            os.remove("{}/corsica_daemon.log".format(log_path))
        os.symlink(filename, "{}/corsica_daemon.log".format(log_path))

        formatter = logging.Formatter('%(asctime)s %(name)-15s %(levelname)-8s %(message)s')
        fh.setFormatter(formatter)
        logging.getLogger().addHandler(fh)


def log_to_var(used_loggers):
    string_io = io.StringIO()
    ch = logging.StreamHandler(string_io)
    formatter = logging.Formatter('%(asctime)s %(name)-15s %(levelname)-8s %(message)s')
    ch.setFormatter(formatter)
    for logger in used_loggers:
        logging.getLogger(logger).addHandler(ch)
        logging.getLogger(logger).setLevel(logging.INFO)
    return string_io


def get_log_content(stringio):
    log_contents = stringio.getvalue()
    stringio.truncate(0)
    stringio.seek(0)
    return log_contents


def _log(logger, message, level):
    logging.getLogger(logger).log(level, message)


def _info(logger, message):
    _log(logger, message, logging.INFO)


def _debug(logger, message):
    _log(logger, message, logging.DEBUG)


def _warning(logger, message):
    _log(logger, message, logging.WARNING)


def _error(logger, message):
    _log(logger, message, logging.ERROR)


def _exception(logger, message):
    logging.getLogger(logger).exception(message)
