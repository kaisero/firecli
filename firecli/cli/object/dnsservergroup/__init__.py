from logging import getLogger
from typing import Any, Dict

import click

from firecli.api.click import FireCliGroup
from firecli.cli.object.dnsservergroup.override import override

logger = getLogger(__name__)

HELP: Dict[str, Any]
HELP = {'cmd': 'DnsServerGroup object commands'}


@click.group(cls=FireCliGroup('object.dnsservergroup'), short_help=HELP['cmd'])
def dnsservergroup():
    pass


dnsservergroup.add_command(override)
