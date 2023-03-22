from logging import getLogger
from typing import Any, Dict

import click

from firecli.api.click import FireCliCommand, FireCliGroup
from firecli.api.click.callback import validate_and_load_yaml
from firecli.cli.object.dnsservergroup.override import export_cfg as export_dnsservergroup
from firecli.cli.object.dnsservergroup.override import import_cfg as import_dnsservergroup
from firecli.cli.object.host.override import export_cfg as export_host
from firecli.cli.object.host.override import import_cfg as import_host
from firecli.cli.object.ipv4addresspool.override import export_cfg as export_ipv4addresspool
from firecli.cli.object.ipv4addresspool.override import import_cfg as import_ipv4addresspool
from firecli.cli.object.network.override import export_cfg as export_network
from firecli.cli.object.network.override import import_cfg as import_network
from firecli.cli.object.networkgroup.override import export_cfg as export_networkgroup
from firecli.cli.object.networkgroup.override import import_cfg as import_networkgroup
from firecli.cli.object.range.override import export_cfg as export_range
from firecli.cli.object.range.override import import_cfg as import_range
from firecli.cli.object.timezone.override import export_cfg as export_timezone
from firecli.cli.object.timezone.override import import_cfg as import_timezone
from firecli.cli.object.url.override import export_cfg as export_url
from firecli.cli.object.url.override import import_cfg as import_url

logger = getLogger(__name__)

HELP: Dict[str, Any]
HELP = {
    'cmd': 'Object override commands',
    'import': {
        'cmd': 'Import object overrides from yaml configuration file',
        'src': 'Path to yaml import file, e.g. /tmp/overrides.yml',
    },
    'export': {
        'cmd': 'Export object overrides to yaml configuration file',
        'dst': 'Path to yaml export file. e.g. /tmp/overrides.yml',
    },
}


@click.group(cls=FireCliGroup('object.override'), short_help=HELP['cmd'])
def override():
    """ Object overrride commands
    """
    pass


@override.command(cls=FireCliCommand('object.override.import'), name='import', short_help=HELP['import']['cmd'])
@click.option(
    '-s',
    '--src',
    'src',
    callback=validate_and_load_yaml,
    default='overrides.yml',
    required=False,
    type=click.Path(exists=True, readable=True),
    help=HELP['import']['src'],
)
@click.pass_context
def import_cfg(ctx, src):
    """Import object overrides from yaml configuration file

    \b
    Example:
        firecli object override import --src /tmp/overrides.yml

    \b
    Import supports dry-mode to only display changes that would occur:
        firecli --dry-mode object override import --src /tmp/overrides.yml

    \b
    Import File Format:
        objects:
          dnsservergroups:
            - name: FireCliTestDnsServerGroupObj
              overrides:
                - target: ftd01.example.com
                  values:
                    - 198.18.100.1
                    - 198.18.101.1
                - target: ftd02.example.com
                  values:
                    - 198.18.200.1
                    - 198.18.200.2
          hosts:
            - name: FireCliTestHostObj
              overrides:
                - target: ftd01.example.com
                  value: 198.18.100.1
                - target: ftd02.example.com
                  value: 198.18.200.1
          ipv4addresspools:
            - name: FireCliTestIpv4AddressPoolObj
              overrides:
                - target: ftd01.example.com
                  value: 198.18.100.0-198.18.100.100/24
                - target: ftd02.example.com
                  value: 198.18.200.0-198.18.200.100/24
          networks:
            - name: FireCliTestNetObj
              overrides:
                - target: ftd01.example.com
                  value: 198.18.100.0/24
                - target: ftd02.example.com
                  value: 198.18.200.0/24
          networkgroups:
            - name: FireCliObjectGroup
              overrides:
                - target: ftd01.example.com
                  values:
                    - 198.18.0.0/24
                    - 198.18.1.0/24
                    - 198.18.2.1
                - target: ftd02.example.com
                  values:
                    - 198.19.0.0/24
                    - 198.19.1.0/24
                    - 198.19.2.1
          ranges:
            - name: FireCliTestRangeObj
              overrides:
                - target: ftd01.example.com
                  value: 198.18.100.0-198.18.100.100
                - target: ftd02.example.com
                  value: 198.18.200.0-198.18.200.100
          timezones:
            - name: FireCliTestTimezoneObj
              overrides:
                - target: ftd01.example.com
                  value: US/Washington
                - target: ftd02.example.com
                  value: Europe/Vienna
          urls:
            - name: FireCliTestUrlObj
              overrides:
                - target: ftd01.example.com
                  value: www.example.com
                - target: ftd02.example.com
                  value: vpn.example.com
    """
    ctx.forward(import_dnsservergroup)
    ctx.forward(import_host)
    ctx.forward(import_ipv4addresspool)
    ctx.forward(import_network)
    ctx.forward(import_range)
    ctx.forward(import_networkgroup)
    ctx.forward(import_timezone)
    ctx.forward(import_url)


@override.command(cls=FireCliCommand('object.override.export'), name='export', short_help=HELP['export']['cmd'])
@click.option(
    '-d', '--dst', 'dst', default='overrides.yml', required=False, type=click.Path(), help=HELP['export']['dst']
)
@click.pass_context
def export_cfg(ctx, dst):
    """Export object overrides to yaml configuration file

    \b
    Example:
        firecli object override export --dst /tmp/overrides.yml

    """
    ctx.forward(export_dnsservergroup)
    ctx.forward(export_host)
    ctx.forward(export_ipv4addresspool)
    ctx.forward(export_network)
    ctx.forward(export_range)
    ctx.forward(export_networkgroup)
    ctx.forward(export_timezone)
    ctx.forward(export_url)
