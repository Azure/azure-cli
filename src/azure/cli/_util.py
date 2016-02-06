import logging
import types

try:
    from importlib import import_module
except ImportError:
    def import_module(mod):
        m = __import__(mod)
        for b in mod.split('.'):
            m = gettatr(m, b)
        return m
