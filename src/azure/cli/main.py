import logging
import os

from ._argparse import ArgumentParser
from ._logging import configure_logging
from ._session import Session
from ._util import import_module

__author__ = "Microsoft Corporation <python@microsoft.com>"
__version__ = "2016.2.4"

# TODO: detect language and load correct resources
RC = import_module('azure.cli.resources-en_US')

# CONFIG provides external configuration options
CONFIG = Session()

# SESSION provides read-write session variables
SESSION = Session()

def main(args):
    CONFIG.load(os.path.expanduser('~/az.json'))
    SESSION.load(os.path.expanduser('~/az.sess'), max_age=3600)

    configure_logging(args, CONFIG)

    parser = ArgumentParser(RC.PROG)

    import azure.cli.commands as commands
    parser.doc_source = os.path.dirname(commands.__file__)
    # TODO: detect language
    parser.doc_suffix = '.en_US.txt'

    # Find the first noun on the command line and only load commands from that
    # module to improve startup time.
    for a in args:
        if not a.startswith('-'):
            commands.add_to_parser(parser, a)
            break
    else:
        # No noun found, so load all commands.
        commands.add_to_parser(parser)
    
    try:
        parser.execute(args)
    except RuntimeError as ex:
        logging.error(ex.args[0])
        return ex.args[1] if len(ex.args) >= 2 else -1
