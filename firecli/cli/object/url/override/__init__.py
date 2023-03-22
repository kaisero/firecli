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
    'cmd': 'URL object override commands',
    'import': {
        'cmd': 'Import url object overrides from yaml configuration file',
        'src': 'Path to yaml import file, e.g. /tmp/overrides.yml',
    },
    'export': {
        'cmd': 'Export url object overrides to yaml configuration file',
        'dst': 'Path to yaml export file. e.g. /tmp/overrides.yml',
    },
}


@click.group(cls=FireCliGroup('object.url.override'), help=HELP['cmd'])
def override():
    pass


@override.command(cls=FireCliCommand('object.url.override.import'), name='import', short_help=HELP['import']['cmd'])
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
        firecli object url override import --src /tmp/overrides.yml

    \b
    Import supports dry-mode to only display changes that would occur:
        firecli --dry-mode object url override import --src /tmp/overrides.yml

    \b
    Import File Format:
        objects:
          urls:
            - name: FireCliTestUrlObj
              overrides:
                - target: ftd01.example.com
                  value: www.example.com
                - target: ftd02.example.com
                  value: www.example02.com
    """
    fmc = obj.api.fmc  # type: FMC

    logger.info('Validating Object Override configuration...')
    urls = fmc.object.url.get()
    devices = fmc.device.devicerecord.get()
    devicehapairs = fmc.devicehapair.ftdhapair.get()
    unknown_urls = []
    unknown_devices = []
    for url in src['objects']['urls']:
        obj_exists = False
        for item in urls:
            if item['name'] == url['name']:
                url['id'] = item['id']
                obj_exists = True
        if not obj_exists:
            unknown_urls.append(url['name'])
        for override in url['overrides']:
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
    if len(unknown_urls) > 0:
        logger.error('URL Object(s) not found: %s. Exiting', ', '.join(unknown_urls))
        sys.exit(os.EX_DATAERR)

    logger.info('Updating Object Override configuration according to configuration file')
    for url in src['objects']['urls']:
        container_uuid = None
        for item in urls:
            if item['name'] == url['name']:
                container_uuid = item['id']
        existing_overrides = fmc.object.url.override.get(container_uuid=container_uuid)
        for override in url['overrides']:
            identical_override_already_exists = False
            override_for_device_already_exists = False
            existing_override_for_device = None
            for existing_override in existing_overrides:
                if existing_override['overrides']['target']['name'] == override['target']:
                    existing_override_for_device = existing_override
                    override_for_device_already_exists = True
                    if existing_override['url'] == override['value']:
                        identical_override_already_exists = True
            if not identical_override_already_exists:
                if override_for_device_already_exists:
                    logger.info(
                        'URL Object Override for %s and device %s already exists. ' 'Updating value from %s to %s',
                        url['name'],
                        override['target'],
                        existing_override_for_device['url'],
                        override['value'],
                    )
                else:
                    logger.info(
                        'Creating new URL Object Override for %s and device %s with value %s',
                        url['name'],
                        override['target'],
                        override['value'],
                    )
                data = {
                    'overrides': {
                        'parent': {'id': url['id']},
                        'target': {'id': override['target_id'], 'type': 'Device'},
                    },
                    'url': override['value'],
                    'name': url['name'],
                    'id': url['id'],
                }
                try:
                    fmc.object.url.update(data=data)
                except GenericApiError as exc:
                    logger.error('Operation failed with error: %s', str(exc))

            else:
                logger.debug(
                    'URL Object Override for %s and device %s with value %s already exists. Skipping...',
                    url['name'],
                    override['target'],
                    override['value'],
                )


@override.command(cls=FireCliCommand('object.url.override.export'), name='export', short_help=HELP['export']['cmd'])
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
        firecli object url override export --dst /tmp/overrides.yml

    """
    fmc = obj.api.fmc  # type: FMC
    logger.info('Downloading URL Object Override configuration from FMC...')
    urls = fmc.object.url.get()
    overrides = []
    for url in urls:
        if url['overridable']:
            override = fmc.object.url.override.get(container_uuid=url['id'])
            if len(override) > 0:
                overrides.append(override)

    logger.info('Parsing URL Object Overrides...')
    report = {'objects': {'urls': []}}
    for obj in overrides:
        url = {'name': obj[0]['name'], 'overrides': []}
        for item in obj:
            override = {'target': item['overrides']['target']['name'], 'value': item['url']}
            url['overrides'].append(override)

        report['objects']['urls'].append(url)

    logger.info('Exporting Object Override configuration to %s', str(dst))
    if Path(dst).exists():
        with open(dst, 'r') as f:
            dst_yaml = yaml.safe_load(f)
        dst_yaml['objects']['urls'] = report['objects']['urls']
        report = dst_yaml
    with open(dst, 'w') as f:
        yaml.dump(report, f)
