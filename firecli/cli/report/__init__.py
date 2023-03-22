from logging import getLogger
from typing import Dict

import click

from fireREST import FMC

from firecli.api.afa import AFA
from firecli.api.click import FireCliCommand, FireCliGroup
from firecli.api.click import callback
from firecli.api import report as report_api


logger = getLogger(__name__)

HELP: Dict[str, Dict]
HELP = {
    'cmd': 'Configuration and compliance reporting',
    'no_of_accessrules': {
        'cmd': 'Create report that lists the number of accessrules',
        'accesspolicy': 'Name of accesspolicy',
        'format': 'Report file format',
        'format_choices': ['csv'],
        'output_dir': 'Output directory to which report is written',
    },
    'accessrules_without_comments': {
        'cmd': 'Create report that lists all accessrules without comments',
        'accesspolicy': 'Name of accesspolicy',
        'format': 'Report file format',
        'format_choices': ['csv'],
        'output_dir': 'Output directory to which report is written',
        'summary': 'Only export number of uncommented accessrules grouped by policy',
    },
    'accessrules_without_ticketid': {
        'cmd': 'Create report that lists all accessrules without a ticket id',
        'accesspolicy': 'Name of accesspolicy',
        'format': 'Report file format',
        'format_choices': ['csv'],
        'output_dir': 'Output directory to which report is written',
        'patterns': 'One or more regular expressions to look for in rule name and comments',
        'summary': 'Only export number of uncommented accessrules grouped by policy',
    },
    'noncompliant_accessrules': {
        'cmd': 'Create report that lists all risky rules ',
        'device': 'Name of device in algosec firewall analyzer',
        'exclude': 'List of rules that will be ignored',
        'format': 'Report file format',
        'format_choices': ['csv'],
        'risks': 'List of risk ids that will be included in report',
        'output_dir': 'Output directory to which report is written',
        'name': 'Custom filename for report',
        'summary': 'Only export number of noncompliant accessrules grouped by device',
    },
    'noncompliant_network_segments': {
        'cmd': '',
        'device': 'Name of device in firepower management center',
        'format': 'Report file format',
        'format_choices': ['csv'],
        'networks': 'List of source and destination networks in format src1,src2:dst1,dst2,src3,src4:dst3,dst4',
        'output_dir': 'Output directory to which report is written',
    },
}


@click.group(cls=FireCliGroup('report'), short_help=HELP['cmd'])
def report():
    pass


@report.command(
    cls=FireCliCommand('report.no_of_accessrules'),
    name='no-of-accessrules',
    short_help=HELP['no_of_accessrules']['cmd'],
)
@click.option(
    '-a',
    '--accesspolicy',
    callback=callback.resolve_accesspolicy_name,
    required=False,
    type=str,
    help=HELP['no_of_accessrules']['accesspolicy'],
)
@click.option(
    '-f',
    '--format',
    'fmt',
    default='csv',
    required=False,
    type=click.Choice(HELP['no_of_accessrules']['format_choices']),
    help=HELP['no_of_accessrules']['format'],
)
@click.option(
    '-o',
    '--output-dir',
    'output_dir',
    callback=callback.resolve_path,
    default='./',
    required=False,
    type=click.Path(exists=True, file_okay=False, dir_okay=True, writable=True),
    help=HELP['no_of_accessrules']['output_dir'],
)
@click.pass_context
def no_of_accessrules(ctx, accesspolicy, fmt, output_dir):
    """Create report that lists the number of accessrules for each accesspolicy

    \b
    Example:
        firecli report no-of-accessrules

    \b
    The output directory can be set manually using the -o option. Default is the current working directory
    \b
        firecli report no-of-accessrules -o /opt/firecli/reports

    \b
    The output can be limited to a single accesspolicy by using the -a option
    \b
        firecli report no-of-accessrules -a FireCli-AccessPolicy

    \b
    Currently only csv format is supported. Example Report:
    \b
        device,device_id,policy,policy_id,rulecount

    """
    fmc = ctx.obj.api.fmc  # type: FMC
    report_api.log_report_gen(ctx)
    data = report_api.accessrule_count(fmc, accesspolicy)
    path = report_api.report_path(ctx.command.name, output_dir, fmt)
    report_api.save(path, data)


