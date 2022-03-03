# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import time
from knack.util import todict
from msrestazure.tools import parse_resource_id
from azure.cli.core.azclierror import (
    ValidationError,
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


def create_key_vault_reference_connection_if_not_exist(cmd, client, source_id, key_vault_id):
    from ._validators import get_source_resource_name
    from knack.log import get_logger
    logger = get_logger(__name__)

    logger.warning('get valid key vualt reference connection')
    all_connections = todict(client.list(resource_uri = source_id))
    key_vault_connections = []
    for connection in all_connections:  # pylint: disable=not-an-iterable
        if connection.get('targetId') == key_vault_id:
            key_vault_connections.append(connection)

    source_name = get_source_resource_name(cmd)
    auth_info = get_auth_if_no_valid_key_vault_connection(logger, source_name, source_id, key_vault_connections)
    if not auth_info:
        return

    # No Valid Key Vault Connection, Create
    logger.warning('no valid key vault connection found. Creating...')

    from ._resource_config import CLIENT_TYPE

    connection_name = generate_random_string(prefix='keyvault_')
    parameters = {
        'target_id': key_vault_id,
        'auth_info': auth_info,
        'client_type': CLIENT_TYPE.Dotnet,  # Key Vault Configuration are same across all client types
    }

    return auto_register(client.begin_create_or_update,
                         resource_uri=source_id,
                         linker_name=connection_name,
                         parameters=parameters)


def get_auth_if_no_valid_key_vault_connection(logger, source_name, source_id, key_vault_connections):
    auth_type = 'systemAssignedIdentity'
    client_id = None
    subscription_id = None

    if len(key_vault_connections) > 0:
        from ._resource_config import RESOURCE
        from msrestazure.tools import (
            parse_resource_id,
            is_valid_resource_id
        )

        # https://docs.microsoft.com/azure/app-service/app-service-key-vault-references
        if source_name == RESOURCE.WebApp:
            try:
                webapp = run_cli_cmd('az rest -u {}?api-version=2020-09-01 -o json'.format(source_id))
                reference_identity = webapp.get('properties').get('keyVaultReferenceIdentity')
            except Exception as e:
                raise ValidationError('{}. Unable to get "properties.keyVaultReferenceIdentity" from {}.'
                                      'Please check your source id is correct.'.format(e, source_id))

            if is_valid_resource_id(reference_identity):  # User Identity
                auth_type = 'userAssignedIdentity'
                segments = parse_resource_id(reference_identity)
                subscription_id = segments.get('subscription')
                try:
                    identity = webapp.get('identity').get('userAssignedIdentities').get(reference_identity)
                    client_id = identity.get('clientId')
                except Exception:  # pylint: disable=broad-except
                    try:
                        identity = run_cli_cmd('az identity show --ids {} -o json'.format(reference_identity))
                        client_id = identity.get('clientId')
                    except Exception:  # pylint: disable=broad-except
                        pass
                if not subscription_id or not client_id:
                    raise ValidationError('Unable to get subscriptionId or clientId'
                                          'of the keyVaultReferenceIdentity {}'.format(reference_identity))
                for connection in key_vault_connections:
                    auth_info = connection.get('authInfo')
                    if auth_info.get('clientId') == client_id and auth_info.get('subscriptionId') == subscription_id:
                        logger.warning('key vualt reference connection: %s', connection.get('id'))
                        return
            else:  # System Identity
                for connection in key_vault_connections:
                    if connection.get('authInfo').get('authType') == auth_type:
                        logger.warning('key vualt reference connection: %s', connection.get('id'))
                        return
        else:
            logger.warning('key vualt reference connection: %s', key_vault_connections[0].get('id'))
            return

    auth_info = {
        'authType': auth_type
    }
    if client_id and subscription_id:
        auth_info['clientId'] = client_id
        auth_info['subscriptionId'] = subscription_id
    return auth_info
