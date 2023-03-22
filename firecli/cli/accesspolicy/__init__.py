import sys
from datetime import datetime
from logging import getLogger
from pprint import pprint
from typing import Any, Dict

import click
from fireREST import FMC
from fireREST.exceptions import ResourceNotFoundError

from firecli.api import API
from firecli.api.cache import FmcCache
from firecli.api.click import FireCliGroup, FireCliCommand
from firecli.cli.accesspolicy.filepolicy import filepolicy

logger = getLogger(__name__)

HELP: Dict[str, Any]
HELP = {
    'cmd': 'Accesspolicy management',
    'name': 'Name of accesspolicy',
    'device': 'Name of assigned device',
    'export': {
        'cmd': 'Export accesspolicy configuration',
        'filter': 'Filter accessrules',
        'format': 'Export file format',
        'include-hitcount': 'Include rule hitcount',
        'export-dir': 'Directory to which the export will be saved',
    },
}


@click.group(cls=FireCliGroup('accesspolicy'), short_help=HELP['cmd'])
@click.option('--name', required=False, type=str, help=HELP['name'])
@click.option('--device', required=False, type=str, help=HELP['device'])
@click.pass_obj
def accesspolicy(obj, name, device):
    fmc = obj.api.fmc  # type: FMC
    state = obj.state

    try:
        state['accesspolicy'] = fmc.policy.accesspolicy.get(name=name)
    except ResourceNotFoundError:
        logger.error('Accesspolicy "%s" not found. Exiting.', name)
        sys.exit(2)

    obj.state['device'] = {'name': None, 'id': None}
    if device:
        try:
            devicehapair = fmc.devicehapair.ftdhapair.get(name=device)
            state['device'] = devicehapair['primary']['id']
        except ResourceNotFoundError:
            try:
                state['device'] = fmc.device.devicerecord.get(name=device)
            except ResourceNotFoundError:
                logger.error('Device "%s" not found. Exiting.', device)
                sys.exit(2)
    else:
        try:
            policyassignment = fmc.assignment.policyassignment.get(uuid=state['accesspolicy']['id'])
            if policyassignment['targets'][0]['type'] == 'DeviceHAPair':
                hapair_id = policyassignment['targets'][0]['id']
                device_id = fmc.devicehapair.ftdhapair.get(uuid=hapair_id)['primary']['id']
                state['device'] = fmc.device.devicerecord.get(uuid=device_id)
            else:
                state['device'] = policyassignment['targets'][0]
            logger.debug(
                'No device set during initialization. Got "%s" as first match from accesspolicy',
                state['device']['name'],
            )
        except ResourceNotFoundError:
            logger.debug('Accesspolicy "%s" is not assigned to any device. Could not auto-populate device', name)


@accesspolicy.command(cls=FireCliCommand('accesspolicy.export'), help=HELP['export']['cmd'])
@click.option(
    '--filter',
    'policy_filter',
    required=False,
    type=click.Choice(['parent', 'child']),
    default='child',
    help=HELP['export']['filter'],
)
@click.option(
    '--format', 'fmt', required=False, type=click.Choice(['csv', 'xlsx']), default='csv', help=HELP['export']['format']
)
@click.option(
    '--include-hitcount',
    'include_hitcount',
    is_flag=True,
    required=False,
    default=False,
    help=HELP['export']['include-hitcount'],
)
@click.option('--dir', 'export_dir', required=False, type=str, default='', help=HELP['export']['export-dir'])
@click.pass_obj
def export(obj, policy_filter, fmt, include_hitcount, export_dir):
    api = obj.api  # type: API
    fmc = api.fmc  # type: FMC
    cfg = obj.cfg
    policy = obj.state['accesspolicy']
    device = obj.state['device']
    export_filename = f'{policy["name"]}_{datetime.now().strftime("%Y%m%d-%H%M%S")}.{fmt}'
    export_filename = f'{export_dir}/{export_filename}' if export_dir != '' else export_filename

    logger.info('Exporting accesspolicy "%s" in %s format...', policy['name'], fmt)
    cache = FmcCache(cfg['cache_dir']).load()
    accessrules = api.filtered_accessrules(
        policy['id'], fmc.policy.accesspolicy.accessrule.get(container_uuid=policy['id']), policy_filter
    )
    accessrules = api.expanded_accessrules(accessrules, cache['objects'].cache, device['id'])

    if include_hitcount:
        hitcounts = fmc.policy.accesspolicy.operational.hitcount.get(
            container_uuid=policy['id'], device_id=device['id']
        )
        for accessrule in accessrules:
            for hitcount in hitcounts:
                if hitcount['rule']['id'] == accessrule['id']:
                    accessrule['hitcount'] = hitcount

    report = [api.csv_header('accessrule')]
    report.extend([api.accessrule_to_csv(item) for item in accessrules])
    report = api.csv_squashed(report)

    logger.info('Saving report to %s', export_filename)
    if fmt == 'csv':
        with open(f'{export_filename}', 'w') as f:
            f.write('\n'.join(report))
    elif fmt == 'xlsx':
        workbook = api.to_excel('accesspolicy', report)
        workbook.save(f'{export_filename}')


accesspolicy.add_command(export)
accesspolicy.add_command(filepolicy)
