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
    'cmd': 'Network object override commands',
    'import': {
        'cmd': 'Import network object overrides from yaml configuration file',
        'src': 'Path to yaml import file, e.g. /tmp/overrides.yml',
    },
    'export': {
        'cmd': 'Export network object overrides to yaml configuration file',
        'dst': 'Path to yaml export file. e.g. /tmp/overrides.yml',
    },
}


@click.group(cls=FireCliGroup('object.network.override'), short_help=HELP['cmd'])
def override():
    pass


@override.command(
    cls=FireCliCommand('object.network.override.import_cfg'), name='import', short_help=HELP['import']['cmd']
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
        firecli object network override import --src /tmp/overrides.yml

    \b
    Import supports dry-mode to only display changes that would occur:
        firecli --dry-mode object network override import --src /tmp/overrides.yml

    \b
    Import File Format:
        objects:
          networks:
            - name: FireCliTestNetworkObj
              overrides:
                - target: ftd01.example.com
                  value: 198.18.100.0/24
                - target: ftd02.example.com
                  value: 198.18.200.0/24
    """
    fmc = obj.api.fmc  # type: FMC

    logger.info('Validating Object Override configuration...')
    networks = fmc.object.network.get()
    devices = fmc.device.devicerecord.get()
    devicehapairs = fmc.devicehapair.ftdhapair.get()
    unknown_networks = []
    unknown_devices = []
    for network in src['objects']['networks']:
        obj_exists = False
        for item in networks:
            if item['name'] == network['name']:
                network['id'] = item['id']
                obj_exists = True
        if not obj_exists:
            unknown_networks.append(network['name'])
        for override in network['overrides']:
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
    if len(unknown_networks) > 0:
        logger.error('Network Object(s) not found: %s. Exiting', ', '.join(unknown_networks))
        sys.exit(os.EX_DATAERR)

    logger.info('Updating Object Override configuration according to configuration file')
    for network in src['objects']['networks']:
        container_uuid = None
        for item in networks:
            if item['name'] == network['name']:
                container_uuid = item['id']
                network['type'] = item['type']
        existing_overrides = fmc.object.network.override.get(container_uuid=container_uuid)
        for override in network['overrides']:
            identical_override_already_exists = False
            override_for_device_already_exists = False
            existing_override_for_device = None
            for existing_override in existing_overrides:
                if existing_override['overrides']['target']['name'] == override['target']:
                    existing_override_for_device = existing_override
                    override_for_device_already_exists = True
                    if existing_override['value'] == override['value']:
                        identical_override_already_exists = True
            if not identical_override_already_exists:
                if override_for_device_already_exists:
                    logger.info(
                        'Network Object Override for %s and device %s already exists. ' 'Updating value from %s to %s',
                        network['name'],
                        override['target'],
                        existing_override_for_device['value'],
                        override['value'],
                    )
                else:
                    logger.info(
                        'Creating new Network Object Override for %s and device %s with value %s',
                        network['name'],
                        override['target'],
                        override['value'],
                    )
                data = {
                    'overrides': {
                        'parent': {'id': network['id']},
                        'target': {'id': override['target_id'], 'type': 'Device'},
                    },
                    'value': override['value'],
                    'name': network['name'],
                    'id': network['id'],
                }
                try:
                    fmc.object.network.update(data=data)
                except GenericApiError as exc:
                    logger.error('Operation failed with error: %s', str(exc))

            else:
                logger.debug(
                    'Network Object Override for %s and device %s with value %s already exists. Skipping...',
                    network['name'],
                    override['target'],
                    override['value'],
                )


@override.command(
    cls=FireCliCommand('object.network.override.import_cfg'), name='export', short_help=HELP['export']['cmd']
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
        firecli object network override export --dst /tmp/overrides.yml

    """
    fmc = obj.api.fmc  # type: FMC
    logger.info('Downloading Network Object Override configuration from FMC...')
    networks = fmc.object.network.get()
    overrides = []
    for network in networks:
        if network['overridable']:
            override = fmc.object.network.override.get(container_uuid=network['id'])
            if len(override) > 0:
                overrides.append(override)

    logger.info('Parsing Network Object Overrides...')
    report = {'objects': {'networks': []}}

    for obj in overrides:
        network = {'name': obj[0]['name'], 'overrides': []}
        for item in obj:
            override = {'target': item['overrides']['target']['name'], 'value': item['value']}
            network['overrides'].append(override)

        report['objects']['networks'].append(network)

    logger.info('Exporting Object Override configuration to %s', str(dst))
    if Path(dst).exists():
        with open(dst, 'r') as f:
            dst_yaml = yaml.safe_load(f)
        dst_yaml['objects']['networks'] = report['objects']['networks']
        report = dst_yaml
    with open(dst, 'w') as f:
        yaml.dump(report, f)
