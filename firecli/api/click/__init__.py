import click
import sys

from logging import getLogger

from benedict import benedict

from firecli import CFG

logger = getLogger(__name__)


def FireCliGroup(path):  # noqa 806
    class CustomGroup(click.Group):
        def make_context(self, info_name, args, parent=None, **extra):
            """Load option values from configuration if options are not passed on CLI
            """
            if '--help' not in sys.argv[1:] and '-h' not in sys.argv[1:]:
                if path is not None:
                    try:
                        args = list(args)
                        options = benedict(CFG['options'])[path]
                        for param in self.params:
                            if param.name in options.keys() and not option_set(param, args):
                                param_value = options[param.name]
                                logger.debug(
                                    'Got param "%s" with value "%s" from configuration file', param.name, param_value
                                )
                                if param_value:
                                    args.append(param.opts[0])
                                if not param.is_bool_flag:
                                    args.append(param_value)
                    except (AttributeError, KeyError):
                        logger.debug('Options in configuration file invalid. Skipping...')
            return super(CustomGroup, self).make_context(info_name, args, parent, **extra)

        def invoke(self, ctx):
            if '--help' in sys.argv[1:] or '-h' in sys.argv[1:]:
                # workaround to not run group code when help is executed for subcommand
                self.callback = None
            return super(CustomGroup, self).invoke(ctx)

    return CustomGroup


def FireCliCommand(path):  # noqa 806
    class CustomCommand(click.Command):
        def make_context(self, info_name, args, parent=None, **extra):
            """Load option values from configuration if options are not passed on CLI
            """
            if '--help' not in sys.argv[1:] and '-h' not in sys.argv[1:]:
                if path is not None:
                    try:
                        args = list(args)
                        options = benedict(CFG['options'])[path]
                        for param in self.params:
                            if param.name in options.keys() and not option_set(param, args):
                                param_value = options[param.name]
                                logger.debug(
                                    'Got param "%s" with value "%s" from configuration file', param.name, param_value
                                )
                                if param_value:
                                    args.append(param.opts[0])
                                if not param.is_bool_flag:
                                    args.append(param_value)
                    except (AttributeError, KeyError):
                        logger.debug('Options in configuration file invalid. Skipping...')
            return super(CustomCommand, self).make_context(info_name, args, parent, **extra)

    return CustomCommand


def option_set(param, args):
    """Check if an option is set via CLI
    """
    for arg in args:
        try:
            if arg in param.opts:
                return True
        except IndexError:
            return False
    return False
