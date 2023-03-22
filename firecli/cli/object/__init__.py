from logging import getLogger
from typing import Any, Dict

import click

from firecli.api.click import FireCliGroup
from firecli.cli.object.dnsservergroup import dnsservergroup
from firecli.cli.object.host import host
from firecli.cli.object.ipv4addresspool import ipv4addresspool
from firecli.cli.object.network import network
from firecli.cli.object.networkgroup import networkgroup
from firecli.cli.object.override import override
from firecli.cli.object.range import network_range
from firecli.cli.object.timezone import timezone
from firecli.cli.object.url import url

logger = getLogger(__name__)

HELP: Dict[str, Any]
HELP = {'cmd': 'Object management'}


@click.group(cls=FireCliGroup('obj'), name='object', short_help=HELP['cmd'])
def obj():
    pass


obj.add_command(dnsservergroup)
obj.add_command(host)
obj.add_command(ipv4addresspool)
obj.add_command(network)
obj.add_command(networkgroup)
obj.add_command(network_range)
obj.add_command(override)
obj.add_command(timezone)
obj.add_command(url)
