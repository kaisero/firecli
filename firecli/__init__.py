#!/usr/bin/env python
#
# This file is part of FireCLI

import logging.config
import os
import platform
import sys
import uuid
from pathlib import Path
from string import Template

import stackprinter
import yaml

from pythonjsonlogger.jsonlogger import JsonFormatter

# Error out if run with Python 2
if int(platform.python_version_tuple()[0]) != 3 or int(platform.python_version_tuple()[1]) < 6:
    print('Python 2 is not supported; please run FireCLI using Python 3.7+')
    sys.exit(1)

# install stackprinter hook to enhance exception output
stackprinter.set_excepthook(style='darkbg2')


# Constant definitions
BASE_DIR = Path(__file__).resolve().parent
PROJECT_NAME = 'firecli'

SITE_PACKAGES_DIR = 'site-packages'
SYSTEM_CFG_DIR = f'/etc/{PROJECT_NAME}'
SYSTEM_CFG_DIR_DEFAULT = f'{sys.prefix}/{PROJECT_NAME}/etc'
SYSTEM_LOG_DIR = '/var/log'
SYSTEM_LOG_FILE = f'{SYSTEM_LOG_DIR}/{PROJECT_NAME}.log'

MODULE_CFG_DIR = f'{BASE_DIR}/etc'
MAC_MODULE_CFG_DIR = f'{BASE_DIR.parent.parent.parent.parent}/{PROJECT_NAME}/etc'
PROJECT_DIR = BASE_DIR.parent
PROJECT_CFG_DIR = f'{PROJECT_DIR}/etc'

HOME_DIR = Path.home()
HOME_CFG_DIR = f'{HOME_DIR}/.{PROJECT_NAME}'
HOME_LOG_DIR = f'{HOME_CFG_DIR}/logs'

CFG_DIRS = [HOME_CFG_DIR, SYSTEM_CFG_DIR, SYSTEM_CFG_DIR_DEFAULT, MODULE_CFG_DIR, MAC_MODULE_CFG_DIR, PROJECT_CFG_DIR]


# Auto generated session id used in log messages
SESSION_ID = str(uuid.uuid4())[:8]


# Configuration Loader
def load_cfg(cfg_file: str):
    """Find configuration file based on CFG_DIRS order
    """
    for cfg_dir in CFG_DIRS:
        fullpath = Path(f'{cfg_dir}/{cfg_file}')
        if fullpath.is_file():
            return str(fullpath)
    print(f'Could not find Configuration file {cfg_file} in any of the following cfg directories: {CFG_DIRS}')


# Log Directory locator
def log_dir(cfg: dict):
    """Set correct logging directory based on mode of execution
    """
    if 'log_dir' in cfg:
        if cfg['log_dir'] is not None:
            return str(Path(cfg['log_dir']).expanduser())
    if PROJECT_DIR.stem != SITE_PACKAGES_DIR:
        return PROJECT_DIR
    if os.access(SYSTEM_LOG_FILE, os.W_OK):
        return SYSTEM_LOG_DIR
    return HOME_LOG_DIR


# Initialize home logging directory
Path(HOME_LOG_DIR).mkdir(parents=True, exist_ok=True)

# Load application configuration
with open(load_cfg(f'{PROJECT_NAME}.yml')) as f:
    CFG = yaml.safe_load(f)

# Load logging configuration
with open(load_cfg('logging.yml')) as f:
    logging_cfg = yaml.safe_load(f)


class FileFormatter(JsonFormatter):
    def formatException(self, exc_info):
        msg = stackprinter.format(exc_info)
        msg_indented = '    ' + '\n    '.join(msg.split('\n')).strip()
        return msg_indented


class ConsoleFormatter(logging.Formatter):
    def formatException(self, exc_info):
        msg = stackprinter.format(exc_info)
        msg_indented = '    ' + '\n    '.join(msg.split('\n')).strip()
        return msg_indented


class FileLoggingFilter(logging.Filter):
    def __init__(self):
        self.session_id = SESSION_ID
        super().__init__()

    def filter(self, record):
        record.session_id = self.session_id
        return True


class ConsoleLoggingFilter(logging.Filter):
    def __init__(self, clear=True):
        self.session_id = SESSION_ID
        super().__init__()

    def filter(self, record):
        # do not log exceptions to console using logger
        # fixes duplicate stacktraces (stderr + logger)
        if record.exc_info:
            return False
        record.session_id = self.session_id
        return True


logging_dir = log_dir(CFG)
logging_filename = Template(logging_cfg['handlers']['file']['filename']).substitute(
    LOG_DIR=logging_dir, PROJECT_NAME=PROJECT_NAME
)
logging_cfg['handlers']['file']['filename'] = logging_filename
logging.config.dictConfig(logging_cfg)
CFG['logfile'] = logging_filename

logger = logging.getLogger(__name__)
