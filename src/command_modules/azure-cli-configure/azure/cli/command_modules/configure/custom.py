# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function
import os
from six.moves import configparser  # pylint: disable=redefined-builtin
from adal.adal_error import AdalError

import azure.cli.core.azlogging as azlogging
from azure.cli.core._config import (GLOBAL_CONFIG_PATH, ENV_VAR_PREFIX, set_global_config)
from azure.cli.core._util import CLIError
from azure.cli.core.prompting import (prompt,
                                      prompt_y_n,
                                      prompt_choice_list,
                                      prompt_pass,
                                      NoTTYException)
from azure.cli.command_modules.configure._consts import (OUTPUT_LIST, LOGIN_METHOD_LIST,
                                                         MSG_INTRO,
                                                         MSG_CLOSING,
                                                         MSG_GLOBAL_SETTINGS_LOCATION,
                                                         MSG_HEADING_CURRENT_CONFIG_INFO,
                                                         MSG_HEADING_ENV_VARS,
                                                         MSG_PROMPT_MANAGE_GLOBAL,
                                                         MSG_PROMPT_GLOBAL_OUTPUT,
                                                         MSG_PROMPT_LOGIN,
                                                         MSG_PROMPT_TELEMETRY,
                                                         MSG_PROMPT_FILE_LOGGING)
from azure.cli.command_modules.configure._utils import get_default_from_config
import azure.cli.command_modules.configure._help  # pylint: disable=unused-import

logger = azlogging.get_az_logger(__name__)

answers = {}

def _print_cur_configuration(file_config):
    print(MSG_HEADING_CURRENT_CONFIG_INFO)
    for section in file_config.sections():
        print()
        print('[{}]'.format(section))
        for option in file_config.options(section):
            print('{} = {}'.format(option, file_config.get(section, option)))
    env_vars = [ev for ev in os.environ if ev.startswith(ENV_VAR_PREFIX)]
    if env_vars:
        print(MSG_HEADING_ENV_VARS)
        print('\n'.join(['{} = {}'.format(ev, os.environ[ev]) for ev in env_vars]))

def _config_env_public_azure(_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.resource.resources import ResourceManagementClient
    from azure.cli.core._profile import Profile
    # Determine if user logged in
    try:
        list(get_mgmt_service_client(ResourceManagementClient).resources.list())
    except CLIError:
        # Not logged in
        login_successful = False
        while not login_successful:
            method_index = prompt_choice_list(MSG_PROMPT_LOGIN, LOGIN_METHOD_LIST)
            answers['login_index'] = method_index
            answers['login_options'] = str(LOGIN_METHOD_LIST)
            profile = Profile()
            interactive = False
            username = None
            password = None
            service_principal = None
            tenant = None
            if method_index == 0: # device auth
                interactive = True
            elif method_index == 1: # username and password
                username = prompt('Username: ')
                password = prompt_pass(msg='Password: ')
            elif method_index == 2: # service principal with secret
                service_principal = True
                username = prompt('Service principal: ')
                tenant = prompt('Tenant: ')
                password = prompt_pass(msg='Client secret: ')
            elif method_index == 3: # skip
                return
            try:
                profile.find_subscriptions_on_login(
                    interactive,
                    username,
                    password,
                    service_principal,
                    tenant)
                login_successful = True
                logger.warning('Login successful!')
            except AdalError as err:
                logger.error('Login error!')
                logger.error(err)

def _handle_global_configuration():
    # print location of global configuration
    print(MSG_GLOBAL_SETTINGS_LOCATION.format(GLOBAL_CONFIG_PATH))
    # set up the config parsers
    file_config = configparser.SafeConfigParser()
    config_exists = file_config.read([GLOBAL_CONFIG_PATH])
    global_config = configparser.SafeConfigParser()
    global_config.read(GLOBAL_CONFIG_PATH)
    should_modify_global_config = False
    if config_exists:
        # print current config and prompt to allow global config modification
        _print_cur_configuration(file_config)
        should_modify_global_config = prompt_y_n(MSG_PROMPT_MANAGE_GLOBAL, default='n')
        answers['modify_global_prompt'] = should_modify_global_config
    if not config_exists or should_modify_global_config:
        # no config exists yet so configure global config or user wants to modify global config
        output_index = prompt_choice_list(MSG_PROMPT_GLOBAL_OUTPUT, OUTPUT_LIST,
                                          default=get_default_from_config(global_config, \
                                          'core', 'output', OUTPUT_LIST))
        answers['output_type_prompt'] = output_index
        answers['output_type_options'] = str(OUTPUT_LIST)
        enable_file_logging = prompt_y_n(MSG_PROMPT_FILE_LOGGING, default='n')
        allow_telemetry = prompt_y_n(MSG_PROMPT_TELEMETRY, default='y')
        answers['telemetry_prompt'] = allow_telemetry
        # save the global config
        try:
            global_config.add_section('core')
        except configparser.DuplicateSectionError:
            pass
        try:
            global_config.add_section('logging')
        except configparser.DuplicateSectionError:
            pass
        global_config.set('core', 'output', OUTPUT_LIST[output_index]['name'])
        global_config.set('core', 'collect_telemetry', 'yes' if allow_telemetry else 'no')
        global_config.set('logging', 'enable_log_file', 'yes' if enable_file_logging else 'no')
        set_global_config(global_config)

def handle_configure():
    try:
        print(MSG_INTRO)
        _handle_global_configuration()
        print(MSG_CLOSING)
        # TODO: log_telemetry('configure', **answers)
    except NoTTYException:
        raise CLIError('This command is interactive and no tty available.')
    except (EOFError, KeyboardInterrupt):
        print()