@report.command(
    cls=FireCliCommand('report.accessrules_without_comments'),
    name='accessrules-without-comments',
    short_help=HELP['accessrules_without_comments']['cmd'],
)
@click.option(
    '-a',
    '--accesspolicy',
    callback=callback.resolve_accesspolicy_name,
    required=False,
    type=str,
    help=HELP['accessrules_without_comments']['accesspolicy'],
)
@click.option(
    '-f',
    '--format',
    'fmt',
    default='csv',
    required=False,
    type=click.Choice(HELP['accessrules_without_comments']['format_choices']),
    help=HELP['accessrules_without_comments']['format'],
)
@click.option(
    '-o',
    '--output-dir',
    'output_dir',
    callback=callback.resolve_path,
    default='.',
    required=False,
    type=click.Path(exists=True, file_okay=False, dir_okay=True, writable=True),
    help=HELP['accessrules_without_comments']['output_dir'],
)
@click.option('-s', '--summary', is_flag=True, help=HELP['accessrules_without_comments']['summary'])
@click.pass_context
def accessrules_without_comments(ctx, accesspolicy, fmt, output_dir, summary):
    """Create report that lists all accessrules without comments

    \b
    Example:
        firecli report accessrules-without-comments

    \b
    The output directory can be set manually using the -o option. Default is the current working directory
    \b
        firecli report accessrules-without-comments -o /opt/firecli/reports
    \b
    The output can be limited to a single accesspolicy by using the -a option
    \b
        firecli report accessrules-without-comments -a FireCli-AccessPolicy

    \b

    A summary report that only lists the no. of uncommented rules per accesspolicy can be created using the -s option

    \b
        firecli report accessrules-without-comments -s

    \b
    Currently only csv format is supported.

    \b
    Details report format:
    \b
        device,device_id,policy,policy_id,rule,rule_id
    \b
    Summary report format:
    \b
        device,device_id,policy,policy_id,rulecount,uncommented_rule_count

    """
    fmc = ctx.obj.api.fmc  # type: FMC
    report_api.log_report_gen(ctx)
    data = report_api.accessrules_without_comments(fmc, accesspolicy)
    path = report_api.report_path(ctx.command.name, output_dir, fmt, summary)
    report_api.save(path, data)


@report.command(
    cls=FireCliCommand('report.accessrules_without_ticketid'),
    name='accessrules-without-ticket-id',
    short_help=HELP['accessrules_without_ticketid']['cmd'],
)
@click.option(
    '-a',
    '--accesspolicy',
    callback=callback.resolve_accesspolicy_name,
    required=False,
    type=str,
    help=HELP['accessrules_without_ticketid']['accesspolicy'],
)
@click.option(
    '-f',
    '--format',
    'fmt',
    default='csv',
    required=False,
    type=click.Choice(HELP['accessrules_without_ticketid']['format_choices']),
    help=HELP['accessrules_without_ticketid']['format'],
)
@click.option(
    '-o',
    '--output-dir',
    'output_dir',
    callback=callback.resolve_path,
    default='.',
    required=False,
    type=click.Path(exists=True, file_okay=False, dir_okay=True, writable=True),
    help=HELP['accessrules_without_ticketid']['output_dir'],
)
@click.option(
    '-p',
    '--patterns',
    'patterns',
    callback=callback.list_from_string,
    default='.*Ticket#.*',
    required=False,
    type=str,
    help=HELP['accessrules_without_ticketid']['patterns'],
)
@click.option('-s', '--summary', is_flag=True, help=HELP['accessrules_without_ticketid']['summary'])
@click.pass_context
def accessrules_without_ticketid(ctx, accesspolicy, fmt, output_dir, patterns, summary):
    """Create report that lists all accessrules without ticketnumbers in name or comments

    \b
    Example:
        firecli report accessrules-without-ticketid -p ".*TicketNr.*"

    \b
    The patterns option can include one or multiple regular expressions which will be matched against
    accessrule names and the content of all associated comments
    \b

    \b
    The output directory can be set manually using the -o option. Default is the current working directory
    \b
        firecli report accessrules-without-ticketid -o /opt/firecli/reports
    \b
    The output can be limited to a single accesspolicy by using the -a option
    \b
        firecli report accessrules-without-ticketid -a FireCli-AccessPolicy

    \b

    A summary report that only lists the no. of rules without a ticketid per policy can be created using the -s option

    \b
        firecli report accessrules-without-ticketid -s

    \b
    Currently only csv format is supported.

    \b
    Details report format:
    \b
        device,device_id,policy,policy_id,rule,rule_id
    \b
    Summary report format:
    \b
        device,device_id,policy,policy_id,rule_count,rules_without_ticketid_count

    """
    fmc = ctx.obj.api.fmc  # type: FMC
    report_api.log_report_gen(ctx)
    data = report_api.accessrules_without_ticket_id(fmc, patterns, accesspolicy)
    path = report_api.report_path(ctx.command.name, output_dir, fmt, summary)
    report_api.save(path, data)


