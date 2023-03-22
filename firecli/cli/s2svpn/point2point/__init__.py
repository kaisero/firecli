import sys
from logging import getLogger
from typing import Dict

import click
from fireREST.exceptions import ResourceNotFoundError

from firecli.api.click import FireCliGroup, FireCliCommand
from firecli.cli import helper

logger = getLogger(__name__)

HELP: Dict[str, Dict]
HELP = {
    'cmd': 'Point-to-Point VPN commands',
    'name': 'Name of the point-to-point vpn topology',
    'create': {
        'cmd': 'Create point-to-point vpn topology',
        'local_device': 'Name of local vpn headend',
        'local_interface': 'Name of the local vpn headend interface',
        'local_networks': 'List of local network objects. e.g. NET_LAN_1,NET_LAN_2,H_EXAMPLE_COM',
        'remote_device': 'Name of remote vpn headend',
        'remote_interface': 'IP address of interface name of remote vpn headend',
        'remote_networks': 'List of local network objects. e.g. NET_LAN_1,NET_LAN_2,H_EXAMPLE_COM',
        'ikev2_policy': 'Name of IKEv2 policy',
        'ikev2_psk': 'Preshared key for authentication',
        'ipsec_proposal': 'Name of ipsec proposal',
        'ipsec_enable_rri': 'Enable reverse route injection',
        'ipsec_lifetime': 'IPSec connection lifetime in seconds',
    },
}


@click.group(cls=FireCliGroup('s2svpn.point2point'), short_help=HELP['cmd'])
@click.option('--name', required=False, type=str, help=HELP['name'])
@click.pass_obj
def point2point(obj, name):
    obj['vpn'] = {'name': name, 'id': None}


@point2point.command(cls=FireCliCommand('s2svpn.point2point.create'), short_help=HELP['create']['cmd'])
@click.option('--local-device', required=False, type=str, help=HELP['create']['local_device'])
@click.option('--local-interface', required=False, type=str, help=HELP['create']['local_interface'])
@click.option('--local-networks', required=False, type=str, help=HELP['create']['local_networks'])
@click.option('--remote-device', required=False, type=str, help=HELP['create']['remote_device'])
@click.option('--remote-interface', required=False, type=str, help=HELP['create']['remote_interface'])
@click.option('--remote-networks', required=False, type=str, help=HELP['create']['remote_networks'])
@click.option('--ikev2-policy', required=False, type=str, help=HELP['create']['ikev2_policy'])
@click.option('--ikev2-psk', required=False, type=str, help=HELP['create']['ikev2_psk'])
@click.option('--ipsec-proposal', required=False, type=str, help=HELP['create']['ipsec_proposal'])
@click.option(
    '--ipsec-enable-rri', required=False, default=False, is_flag=True, help=HELP['create']['ipsec_enable_rri']
)
@click.option(
    '--ipsec-pfs-dh-group',
    required=False,
    default='None',
    type=click.Choice(['None', '1', '2', '5', '14', '15', '16', '19', '20', '21', '24']),
    help=HELP['create']['ipsec_proposal'],
)
@click.option('--ipsec-lifetime', required=False, type=int, default=28800, help=HELP['create']['ipsec_lifetime'])
@click.pass_obj
def create(
    obj,
    local_device,
    local_interface,
    local_networks,
    remote_device,
    remote_interface,
    remote_networks,
    ikev2_policy,
    ikev2_psk,
    ipsec_proposal,
    ipsec_enable_rri,
    ipsec_pfs_dh_group,
    ipsec_lifetime,
):
    api = obj.api
    fmc = api.fmc

    logger.info('Validating input params...')

    try:
        vpn = {'id': None, 'name': obj['vpn']['name'], 'topologyType': 'POINT_TO_POINT', 'ikeV2Enabled': True}
        ikesettings = {
            'id': None,
            'ikeV2Settings': {
                'authenticationType': 'MANUAL_PRE_SHARED_KEY',
                'manualPreSharedKey': ikev2_psk,
                'policy': {'id': fmc.object.ikev2policy.get(name=ikev2_policy)['id']},
            },
        }
        ipsecsettings = {
            'lifetimeSeconds': ipsec_lifetime,
            'enableRRI': ipsec_enable_rri,
            'ikeV2IpsecProposal': [{'id': fmc.object.ikev2ipsecproposal.get(name=ipsec_proposal)['id']}],
            'perfectForwardSecrecy': {
                'enabled': True if ipsec_pfs_dh_group != 'None' else False,
                'modulusGroup': ipsec_pfs_dh_group if ipsec_pfs_dh_group != 'None' else '1',
            },
        }
        endpoints = [
            {
                'name': local_device,
                'device': {'name': local_device, 'id': fmc.device.devicerecord.get(name=local_device)},
                'interface': {'id': None},
                'protectedNetworks': {},
                'extranet': False,
                'connectionType': 'BIDIRECTIONAL',
                'peerType': 'PEER',
            },
            {
                'name': remote_device,
                'extranet': True,
                'extranetInfo': {'name': remote_device, 'ipAddress': remote_interface, 'isDynamicIP': False},
                'protectedNetworks': {},
                'connectionType': 'ORIGINATE_ONLY',
                'peerType': 'PEER',
            },
        ]
        endpoints[0]['interface']['id'] = fmc.device.devicerecord.subinterface.get(
            container_uuid=endpoints[0]['device']['id'], name=local_interface
        )

    except ResourceNotFoundError as exc:
        logger.error(str(exc))
        sys.exit(2)

    s2svpn_networks = helper.parsed_s2svpn_networks(fmc, local_networks, remote_networks)
    endpoints[0]['protectedNetworks'] = s2svpn_networks['local']
    endpoints[1]['protectedNetworks'] = s2svpn_networks['remote']

    logger.info('Input validation passed successfully')

    logger.info('Creating point-to-point vpn topology "%s"', vpn['name'])
    vpn_result = fmc.policy.ftds2svpn.create(data=vpn)
    vpn = vpn_result.json()

    logger.info('Assigning ikev2 settings to vpn topology')
    ikesettings['id'] = vpn['ikeSettings']['id']
    fmc.policy.ftds2svpn.ikesettings.update(container_uuid=vpn['id'], data=ikesettings)

    logger.info('Assigning ipsec settings to vpn topology')
    ipsecsettings['id'] = vpn['ipsecSettings']['id']
    fmc.policy.ftds2svpn.ipsecsettings.update(container_uuid=vpn['id'], data=ipsecsettings)

    logger.info('Assigning local endpoint to vpn topology')
    fmc.policy.ftds2svpn.endpoint.create(container_uuid=vpn['id'], data=endpoints[0])

    logger.info('Assigning remote endpoint to vpn topology')
    fmc.policy.ftds2svpn.endpoint.create(container_uuid=vpn['id'], data=endpoints[1])

    logger.info('Successfully created vpn topology')
