#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
from setuptools import find_packages, setup, Command

# Package meta-data.
NAME = 'kpoller'
DESCRIPTION = 'short description'
URL = 'https://github.com/adikue/krygina_cather'
EMAIL = 'adikue@gmail.com'
AUTHOR = 'Ivan Vovk'
REQUIRES_PYTHON = '>=2.7, <3'

# What packages are required for this module to be executed?
REQUIRED = [
    "selenium"
]

here = os.path.abspath(os.path.dirname(__file__))
# Load the package's __version__.py module as a dictionary.
about = {}

with open(os.path.join(here, NAME, '__version__.py')) as f:
    exec(f.read(), about)


setup(
    name=NAME,
    version=about['__version__'],
    description=DESCRIPTION,
    long_description='long_description',
    author=AUTHOR,
    author_email=EMAIL,
    python_requires=REQUIRES_PYTHON,
    url=URL,
    packages=find_packages(exclude=["tests"]),
    scripts=['bin/kpoller'],
    data_files=[('/etc/systemd/system/', ['unit/kpoller.service']),
                ('/etc/kpoller/', ['kp.db', 'config/kpoller.conf']),],
    install_requires=REQUIRED,
    include_package_data=False,
    license='MIT',
    classifiers=[
        # Trove classifiers
        # Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
        'License :: Other/Proprietary License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: Implementation :: CPython',
    ]
)
