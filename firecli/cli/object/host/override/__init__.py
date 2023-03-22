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
    'cmd': 'Host object override commands',
    'import': {
        'cmd': 'Import host object overrides from yaml configuration file',
        'src': 'Path to yaml import file, e.g. /tmp/overrides.yml',
    },
    'export': {
        'cmd': 'Export host object overrides to yaml configuration file',
        'dst': 'Path to yaml export file. e.g. /tmp/overrides.yml',
    },
}


@click.group(cls=FireCliGroup('object.host.override'), short_help=HELP['cmd'])
def override():
    pass


@override.command(
    cls=FireCliCommand('object.host.override.import_cfg'), name='import', short_help=HELP['import']['cmd']
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
        firecli object host override import --src /tmp/overrides.yml

    \b
    Import supports dry-mode to only display changes that would occur:
        firecli --dry-mode object host override import --src /tmp/overrides.yml

    \b
    Import File Format:
        objects:
          hosts:
            - name: FireCliTestHostObj
              overrides:
                - target: ftd01.example.com
                  value: 198.18.100.1
                - target: ftd02.example.com
                  value: 198.18.200.1
    """
    fmc = obj.api.fmc  # type: FMC

    logger.info('Validating Object Override configuration...')
    hosts = fmc.object.host.get()
    devices = fmc.device.devicerecord.get()
    devicehapairs = fmc.devicehapair.ftdhapair.get()
    unknown_hosts = []
    unknown_devices = []
    for host in src['objects']['hosts']:
        obj_exists = False
        for item in hosts:
            if item['name'] == host['name']:
                host['id'] = item['id']
                obj_exists = True
        if not obj_exists:
            unknown_hosts.append(host['name'])
        for obj_override in host['overrides']:
            device_exists = False
            for device in devices:
                if device['name'] == obj_override['target']:
                    obj_override['target_id'] = device['id']
                    device_exists = True
            for device in devicehapairs:
                if device['name'] == obj_override['target']:
                    obj_override['target_id'] = device['primary']['id']
                    device_exists = True
            if not device_exists:
                unknown_devices.append(obj_override['target'])
    if len(unknown_devices) > 0:
        logger.error('Device(s) not found: %s. Exiting', ', '.join(unknown_devices))
        sys.exit(os.EX_DATAERR)
    if len(unknown_hosts) > 0:
        logger.error('Host Object(s) not found: %s. Exiting', ', '.join(unknown_hosts))
        sys.exit(os.EX_DATAERR)

    logger.info('Updating Object Override configuration according to configuration file')
    for host in src['objects']['hosts']:
        container_uuid = None
        for item in hosts:
            if item['name'] == host['name']:
                container_uuid = item['id']
        existing_overrides = fmc.object.host.override.get(container_uuid=container_uuid)
        for obj_override in host['overrides']:
            identical_override_already_exists = False
            override_for_device_already_exists = False
            existing_override_for_device = None
            for existing_override in existing_overrides:
                if existing_override['overrides']['target']['name'] == obj_override['target']:
                    existing_override_for_device = existing_override
                    override_for_device_already_exists = True
                    if existing_override['value'] == obj_override['value']:
                        identical_override_already_exists = True
            if not identical_override_already_exists:
                if override_for_device_already_exists:
                    logger.info(
                        'Host Object Override for %s and device %s already exists. ' 'Updating value from %s to %s',
                        host['name'],
                        obj_override['target'],
                        existing_override_for_device['value'],
                        obj_override['value'],
                    )
                else:
                    logger.info(
                        'Creating new Host Object Override for %s and device %s with value %s',
                        host['name'],
                        obj_override['target'],
                        obj_override['value'],
                    )
                data = {
                    'overrides': {
                        'parent': {'id': host['id']},
                        'target': {'id': obj_override['target_id'], 'type': 'Device'},
                    },
                    'value': obj_override['value'],
                    'name': host['name'],
                    'id': host['id'],
                }
                try:
                    fmc.object.host.update(data=data)
                except GenericApiError as exc:
                    logger.error('Operation failed with error: %s', str(exc))

            else:
                logger.debug(
                    'Host Object Override for %s and device %s with value %s already exists. Skipping...',
                    host['name'],
                    obj_override['target'],
                    obj_override['value'],
                )


@override.command(
    cls=FireCliCommand('object.host.override.export_cfg'), name='export', short_help=HELP['export']['cmd']
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
        firecli object host override export --dst /tmp/overrides.yml

    """
    fmc = obj.api.fmc  # type: FMC
    logger.info('Downloading Host Object Override configuration from FMC...')
    hosts = fmc.object.host.get()
    overrides = []
    for host in hosts:
        if host['overridable']:
            obj_override = fmc.object.host.override.get(container_uuid=host['id'])
            if len(obj_override) > 0:
                overrides.append(obj_override)

    logger.info('Parsing Host Object Overrides...')
    report = {'objects': {'hosts': []}}
    for obj in overrides:
        host = {'name': obj[0]['name'], 'overrides': []}
        for item in obj:
            obj_override = {'target': item['overrides']['target']['name'], 'value': item['value']}
            host['overrides'].append(obj_override)

        report['objects']['hosts'].append(host)

    logger.info('Exporting Object Override configuration to %s', str(dst))
    if Path(dst).exists():
        with open(dst, 'r') as f:
            dst_yaml = yaml.safe_load(f)
        dst_yaml['objects']['hosts'] = report['objects']['hosts']
        report = dst_yaml
    with open(dst, 'w') as f:
        yaml.dump(report, f)
