from logging import getLogger
from typing import Any, Dict

import click

from firecli.api.click import FireCliGroup
from firecli.cli.s2svpn.point2point import point2point

logger = getLogger(__name__)

HELP: Dict[str, Any]
HELP = {'cmd': 'Site2Site vpn management'}


@click.group(cls=FireCliGroup('s2svpn'), short_help=HELP['cmd'])
def s2svpn():
    pass


s2svpn.add_command(point2point)
