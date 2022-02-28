# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import time
from msrestazure.tools import parse_resource_id
from azure.cli.core.azclierror import (
    CLIInternalError
)


def should_load_source(source):
    '''Check whether to load `az {source} connection`
    If {source} is an extension (e.g, spring-cloud), load the command group only when {source} is installed
    :param source: the source resource type
    '''
    from azure.cli.core.extension.operations import list_extensions
    from ._resource_config import SOURCE_RESOURCES_IN_EXTENSION

    # names of CLI installed extensions
    installed_extensions = [item.get('name') for item in list_extensions()]
    # if source resource is released as an extension, load our command groups
    # only when the extension is installed
    if source not in SOURCE_RESOURCES_IN_EXTENSION or source.value in installed_extensions:
        return True
    return False


def generate_random_string(length=5, prefix='', lower_only=False, ensure_complexity=False):
    '''Generate a random string
    :param length: the length of generated random string, not including the prefix
    :param prefix: the prefix string
    :param lower_only: ensure the generated string only includes lower case characters
    :param ensure_complexity: ensure the generated string satisfy complexity requirements
    '''
    import random
    import string

    if lower_only and ensure_complexity:
        raise CLIInternalError('lower_only and ensure_complexity can not both be specified to True')
    if ensure_complexity and length < 8:
        raise CLIInternalError('ensure_complexity needs length >= 8')

    character_set = string.ascii_letters + string.digits
    if lower_only:
        character_set = string.ascii_lowercase

    while True:
        randstr = '{}{}'.format(prefix, ''.join(random.sample(character_set, length)))
        lowers = [c for c in randstr if c.islower()]
        uppers = [c for c in randstr if c.isupper()]
        numbers = [c for c in randstr if c.isnumeric()]
        if not ensure_complexity or (lowers and uppers and numbers):
            break

    return randstr


def run_cli_cmd(cmd, retry=0):
    '''Run a CLI command
    :param cmd: The CLI command to be executed
    :param retry: The times to re-try
    '''
    import json
    import subprocess

    output = subprocess.run(cmd, shell=True, check=False, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    if output.returncode != 0:
        if retry:
            run_cli_cmd(cmd, retry - 1)
        else:
            raise CLIInternalError('Command execution failed, command is: '
                                   '{}, error message is: {}'.format(cmd, output.stderr))

    return json.loads(output.stdout) if output.stdout else None


def set_user_token_header(client, cli_ctx):
    '''Set user token header to work around OBO'''
    from azure.cli.core._profile import Profile

    # pylint: disable=protected-access
    # HACK: set custom header to work around OBO
    profile = Profile(cli_ctx=cli_ctx)
    creds, _, _ = profile.get_raw_token()
    client._client._config.headers_policy._headers['x-ms-serviceconnector-user-token'] = creds[1]
    # HACK: hide token header
    client._config.logging_policy.headers_to_redact.append('x-ms-serviceconnector-user-token')

    return client


def provider_is_registered(subscription=None):
    # register the provider
    subs_arg = ''
    if subscription:
        subs_arg = '--subscription {}'.format(subscription)
    output = run_cli_cmd('az provider show -n Microsoft.ServiceLinker {}'.format(subs_arg))
    if output.get('registrationState') == 'NotRegistered':
        return False
    return True


def register_provider(subscription=None):
    from knack.log import get_logger
    logger = get_logger(__name__)

    logger.warning('Provider Microsoft.ServiceLinker is not registered, '
                   'trying to register. This usually takes 1-2 minutes.')

    subs_arg = ''
    if subscription:
        subs_arg = '--subscription {}'.format(subscription)

    # register the provider
    run_cli_cmd('az provider register -n Microsoft.ServiceLinker {}'.format(subs_arg))

    # verify the registration, 30 * 10s polling the result
    MAX_RETRY_TIMES = 30
    RETRY_INTERVAL = 10

    count = 0
    while count < MAX_RETRY_TIMES:
        time.sleep(RETRY_INTERVAL)
        output = run_cli_cmd('az provider show -n Microsoft.ServiceLinker {}'.format(subs_arg))
        current_state = output.get('registrationState')
        if current_state == 'Registered':
            return True
        if current_state == 'Registering':
            count += 1
        else:
            return False
    return False


def auto_register(func, *args, **kwargs):
    import copy
    from azure.core.polling._poller import LROPoller
    from azure.core.exceptions import HttpResponseError

    # kwagrs will be modified in SDK
    kwargs_backup = copy.deepcopy(kwargs)
    try:
        res = func(*args, **kwargs)
        if isinstance(res, LROPoller):
            # polling the result to handle the case when target subscription is not registered
            return res.result()
        return res

    except HttpResponseError as ex:
        # source subscription is not registered
        if ex.error and ex.error.code == 'SubscriptionNotRegistered':
            if register_provider():
                return func(*args, **kwargs_backup)
            raise CLIInternalError('Registeration failed, please manually run command '
                                   '`az provider register -n Microsoft.ServiceLinker` to register the provider.')
        # target subscription is not registered, raw check
        if ex.error and ex.error.code == 'UnauthorizedResourceAccess' and 'not registered' in ex.error.message:
            if 'parameters' in kwargs_backup and 'target_id' in kwargs_backup.get('parameters'):
                segments = parse_resource_id(kwargs_backup.get('parameters').get('target_id'))
                target_subs = segments.get('subscription')
                # double check whether target subscription is registered
                if not provider_is_registered(target_subs):
                    if register_provider(target_subs):
                        return func(*args, **kwargs_backup)
                    raise CLIInternalError('Registeration failed, please manually run command '
                                           '`az provider register -n Microsoft.ServiceLinker --subscription {}` '
                                           'to register the provider.'.format(target_subs))
        raise ex
