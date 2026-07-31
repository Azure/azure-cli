# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import re
import time
from knack.log import get_logger
from knack.util import todict, CLIError
from azure.cli.core.azclierror import (
    ValidationError,
    CLIInternalError
)
# from azure.cli.core._profile import Profile
from ._resource_config import (
    RESOURCE
)
from azure.cli.core import get_default_cli
from azure.mgmt.core.tools import (
    parse_resource_id,
    is_valid_resource_id as is_valid_resource_id_sdk
)

logger = get_logger(__name__)


def is_valid_resource_id(value):
    return is_valid_resource_id_sdk(value)


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
        raise CLIInternalError(
            'lower_only and ensure_complexity can not both be specified to True')
    if ensure_complexity and length < 8:
        raise CLIInternalError('ensure_complexity needs length >= 8')

    character_set = string.ascii_letters + string.digits
    if lower_only:
        character_set = string.ascii_lowercase

    while True:
        randstr = '{}{}'.format(prefix, ''.join(
            random.sample(character_set, length)))
        lowers = [c for c in randstr if c.islower()]
        uppers = [c for c in randstr if c.isupper()]
        numbers = [c for c in randstr if c.isnumeric()]
        if not ensure_complexity or (lowers and uppers and numbers):
            break

    return randstr


def run_cli_cmd(cmd, retry=0, interval=0, should_retry_func=None):
    '''Run a CLI command
    :param cmd: The CLI command to be executed
    :param retry: The times to re-try
    :param interval: The seconds wait before retry
    '''
    output = _in_process_execute(cmd)

    if output.error or (should_retry_func and should_retry_func(output)):
        if retry:
            time.sleep(interval)
            return run_cli_cmd(cmd, retry - 1, interval)
        raise CLIInternalError('Command execution failed, command is: '
                               '{}, error message is: \n {}'.format(cmd, output.error))
    return output.result


def _in_process_execute(command):
    import shlex

    if command.startswith('az '):
        command = command[3:]

    cli = get_default_cli()
    cli.invoke(shlex.split(command), out_file=open(os.devnull, 'w'))  # Don't print output
    return cli.result


# pylint: disable=unused-argument
def set_user_token_header(client, cli_ctx):
    '''Set user token header to work around OBO'''

    # pylint: disable=protected-access
    # HACK: set custom header to work around OBO
    # profile = Profile(cli_ctx=cli_ctx)
    # creds, _, _ = profile.get_raw_token()
    # client._client._config.headers_policy._headers['x-ms-serviceconnector-user-token'] = creds[1]
    # HACK: hide token header
    client._config.logging_policy.headers_to_redact.append(
        'x-ms-serviceconnector-user-token')

    return client


def set_user_token_by_source_and_target(client, cli_ctx, source, target):
    '''Set user token header to work around OBO according to source and target'''
    # deprecated
    # if source in SOURCE_RESOURCES_USERTOKEN or target in TARGET_RESOURCES_USERTOKEN:
    #     return set_user_token_header(client, cli_ctx)
    return client


def provider_is_registered(subscription=None):
    # register the provider
    subs_arg = ''
    if subscription:
        subs_arg = '--subscription "{}"'.format(subscription)
    output = run_cli_cmd(
        'az provider show -n Microsoft.ServiceLinker {}'.format(subs_arg))
    if output.get('registrationState') == 'NotRegistered':
        return False
    return True


