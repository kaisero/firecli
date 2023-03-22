#!/usr/bin/env python
#
# This file is part of FireCLI

import firecli
from firecli import cli

logger = firecli.logger


def main():
    try:
        cli.main()
    except Exception as exc:  # noqa: B902
        logger.critical(str(exc), exc_info=True)
        raise


if __name__ == '__main__':
    main()
