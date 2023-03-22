from logging import getLogger

from fireREST import FMC
from fireREST.exceptions import ResourceNotFoundError

logger = getLogger(__name__)


def parsed_networks(fmc: FMC, networks: str):
    """parse list of network(group) names into list of uuids exit on failure
    """
    networks = networks.split(',')
    uuids = list()
    for network in networks:
        try:
            uuid = fmc.object.networkgroup.get(name=network)
        except ResourceNotFoundError:
            try:
                uuid = fmc.object.network.get(name=network)
            except ResourceNotFoundError:
                try:
                    uuid = fmc.object.host.get(name=network)
                except ResourceNotFoundError:
                    raise
        uuids.append(uuid)
    return uuids


def parsed_s2svpn_networks(fmc: FMC, local_networks: str, remote_networks):
    """parse s2svpn local and remote network definitions
    """
    if local_networks == remote_networks:
        uuid = fmc.object.extendedaccesslist.get(name=local_networks)
        protected_networks = {'local': {'acl': {'id': uuid}}, 'remote': {'acl': {'id': uuid}}}
    else:
        protected_networks = {
            'local': {'networks': parsed_networks(fmc, local_networks)},
            'remote': {'networks': parsed_networks(fmc, remote_networks)},
        }
    return protected_networks