def register_provider(subscription=None):
    logger.warning('Provider Microsoft.ServiceLinker is not registered, '
                   'trying to register. This usually takes 1-2 minutes.')

    subs_arg = ''
    if subscription:
        subs_arg = '--subscription "{}"'.format(subscription)

    # register the provider
    run_cli_cmd(
        'az provider register -n Microsoft.ServiceLinker {}'.format(subs_arg))

    # verify the registration, 30 * 10s polling the result
    MAX_RETRY_TIMES = 30
    RETRY_INTERVAL = 10

    count = 0
    while count < MAX_RETRY_TIMES:
        time.sleep(RETRY_INTERVAL)
        output = run_cli_cmd(
            'az provider show -n Microsoft.ServiceLinker {}'.format(subs_arg))
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
            raise CLIInternalError('Registration failed, please manually run command '
                                   '`az provider register -n Microsoft.ServiceLinker` to register the provider.')
        # target subscription is not registered, raw check
        if ex.error and ex.error.code == 'UnauthorizedResourceAccess' and 'not registered' in ex.error.message:
            if 'parameters' in kwargs_backup and 'target_id' in kwargs_backup.get('parameters'):
                segments = parse_resource_id(
                    kwargs_backup.get('parameters').get('target_id'))
                target_subs = segments.get('subscription')
                # double check whether target subscription is registered
                if not provider_is_registered(target_subs):
                    if register_provider(target_subs):
                        return func(*args, **kwargs_backup)
                    raise CLIInternalError('Registration failed, please manually run command '
                                           '`az provider register -n Microsoft.ServiceLinker --subscription {}` '
                                           'to register the provider.'.format(target_subs))
        raise ex


def create_key_vault_reference_connection_if_not_exist(cmd, client, source_id, key_vault_id,
                                                       scope=None):  # Resource.ContainerApp
    from ._validators import get_source_resource_name

    logger.warning('get valid key vault reference connection')
    key_vault_connections = []
    for connection in client.list(resource_uri=source_id):
        connection = todict(connection)
        if connection.get('targetService', {}).get('id') == key_vault_id:
            key_vault_connections.append(connection)

    source_name = get_source_resource_name(cmd)
    auth_info = get_auth_if_no_valid_key_vault_connection(
        source_name, source_id, key_vault_connections)
    if not auth_info:
        return

    # No Valid Key Vault Connection, Create
    logger.warning('no valid key vault connection found. Creating...')

    from ._resource_config import (
        CLIENT_TYPE
    )

    connection_name = generate_random_string(prefix='keyvault_')
    parameters = {
        'target_service': {
            "type": "AzureResource",
            "id": key_vault_id
        },
        'auth_info': auth_info,
        # Container App container name
        'scope': scope,
        # Key Vault Configuration are same across all client types
        'client_type': CLIENT_TYPE.Dotnet,
    }

    if source_name == RESOURCE.KubernetesCluster:
        parameters['target_service']['resource_properties'] = {
            'type': 'KeyVault',
            'connect_as_kubernetes_csi_driver': True,
        }

    return auto_register(client.begin_create_or_update,
                         resource_uri=source_id,
                         linker_name=connection_name,
                         parameters=parameters)


def get_auth_if_no_valid_key_vault_connection(source_name, source_id, key_vault_connections):
    if source_name == RESOURCE.WebApp:
        return get_auth_if_no_valid_key_vault_connection_for_webapp(source_id, key_vault_connections)

    if source_name == RESOURCE.ContainerApp:
        return get_auth_if_no_valid_key_vault_connection_for_containerapp(key_vault_connections)

    # any connection with csi enabled is a valid connection
    if source_name == RESOURCE.KubernetesCluster:
        for connection in key_vault_connections:
            if connection.get('targetService', {}).get(
                    'resourceProperties', {}).get('connectAsKubernetesCsiDriver'):
                return
        return {'authType': 'userAssignedIdentity'}

    # other source types
    if key_vault_connections:
        logger.warning('key vault reference connection: %s',
                       key_vault_connections[0].get('id'))
        return

    return {'authType': 'systemAssignedIdentity'}


