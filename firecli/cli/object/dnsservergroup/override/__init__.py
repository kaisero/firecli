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
    'cmd': 'DnsServerGroup object override commands',
    'import': {
        'cmd': 'Import dnsservergroup object overrides from yaml configuration file',
        'src': 'Path to yaml import file, e.g. /tmp/overrides.yml',
    },
    'export': {
        'cmd': 'Export dnsservergroup object overrides to yaml configuration file',
        'dst': 'Path to yaml export file. e.g. /tmp/overrides.yml',
    },
}


@click.group(cls=FireCliGroup('object.dnsservergroup.override'), short_help=HELP['cmd'])
def override():
    pass


@override.command(
    cls=FireCliCommand('object.dnsservergroup.override.import_cfg'), name='import', short_help=HELP['import']['cmd']
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
        firecli object dnsservergroup override import --src /tmp/overrides.yml

    \b
    Import supports dry-mode to only display changes that would occur:
        firecli --dry-mode object dnsservergroup override import --src /tmp/overrides.yml

    \b
    Import File Format:
        objects:
          dnsservergroups:
            - name: FireCliTestDnsServerGroupObj
              overrides:
                - target: ftd01.example.com
                  values:
                    - 198.18.100.1
                    - 198.18.101.1
                - target: ftd02.example.com
                  values:
                    - 198.18.200.1
                    - 198.18.200.2
    """
    fmc = obj.api.fmc  # type: FMC

    logger.info('Validating Object Override configuration...')
    dnsservergroups = fmc.object.dnsservergroup.get()
    devices = fmc.device.devicerecord.get()
    devicehapairs = fmc.devicehapair.ftdhapair.get()
    unknown_dnsservergroups = []
    unknown_devices = []
    for dnsservergroup in src['objects']['dnsservergroups']:
        obj_exists = False
        for item in dnsservergroups:
            if item['name'] == dnsservergroup['name']:
                dnsservergroup['id'] = item['id']
                obj_exists = True
        if not obj_exists:
            unknown_dnsservergroups.append(dnsservergroup['name'])
        for obj_override in dnsservergroup['overrides']:
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
    if len(unknown_dnsservergroups) > 0:
        logger.error('DnsServerGroup Object(s) not found: %s. Exiting', ', '.join(unknown_dnsservergroups))
        sys.exit(os.EX_DATAERR)

    logger.info('Updating Object Override configuration according to configuration file')
    for dnsservergroup in src['objects']['dnsservergroups']:
        container_uuid = None
        for item in dnsservergroups:
            if item['name'] == dnsservergroup['name']:
                container_uuid = item['id']
        existing_overrides = fmc.object.dnsservergroup.override.get(container_uuid=container_uuid)
        for obj_override in dnsservergroup['overrides']:
            identical_override_already_exists = False
            override_for_device_already_exists = False
            existing_override_for_device = None
            existing_override_dns_servers = None
            for existing_override in existing_overrides:
                if existing_override['overrides']['target']['name'] == obj_override['target']:
                    existing_override_for_device = existing_override
                    existing_override_dns_servers = [srv['name-server'] for srv in existing_override['dnsservers']]
                    override_for_device_already_exists = True
                    if existing_override_dns_servers == obj_override['values']:
                        identical_override_already_exists = True
            if not identical_override_already_exists:
                if override_for_device_already_exists:
                    logger.info(
                        'DnsServerGroup Object Override for %s and device %s already exists. '
                        'Updating value from %s to %s',
                        dnsservergroup['name'],
                        obj_override['target'],
                        existing_override_dns_servers,
                        obj_override['values'],
                    )
                else:
                    logger.info(
                        'Creating new DnsServerGroup Object Override for %s and device %s with value %s',
                        dnsservergroup['name'],
                        obj_override['target'],
                        obj_override['values'],
                    )
                data = {
                    'overrides': {
                        'parent': {'id': dnsservergroup['id']},
                        'target': {'id': obj_override['target_id'], 'type': 'Device'},
                    },
                    'dnsservers': [{'name-server': item} for item in obj_override['values']],
                    'name': dnsservergroup['name'],
                    'type': 'DNSServerGroupObject',
                    'id': dnsservergroup['id'],
                }
                try:
                    fmc.object.dnsservergroup.update(data=data)
                except GenericApiError as exc:
                    logger.error('Operation failed with error: %s', str(exc))

            else:
                logger.debug(
                    'DnsServerGroup Object Override for %s and device %s with value %s already exists. Skipping...',
                    dnsservergroup['name'],
                    obj_override['target'],
                    obj_override['values'],
                )


@override.command(
    cls=FireCliCommand('object.dnsservergroup.override.export_cfg'), name='export', short_help=HELP['export']['cmd']
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
        firecli object dnsservergroup override export --dst /tmp/overrides.yml

    """
    fmc = obj.api.fmc  # type: FMC
    logger.info('Downloading DnsServerGroup Object Override configuration from FMC...')
    dnsservergroups = fmc.object.dnsservergroup.get()
    overrides = []
    for dnsservergroup in dnsservergroups:
        if dnsservergroup['overridable']:
            obj_override = fmc.object.dnsservergroup.override.get(container_uuid=dnsservergroup['id'])
            if len(obj_override) > 0:
                overrides.append(obj_override)

    logger.info('Parsing DnsServerGroup Object Overrides...')
    report = {'objects': {'dnsservergroups': []}}
    for obj in overrides:
        dnsservergroup = {'name': obj[0]['name'], 'overrides': []}
        for item in obj:
            servers = [srv['name-server'] for srv in item['dnsservers']]
            obj_override = {'target': item['overrides']['target']['name'], 'values': servers}
            dnsservergroup['overrides'].append(obj_override)

        report['objects']['dnsservergroups'].append(dnsservergroup)

    logger.info('Exporting Object Override configuration to %s', str(dst))
    if Path(dst).exists():
        with open(dst, 'r') as f:
            dst_yaml = yaml.safe_load(f)
        dst_yaml['objects']['dnsservergroups'] = report['objects']['dnsservergroups']
        report = dst_yaml
    with open(dst, 'w') as f:
        yaml.dump(report, f)
