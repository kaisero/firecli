from logging import getLogger
from typing import Dict

import click

from firecli.api.cache import FmcCache
from firecli.api.click import FireCliGroup, FireCliCommand


logger = getLogger(__name__)

HELP: Dict[str, Dict]
HELP = {'cache': {'cmd': 'Local cache management', 'init': {'cmd': 'Initialize configuration cache'}}}


@click.group(cls=FireCliGroup('cache'), short_help=HELP['cache']['cmd'])
def cache():
    pass


@cache.command(cls=FireCliCommand('cache.init'), short_help=HELP['cache']['init']['cmd'])
@click.pass_obj
def init(obj):
    api = obj.api
    cfg = obj.cfg
    cache_dir = cfg['cache_dir']

    logger.info('Downloading firepower configuration...')
    fmc_cache = FmcCache(cache_dir, api)
    fmc_cache.download()
    fmc_cache.save()
    logger.info('Successfully saved cache files to %s', fmc_cache.directory)
