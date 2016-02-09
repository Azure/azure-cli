import logging

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
    
    parser = ArgumentParser(
        prog=RC.PROG,
        description=RC.DESCRIPTION,
        fromfile_prefix_chars='@',
    )

    parser.add_argument('--api-version', help=RC.API_VERSION_HELP)

    services = parser.add_subparsers(
        title=RC.SERVICES,
        help=RC.SERVICES_HELP,
        dest='service',
    )
    
    from .commands import add_commands, process_command
    callbacks = add_commands(services)
    
    args = parser.parse_args(argv)
    if not args.service:
        parser.print_help()
        return 1
    
    if args.api_version:
        logging.debug('Using api version %s', args.api_version)
        # TODO: Force use of specified version
        # Probably by extending azure.__path__ to load the correct version of azure.mgmt
        pass
    
    try:
        process_command(args)
    except RuntimeError as ex:
        logging.error(ex.args[0])
        return ex.args[1] if len(ex.args) >= 2 else -1
