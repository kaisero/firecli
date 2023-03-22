.. FireCLI documentation master file, created by
   sphinx-quickstart on Mon Dec  7 17:24:47 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

=======
FireCLI
=======

FireCLI is a command line interface to Firepower Management Center
that can perform a variety of tasks ranging from report generation
to import/export of configuration elements like object overrides and s2svpns

============
Installation
============

FireCLI requires Python version >= 3.7 and FMC version >= 6.6.0.
An installation package can be built and installed with the following commands

.. code-block:: shell

  python setup.py
  pip install dist/firecli-1.1.0.tar.gz

.. note:: FireCLI is not distributed through PyPi. Simply running `pip install firecli` will not work

Shell Autocomplete
==================

Since command autocomplete is handled by the systems shell autocomplete
cannot be shipped automatically. Depending on the shell you are using the
following options can be used to generate completion code as static script.
That code can then be loaded by your shell.

Bash

.. code-block:: shell

  _FIRECLI_COMPLETE=source_bash firecli > firecli-complete.sh

Fish

.. code-block:: shell

  _FIRECLI_COMPLETE=source_fish firecli > firecli-complete.sh

Zsh

.. code-block:: shell

  _FIRECLI_COMPLETE=source_zsh firecli > firecli-complete.sh

Manpage
=======

Manpages can be generated and are not shipped by default. To generate manpages the
following procedure must be executed

.. code-block:: shell

  pipenv install --dev --skip-lock
  pipenv shell
  click-man firecli

Documentation
=============

The documentation you are currently reading is generated using Sphinx and RTD theme.
Documentation can be rendered using the following procedure

.. code-block:: shell

  pipenv install --dev --skip-lock
  pipenv shell
  cd docs
  make html

=============
Configuration
=============

By default a configuration file is being shipped to `$INSTALL_DIR/etc/firecli.yml`
FireCLI tries to detect user specific and system wide configuration files by checking
the filesystem in the following order:

1. Check for user specific configuration

.. code-block:: shell

  $HOME_DIR/.firecli/firecli.yml

2. Check for system wide configuration

.. code-block:: shell

  /etc/firecli/firecli.yml

3. Load default configuration from installation directory

.. code-block:: shell

  $INSTALL_DIR/etc/firecli.yml


Configuration File
==================

The configuration file written in YAML format and includes the following options by default

.. code-block:: yaml

   cache_dir: /tmp/firecli
   log_dir:
   hostname: fmc.example.com
   username: firerest
   password: ChangeMeForSecurity123!
   domain: Global/DEV

   options:
     s2svpn:
       point2point:
         name: example-p2p-topology
         create:
           local_device: ftd01.example.com
           local_interface: OUTSIDE
           local_networks: H_OBJ
           remote_device: ftd02.example.com
           remote_interface: 1.1.1.1
           remote_networks: N_OBJ
           ikev2_policy: AES256-SHA256-DH21
           ikev2_psk: Test123
           ipsec_proposal: AES256-SHA256
           ipsec_lifetime: 28800
           ipsec_enable_rri: False
           ipsec_pfs_dh_group: None


Logging
=======

All operations that are displayed during execution are written to disk by default.
The following order is being followed to determine to which file logs should be written:

1. logging directory defined in `firecli.yml` using the `log_dir` variable

2. Check if user is permitted to write to system wide logfile

code-block:: shell

  /var/log/firecli.log

3. Write logfile to users home directory

code-block:: shell

  $HOME_DIR/.firecli/logs/firecli.log

================
Usage
================

.. click:: cli:main
   :prog: firecli
   :nested: full

=====
Index
=====

* :ref:`genindex`
