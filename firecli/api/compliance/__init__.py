from logging import getLogger
from typing import Dict, List

import netaddr

from firecli.api import helper

logger = getLogger()


class ZoneCompliance(object):
    def __init__(self, zones: List, matrix: Dict, accessrules: List):
        self.zones = self.parse_zones(zones)
        self.matrix = matrix
        self.accessrules = accessrules
        self.ip_default = netaddr.IPNetwork('0.0.0.0/0')

    def parse_zones(self, zones: List):
        for zone in zones:
            for index, network in enumerate(zone['networks']):
                zone['networks'][index] = helper.ip_address(network)
        return zones

    def lookup_zones(self, ip_address: str):
        ip_address = helper.ip_address(ip_address)
        zones = list()
        if ip_address == self.ip_default:
            for zone in self.zones:
                for network in zone['networks']:
                    if network == ip_address:
                        zones.append(zone['name'])
                        return zones
        for zone in self.zones:
            for network in zone['networks']:
                if network != self.ip_default:
                    if helper.ip_includes(ip_address, network):
                        zones.append(zone['name'])
        return zones

    def comm_is_compliant(self, src: str, dst: str):
        """Check if a specified source address should be allowed to
        communicate with a specified destination address

        :param src: source ipaddress object
        :param dst: destination ipaddress object
        :return: True if communication is compliant, False if communication is not compliant, None if matrix lookup
                 yields no result
        """
        compliant = True
        if ':' in src or ':' in dst:
            logger.warning('IPv6 is not supported. Skipping evaluation')
            return None
        src_zones = self.lookup_zones(src)
        dst_zones = self.lookup_zones(dst)
        for src_zone in src_zones:
            for dst_zone in dst_zones:
                if dst_zone in self.matrix[src_zone]:
                    logger.info(
                        'Destination Zone %s not found in matrix. Communication is not compliant with security matrix',
                        dst_zone,
                    )
                    compliant = False
                    logger.info(
                        'Destination Zone %s found in matrix. Communication is compliant with security matrix', dst_zone
                    )
        return compliant

    def _accessrule_report_item(self, accessrule, src, dst):
        return {
            'name': accessrule['name'],
            'src': src,
            'srcZones': self.lookup_zones(src['value']),
            'dst': dst,
            'dstZones': self.lookup_zones(dst['value']),
        }

    def check_accessrule(self, accessrule):
        logger.debug('Cecking access rule %s for compliance violations', accessrule['name'])
        report = {'id': accessrule['id'], 'name': accessrule['name'], 'violations': list()}
        sources = helper.flattened_objects(accessrule, 'sourceNetworks')
        destinations = helper.flattened_objects(accessrule, 'destinationNetworks')

        # check literals
        for src in sources['literals']:
            for dst in destinations['literals']:
                comm_is_compliant = self.comm_is_compliant(src['value'], dst['value'])
                if comm_is_compliant is False:
                    report['violations'].append(self._accessrule_report_item(accessrule, src, dst))
            for dst in destinations['objects']:
                comm_is_compliant = self.comm_is_compliant(src['value'], dst['value'])
                if comm_is_compliant is False:
                    report['violations'].append(self._accessrule_report_item(accessrule, src, dst))

        # check objects
        for src in sources['objects']:
            for dst in destinations['literals']:
                comm_is_compliant = self.comm_is_compliant(src['value'], dst['value'])
                if comm_is_compliant is False:
                    report['violations'].append(self._accessrule_report_item(accessrule, src, dst))
            for dst in destinations['objects']:
                comm_is_compliant = self.comm_is_compliant(src['value'], dst['value'])
                if comm_is_compliant is False:
                    report['violations'].append(self._accessrule_report_item(accessrule, src, dst))
        return report

    def check_compliance(self):
        report = list()
        for accessrule in self.accessrules:
            report.append(self.check_accessrule(accessrule))
        return report
