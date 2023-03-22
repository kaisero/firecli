import sys
from logging import getLogger
from pprint import pprint
from typing import Dict

import click
from fireREST.exceptions import ResourceNotFoundError

from firecli.api.cache import FmcCache
from firecli.api.click import FireCliGroup, FireCliCommand
from firecli.api.compliance import ZoneCompliance

logger = getLogger(__name__)

HELP: Dict[str, Dict]
HELP = {
    'compliance': {
        'cmd': 'Security compliance checks',
        'profile': 'Configuration profile used to apply compliance checks against',
        'inter-zone-communication': {
            'cmd': 'Check accesspolicy against zone concept',
            'accesspolicy': 'Accesspolicy that will be validated',
            'device': 'Associated device. Neccessary to parse obj overrides correctly',
        },
    }
}


@click.group(cls=FireCliGroup('compliance'), short_help=HELP['compliance']['cmd'])
@click.option('--profile', required=False, type=str, default='default', help=HELP['compliance']['profile'])
@click.pass_obj
def compliance(obj, profile):
    """compliance grouping command. Placeholder for cache related commands
    """
    obj['compliance'] = {'profile': profile}


@compliance.command(
    cls=FireCliCommand('compliance.inter_zone_communication'),
    short_help=HELP['compliance']['inter-zone-communication']['cmd'],
)
@click.option(
    '--accesspolicy', required=False, type=str, help=HELP['compliance']['inter-zone-communication']['accesspolicy']
)
@click.option('--device', required=False, type=str, help=HELP['compliance']['inter-zone-communication']['device'])
@click.pass_obj
def inter_zone_communication(obj, accesspolicy, device):
    api = obj.api
    fmc = api.fmc
    cfg = obj.cfg
    profile = cfg['compliance']['profiles'][cfg['compliance']['profile']]

    try:
        accesspolicy = fmc.policy.accesspolicy.get(name=accesspolicy)
    except ResourceNotFoundError:
        logger.error('Could not find accesspolicy "%s". Exiting.', accesspolicy)
        sys.exit(2)
    try:
        devicehapair = fmc.devicehapair.ftddevicehapair.get(name=device)
        device = devicehapair['primary']['id']
    except ResourceNotFoundError:
        try:
            device = fmc.device.devicerecord.get(name=device)
        except ResourceNotFoundError:
            logger.error('Could not find device "%s". Exiting.', device)
            sys.exit(2)

    fmc_cache = FmcCache(cfg['cache_dir']).load()
    for policy in fmc_cache['policies'].cache['accesspolicy']:
        if policy['id'] == accesspolicy['id']:
            accessrules = policy['rules']
            accessrules = api.expanded_accessrules(accessrules, fmc['objects'].cache, device['id'])
            zone_compliance = ZoneCompliance(profile['zones'], profile['matrix'], accessrules)
            report = zone_compliance.check_compliance()
            pprint(report)
