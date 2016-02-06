import argparse
import configparser
import logging
import os

# The API version of a particular azure-cli version is fixed.
# To allow for
API_VERSION = '2016-02-04'

try:
    from importlib import import_module
except ImportError:
    def import_module(mod):
        m = __import__(mod)
        for b in mod.split('.'):
            m = gettatr(m, b)
        return m

# TODO: detect language and load correct resources
RC = import_module('azure.cli.resources-en_US')

def _set_log_level(argv):
    # TODO: Configure logging handler to log messages to .py file
    # Thinking here:
    #   INFO messages as Python code
    #   DEBUG messages (if -v) as comments
    #   WARNING/ERROR messages as clearly marked comments
    level = logging.WARNING
    if '-v' in argv or '--verbose' in argv:
        level = logging.DEBUG
        argv[:] = [a for a in argv if a not in {'-v', '--verbose'}]

    logging.basicConfig(level=level)

_loaded_config = None
def _get_config():
    global _loaded_config
    if _loaded_config is None:
        cfg = configparser.RawConfigParser()
        cfg.read(os.path.expanduser('~/azure.ini'))
        _loaded_config = cfg
    return _loaded_config

def main(argv):
    _set_log_level(argv)
    parser = argparse.ArgumentParser(
        description=RC.DESCRIPTION,
        fromfile_prefix_chars='@',
    )

    services = parser.add_subparsers(
        title=RC.SERVICES,
        help=RC.SERVICES_HELP,
        dest='service',
    )
    
    from .commands import add_commands, process_command
    callbacks = add_commands(services.add_parser)
    
    args = parser.parse_args(argv)
    
    process_command(args)
