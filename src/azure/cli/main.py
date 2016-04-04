from __future__ import print_function

import os
import sys
from datetime import datetime, timedelta

from .application import Application, Configuration

from ._logging import configure_logging, logger
from ._session import Session
from ._output import OutputProducer
from ._util import should_use_private_pypi

from azure.cli.utils.update_checker import check_for_cli_update, UpdateCheckError

# CONFIG provides external configuration options
CONFIG = Session()

# SESSION provides read-write session variables
SESSION = Session()

UPDATE_CHECK_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DAYS_BETWEEN_UPDATE_CHECK = 7

def _should_check_for_update(config_key, now):
    config_data = CONFIG.get(config_key)
    if not config_data:
        return True
    last_checked = datetime.strptime(config_data['last_checked'], UPDATE_CHECK_DATE_FORMAT)
    expiry = last_checked + timedelta(days=DAYS_BETWEEN_UPDATE_CHECK)
    # prev check not expired yet and there wasn't an update available from our previous check
    return False if  expiry >= now and not config_data['update_available'] else True

def _save_update_data(config_key, now, update_info):
    CONFIG[config_key] = {
        'last_checked': now.strftime(UPDATE_CHECK_DATE_FORMAT),
        'latest_version': str(update_info['latest_version'])
                          if update_info['latest_version'] else None,
        'current_version': str(update_info['current_version'])
                           if update_info['current_version'] else None,
        'update_available': update_info['update_available'],
    }

def _check_for_cli_update():
    config_key = 'update_check_cli'
    now = datetime.now()
    if not _should_check_for_update(config_key, now):
        return
    try:
        use_private = should_use_private_pypi()
        update_info = check_for_cli_update(private=use_private)
        _save_update_data(config_key, now, update_info)
        if update_info['update_available']:
            print("Current version of CLI {}. Version {} is available. \
Update with 'az components update self{}'"
                  .format(update_info['current_version'], update_info['latest_version'],
                          ' -p' if use_private else ''))
    except UpdateCheckError as err:
        logger.info('Unable to check for updates. ' + str(err))

def main(args, file=sys.stdout): #pylint: disable=redefined-builtin
    CONFIG.load(os.path.expanduser('~/az.json'))
    SESSION.load(os.path.expanduser('~/az.sess'), max_age=3600)

    configure_logging(args, CONFIG)

    from ._locale import install as locale_install
    locale_install(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'locale',
                                CONFIG.get('locale', 'en-US')))

    config = Configuration(args)
    app = Application(config)
    app.load_commands()
    try:
        cmd_result = app.execute(args)
        # Commands can return a dictionary/list of results
        # If they do, we print the results.
        if cmd_result:
            formatter = OutputProducer.get_formatter(app.configuration.output_format)
            OutputProducer(formatter=formatter, file=file).out(cmd_result)
        _check_for_cli_update()
    except RuntimeError as ex:
        logger.error(ex.args[0])
        return ex.args[1] if len(ex.args) >= 2 else -1
    except KeyboardInterrupt:
        return -1

