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
from ._resource_config import (
    SOURCE_RESOURCES_USERTOKEN,
    TARGET_RESOURCES_USERTOKEN,
    RESOURCE
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


def set_user_token_by_source_and_target(client, cli_ctx, source, target):
    '''Set user token header to work around OBO according to source and target'''
    if source in SOURCE_RESOURCES_USERTOKEN or target in TARGET_RESOURCES_USERTOKEN:
        return set_user_token_header(client, cli_ctx)
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
    key_vault_connections = []
    for connection in client.list(resource_uri=source_id):
        connection = todict(connection)
        if connection.get('targetService', dict()).get('id') == key_vault_id:
            key_vault_connections.append(connection)

    source_name = get_source_resource_name(cmd)
    auth_info = get_auth_if_no_valid_key_vault_connection(logger, source_name, source_id, key_vault_connections)
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
        'client_type': CLIENT_TYPE.Dotnet,  # Key Vault Configuration are same across all client types
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


def get_auth_if_no_valid_key_vault_connection(logger, source_name, source_id, key_vault_connections):
    auth_type = 'systemAssignedIdentity'
    client_id = None
    subscription_id = None

    if key_vault_connections:
        from msrestazure.tools import (
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

        # any connection with csi enabled is a valid connection
        elif source_name == RESOURCE.KubernetesCluster:
            for connection in key_vault_connections:
                if connection.get('target_service', dict()).get(
                        'resource_properties', dict()).get('connect_as_kubernetes_csi_driver'):
                    return
            return {'authType': 'userAssignedIdentity'}

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


def enable_mi_for_db_linker(cli_ctx, source_id, target_id, auth_info, source_type, target_type):
    if(target_type in {RESOURCE.Postgres} and auth_info['auth_type'] == 'systemAssignedIdentity'):
        # object_id = run_cli_cmd('az webapp show --ids {0}'.format(source_id)).get('identity').get('principalId')
        # enable source mi
        identity = None
        if source_type == RESOURCE.SpringCloudDeprecated or source_type == RESOURCE.SpringCloud:
            identity = get_springcloud_identity(source_id)
        object_id = identity.get('principalId')
        client_id = run_cli_cmd('az ad sp show --id {0}'.format(object_id)).get('appId')

        # add new firewall rule
        ipname = generate_random_string(prefix='svc_')
        deny_public_access = set_target_firewall(target_id, target_type, True, ipname)

        aaduser = generate_random_string(prefix="aad_" + target_type.value + '_')
        create_aad_user_in_db(cli_ctx, target_id, aaduser, client_id)

        # remove firewall rule
        set_target_firewall(target_id, target_type, False, ipname, deny_public_access)

        return {
            'auth_type': 'secret',
            'name': aaduser,
            'secret_info': {
                'secret_type': 'rawValue'
            }
        }


def set_target_firewall(target_id, target_type, add_new_rule, ipname, deny_public_access=False):
    if target_type == RESOURCE.Postgres:
        target_segments = parse_resource_id(target_id)
        rg = target_segments.get('resource_group')
        server = target_segments.get('name')
        if add_new_rule:
            target = run_cli_cmd('az postgres server show --ids {}'.format(target_id))
            if target.get('publicNetworkAccess') == "Disabled":
                run_cli_cmd('az postgres server update --public Enabled --ids {}'.format(target_id))
            run_cli_cmd(
                'az postgres server firewall-rule create -g {0} -s {1} -n {2} '
                '--start-ip-address 0.0.0.0 --end-ip-address 255.255.255.255'.format(rg, server, ipname)
            )
            return target.get('publicNetworkAccess') == "Disabled"

        run_cli_cmd('az postgres server firewall-rule delete -g {0} -s {1} -n {2} -y'.format(rg, server, ipname))
        if deny_public_access:
            run_cli_cmd('az postgres server update --public Disabled --ids {}'.format(target_id))


def create_aad_user_in_db(cli_ctx, target_id, aaduser, client_id):
    import psycopg2
    from azure.cli.core._profile import Profile

    # pylint: disable=protected-access
    profile = Profile(cli_ctx=cli_ctx)

    # Update connection string information
    target_segments = parse_resource_id(target_id)
    dbserver = target_segments.get('name')
    host = "{0}.postgres.database.azure.com".format(dbserver)
    dbname = target_segments.get('child_name_1')
    user = profile.get_current_account_user() + '@' + dbserver
    password = run_cli_cmd('az account get-access-token --resource-type oss-rdbms').get('accessToken')
    sslmode = "require"

    # Construct connection string
    conn_string = "host={0} user={1} dbname={2} password={3} sslmode={4}".format(host, user, dbname, password, sslmode)
    try:
        conn = psycopg2.connect(conn_string)
    except psycopg2.Error as e:
        raise e
    print("Connection established")

    cursor = conn.cursor()

    try:
        cursor.execute("SET aad_validate_oids_in_tenant = off;")
        cursor.execute("CREATE ROLE {0} WITH LOGIN PASSWORD '{1}' IN ROLE azure_ad_user;".format(aaduser, client_id))
        print("New DB AAD user {0} is created".format(aaduser))
    except psycopg2.Error as e:  # role "aaduser" already exists
        print(e)
        conn.commit()

    try:
        cursor.execute("GRANT ALL PRIVILEGES ON DATABASE {} TO {};".format(dbname, aaduser))
        print("AAD user {} is granted with database {} privileges".format(dbname, aaduser))
    except psycopg2.Error as e:
        print(e)
        conn.commit()

    # Clean up
    cursor.close()
    conn.close()


def get_springcloud_identity(source_id):
    segments = parse_resource_id(source_id)
    spring = segments.get('name')
    app = segments.get('child_name_1')
    rg = segments.get('resource_group')
    identity = run_cli_cmd('az spring-cloud app show -g {0} -s {1} -n {2}'.format(rg, spring, app)).get('identity')
    if (identity is None or identity.get('type') != "SystemAssigned"):
        # assign system identity
        run_cli_cmd('az spring-cloud app identity assign -g {0} -s {1} -n {2}'.format(rg, spring, app))
        print('spring cloud app identity is enabled.')
        cnt = 0
        while (identity is None and cnt < 5):
            identity = run_cli_cmd('az spring-cloud app show -g {0} -s {1} -n {2}'.format(rg, spring, app)).get(
                'identity')
            time.sleep(3)
            cnt += 1
    return identity
