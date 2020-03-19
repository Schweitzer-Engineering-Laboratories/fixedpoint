#!/usr/bin/env python3
from setuptools import setup
from setuptools.config import read_configuration
from pathlib import Path

cfg = read_configuration(Path(__file__).parent / 'setup.cfg')

setup(**cfg['metadata'], **cfg['options'])
