from __future__ import print_function
import os

import collections
from datetime import datetime, timedelta
from .._logging import logger
from azure.cli.utils.update_checker import check_for_cli_update, UpdateCheckError

data = collections.namedtuple('Data', 'disable_version_check')

UPDATE_CHECK_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DAYS_BETWEEN_UPDATE_CHECK = 7
AZURE_CLI_UPDATE_CHECK_USE_PRIVATE = "AZURE_CLI_UPDATE_CHECK_USE_PRIVATE"

def should_use_private_pypi():
    return bool(os.environ.get(AZURE_CLI_UPDATE_CHECK_USE_PRIVATE))

def _should_check_for_update(CONFIG, config_key, now):
    config_data = CONFIG.get(config_key)
    if not config_data:
        return True
    last_checked = datetime.strptime(config_data['last_checked'], UPDATE_CHECK_DATE_FORMAT)
    expiry = last_checked + timedelta(days=DAYS_BETWEEN_UPDATE_CHECK)
    # prev check not expired yet and there wasn't an update available from our previous check
    return False if  expiry >= now and not config_data['update_available'] else True

def _save_update_data(CONFIG, config_key, now, update_info):
    CONFIG[config_key] = {
        'last_checked': now.strftime(UPDATE_CHECK_DATE_FORMAT),
        'latest_version': str(update_info['latest_version'])
                          if update_info['latest_version'] else None,
        'current_version': str(update_info['current_version'])
                           if update_info['current_version'] else None,
        'update_available': update_info['update_available'],
    }

def _check_for_cli_update(CONFIG):
    config_key = 'update_check_cli'
    now = datetime.now()
    if not _should_check_for_update(CONFIG, config_key, now):
        return
    try:
        use_private = should_use_private_pypi()
        update_info = check_for_cli_update(private=use_private)
        _save_update_data(CONFIG, config_key, now, update_info)
        if update_info['update_available']:
            print("Current version of CLI {}. Version {} is available. \
Update with 'az components update-self{}'"
                  .format(update_info['current_version'], update_info['latest_version'],
                          ' -p' if use_private else ''))
    except UpdateCheckError as err:
        logger.info('Unable to check for updates. ' + str(err))


def _register_global_parameter(parser):
    parser.add_argument('--disable-version-check', dest='_disable_version_check',
                        action='store_true',
                        help='Disable version checking of the CLI and the installed components.')

def register(application):
    def handle_disable_version_check_parameter(args):
        data.disable_version_check = bool(args._disable_version_check) # pylint: disable=protected-access

    def handle_update_checking(_):
        if not data.disable_version_check: # pylint: disable=no-member
            from azure.cli.main import CONFIG
            _check_for_cli_update(CONFIG)

    # Register our global parameter
    application.register(application.GLOBAL_PARSER_CREATED, _register_global_parameter)
    # Check to see if the parameter was set
    application.register(application.COMMAND_PARSER_PARSED, handle_disable_version_check_parameter)
    # Once the command has completed, we check for updates
    application.register(application.COMMAND_FINISHED, handle_update_checking)
