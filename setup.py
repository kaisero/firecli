#!/usr/bin/env python

from pathlib import Path

import setuptools

ROOT = Path(__file__).parent

with open('README.md', 'r') as readme:
    long_description = readme.read()

exec(open(f'{ROOT}/firecli/version.py', 'r').read())

setuptools.setup(
    name='firecli',
    version=__version__,  # noqa: F821
    author='Oliver Kaiser',
    author_email='oliver.kaiser@outlook.com',
    description='FireCLI is a command line interface to Firepower Management Center',
    keywords='cisco firepower fmc ftd fpr api rest python api cli',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://git.ong.at/cisco/firecli.git',
    packages=setuptools.find_packages(),
    install_requires=[
        'click<=8.0.4',
        'fireREST>=1.0.9',
        'jsonschema>=3.2.0',
        'netaddr>=0.8.0',
        'openpyxl>=3.0.3',
        'PyYAML>=5.3.1',
        'python-benedict>=0.18.1',
        'python-json-logger>=2.0.1',
        'rich>=9.2.0',
        'stackprinter>=0.2.5',
    ],
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 3',
    ],
    entry_points={'console_scripts': ['firecli = firecli.cli:main']},
    data_files=[('firecli/etc', [str(f) for f in Path('etc/').glob('*') if f.is_file()])],
)
