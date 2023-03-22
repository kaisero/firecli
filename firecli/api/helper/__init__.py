import socket
import struct

from logging import getLogger
from typing import Dict

import netaddr

logger = getLogger()


def obj_is_group(obj: Dict):
    if 'group' in obj['type'].lower():
        return True
    return False


def literals_in_obj(obj: Dict):
    if 'literals' in obj:
        return True
    return False


def objects_in_obj(obj: Dict):
    """Check if object includes nested objects
    :param obj: Object returned by FMC REST API
    :type obj: Dict
    :return: True if key 'objects' is defined in obj, False otherwise
    :rtype: bool
    """
    if 'objects' in obj:
        return True
    return False


def formatted_flattened_obj(name: str, value: str):
    return {'name': name, 'value': value}


def flattened_objects(accessrule: Dict, field: str):
    result = {'literals': list(), 'objects': list()}
    if field in accessrule:
        if literals_in_obj(accessrule[field]):
            for literal in accessrule[field]:
                result['literals'].append(formatted_flattened_obj('Literal', literal['value']))
        if objects_in_obj(accessrule[field]):
            for obj in accessrule[field]['objects']:
                pipeline = [obj]
                while pipeline:
                    obj = pipeline[0]
                    if obj_is_group(obj):
                        # add literals to result
                        if literals_in_obj(obj):
                            for literal in obj['literals']:
                                result['literals'].append(formatted_flattened_obj(obj['name'], literal['value']))
                        # add nested objects to result
                        if objects_in_obj(obj):
                            for nested_obj in obj['objects']:
                                if objects_in_obj(nested_obj):
                                    pipeline.append(nested_obj)
                                else:
                                    result['objects'].append(
                                        formatted_flattened_obj(nested_obj['name'], nested_obj['value'])
                                    )
                    else:
                        if obj['type'].lower() in ('host', 'network', 'range'):
                            result['objects'].append(formatted_flattened_obj(obj['name'], obj['value']))
                        else:
                            logger.warning('Unsupported object type %s. Ignoring object.', obj['type'])
                    # remove processed item from pipeline
                    pipeline.pop(0)

    if not result['literals'] and not result['objects']:
        result['literals'].append({'name': 'Literal', 'value': '0.0.0.0/0'})
    return result


def ip_address(ipaddr: str):
    """Cast ipaddress from string to netaddr.IPAddress or netaddr.IPNetwork depending on type
    :param ipaddr: ipv4 address (e.g. 198.18.0.1, 198.18.1.0/24)
    :type ipaddr: str
    :return: netaddr.IPAddress or netaddr.IPNetwork object
    :rtype: netaddr.IPAddress or netaddr.IPNetwork
    """
    if '/' not in ipaddr:
        return netaddr.IPAddress(ipaddr)
    return netaddr.IPNetwork(ipaddr)


def cidr_to_netmask(cidr: int):
    host_bits = 32 - cidr
    return socket.inet_ntoa(struct.pack('!I', (1 << 32) - (1 << host_bits)))


def ip_includes(src: object, dst: object):
    """Compare source and destination ipv4 address to determine if
    one or the other is part of each others ip space
    :param src: source ip address
    :type src: netaddr.IPAddress or netaddr.IPNetwork
    :param dst: destination ip address
    :type dst: :type src: netaddr.IPAddress or netaddr.IPNetwork
    :return: True if src and destination share common ip network
    :rtype: bool
    """
    if isinstance(src, netaddr.IPAddress):
        if isinstance(dst, netaddr.IPAddress):
            if src == dst:
                return True
            return False
        else:
            if src in dst:
                return True
            return False
    else:
        if isinstance(dst, netaddr.IPAddress):
            if dst in src:
                return True
            return False
        else:
            if src in dst or dst in src:
                return True
            return False