# https://learn.microsoft.com/azure/app-service/app-service-key-vault-references
def get_auth_if_no_valid_key_vault_connection_for_webapp(source_id, key_vault_connections):

    try:
        webapp = run_cli_cmd(
            'az rest -u "{}?api-version=2020-09-01" -o json'.format(source_id))
        reference_identity = webapp.get(
            'properties').get('keyVaultReferenceIdentity')
    except Exception as e:
        raise ValidationError('{}. Unable to get "properties.keyVaultReferenceIdentity" from {}.'
                              'Please check your source id is correct.'.format(e, source_id))

    if is_valid_resource_id(reference_identity):  # User Identity
        auth_type = 'userAssignedIdentity'
        segments = parse_resource_id(reference_identity)
        subscription_id = segments.get('subscription')
        try:
            identity = webapp.get('identity').get(
                'userAssignedIdentities').get(reference_identity)
            client_id = identity.get('clientId')
        except Exception:  # pylint: disable=broad-except
            try:
                identity = run_cli_cmd(
                    'az identity show --ids "{}" -o json'.format(reference_identity))
                client_id = identity.get('clientId')
            except Exception:  # pylint: disable=broad-except
                pass
        if not subscription_id or not client_id:
            raise ValidationError('Unable to get subscriptionId or clientId'
                                  'of the keyVaultReferenceIdentity {}'.format(reference_identity))
        for connection in key_vault_connections:
            auth_info = connection.get('authInfo')
            if auth_info.get('clientId') == client_id and auth_info.get('subscriptionId') == subscription_id:
                logger.warning(
                    'key vault reference connection: %s', connection.get('id'))
                return
        return {'authType': auth_type, 'clientId': client_id, 'subscriptionId': subscription_id}

    # System Identity
    auth_type = 'systemAssignedIdentity'
    for connection in key_vault_connections:
        if connection.get('authInfo').get('authType') == auth_type:
            logger.warning(
                'key vault reference connection: %s', connection.get('id'))
            return
    return {'authType': auth_type}


def get_auth_if_no_valid_key_vault_connection_for_containerapp(key_vault_connections):
    auth_type = 'systemAssignedIdentity'  # Use system identity by default
    for connection in key_vault_connections:
        if connection.get('authInfo').get('authType') == auth_type:
            logger.warning(
                'key vault reference connection: %s', connection.get('id'))
            return
    return {'authType': auth_type}


def create_app_config_connection_if_not_exist(cmd, client, source_id, app_config_id,
                                              scope=None):  # Resource.ContainerApp
    from ._validators import get_source_resource_name

    logger.warning('looking for valid app configuration connections')
    for connection in client.list(resource_uri=source_id):
        connection = todict(connection)
        if connection.get('targetService', {}).get('id') == app_config_id:
            logger.warning('Valid app configuration connection found.')
            return

    logger.warning('no valid app configuration connection found. Creating with system identity...')

    from ._resource_config import (
        CLIENT_TYPE
    )

    connection_name = generate_random_string(prefix='appconfig_')
    parameters = {
        'target_service': {
            "type": "AzureResource",
            "id": app_config_id
        },
        'auth_info': {
            'authType': 'systemAssignedIdentity'
        },
        # Container App container name
        'scope': scope,
        'client_type': CLIENT_TYPE.Blank,
    }

    source_name = get_source_resource_name(cmd)
    if source_name == RESOURCE.KubernetesCluster:
        parameters['target_service']['resource_properties'] = {
            'type': 'KeyVault',
            'connect_as_kubernetes_csi_driver': True,
        }

    return auto_register(client.begin_create_or_update,
                         resource_uri=source_id,
                         linker_name=connection_name,
                         parameters=parameters)


def get_object_id_of_current_user():
    signed_in_user_info = run_cli_cmd('az account show -o json')
    if not isinstance(signed_in_user_info, dict):
        raise CLIInternalError(
            f"Can't parse login user information {signed_in_user_info}")
    signed_in_user = signed_in_user_info.get('user')
    user_type = signed_in_user.get('type')
    if not user_type or not signed_in_user.get('name'):
        raise CLIInternalError(
            f"Can't get user type or name from signed-in user {signed_in_user}")
    try:
        if user_type == 'user':
            user_info = run_cli_cmd('az ad signed-in-user show -o json')
            user_object_id = user_info.get('objectId') if user_info.get(
                'objectId') else user_info.get('id')
            return user_object_id
        if user_type == 'servicePrincipal':
            user_info = run_cli_cmd(
                f'az ad sp show --id "{signed_in_user.get("name")}" -o json')
            user_object_id = user_info.get('id')
            return user_object_id
    except CLIInternalError as e:
        if 'AADSTS530003' in e.error_msg:
            logger.warning(
                'Please ask your IT department for help to join this device to Azure Active Directory.')
        raise e


