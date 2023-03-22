import sys

from logging import getLogger
from typing import Dict

import click

from fireREST.exceptions import ResourceNotFoundError

from firecli.api.click import FireCliCommand, FireCliGroup

logger = getLogger(__name__)

HELP: Dict[str, Dict]
HELP = {
    'cmd': 'Manage filepolicy in accesspolicy',
    'name': 'Name of filepolicy',
    'enable': {
        'cmd': 'Enable filepolicy for rules matching a specified protocol filter',
        'protocols': 'Protocols for which filepolicy will be enabled',
        'protocols_choices': ['any', 'supported', 'ftp', 'http', 'smb', 'smtp'],
    },
}


@click.group(cls=FireCliGroup('accesspolicy.filepolicy'), short_help=HELP['cmd'])
@click.option('--name', required=False, type=str, help=HELP['name'])
@click.pass_obj
def filepolicy(obj, name):
    fmc = obj.api.fmc
    state = obj.state

    try:
        state['accesspolicy']['filepolicy'] = fmc.policy.filepolicy.get(name=name)
    except ResourceNotFoundError:
        logger.error('Filepolicy "%s" not found. Exiting.', name)
        sys.exit(2)


@filepolicy.command(cls=FireCliCommand('accesspolicy.filepolicy.enable'), short_help=HELP['enable']['cmd'])
@click.option(
    '--protocols', required=False, type=click.Choice(HELP['enable']['protocols_choices']), help=HELP['enable']['cmd']
)
@click.pass_obj
def enable(obj, protocols):
    api = obj.api
    accesspolicy = obj.state['accesspolicy']
    filepolicy = accesspolicy['filepolicy']

    logger.info(
        'Applying filepolicy "%s" to all accessrules in "%s" that match destination protocol "%s"',
        filepolicy['name'],
        accesspolicy['name'],
        protocols,
    )

    api.accesspolicy_filepolicy_enable(accesspolicy['id'], filepolicy['id'], protocols)
