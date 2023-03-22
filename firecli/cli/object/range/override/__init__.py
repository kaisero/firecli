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
    'cmd': 'Range object override commands',
    'import': {
        'cmd': 'Import range object overrides from yaml configuration file',
        'src': 'Path to yaml import file. e.g. /tmp/overrides.yml',
    },
    'export': {
        'cmd': 'Export range object overrides to yaml configuration file',
        'dst': 'Path to yaml export file. e.g. /tmp/overrides.yml',
    },
}


@click.group(cls=FireCliGroup('object.range.override'), short_help=HELP['cmd'])
def override():
    pass


@override.command(cls=FireCliCommand('object.range.override.import'), name='import', short_help=HELP['import']['cmd'])
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
        firecli object range override import --src /tmp/overrides.yml

    \b
    Import supports dry-mode to only display changes that would occur:
        firecli --dry-mode object range override import --src /tmp/overrides.yml

    \b
    Import File Format:
        objects:
          ranges:
            - name: FireCliTestRangeObj
              overrides:
                - target: ftd01.example.com
                  value: 198.18.100.0-198.18.100.100
                - target: ftd02.example.com
                  value: 198.18.200.0-198.18.200.100
    """
    fmc = obj.api.fmc  # type: FMC

    logger.info('Validating Object Override configuration...')
    ranges = fmc.object.range.get()
    devices = fmc.device.devicerecord.get()
    devicehapairs = fmc.devicehapair.ftdhapair.get()
    unknown_ranges = []
    unknown_devices = []
    for range in src['objects']['ranges']:
        obj_exists = False
        for item in ranges:
            if item['name'] == range['name']:
                range['id'] = item['id']
                obj_exists = True
        if not obj_exists:
            unknown_ranges.append(range['name'])
        for override in range['overrides']:
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
    if len(unknown_ranges) > 0:
        logger.error('range Object(s) not found: %s. Exiting', ', '.join(unknown_ranges))
        sys.exit(os.EX_DATAERR)

    logger.info('Updating Object Override configuration according to configuration file')
    for range in src['objects']['ranges']:
        container_uuid = None
        for item in ranges:
            if item['name'] == range['name']:
                container_uuid = item['id']
                range['type'] = item['type']
        existing_overrides = fmc.object.range.override.get(container_uuid=container_uuid)
        for override in range['overrides']:
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
                        'Range Object Override for %s and device %s already exists. ' 'Updating value from %s to %s',
                        range['name'],
                        override['target'],
                        existing_override_for_device['value'],
                        override['value'],
                    )
                else:
                    logger.info(
                        'Creating new range Object Override for %s and device %s with value %s',
                        range['name'],
                        override['target'],
                        override['value'],
                    )
                data = {
                    'overrides': {
                        'parent': {'id': range['id']},
                        'target': {'id': override['target_id'], 'type': 'Device'},
                    },
                    'value': override['value'],
                    'name': range['name'],
                    'id': range['id'],
                }
                try:
                    fmc.object.range.update(data=data)
                except GenericApiError as exc:
                    logger.error('Operation failed with error: %s', str(exc))

            else:
                logger.debug(
                    'Range Object Override for %s and device %s with value %s already exists. Skipping...',
                    range['name'],
                    override['target'],
                    override['value'],
                )


@override.command(cls=FireCliCommand('object.range.override.export'), name='export', short_help=HELP['export']['cmd'])
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
        firecli object range override export --dst /tmp/overrides.yml

    """
    fmc = obj.api.fmc  # type: FMC
    logger.info('Downloading Range Object Override configuration from FMC...')
    network_ranges = fmc.object.range.get()
    overrides = []
    for network_Range in network_ranges:
        if network_Range['overridable']:
            override = fmc.object.range.override.get(container_uuid=network_Range['id'])
            if len(override) > 0:
                overrides.append(override)

    logger.info('Parsing Range Object Overrides...')
    report = {'objects': {'ranges': []}}
    for obj in overrides:
        network_Range = {'name': obj[0]['name'], 'overrides': []}
        for item in obj:
            override = {'target': item['overrides']['target']['name'], 'value': item['value']}
            network_Range['overrides'].append(override)

        report['objects']['ranges'].append(network_Range)

    logger.info('Exporting Object Override configuration to %s', str(dst))
    if Path(dst).exists():
        with open(dst, 'r') as f:
            dst_yaml = yaml.safe_load(f)
        dst_yaml['objects']['ranges'] = report['objects']['ranges']
        report = dst_yaml
    with open(dst, 'w') as f:
        yaml.dump(report, f)