def get_cloud_conn_auth_info(secret_auth_info, secret_auth_info_auto,
                             user_identity_auth_info, system_identity_auth_info,
                             service_principal_auth_info_secret, new_addon,
                             auth_action=None, config_action=None, target_type=None):
    all_auth_info = []
    if secret_auth_info is not None:
        all_auth_info.append(secret_auth_info)
    if secret_auth_info_auto is not None:
        all_auth_info.append(secret_auth_info_auto)
    if user_identity_auth_info is not None:
        all_auth_info.append(user_identity_auth_info)
    if system_identity_auth_info is not None:
        all_auth_info.append(system_identity_auth_info)
    if service_principal_auth_info_secret is not None:
        all_auth_info.append(service_principal_auth_info_secret)
    if len(all_auth_info) == 0:
        if (auth_action == 'optOutAllAuth' and config_action == 'optOut') \
           or target_type == RESOURCE.ContainerApp:
            return None
        raise ValidationError('At least one auth info is needed')
    if not new_addon and len(all_auth_info) != 1:
        raise ValidationError('Only one auth info is needed')
    auth_info = all_auth_info[0] if len(all_auth_info) == 1 else None
    if auth_info is not None and auth_action is not None:
        auth_info.update({'auth_mode': auth_action})
    return auth_info


def get_local_conn_auth_info(secret_auth_info, secret_auth_info_auto,
                             user_account_auth_info, service_principal_auth_info_secret):
    all_auth_info = []
    if secret_auth_info is not None:
        all_auth_info.append(secret_auth_info)
    if secret_auth_info_auto is not None:
        all_auth_info.append(secret_auth_info_auto)
    if user_account_auth_info is not None:
        all_auth_info.append(user_account_auth_info)
    if service_principal_auth_info_secret is not None:
        all_auth_info.append(service_principal_auth_info_secret)
    auth_info = all_auth_info[0] if len(all_auth_info) == 1 else None
    return auth_info


def _get_azext_module(extension_name, module_name):
    try:
        # Adding the installed extension in the path
        from azure.cli.core.extension.operations import add_extension_to_path
        add_extension_to_path(extension_name)
        # Import the extension module
        from importlib import import_module
        azext_custom = import_module(module_name)
        return azext_custom
    except ImportError as ie:
        raise CLIInternalError(ie)


def _get_or_add_extension(cmd, extension_name, extension_module, update=False):
    from azure.cli.core.extension import (
        ExtensionNotInstalledException, get_extension)
    try:
        get_extension(extension_name)
        if update:
            return _update_extension(cmd, extension_name, extension_module)
    except ExtensionNotInstalledException:
        return _install_extension(cmd, extension_name)
    return True


def _update_extension(cmd, extension_name):
    from azure.cli.core.extension import ExtensionNotInstalledException
    try:
        from azure.cli.core.extension import operations
        operations.update_extension(cmd=cmd, extension_name=extension_name)
        operations.reload_extension(extension_name=extension_name)
    except CLIError as err:
        logger.info(err)
    except ExtensionNotInstalledException as err:
        logger.debug(err)
        return False
    except ModuleNotFoundError as err:
        logger.debug(err)
        logger.error(
            "Error occurred attempting to load the extension module. Use --debug for more information.")
        return False
    return True


def _install_extension(cmd, extension_name):
    try:
        from azure.cli.core.extension import operations
        operations.add_extension(cmd=cmd, extension_name=extension_name)
    except Exception:  # nopa pylint: disable=broad-except
        return False
    return True