@report.command(
    cls=FireCliCommand('report.noncompliant_accessrules'),
    name='noncompliant-accessrules',
    short_help=HELP['noncompliant_accessrules']['cmd'],
)
@click.option('-d', '--device', required=False, type=str, help=HELP['noncompliant_accessrules']['device'])
@click.option(
    '-e',
    '--exclude',
    'exclude',
    callback=callback.list_from_string,
    default='',
    required=False,
    type=str,
    help=HELP['noncompliant_accessrules']['exclude'],
)
@click.option(
    '-f',
    '--format',
    'fmt',
    default='csv',
    required=False,
    type=click.Choice(HELP['noncompliant_accessrules']['format_choices']),
    help=HELP['noncompliant_accessrules']['format'],
)
@click.option(
    '-o',
    '--output-dir',
    'output_dir',
    callback=callback.resolve_path,
    default='.',
    required=False,
    type=click.Path(exists=True, file_okay=False, dir_okay=True, writable=True),
    help=HELP['noncompliant_accessrules']['output_dir'],
)
@click.option('-n', '--name', 'name', required=False, type=str, help=HELP['noncompliant_accessrules']['name'])
@click.option(
    '-r',
    '--risks',
    callback=callback.list_from_string,
    default='',
    required=False,
    type=str,
    help=HELP['noncompliant_accessrules']['risks'],
)
@click.option('-s', '--summary', is_flag=True, help=HELP['noncompliant_accessrules']['summary'])
@click.pass_context
def noncompliant_accessrules(ctx, device, exclude, fmt, output_dir, name, risks, summary):
    """Create report that lists all accessrules that are classified as risky rules in algosec firewall analyzer

    \b
    Example:
        firecli report noncompliant-accessrules

    \b
    The output directory can be set manually using the -o option. Default is the current working directory
    \b
        firecli report noncompliant-accessrules -o /opt/firecli/reports
    \b
    The output can be limited to a single device by using the -d option
    \b
        firecli report noncompliant-accessrules -d ftd01.example.com

    \b
    Risky rules can be excluded to filter false positives from the report
    \b
        firecli report noncompliant-accessrules -e "RuleName1 RuleName2 RuleName3"

    \b
    Risky rules can be filtered by specifying relevant risk IDs that will be included in the report
    \b
        firecli report noncompliant-accessrules -r "C00001 C00002 C00003"

    \b
    A summary report that only lists the no. of noncompliant rules per policy can be created using the -s option

    \b
        firecli report noncompliant-accessrules -s

    \b
    Currently only csv format is supported.

    \b
    Details report format:
    \b
        device,device_id,policy,policy_id,rule,rule_id,risk
    \b
    Summary report format:
    \b
        device,policy,rulecount,noncompliant_rules
        ftd01.example.com,FireCli-Policy,1000,250

    """
    afa = ctx.obj.api.afa  # type: AFA
    fmc = ctx.obj.api.fmc  # type: FMC
    filename = ctx.command.name if not name else name
    report_api.log_report_gen(ctx)
    data = report_api.noncompliant_accessrules(afa, fmc, device, exclude, risks)
    path = report_api.report_path(filename, output_dir, fmt, summary)
    report_api.save(path, data)


@report.command(
    cls=FireCliCommand('report.noncompliant_network_segments'),
    name='noncompliant-network-segments',
    short_help=HELP['noncompliant_network_segments']['cmd'],
)
@click.option(
    '-d',
    '--device',
    callback=callback.resolve_device_name,
    default='ftd01.example.com',
    required=False,
    type=str,
    help=HELP['noncompliant_network_segments']['device'],
)
@click.option(
    '-f',
    '--format',
    'fmt',
    default='csv',
    required=False,
    type=click.Choice(HELP['noncompliant_network_segments']['format_choices']),
    help=HELP['noncompliant_network_segments']['format'],
)
@click.option(
    '-n',
    '--networks',
    callback=callback.noncompliant_network_segments_networks,
    required=False,
    type=str,
    help=HELP['noncompliant_network_segments']['networks'],
)
@click.option(
    '-o',
    '--output-dir',
    'output_dir',
    callback=callback.resolve_path,
    default='.',
    required=False,
    type=click.Path(exists=True, file_okay=False, dir_okay=True, writable=True),
    help=HELP['noncompliant_network_segments']['output_dir'],
)
@click.pass_context
def noncompliant_network_segments(ctx, device, fmt, networks, output_dir):
    """Create report that lists all noncompliant network segments that should not be able to communicate
    with each other. The report checks a list of source and destination networks and checks the firewalls
    routing table to find out if the segments are seperated

    \b
    Example:
        firecli report noncompliant-network-segments

    \b
    The output directory can be set manually using the -o option. Default is the current working directory
    \b
        firecli report noncompliant-network-segments -o /opt/firecli/reports
    \b
    A single device must be specified by using the -d option
    \b
        firecli report noncompliant-network-segments -d ftd01.example.com

    \b
    A list of source and destination networks that should not exist on the same interface
    must be specified in firecli.yml for this report to work correctly.

    \b
    Currently only csv format is supported.

    \b
    Details report format:
    \b
        device,device_id,source,source_network,destination,destination_network,firewalled
    \b
    """
    fmc = ctx.obj.api.fmc  # type: FMC
    report_api.log_report_gen(ctx)
    data = report_api.noncompliant_network_segments(fmc, device, networks)
    path = report_api.report_path(ctx.command.name, output_dir, fmt)
    report_api.save(path, data)
