import logging
import sys

from functools import wraps
from logging import getLogger
from os import environ
from typing import Dict, Any

import click

from firecli import CFG
from firecli.api import API
from firecli.api.click import FireCliGroup
from firecli.api.state import State
from firecli.cli.accesspolicy import accesspolicy
from firecli.cli.cache import cache
from firecli.cli.compliance import compliance
from firecli.cli.log import log
from firecli.cli.object import obj
from firecli.cli.report import report
from firecli.cli.s2svpn import s2svpn
from firecli.cli.sync import sync
from firecli.version import __version__

from rich.console import Console

HELP: Dict[str, Any]
HELP = {
    'cfg': 'Path to configuration file',
    'hostname': 'Hostname of Firepower Management Center',
    'domain': 'Management domain of Firepower Management Center',
    'username': 'Username of fmc api user. It is recommended to create a dedicated api user',
    'password': 'Password of fmc api user',
    'timeout': 'Api request timeout in seconds for connections to Firepower Management Center',
    'afa-hostname': 'Hostname of AlgoSec Firewall Analyzer',
    'afa-username': 'Username of afa api user. It is recommended to create a dedicated api user',
    'afa-password': 'Password of afa api user',
    'afa-timeout': 'Api request timeout in seconds for connections to AlgoSec Firewall Analyzer',
    'dry_run': 'Display changes without performing an action',
    'debug': 'Enable debug loglevel',
    'trace': 'Enable trace loglevel. Includes debug logging for all api calls',
    'no_proxy': 'Ignore system proxy settings',
}

DEFAULTS = {
    'hostname': None,
    'domain': None,
    'username': None,
    'password': None,
    'timeout': None,
    'afa-hostname': None,
    'afa-username': None,
    'afa-password': None,
    'afa-timeout': None,
    'dry_run': False,
    'debug': False,
    'trace': False,
    'no_proxy': False,
}

logger = getLogger(__name__)

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


def log_exceptions(f):
    """ log exceptions
    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as exc:  # noqa: B902
            logger.critical(str(exc), exc_info=True)
            raise

    return wrapper


@click.group(FireCliGroup(''), invoke_without_command=False, no_args_is_help=True, context_settings=CONTEXT_SETTINGS)
@click.version_option(prog_name='FireCLI', version=__version__)
@click.option('--hostname', type=str, default=DEFAULTS['hostname'], help=HELP['hostname'])
@click.option('--domain', type=str, default=DEFAULTS['domain'], help=HELP['domain'])
@click.option('--username', type=str, default=DEFAULTS['username'], help=HELP['username'])
@click.option('--password', type=str, default=DEFAULTS['password'], help=HELP['password'])
@click.option('--timeout', type=int, default=DEFAULTS['timeout'], help=HELP['timeout'])
@click.option('--afa-hostname', type=str, default=DEFAULTS['afa-hostname'], help=HELP['afa-hostname'])
@click.option('--afa-username', type=str, default=DEFAULTS['afa-username'], help=HELP['afa-username'])
@click.option('--afa-password', type=str, default=DEFAULTS['afa-password'], help=HELP['afa-password'])
@click.option('--afa-timeout', type=int, default=DEFAULTS['afa-timeout'], help=HELP['afa-timeout'])
@click.option('--dry-run', default=DEFAULTS['dry_run'], is_flag=True, help=HELP['dry_run'])
@click.option('--debug', default=DEFAULTS['debug'], is_flag=True, help=HELP['debug'])
@click.option('--trace', default=DEFAULTS['trace'], is_flag=True, help=HELP['trace'])
@click.option('--no-proxy', default=DEFAULTS['no_proxy'], is_flag=True, help=HELP['no_proxy'])
@click.pass_context
@log_exceptions
def main(
    ctx,
    hostname,
    domain,
    username,
    password,
    timeout,
    afa_hostname,
    afa_username,
    afa_password,
    afa_timeout,
    dry_run,
    debug,
    trace,
    no_proxy,
):
    """FireCLI is a command line interface to Firepower Management Center that automates a variety of tasks
    """
    if '--help' not in sys.argv[1:] and '-h' not in sys.argv[1:]:
        # enable debug logging if --debug flag is set
        if debug or trace:
            loggers = ['firecli', 'fireREST'] if trace else ['firecli']
            loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict if name in loggers]
            for item in loggers:
                item.setLevel(logging.DEBUG)
        else:
            firerest_loggers = [
                logging.getLogger(name) for name in logging.root.manager.loggerDict if 'fireREST' in name
            ]
            for item in firerest_loggers:
                item.setLevel(logging.WARNING)

        # disable proxy settings if --no-proxy flag is set
        if no_proxy:
            try:
                del environ['http_proxy']
                del environ['https_proxy']
                logger.debug(
                    'System proxy settings were overwritten manually. '
                    'API calls to fmc will be performed directly and not through system proxy'
                )
            except KeyError:
                pass

        # configuration
        CFG['dry_run'] = dry_run

        # overwrite configuration if set manually
        fmc_options = {
            'hostname': hostname,
            'domain': domain,
            'username': username,
            'password': password,
            'timeout': timeout,
        }
        afa_options = {
            'afa-hostname': afa_hostname,
            'afa-username': afa_username,
            'afa-password': afa_password,
            'afa-timeout': afa_timeout,
        }

        for k, v in fmc_options.items():
            if v is not DEFAULTS[k]:
                CFG['fmc'][k] = v

        for k, v in afa_options.items():
            if v is not DEFAULTS[k]:
                CFG['afa'][k.replace('afa-', '')] = v

        # cache directory
        CFG['cache_dir'] = f'{CFG["cache_dir"]}/{CFG["fmc"]["hostname"]}/{CFG["fmc"]["domain"]}'

        # State object initialization
        api = API(cfg=CFG)
        cfg = CFG
        console = Console()
        ctx.obj = State(api=api, cfg=cfg, console=console)


main.add_command(accesspolicy)
main.add_command(cache)
main.add_command(compliance)
main.add_command(log)
main.add_command(obj)
main.add_command(report)
main.add_command(sync)
main.add_command(s2svpn)
