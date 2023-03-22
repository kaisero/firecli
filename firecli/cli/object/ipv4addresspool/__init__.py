from logging import getLogger
from typing import Any, Dict

import click

from firecli.api.click import FireCliGroup
from firecli.cli.object.ipv4addresspool.override import override

logger = getLogger(__name__)

HELP: Dict[str, Any]
HELP = {'cmd': 'Ipv4AddressPool object commands'}


@click.group(cls=FireCliGroup('object.ipv4addresspool'), short_help=HELP['cmd'])
def ipv4addresspool():
    pass


ipv4addresspool.add_command(override)
