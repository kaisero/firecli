import csv
import re

from functools import partial
from logging import getLogger
from typing import Dict, List

from firecli.api.afa import AFA

from click import Context
from fireREST import FMC
from fireREST.exceptions import ResourceNotFoundError

logger = getLogger(__name__)


def assigned_accesspolicies(fmc: FMC, accesspolicy=None):
    assignments = []
    if accesspolicy:
        try:
            assignment = fmc.assignment.policyassignment.get(uuid=accesspolicy['id'])
            assignments.append(assignment)
        except ResourceNotFoundError:
            logger.error(
                'Accesspolicy "%s" is not assigned to any device. Make sure policy is assigned to device',
                accesspolicy['name'],
            )
            raise
    else:
        try:
            assignments = [
                assignment
                for assignment in fmc.assignment.policyassignment.get()
                if assignment['policy']['type'] == 'AccessPolicy'
            ]
        except ResourceNotFoundError:
            logger.error('Accesspolicies are not assigned to any devices. Make sure policy assignments exist.')
            raise
    return assignments


def afa_resources(fmc: FMC, device: str):
    resolved_device = None
    resolved_policy = None
    try:
        resolved_device = fmc.devicehapair.ftdhapair.get(name=device)
    except ResourceNotFoundError:
        try:
            resolved_device = fmc.device.devicerecord.get(name=device)
        except ResourceNotFoundError:
            logger.error('"%s" not found. Make sure device exists...', device)
            raise
    for assignment in fmc.assignment.policyassignment.get():
        if assignment['policy']['type'] == 'AccessPolicy':
            for target in assignment['targets']:
                if target['name'] == resolved_device['name']:
                    resolved_policy = assignment['policy']
    if not resolved_policy:
        raise ResourceNotFoundError(f'Could not find policy assigned to device "{device}"')
    return resolved_device, resolved_policy


def accessrule_without_ticket_id(patterns: List, accessrule: Dict):
    for pattern in patterns:
        if re.match(pattern, accessrule['name']):
            logger.debug('Pattern "%s" found in accessrule name "%s"', pattern, accessrule['name'])
            return False
        try:
            for comment in accessrule['commentHistoryList']:
                if re.match(pattern, comment['comment']):
                    logger.debug(
                        'Pattern "%s" found in accessrule "%s" comment "%s"',
                        pattern,
                        accessrule['name'],
                        comment['comment'],
                    )
                    return False
        except KeyError:
            pass
    return True


def matches_risk(risks: List, risky_rule: Dict):
    if len(risks) == 0:
        return True
    for risk in risky_rule['risks']:
        if risk['code'] in risks:
            return True
    return False


def matches_relevant_risky_rules(exclusions: List, risky_rule: Dict):
    if risky_rule['ruleId'].replace('_', '-') in exclusions:
        return False
    return True


def accessrule_count(fmc: FMC, accesspolicy=None):
    result = []
    assignments = assigned_accesspolicies(fmc, accesspolicy)
    for assignment in assignments:
        device = assignment['targets'][0]['name']
        device_id = assignment['targets'][0]['id']
        policy = assignment['policy']['name']
        policy_id = assignment['policy']['id']
        rulecount = len(fmc.policy.accesspolicy.accessrule.get(container_uuid=policy_id))
        result.append(
            {'device': device, 'device_id': device_id, 'policy': policy, 'policy_id': policy_id, 'rulecount': rulecount}
        )
    return result


def accessrules_without_comments(fmc: FMC, accesspolicy=None):
    result = []
    assignments = assigned_accesspolicies(fmc, accesspolicy)
    for assignment in assignments:
        device = assignment['targets'][0]['name']
        device_id = assignment['targets'][0]['id']
        policy = assignment['policy']['name']
        policy_id = assignment['policy']['id']
        logger.debug('Searching for accessrules without comments in "%s" accesspolicy', policy)
        accessrules = fmc.policy.accesspolicy.accessrule.get(container_uuid=policy_id)
        result.extend(
            [
                {
                    'device': device,
                    'device_id': device_id,
                    'policy': policy,
                    'policy_id': policy_id,
                    'rule': rule['name'],
                    'rule_id': rule['id'],
                }
                for rule in accessrules
                if 'commentHistoryList' not in rule
            ]
        )
        logger.debug('Found %s accessrules without comments in "%s" accesspolicy', len(result), policy)
    return result


