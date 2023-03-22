# FireCLI

FireCLI is a command line interface to Firepower Management Center
that can perform a variety of tasks ranging from report generation
to import/export of configuration elements like object overrides and s2svpns

## Requirements

FireCLI requires Python version >= 3.7 and FMC version >= 6.6.0

## Installation

Build and install FireCLI

```shell
tox -e build
pip install dist/firecli-1.1.0.tar.gz
```

Generate documentation

```shell
tox -e docs
```

## Usage

```shell
Usage: firecli.py [OPTIONS] COMMAND [ARGS]...

  FireCLI is a command line interface to Firepower Management Center that
  automates a variety of tasks

Options:
  --version          Show the version and exit.
  --hostname TEXT    Hostname of firepower management center
  --domain TEXT      Management domain of FMC
  --username TEXT    Username of fmc api user. It is recommended to create a
                     dedicated api user

  --password TEXT    Password of fmc api user
  --timeout INTEGER  Api request timeout in seconds
  --dry-run          Display changes without performing an action
  --debug            Enable debug loglevel
  --trace            Enable trace loglevel (Debug + FireREST api calls)
  --no-proxy         Ignore system proxy settings
  -h, --help         Show this message and exit.

Commands:
  accesspolicy  Accesspolicy management
  cache         Local cache management
  compliance    Security compliance checks
  log           Application log analysis
  object        Object management
  s2svpn        Site2Site vpn management
  sync          Configuration synchronisation
```

## Documentation

See `docs/` for additional project documentation.

## Author Information

Oliver Kaiser (oliver.kaiser@outlook.com)
