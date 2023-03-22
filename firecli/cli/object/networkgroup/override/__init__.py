import os
import sys
from logging import getLogger
from pathlib import Path
from typing import Any, Dict

import click
import yaml
from fireREST import FMC
from fireREST.exceptions import GenericApiError

from firecli.api.click import FireCliCommand, FireCliGroup
from firecli.api.click.callback import validate_and_load_yaml


logger = getLogger(__name__)

HELP: Dict[str, Any]
HELP = {
    'cmd': 'NetworkGroup object override commands',
    'import': {
        'cmd': 'Import networkgroup object overrides from yaml configuration file',
        'src': 'Path to yaml import file, e.g. /tmp/overrides.yml',
    },
    'export': {
        'cmd': 'Export networkgroup object overrides to yaml configuration file',
        'dst': 'Path to yaml export file. e.g. /tmp/overrides.yml',
    },
}


@click.group(cls=FireCliGroup('object.networkgroup.override'), short_help=HELP['cmd'])
def override():
    pass


@override.command(
    cls=FireCliCommand('object.networkgroup.override.import'), name='import', short_help=HELP['import']['cmd']
)
@click.option(
    '-s',
    '--src',
    'src',
    callback=validate_and_load_yaml,
    default='overrides.yml',
    required=False,
    type=click.Path(exists=True, readable=True),
    help=HELP['import']['src'],
)
@click.pass_obj
def import_cfg(obj, src):
    """Import object overrides from yaml configuration file

    \b
    Example:
        firecli object override import --src /tmp/overrides.yml

    \b
    Import supports dry-mode to only display changes that would occur:
        firecli --dry-mode object networkgroup override import --src /tmp/overrides.yml

    \b
    Import File Format:
        objects:
          networkgroups:
            - name: FireCliObjectGroup
              overrides:
                - target: ftd01.example.com
                  values:
                    - 198.18.0.0/24
                    - 198.18.1.0/24
                    - 198.18.2.1
                - target: ftd02.example.com
                  values:
                    - 198.19.0.0/24
                    - 198.19.1.0/24
                    - 198.19.2.1
    """
    fmc = obj.api.fmc  # type: FMC

    logger.info('Validating Object Override configuration...')
    networkgroups = fmc.object.networkgroup.get()
    devices = fmc.device.devicerecord.get()
    devicehapairs = fmc.devicehapair.ftdhapair.get()
    unknown_networkgroups = []
    unknown_devices = []
    for networkgroup in src['objects']['networkgroups']:
        obj_exists = False
        for item in networkgroups:
            if item['name'] == networkgroup['name']:
                networkgroup['id'] = item['id']
                obj_exists = True
        if not obj_exists:
            unknown_networkgroups.append(networkgroup['name'])
        for override in networkgroup['overrides']:
            device_exists = False
            for device in devices:
                if device['name'] == override['target']:
                    override['target_id'] = device['id']
                    device_exists = True
            for device in devicehapairs:
                if device['name'] == override['target']:
                    override['target_id'] = device['primary']['id']
                    device_exists = True
            if not device_exists:
                unknown_devices.append(override['target'])
    if len(unknown_devices) > 0:
        logger.error('Device(s) not found: %s. Exiting', ', '.join(unknown_devices))
        sys.exit(os.EX_DATAERR)
    if len(unknown_networkgroups) > 0:
        logger.error('Networkgroup Object(s) not found: %s. Exiting', ', '.join(unknown_networkgroups))
        sys.exit(os.EX_DATAERR)

    logger.info('Updating Object Override configuration according to configuration file')
    for networkgroup in src['objects']['networkgroups']:
        container_uuid = None
        for item in networkgroups:
            if item['name'] == networkgroup['name']:
                container_uuid = item['id']
                networkgroup['type'] = item['type']
        existing_overrides = fmc.object.networkgroup.override.get(container_uuid=container_uuid)
        for override in networkgroup['overrides']:
            identical_override_already_exists = False
            override_for_device_already_exists = False
            existing_values = []
            for existing_override in existing_overrides:
                if existing_override['overrides']['target']['name'] == override['target']:
                    override_for_device_already_exists = True
                    if 'literals' in existing_override:
                        existing_values = [item['value'] for item in existing_override['literals']]
                        if existing_values == override['values']:
                            identical_override_already_exists = True
            if not identical_override_already_exists:
                if override_for_device_already_exists:
                    logger.info(
                        'Networkgroup Object Override for %s and device %s already exists. '
                        'Updating value from %s to %s',
                        networkgroup['name'],
                        override['target'],
                        existing_values,
                        override['values'],
                    )
                else:
                    logger.info(
                        'Creating new Networkgroup Object Override for %s and device %s with value %s',
                        networkgroup['name'],
                        override['target'],
                        override['values'],
                    )
                data = {
                    'overrides': {
                        'parent': {'id': networkgroup['id']},
                        'target': {'id': override['target_id'], 'type': 'Device'},
                    },
                    'literals': [],
                    'name': networkgroup['name'],
                    'id': networkgroup['id'],
                }
                for item in override['values']:
                    literal = {'value': item, 'type': 'Network' if '/' in item else 'Range' if '-' in item else 'Host'}
                    data['literals'].append(literal)
                try:
                    fmc.object.networkgroup.update(data=data)
                except GenericApiError as exc:
                    logger.error('Operation failed with error: %s', str(exc))

            else:
                logger.debug(
                    'Networkgroup Object Override for %s and device %s with value %s already exists. Skipping...',
                    networkgroup['name'],
                    override['target'],
                    override['values'],
                )


@override.command(
    cls=FireCliCommand('object.networkgroup.override.export'), name='export', short_help=HELP['export']['cmd']
)
@click.option(
    '-d',
    '--dst',
    'dst',
    default='overrides.yml',
    required=False,
    type=click.Path(writable=True),
    help=HELP['export']['dst'],
)
@click.pass_obj
def export_cfg(obj, dst):
    """Export object overrides to yaml configuration file

    \b
    Example:
        firecli object networkgroup override export --dst /tmp/overrides.yml

    """
    fmc = obj.api.fmc  # type: FMC
    logger.info('Downloading Networkgroup Object Override configuration from FMC...')
    networkgroups = fmc.object.networkgroup.get()
    overrides = []
    for networkgroup in networkgroups:
        if networkgroup['overridable']:
            override = fmc.object.networkgroup.override.get(container_uuid=networkgroup['id'])
            if len(override) > 0:
                overrides.append(override)
    logger.info('Parsing Networkgroup Object Overrides...')
    report = {'objects': {'networkgroups': []}}
    for obj in overrides:
        networkgroup = {'name': obj[0]['name'], 'overrides': []}
        for item in obj:
            override = {
                'target': item['overrides']['target']['name'],
                'values': [literal['value'] for literal in item['literals']],
            }
            networkgroup['overrides'].append(override)

        report['objects']['networkgroups'].append(networkgroup)

    logger.info('Exporting Object Override configuration to %s', str(dst))
    if Path(dst).exists():
        with open(dst, 'r') as f:
            dst_yaml = yaml.safe_load(f)
        dst_yaml['objects']['networkgroups'] = report['objects']['networkgroups']
        report = dst_yaml
    with open(dst, 'w') as f:
        yaml.dump(report, f)
