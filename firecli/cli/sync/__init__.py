import sys
from logging import getLogger
from typing import Dict

import click

from firecli.api import API

from fireREST import FMC
from fireREST.exceptions import ResourceNotFoundError

from firecli.api.click import FireCliCommand, FireCliGroup

logger = getLogger(__name__)

HELP: Dict[str, Dict]
HELP = {
    'sync': {
        'cmd': 'Configuration synchronisation',
        'hapair': {
            'cmd': 'Synchronise configuration between two ftd hapairs',
            'src': 'Name of source devicehapair',
            'dst': 'Name of destination devicehapair',
        },
    }
}


@click.group(cls=FireCliGroup('sync'), short_help=HELP['sync']['cmd'])
def sync():
    pass


@sync.command(cls=FireCliCommand('sync.hapair'), short_help=HELP['sync']['hapair']['cmd'])
@click.option('--src', required=False, type=str, help=HELP['sync']['hapair']['src'])
@click.option('--dst', required=False, type=str, help=HELP['sync']['hapair']['dst'])
@click.pass_obj
def hapair(obj, src, dst):
    api = obj.api  # type: API
    fmc = api.fmc  # type: FMC

    logger.info('Synchronizing configuration from %s to %s...', src, dst)
    try:
        src = fmc.devicehapair.ftdhapair.get(name=src)
        dst = fmc.devicehapair.ftdhapair.get(name=dst)
    except ResourceNotFoundError as exc:
        logger.error(str(exc))
        sys.exit(2)

    api.sync_device_subinterfaces(src['primary']['id'], dst['primary']['id'])
    api.sync_device_staticroutes(src['primary']['id'], dst['primary']['id'])
    api.sync_device_monitoredinterfaces(src['id'], dst['id'])
    api.sync_device_policyassignments(src['primary']['id'], dst['primary']['id'])
    api.deploy_configuration(dst['primary']['id'])
