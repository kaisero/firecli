import json
import os
import pprint
import time

import click

from logging import getLogger
from json import JSONDecodeError
from typing import Any, Dict

from rich.console import Console

from firecli.api.click import FireCliGroup, FireCliCommand

logger = getLogger(__name__)

HELP: Dict[str, Any]
HELP = {
    'cmd': 'Application log analysis',
    'show': {'cmd': 'Display complete log file', 'path': 'Filesystem location of FireCLI log file'},
    'tail': {'cmd': 'Tail application log file', 'path': 'Filesystem location of FireCLI log file'},
}


@click.group(cls=FireCliGroup('log'), short_help=HELP['cmd'])
def log():
    pass


@log.command(cls=FireCliCommand('log.show'), short_help=HELP['show']['cmd'])
@click.option('--path', required=False, type=click.Path(exists=True), help=HELP['show']['path'])
@click.pass_obj
def show(obj, path):
    """Show complete FireCLI log file

    \b
    Example:
        › firecli log show
    \b
        (...)
        {asctime: 2021-01-01 00:00:05,
         exc_info: None,
         levelname: INFO,
         lineno: 26,
         message: Initializing connection to Firepower Management Center (fmc.example.com)...,
         name: firecli.api,
         pathname: /usr/lib/python/firecli/firecli/api/__init__.py,
         session_id: c0181990}
         (...)
    """
    console = obj.console  # type: Console
    logfile = obj.cfg['logfile'] if not path else path

    logger.debug('Opening "%s" to display log entries...', logfile)

    with open(logfile, 'r') as f:
        for line in f.readlines():
            try:
                console.print(
                    pprint.pformat(json.loads(line), width=console.width)
                    .replace('\\n', '')
                    .replace('"', '')
                    .replace("'", '')
                )
            except JSONDecodeError:
                console.print('Parser failed to format log entry. Make sure JSON log entry is valid')
                console.print(line)


@log.command(cls=FireCliCommand('log.tail'), short_help=HELP['tail']['cmd'])
@click.option('--path', required=False, type=click.Path(exists=True), help=HELP['tail']['path'])
@click.pass_obj
def tail(obj, path):
    """Tail FireCLI log file. Only new log entries  of firecli.log will be displayed.

    \b
    Example:
        › firecli log tail
    \b
        (...)
        {asctime: 2021-01-01 00:00:05,
         exc_info: None,
         levelname: INFO,
         lineno: 26,
         message: Initializing connection to Firepower Management Center (fmc.example.com)...,
         name: firecli.api,
         pathname: /usr/lib/python/firecli/firecli/api/__init__.py,
         session_id: c0181990}
        (...)
    """
    console = obj.console  # type: Console
    logfile = obj.cfg['logfile'] if not path else path

    logger.debug('Opening "%s" to tail logfile...', logfile)

    with open(logfile, 'r') as f:
        f.seek(0, os.SEEK_END)
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.1)
                continue
            try:
                console.print(
                    pprint.pformat(json.loads(line), width=console.width)
                    .replace('\\n', '')
                    .replace('"', '')
                    .replace("'", '')
                )
            except JSONDecodeError:
                console.print('Parser failed to format log entry. Make sure JSON log entry is valid')
                console.print(line)


log.add_command(show)
log.add_command(tail)