def accessrules_without_ticket_id(fmc: FMC, patterns: List, accesspolicy=None):
    result = []
    assignments = assigned_accesspolicies(fmc, accesspolicy)
    for assignment in assignments:
        device = assignment['targets'][0]['name']
        device_id = assignment['targets'][0]['id']
        policy = assignment['policy']['name']
        policy_id = assignment['policy']['id']
        logger.debug('Searching for accessrules without ticket IDs in "%s" accesspolicy', policy)
        accessrules = fmc.policy.accesspolicy.accessrule.get(container_uuid=assignment['id'])
        accessrules = filter(partial(accessrule_without_ticket_id, patterns), accessrules)
        result.extend(
            [
                {
                    'device': device,
                    'device_id': device_id,
                    'policy': policy,
                    'policy_id': policy_id,
                    'rule': rule['name'],
                    'rule_id': rule['id'],
                }
                for rule in accessrules
            ]
        )
    return result


def noncompliant_accessrules(afa: AFA, fmc: FMC, device, exclude=None, risks=None):
    result = []
    risky_rules = afa.get_risky_rules(device)['riskyRules']
    risky_rules = filter(partial(matches_risk, risks), risky_rules)
    risky_rules = filter(partial(matches_relevant_risky_rules, exclude), risky_rules)
    device, policy = afa_resources(fmc, device)
    for risky_rule in risky_rules:
        rule_id = risky_rule['ruleId'].replace('_', '-')
        try:
            rule = fmc.policy.accesspolicy.accessrule.get(container_uuid=policy['id'], uuid=rule_id)
        except ResourceNotFoundError:
            rule = {'id': rule_id, 'name': 'RULE-NOT-FOUND-ON-FMC'}
        risk = risky_rule['risks'][0]['title']
        result.append(
            {
                'device': device['name'],
                'device_id': device['id'],
                'policy': policy['name'],
                'policy_id': policy['id'],
                'rule': rule['name'],
                'rule_id': rule['id'],
                'risk': risk,
            }
        )
    return result


def noncompliant_network_segments(fmc: FMC, device: Dict, networks: List):
    result = []
    routes = fmc.device.devicerecord.routing.ipv4staticroute.get(container_uuid=device['id'])
    routing_table = {}
    for route in routes:
        if route['interfaceName'] not in routing_table.keys():
            routing_table[route['interfaceName']] = []
        for network in route['selectedNetworks']:
            if network['type'] == 'Host':
                obj = fmc.object.host.get(uuid=network['id'])['value']
            else:
                obj = fmc.object.network.get(uuid=network['id'])['value']
            routing_table[route['interfaceName']].append(obj)
    for network in networks:
        for _interface, entries in routing_table.items():
            for src in network['src']['values']:
                if src in entries:
                    for dst in network['dst']['values']:
                        if dst in entries:
                            result.append(
                                {
                                    'device': device['name'],
                                    'device_id': device['id'],
                                    'source': network['src']['name'],
                                    'source_network': src,
                                    'destination': network['dst']['name'],
                                    'destination_network': dst,
                                    'firewalled': 'No',
                                }
                            )
    return result


def log_report_gen(ctx: Context):
    logger.info('Generating "%s" report...', ctx.command.name)


def report_path(name: str, directory: str, fmt: str, summary=False):
    path = f'{directory}/{name}'
    if summary:
        path = f'{path}-summary'
    return f'{path}.{fmt}'


def save(path: str, data: List):
    if len(data) > 0:
        if path.split('.')[-1] == 'csv':
            with open(path, 'w') as f:
                logger.info('Saving report to "%s"', path)
                writer = csv.DictWriter(f, data[0].keys())
                writer.writeheader()
                writer.writerows(data)
    else:
        logger.info('Report did not yield any results. Report will not be saved to disk.')
