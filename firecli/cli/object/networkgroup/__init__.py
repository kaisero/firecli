from logging import getLogger
from typing import Any, Dict

import click

from firecli.api.click import FireCliGroup
from firecli.cli.object.networkgroup.override import override

logger = getLogger(__name__)

HELP: Dict[str, Any]
HELP = {'cmd': 'Networkgroup object commands'}


@click.group(cls=FireCliGroup('object.networkgroup'), short_help=HELP['cmd'])
def networkgroup():
    pass


networkgroup.add_command(override)
