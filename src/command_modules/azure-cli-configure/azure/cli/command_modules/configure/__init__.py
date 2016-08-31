#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from __future__ import print_function
import os
import sys
from six.moves import input, configparser #pylint: disable=redefined-builtin
from adal.adal_error import AdalError

from azure.cli.commands import cli_command
import azure.cli._logging as _logging
from azure.cli._config import (GLOBAL_CONFIG_DIR, GLOBAL_CONFIG_PATH,
                               ENV_CONFIG_DIR, ACTIVE_ENV_CONFIG_PATH,
                               ENV_VAR_PREFIX)
from azure.cli.command_modules.configure._consts import (OUTPUT_LIST, CLOUD_LIST, LOGIN_METHOD_LIST,
                                                         MSG_INTRO,
                                                         MSG_CLOSING,
                                                         MSG_GLOBAL_SETTINGS_LOCATION,
                                                         MSG_ACTIVE_ENV_SETTINGS_LOCATION,
                                                         MSG_HEADING_CURRENT_CONFIG_INFO,
                                                         MSG_HEADING_ENV_VARS,
                                                         MSG_PROMPT_MANAGE_GLOBAL,
                                                         MSG_PROMPT_MANAGE_ENVS,
                                                         MSG_PROMPT_GLOBAL_OUTPUT,
                                                         MSG_PROMPT_WHICH_ENV,
                                                         MSG_PROMPT_WHICH_CLOUD,
                                                         MSG_PROMPT_LOGIN)
from azure.cli.command_modules.configure._utils import (prompt_y_n,
                                                        prompt_choice_list,
                                                        get_default_from_config)
import azure.cli.command_modules.configure._help # pylint: disable=unused-import

from azure.cli._util import CLIError
logger = _logging.get_az_logger(__name__)

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

def _get_envs():
    if os.path.isdir(ENV_CONFIG_DIR):
        return [f for f in os.listdir(ENV_CONFIG_DIR) \
                if os.path.isfile(os.path.join(ENV_CONFIG_DIR, f))]
    return []

def _config_env_public_azure(_):
    from azure.cli.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.resource.resources import ResourceManagementClient
    from azure.cli._profile import Profile
    # Determine if user logged in
    try:
        list(get_mgmt_service_client(ResourceManagementClient).resources.list())
    except CLIError:
        # Not logged in
        import getpass
        login_successful = False
        while not login_successful:
            method_index = prompt_choice_list(MSG_PROMPT_LOGIN, LOGIN_METHOD_LIST)
            profile = Profile()
            interactive = False
            username = None
            password = None
            service_principal = None
            tenant = None
            if method_index == 0: # device auth
                interactive = True
            elif method_index == 1: # username and password
                username = input('Username: ')
                password = getpass.getpass('Password: ')
            elif method_index == 2: # service principal with secret
                service_principal = True
                username = input('Service principal: ')
                tenant = input('Tenant: ')
                password = getpass.getpass('Client secret: ')
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

def _create_or_update_env(env_name=None):
    if not env_name:
        # TODO Support new env creation
        print('This feature is coming soon.\n')
        sys.exit(1)
    # get the config parser for this env
    env_config = configparser.SafeConfigParser()
    env_config.read(os.path.join(ENV_CONFIG_DIR, env_name))
    # prompt user to choose cloud for env
    selected_cloud_index = prompt_choice_list(MSG_PROMPT_WHICH_CLOUD, CLOUD_LIST,
                                              default=get_default_from_config(env_config,
                                                                              'cloud',
                                                                              'name',
                                                                              CLOUD_LIST))
    if CLOUD_LIST[selected_cloud_index]['name'] != 'public-azure':
        # TODO support other clouds
        print('Support for other clouds is coming soon.\n')
        sys.exit(1)
    try:
        env_config.add_section('cloud')
    except configparser.DuplicateSectionError:
        pass
    env_config.set('cloud', 'name', CLOUD_LIST[selected_cloud_index]['name'])
    # TODO when we support other clouds, extend this to a class. Keeping it simple for now.
    _config_env_public_azure(env_config)
    # save the config
    if not os.path.isdir(ENV_CONFIG_DIR):
        os.makedirs(ENV_CONFIG_DIR)
    with open(os.path.join(ENV_CONFIG_DIR, env_name), 'w') as configfile:
        env_config.write(configfile)

def _handle_global_configuration():
    # print location of global configuration
    print(MSG_GLOBAL_SETTINGS_LOCATION.format(GLOBAL_CONFIG_PATH))
    if os.path.isfile(ACTIVE_ENV_CONFIG_PATH):
        # print location of the active env configuration if it exists
        print(MSG_ACTIVE_ENV_SETTINGS_LOCATION.format(ACTIVE_ENV_CONFIG_PATH))
    # set up the config parsers
    file_config = configparser.SafeConfigParser()
    config_exists = file_config.read([GLOBAL_CONFIG_PATH, ACTIVE_ENV_CONFIG_PATH])
    global_config = configparser.SafeConfigParser()
    global_config.read(GLOBAL_CONFIG_PATH)
    should_modify_global_config = False
    if config_exists:
        # print current config and prompt to allow global config modification
        _print_cur_configuration(file_config)
        should_modify_global_config = prompt_y_n(MSG_PROMPT_MANAGE_GLOBAL, default='n')
    if not config_exists or should_modify_global_config:
        # no config exists yet so configure global config or user wants to modify global config
        output_index = prompt_choice_list(MSG_PROMPT_GLOBAL_OUTPUT, OUTPUT_LIST,
                                          default=get_default_from_config(global_config, \
                                          'default', 'output', OUTPUT_LIST))
        # save the global config
        try:
            global_config.add_section('default')
        except configparser.DuplicateSectionError:
            pass
        global_config.set('default', 'output', OUTPUT_LIST[output_index]['name'])
        if not os.path.isdir(GLOBAL_CONFIG_DIR):
            os.makedirs(GLOBAL_CONFIG_DIR)
        with open(GLOBAL_CONFIG_PATH, 'w') as configfile:
            global_config.write(configfile)

def _handle_env_configuration():
    envs = _get_envs()
    if envs:
        should_configure_envs = prompt_y_n(MSG_PROMPT_MANAGE_ENVS, default='n')
        if not should_configure_envs:
            return
        env_to_configure_index = prompt_choice_list(MSG_PROMPT_WHICH_ENV, envs + \
                                                    ['Create new environment (not yet supported)'])
        if env_to_configure_index == len(envs):
            # The last choice was picked by the user which corresponds to 'create new environment'
            _create_or_update_env()
        else:
            # modify existing environment
            _create_or_update_env(envs[env_to_configure_index])
    else:
        # no env exists so create first environment
        _create_or_update_env('default')

def handle_configure():
    try:
        print(MSG_INTRO)
        _handle_global_configuration()
        _handle_env_configuration()
        print(MSG_CLOSING)
    except (EOFError, KeyboardInterrupt):
        print()

cli_command('configure', handle_configure)
