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
    'cmd': 'Timezone object override commands',
    'import': {
        'cmd': 'Import timezone object overrides from yaml configuration file',
        'src': 'Path to yaml import file, e.g. /tmp/overrides.yml',
    },
    'export': {
        'cmd': 'Export timezone object overrides to yaml configuration file',
        'dst': 'Path to yaml export file. e.g. /tmp/overrides.yml',
    },
}


@click.group(cls=FireCliGroup('object.timezone.override'), short_help=HELP['cmd'])
def override():
    pass


@override.command(
    cls=FireCliCommand('object.timezone.override.import_cfg'), name='import', short_help=HELP['import']['cmd']
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
        firecli object timezone override import --src /tmp/overrides.yml

    \b
    Import supports dry-mode to only display changes that would occur:
        firecli --dry-mode object timezone override import --src /tmp/overrides.yml

    \b
    Import File Format:
        objects:
          timezones:
            - name: FireCliTestTimezoneObj
              overrides:
                - target: ftd01.example.com
                  value: US/Washington
                - target: ftd02.example.com
                  value: Europe/Vienna
    """
    fmc = obj.api.fmc  # type: FMC

    logger.info('Validating Object Override configuration...')
    timezones = fmc.object.timezone.get()
    devices = fmc.device.devicerecord.get()
    devicehapairs = fmc.devicehapair.ftdhapair.get()
    unknown_timezones = []
    unknown_devices = []
    for timezone in src['objects']['timezones']:
        obj_exists = False
        for item in timezones:
            if item['name'] == timezone['name']:
                timezone['id'] = item['id']
                obj_exists = True
        if not obj_exists:
            unknown_timezones.append(timezone['name'])
        for obj_override in timezone['overrides']:
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
    if len(unknown_timezones) > 0:
        logger.error('Host Object(s) not found: %s. Exiting', ', '.join(unknown_timezones))
        sys.exit(os.EX_DATAERR)

    logger.info('Updating Object Override configuration according to configuration file')
    for timezone in src['objects']['timezones']:
        container_uuid = None
        for item in timezones:
            if item['name'] == timezone['name']:
                container_uuid = item['id']
        existing_overrides = fmc.object.timezone.override.get(container_uuid=container_uuid)
        for obj_override in timezone['overrides']:
            identical_override_already_exists = False
            override_for_device_already_exists = False
            existing_override_for_device = None
            for existing_override in existing_overrides:
                if existing_override['overrides']['target']['name'] == obj_override['target']:
                    existing_override_for_device = existing_override
                    override_for_device_already_exists = True
                    if existing_override['timeZoneId'] == obj_override['value']:
                        identical_override_already_exists = True
            if not identical_override_already_exists:
                if override_for_device_already_exists:
                    logger.info(
                        'Timezone Object Override for %s and device %s already exists. ' 'Updating value from %s to %s',
                        timezone['name'],
                        obj_override['target'],
                        existing_override_for_device['timeZoneId'],
                        obj_override['value'],
                    )
                else:
                    logger.info(
                        'Creating new Timezone Object Override for %s and device %s with value %s',
                        timezone['name'],
                        obj_override['target'],
                        obj_override['value'],
                    )
                data = {
                    'overrides': {
                        'parent': {'id': timezone['id']},
                        'target': {'id': obj_override['target_id'], 'type': 'Device'},
                    },
                    'timeZoneId': obj_override['value'],
                    'name': timezone['name'],
                    'id': timezone['id'],
                }
                try:
                    fmc.object.timezone.update(data=data)
                except GenericApiError as exc:
                    logger.error('Operation failed with error: %s', str(exc))

            else:
                logger.debug(
                    'Timezone Object Override for %s and device %s with value %s already exists. Skipping...',
                    timezone['name'],
                    obj_override['target'],
                    obj_override['value'],
                )


@override.command(
    cls=FireCliCommand('object.timezone.override.export_cfg'), name='export', short_help=HELP['export']['cmd']
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
        firecli object timezone override export --dst /tmp/overrides.yml

    """
    fmc = obj.api.fmc  # type: FMC
    logger.info('Downloading Timezone Object Override configuration from FMC...')
    timezones = fmc.object.timezone.get()
    overrides = []
    for timezone in timezones:
        if timezone['overridable']:
            obj_override = fmc.object.timezone.override.get(container_uuid=timezone['id'])
            if len(obj_override) > 0:
                overrides.append(obj_override)

    logger.info('Parsing Timezone Object Overrides...')
    report = {'objects': {'timezones': []}}
    for obj in overrides:
        timezone = {'name': obj[0]['name'], 'overrides': []}
        for item in obj:
            obj_override = {'target': item['overrides']['target']['name'], 'value': item['timeZoneId']}
            timezone['overrides'].append(obj_override)

        report['objects']['timezones'].append(timezone)

    logger.info('Exporting Object Override configuration to %s', str(dst))
    if Path(dst).exists():
        with open(dst, 'r') as f:
            dst_yaml = yaml.safe_load(f)
        dst_yaml['objects']['timezones'] = report['objects']['timezones']
        report = dst_yaml
    with open(dst, 'w') as f:
        yaml.dump(report, f)
