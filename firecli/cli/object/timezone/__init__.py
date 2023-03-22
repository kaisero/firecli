from logging import getLogger
from typing import Any, Dict

import click

from firecli.api.click import FireCliGroup
from firecli.cli.object.timezone.override import override

logger = getLogger(__name__)

HELP: Dict[str, Any]
HELP = {'cmd': 'Timezone object commands'}


@click.group(cls=FireCliGroup('object.timezone'), short_help=HELP['cmd'])
def timezone():
    pass


timezone.add_command(override)
