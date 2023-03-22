from logging import getLogger
from typing import Any, Dict

import click

from firecli.api.click import FireCliGroup
from firecli.cli.object.url.override import override

logger = getLogger(__name__)

HELP: Dict[str, Any]
HELP = {'cmd': 'URL object commands'}


@click.group(cls=FireCliGroup('object.url'), short_help=HELP['cmd'])
def url():
    pass


url.add_command(override)
