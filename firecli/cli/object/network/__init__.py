from logging import getLogger
from typing import Any, Dict

import click

from firecli.cli.object.network.override import override

logger = getLogger(__name__)

HELP: Dict[str, Any]
HELP = {'cmd': 'Network object commands'}


@click.group(help=HELP['cmd'])
def network():
    pass


network.add_command(override)
