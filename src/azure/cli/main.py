import logging
import os

from ._argparse import ArgumentParser
from ._logging import configure_logging
from ._util import import_module

__author__ = "Microsoft Corporation <python@microsoft.com>"
__version__ = "2016.2.4"

# TODO: detect language and load correct resources
RC = import_module('azure.cli.resources-en_US')

def main(argv):
    # configure_logging will remove any arguments it uses so we do not
    # need to worry about parsing them elsewhere
    argv = configure_logging(argv)
    
    import azure.cli.commands as commands
    parser = ArgumentParser()
    # TODO: detect language
    parser.doc_source = os.path.dirname(commands.__file__)
    parser.doc_suffix = '.en_US.txt'

    commands.add_to_parser(parser)
    
    try:
        parser.execute(argv)
    except RuntimeError as ex:
        logging.error(ex.args[0])
        return ex.args[1] if len(ex.args) >= 2 else -1
