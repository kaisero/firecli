from logging import getLogger
from typing import Any, Dict

import click

from firecli.api.click import FireCliGroup
from firecli.cli.object.range.override import override

logger = getLogger(__name__)

HELP: Dict[str, Any]
HELP = {'cmd': 'Range object commands'}


@click.group(cls=FireCliGroup('object.range'), name='range', help=HELP['cmd'])
def network_range():
    pass


network_range.add_command(override)