def springboot_migration_warning(require_update=False, check_version=False, both_version=False):
    warning_message = "It is recommended to use Spring Cloud Azure version 4.0 and above. \
The configurations in the format of \"azure.cosmos.*\" from Spring Cloud Azure 3.x will no longer be supported after 1st July, 2024. \
Please refer to https://microsoft.github.io/spring-cloud-azure/current/reference/html/appendix.html\
#configuration-spring-cloud-azure-starter-data-cosmos for more details."

    update_message = "\nPlease update your connection to include the configurations for the newer version."

    check_version_message = "\nManaged identity and service principal are only supported \
in Spring Cloud Azure version 4.0 and above. Please check your Spring Cloud Azure version. \
Learn more at https://spring.io/projects/spring-cloud-azure#overview"
    both_version_message = "\nTwo sets of configuration properties will be configured \
according to Spring Cloud Azure version 3.x and 4.x. \
Learn more at https://spring.io/projects/spring-cloud-azure#overview"

    if require_update:
        warning_message += update_message
    if check_version:
        warning_message += check_version_message
    if both_version:
        warning_message += both_version_message

    return warning_message


# LinkerResource Model is converted into dict in update flow,
# which conflicts with the default behavior of creation wrt the key name format.
def get_auth_type_for_update(authInfo):
    if authInfo is None:
        return None
    if 'auth_type' in authInfo:
        return authInfo['auth_type']
    return authInfo['authType']


def get_secret_type_for_update(authInfo):
    if 'secret_info' in authInfo:
        return authInfo['secret_info']['secret_type']
    if 'secretInfo' in authInfo:
        return authInfo['secretInfo']['secretType']
    return ''


# Decorator for AKS configurations.
def is_aks_linker_by_id(resource_id):
    pattern = r'/subscriptions/([^/]+)/resourceGroups/([^/]+)/providers/Microsoft.ContainerService' + \
        r'/managedClusters/([^/]+)/providers/Microsoft.ServiceLinker/linkers/([^/]+)'
    return re.match(pattern, resource_id, re.IGNORECASE) is not None


def get_aks_resource_name(linker):
    secret_name = get_aks_resource_secret_name(linker["name"])
    if linker["authInfo"] is not None and linker["authInfo"].get("authType") == "userAssignedIdentity" and \
            not (linker["targetService"]["resourceProperties"] is not None and
                 linker["targetService"]["resourceProperties"].get("connectAsKubernetesCsiDriver")):
        service_account_name = f'sc-account-{linker["authInfo"].get("clientId")}'
        return {'secret': secret_name, 'serviceAccount': service_account_name}
    return {'secret': secret_name}


def get_aks_resource_secret_name(connection_name):
    valid_name = re.sub(r'[^a-zA-Z0-9]', '', connection_name, flags=re.IGNORECASE)
    return f'sc-{valid_name}-secret'


def compare_properties_changed(new_props, existing_props):
    """
    Deep comparison function that checks if there are meaningful differences
    between new properties and existing properties, ignoring None values.
    Returns True if there are differences that require an update.
    """
    def has_meaningful_changes(new_value, existing_value):
        if new_value is None or new_value == "":
            return False

        if isinstance(new_value, dict) and isinstance(existing_value, dict):
            for key, value in new_value.items():
                if key == "mysql-identity-id" or key == 'user_object_id':
                    continue
                existing_props_key = key
                if '_' in key:
                    existing_props_key = to_camel_case(key)
                existing_nested = existing_value.get(existing_props_key) if existing_value else None
                if has_meaningful_changes(value, existing_nested):
                    return True
            return False
        if isinstance(new_value, dict) and existing_value is None:
            for value in new_value.values():
                if value is not None and value != "":
                    return True
            return False

        return new_value != existing_value

    return has_meaningful_changes(new_props, existing_props)


def to_camel_case(snake_str):
    if not snake_str or '_' not in snake_str:
        return snake_str
    components = snake_str.split('_')
    return components[0] + ''.join(word.capitalize() for word in components[1:])
