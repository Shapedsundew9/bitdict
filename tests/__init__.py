"""Ensures module path is in the python path."""

from os.path import abspath, dirname, join
from sys import path

path.insert(0, abspath(path=join(dirname(p=__file__), "..")))
