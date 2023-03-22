from logging import getLogger
from typing import Any, Dict

import click

from firecli.api.click import FireCliGroup
from firecli.cli.object.host.override import override

logger = getLogger(__name__)

HELP: Dict[str, Any]
HELP = {'cmd': 'Host object commands'}


@click.group(cls=FireCliGroup('object.host'), short_help=HELP['cmd'])
def host():
    pass


host.add_command(override)
