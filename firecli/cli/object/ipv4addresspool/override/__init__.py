import os
import sys

from logging import getLogger
from netaddr import IPAddress
from pathlib import Path
from typing import Any, Dict

import click
import yaml

from fireREST import FMC
from fireREST.exceptions import GenericApiError

from firecli.api.helper import cidr_to_netmask
from firecli.api.click import FireCliCommand, FireCliGroup
from firecli.api.click.callback import validate_and_load_yaml

logger = getLogger(__name__)

HELP: Dict[str, Any]
HELP = {
    'cmd': 'Ipv4AddressPool object override commands',
    'import': {
        'cmd': 'Import ipv4addresspool object overrides from yaml configuration file',
        'src': 'Path to yaml import file, e.g. /tmp/overrides.yml',
    },
    'export': {
        'cmd': 'Export ipv4addresspool object overrides to yaml configuration file',
        'dst': 'Path to yaml export file. e.g. /tmp/overrides.yml',
    },
}


@click.group(cls=FireCliGroup('object.ipv4addresspool.override'), short_help=HELP['cmd'])
def override():
    pass


@override.command(
    cls=FireCliCommand('object.ipv4addresspool.override.import_cfg'), name='import', short_help=HELP['import']['cmd']
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
    """Import ipv4addresspool overrides from yaml configuration file

    \b
    Example:
        firecli object ipv4addresspool override import --src /tmp/overrides.yml

    \b
    Import supports dry-mode to only display changes that would occur:
        firecli --dry-mode object ipv4addresspool override import --src /tmp/overrides.yml

    \b
    Import File Format:
        objects:
          ipv4addresspools:
            - name: FireCliTestIpv4AddressPoolObj
              overrides:
                - target: ftd01.example.com
                  value: 198.18.100.0-198.18.100.100/24
                - target: ftd02.example.com
                  value: 198.18.200.0-198.18.200.100/24
    """
    fmc = obj.api.fmc  # type: FMC

    logger.info('Validating Object Override configuration...')
    ipv4addresspools = fmc.object.ipv4addresspool.get()
    devices = fmc.device.devicerecord.get()
    devicehapairs = fmc.devicehapair.ftdhapair.get()
    unknown_ipv4addresspools = []
    unknown_devices = []
    for ipv4addresspool in src['objects']['ipv4addresspools']:
        obj_exists = False
        for item in ipv4addresspools:
            if item['name'] == ipv4addresspool['name']:
                ipv4addresspool['id'] = item['id']
                obj_exists = True
        if not obj_exists:
            unknown_ipv4addresspools.append(ipv4addresspool['name'])
        for obj_override in ipv4addresspool['overrides']:
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
    if len(unknown_ipv4addresspools) > 0:
        logger.error('Ipv4AddressPool Object(s) not found: %s. Exiting', ', '.join(unknown_ipv4addresspools))
        sys.exit(os.EX_DATAERR)

    logger.info('Updating Object Override configuration according to configuration file')
    for ipv4addresspool in src['objects']['ipv4addresspools']:
        container_uuid = None
        for item in ipv4addresspools:
            if item['name'] == ipv4addresspool['name']:
                container_uuid = item['id']
        existing_overrides = fmc.object.ipv4addresspool.override.get(container_uuid=container_uuid)
        for obj_override in ipv4addresspool['overrides']:
            identical_override_already_exists = False
            override_for_device_already_exists = False
            for existing_override in existing_overrides:
                if 'mask' in existing_override:
                    existing_override_value = f'{existing_override["ipAddressRange"]}/' \
                                              f'{IPAddress(existing_override["mask"]).netmask_bits()}'
                else:
                    existing_override_value = existing_override['ipAddressRange']
                if existing_override['overrides']['target']['name'] == obj_override['target']:
                    override_for_device_already_exists = True
                    if existing_override_value == obj_override['value']:
                        identical_override_already_exists = True
            if not identical_override_already_exists:
                if override_for_device_already_exists:
                    logger.info(
                        'Ipv4AdressPool Object Override for %s and device %s already exists. ' 
                        'Updating value from %s to %s',
                        ipv4addresspool['name'],
                        obj_override['target'],
                        existing_override_value,
                        obj_override['value'],
                    )
                else:
                    logger.info(
                        'Creating new Ipv4AdressPool Object Override for %s and device %s with value %s',
                        ipv4addresspool['name'],
                        obj_override['target'],
                        obj_override['value'],
                    )
                data = {
                    'overrides': {
                        'parent': {'id': ipv4addresspool['id']},
                        'target': {'id': obj_override['target_id'], 'type': 'Device'},
                    },
                    'name': ipv4addresspool['name'],
                    'id': ipv4addresspool['id'],
                }
                if '/' in obj_override['value']:
                    data['ipAddressRange'] = obj_override['value'].split('/')[0]
                    data['mask'] = cidr_to_netmask(obj_override['value'].split('/')[1])
                else:
                    data['ipAddressRange'] = obj_override['value']
                try:
                    fmc.object.ipv4addresspool.update(data=data)
                except GenericApiError as exc:
                    logger.error('Operation failed with error: %s', str(exc))

            else:
                logger.debug(
                    'Ipv4AddressPool Object Override for %s and device %s with value %s already exists. Skipping...',
                    ipv4addresspool['name'],
                    obj_override['target'],
                    obj_override['value'],
                )


@override.command(
    cls=FireCliCommand('object.ipv4addresspool.override.export_cfg'), name='export', short_help=HELP['export']['cmd']
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
        firecli object ipv4addresspool override export --dst /tmp/overrides.yml

    """
    fmc = obj.api.fmc  # type: FMC
    logger.info('Downloading Ipv4AddressPool Object Override configuration from FMC...')
    ipv4addresspools = fmc.object.ipv4addresspool.get()
    overrides = []
    for ipv4addresspool in ipv4addresspools:
        if ipv4addresspool['overridable']:
            obj_override = fmc.object.ipv4addresspool.override.get(container_uuid=ipv4addresspool['id'])
            if len(obj_override) > 0:
                overrides.append(obj_override)

    logger.info('Parsing Ipv4AddressPool Object Overrides...')
    report = {'objects': {'ipv4addresspools': []}}
    for obj in overrides:
        ipv4addresspool = {'name': obj[0]['name'], 'overrides': []}
        for item in obj:
            if 'mask' in item:
                cidr = IPAddress(item["mask"]).netmask_bits()
                value = f'{item["ipAddressRange"]}/{cidr}'
            else:
                value = item['ipAddressRange']
            obj_override = {'target': item['overrides']['target']['name'], 'value': value}
            ipv4addresspool['overrides'].append(obj_override)

        report['objects']['ipv4addresspools'].append(ipv4addresspool)

    logger.info('Exporting Object Override configuration to %s', str(dst))
    if Path(dst).exists():
        with open(dst, 'r') as f:
            dst_yaml = yaml.safe_load(f)
        dst_yaml['objects']['ipv4addresspools'] = report['objects']['ipv4addresspools']
        report = dst_yaml
    with open(dst, 'w') as f:
        yaml.dump(report, f)
