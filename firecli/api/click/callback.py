import click
import copy
import jsonschema
import pathlib
import yaml

from firecli.api import cfg

from fireREST import FMC
from fireREST.exceptions import ResourceNotFoundError


def _option_path(ctx, param):
    """Construct the full path to a called param
    """
    cmd_path = ctx.command_path.split(' ')
    cmd_path.pop(0)
    cmd_path = '.'.join(cmd_path)
    return f'{cmd_path}.{param.name}'


def validate_and_load_yaml(ctx, param, value):
    """Click callback used to load a file using `PyYAML` and validate it using `jsonschema`
    """
    with open(value, 'r') as f:
        try:
            real_value = yaml.safe_load(f)
            cfg.validate(real_value, _option_path(ctx, param))
        except jsonschema.exceptions.ValidationError as exc:
            msg = str(exc)
            if 'None is not of type' in str(exc):
                raise click.BadParameter(f'Schema validation failed with error - {msg}')
            elif real_value:
                raise click.BadParameter(f'Schema validation failed with error - {exc.message}')
            else:
                raise click.BadParameter(f"{value} is empty. See '--help' for required file format...")
        except KeyError as exc:
            msg = f'Schema validation failed. Could not find schema definition for {exc}'
            raise click.BadParameter(f"Failed to load '{value}'.\n{msg}")
        except Exception as exc:  # noqa: B902
            msg = str(exc)
            raise click.BadParameter(f"Failed to load '{value}'.\n{msg}")
    return real_value


def resolve_device_name(ctx, param, value):
    """Click callback used to resolve device name to FMC api object
    """
    fmc = ctx.obj.api.fmc  # type: FMC
    name = copy.copy(value)
    if value:
        try:
            devicehapair = fmc.devicehapair.ftdhapair.get(name=value)
            value = devicehapair['primary']
            value['name'] = name
        except ResourceNotFoundError:
            try:
                value = fmc.device.devicerecord.get(name=value)
            except ResourceNotFoundError:
                raise click.BadParameter(f'"{value}" not found. Make sure device exists...')
    return value


def resolve_accesspolicy_name(ctx, param, value):
    """Click callback used to resolve accesspolicy name to FMC api object
    """
    fmc = ctx.obj.api.fmc  # type: FMC
    if value:
        try:
            return fmc.policy.accesspolicy.get(name=value)
        except ResourceNotFoundError:
            raise click.BadParameter(f'"{value}" not found. Make sure accesspolicy exists...')
    return value


def resolve_path(ctx, param, value):
    """Expand filepath
    """
    return pathlib.Path(value).resolve()


def noncompliant_network_segments_networks(ctx, param, value):
    """Click callback used to create list of source and destination networks for report.noncomplient-network-segments
    command
    """
    if not value:
        raise click.BadParameter('Networks must be configured in firecli.yml configuration file...')
    return value


def list_from_string(ctx, param, value):
    """Click callback used to create a list from a string with items seperated by commas
    """
    if isinstance(value, str):
        value = value.split()
    return value
