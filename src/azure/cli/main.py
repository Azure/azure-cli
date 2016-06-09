import os
import sys

from azure.cli.application import APPLICATION, Configuration
import azure.cli._logging as _logging
from ._session import Session
from ._output import OutputProducer
from ._util import CLIError, show_version_info_exit

logger = _logging.get_az_logger(__name__)

#ACCOUNT contains subscriptions information
# this file will be shared with azure-xplat-cli, which assumes ascii
ACCOUNT = Session('ascii')

# CONFIG provides external configuration options
CONFIG = Session()

# SESSION provides read-write session variables
SESSION = Session()

def main(args, file=sys.stdout, surface_exceptions=False): #pylint: disable=redefined-builtin
    _logging.configure_logging(args)

    if len(args) > 0 and args[0] == '--version':
        show_version_info_exit(file)

    azure_folder = os.path.expanduser('~/.azure')
    if not os.path.exists(azure_folder):
        os.makedirs(azure_folder)
    ACCOUNT.load(os.path.join(azure_folder, 'azureProfile.json'))
    CONFIG.load(os.path.join(azure_folder, 'az.json'))
    SESSION.load(os.path.join(azure_folder, 'az.sess'), max_age=3600)

    config = Configuration(args)
    APPLICATION.initialize(config)

    try:
        cmd_result = APPLICATION.execute(args)
        # Commands can return a dictionary/list of results
        # If they do, we print the results.
        if cmd_result:
            formatter = OutputProducer.get_formatter(APPLICATION.configuration.output_format)
            OutputProducer(formatter=formatter, file=file).out(cmd_result)
    except CLIError as ex:
        if surface_exceptions:
            raise ex
        logger.error(ex.args[0])
        return ex.args[1] if len(ex.args) >= 2 else -1
    except KeyboardInterrupt as ex:
        if surface_exceptions:
            raise KeyboardInterrupt
        return -1
    except Exception as ex: # pylint: disable=broad-except
        logger.exception(ex)
        if surface_exceptions:
            raise ex
        return -1

