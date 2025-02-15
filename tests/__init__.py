"""Ensures module path is in the python path."""

from sys import path
from os.path import abspath, dirname, join

path.insert(0, abspath(path=join(dirname(p=__file__), "..")))
