# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger
from knack.util import todict
from azure.cli.core.util import sdk_no_wait
from azure.cli.core.azclierror import (
    InvalidArgumentValueError,
    RequiredArgumentMissingError,
    ValidationError,
    AzureResponseError
)
from ._resource_config import (
    SUPPORTED_AUTH_TYPE,
    SUPPORTED_CLIENT_TYPE,
    TARGET_RESOURCES,
    TARGET_RESOURCES_USERTOKEN
)
from ._validators import (
    get_source_resource_name,
    get_target_resource_name,
    validate_service_state
)
from ._addon_factory import AddonFactory
from ._utils import (
    set_user_token_header,
    auto_register
)
# pylint: disable=unused-argument


logger = get_logger(__name__)
err_msg = 'Required argument is missing, please provide the arguments: {}'


def connection_list(client,
                    source_resource_group=None,
                    source_id=None,
                    cluster=None,
                    site=None,
                    spring=None, app=None, deployment='default'):
    if not source_id:
        raise RequiredArgumentMissingError(err_msg.format('--source-id'))
    return auto_register(client.list, resource_uri=source_id)


def connection_list_support_types(cmd, client,
                                  target_resource_type=None):
    results = []
    source = get_source_resource_name(cmd)

    targets = SUPPORTED_AUTH_TYPE.get(source).keys()
    if target_resource_type is not None:
        targets = []
        for resource in TARGET_RESOURCES:
            if target_resource_type == resource.value:
                targets.append(resource)
                break

    # use SUPPORTED_AUTH_TYPE to decide target resource, as some
    # target resources are not avialable for certain source resource
    supported_target_resources = SUPPORTED_AUTH_TYPE.get(source).keys()
    for target in supported_target_resources:
        auth_types = SUPPORTED_AUTH_TYPE.get(source).get(target)
        client_types = SUPPORTED_CLIENT_TYPE.get(source).get(target)
        auth_types = [item.value for item in auth_types]
        client_types = [item.value for item in client_types]
        results.append({
            'source': source.value,
            'target': target.value,
            'auth_types': auth_types,
            'client_types': client_types
        })

    return results


def connection_show(client,
                    connection_name=None,
                    source_resource_group=None,
                    source_id=None,
                    indentifier=None,
                    cluster=None,
                    site=None,
                    spring=None, app=None, deployment='default'):
    if not source_id or not connection_name:
        raise RequiredArgumentMissingError(err_msg.format('--source-id, --connection'))
    return auto_register(client.get, resource_uri=source_id, linker_name=connection_name)


def connection_delete(client,
                      connection_name=None,
                      source_resource_group=None,
                      source_id=None,
                      indentifier=None,
                      cluster=None,
                      site=None,
                      spring=None, app=None, deployment='default',
                      no_wait=False):
    if not source_id or not connection_name:
        raise RequiredArgumentMissingError(err_msg.format('--source-id, --connection'))

    return auto_register(sdk_no_wait, no_wait,
                         client.begin_delete,
                         resource_uri=source_id,
                         linker_name=connection_name)


def connection_list_configuration(client,
                                  connection_name=None,
                                  source_resource_group=None,
                                  source_id=None,
                                  indentifier=None,
                                  cluster=None,
                                  site=None,
                                  spring=None, app=None, deployment='default'):
    if not source_id or not connection_name:
        raise RequiredArgumentMissingError(err_msg.format('--source-id, --connection'))
    return auto_register(client.list_configurations,
                         resource_uri=source_id,
                         linker_name=connection_name)


def connection_validate(cmd, client,
                        connection_name=None,
                        source_resource_group=None,
                        source_id=None,
                        indentifier=None,
                        cluster=None,
                        site=None,
                        spring=None, app=None, deployment='default'):
    import re
    from ._validators import get_resource_regex

    if not source_id or not connection_name:
        raise RequiredArgumentMissingError(err_msg.format('--source-id, --connection'))

    # HACK: get linker first to infer target resource type so that user token can be
    # set to work around OBO
    linker = todict(client.get(resource_uri=source_id, linker_name=connection_name))
    target_id = linker.get('targetId')
    for resource_type, resource_id in TARGET_RESOURCES.items():
        matched = re.match(get_resource_regex(resource_id), target_id, re.IGNORECASE)
        if matched and resource_type in TARGET_RESOURCES_USERTOKEN:
            client = set_user_token_header(client, cmd.cli_ctx)

    return auto_register(client.begin_validate, resource_uri=source_id, linker_name=connection_name)


def connection_create(cmd, client,  # pylint: disable=too-many-locals
                      connection_name=None, client_type=None,
                      source_resource_group=None, source_id=None,
                      target_resource_group=None, target_id=None,
                      secret_auth_info=None, secret_auth_info_auto=None,
                      user_identity_auth_info=None, system_identity_auth_info=None,
                      service_principal_auth_info_secret=None,
                      key_vault_id=None,
                      service_endpoint=None,
                      new_addon=False, no_wait=False,
                      cluster=None,
                      site=None,                                             # Resource.WebApp
                      spring=None, app=None, deployment='default',           # Resource.SpringCloud
                      server=None, database=None,                            # Resource.*Postgres, Resource.*Sql*
                      vault=None,                                            # Resource.KeyVault
                      account=None,                                          # Resource.Storage*
                      key_space=None, graph=None, table=None,                # Resource.Cosmos*,
                      config_store=None,                                     # Resource.AppConfig
                      namespace=None,                                        # Resource.EventHub
                      signalr=None):                                         # Resource.SignalR

    if not source_id:
        raise RequiredArgumentMissingError(err_msg.format('--source-id'))
    if not new_addon and not target_id:
        raise RequiredArgumentMissingError(err_msg.format('--target-id'))

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
    if not new_addon and len(all_auth_info) != 1:
        raise ValidationError('Only one auth info is needed')
    auth_info = all_auth_info[0] if len(all_auth_info) == 1 else None

    parameters = {
        'target_id': target_id,
        'auth_info': auth_info,
        'secret_store': {
            'key_vault_id': key_vault_id,
        },
        'client_type': client_type
    }

    # HACK: set user token to work around OBO
    target_type = get_target_resource_name(cmd)
    if target_type in TARGET_RESOURCES_USERTOKEN:
        client = set_user_token_header(client, cmd.cli_ctx)

    if key_vault_id:
        client = set_user_token_header(client, cmd.cli_ctx)
        from ._utils import create_key_vault_reference_connection_if_not_exist
        create_key_vault_reference_connection_if_not_exist(cmd, client, source_id, key_vault_id)

    if service_endpoint:
        client = set_user_token_header(client, cmd.cli_ctx)
        parameters['v_net_solution'] = {
            'type': 'serviceEndpoint'
        }

    if new_addon:
        addon = AddonFactory.get(target_type)(cmd, source_id)
        target_id, auth_info = addon.provision()
        parameters['target_id'] = target_id
        parameters['auth_info'] = auth_info
        logger.warning('Start creating the connection')

        try:
            linker = client.begin_create_or_update(resource_uri=source_id,
                                                   linker_name=connection_name,
                                                   parameters=parameters)
            return linker
        except Exception as e:
            logger.warning('Connection creation failed, start rolling back')
            addon.rollback()
            raise AzureResponseError('{}. Provision failed, please create the target resource '
                                     'manually and then create the connection.'.format(str(e)))

    validate_service_state(parameters)
    return auto_register(sdk_no_wait, no_wait,
                         client.begin_create_or_update,
                         resource_uri=source_id,
                         linker_name=connection_name,
                         parameters=parameters)


def connection_update(cmd, client,  # pylint: disable=too-many-locals
                      connection_name=None, client_type=None,
                      source_resource_group=None, source_id=None, indentifier=None,
                      secret_auth_info=None, secret_auth_info_auto=None,
                      user_identity_auth_info=None, system_identity_auth_info=None,
                      service_principal_auth_info_secret=None,
                      key_vault_id=None,
                      service_endpoint=None,
                      no_wait=False,
                      cluster=None,
                      site=None,                                              # Resource.WebApp
                      deployment='default',
                      spring=None, app=None):                                 # Resource.SpringCloud

    linker = todict(client.get(resource_uri=source_id, linker_name=connection_name))

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

    # validate auth info
    if len(all_auth_info) > 1:
        raise ValidationError('Only one auth info is needed')
    # when user provides auth info
    if len(all_auth_info) == 1:
        auth_info = all_auth_info[0]
    # when user doesn't provide auth info and linker is not secret-with-username type
    elif not all_auth_info and (linker.get('authInfo').get('authType') != 'secret' or
                                not linker.get('authInfo').get('name')):
        auth_info = linker.get('authInfo')
    else:
        raise ValidationError('Auth info argument should be provided when '
                              'updating the connection: {}'.format(linker.get('name')))
    # validate the properties to be updated
    if client_type is None and not all_auth_info:
        raise ValidationError('Either client type or auth info should be specified to update')

    if linker.get('secretStore') and linker.get('secretStore').get('keyVaultId'):
        key_vault_id = key_vault_id or linker.get('secretStore').get('keyVaultId')

    parameters = {
        'target_id': linker.get('targetId'),
        'auth_info': auth_info,
        'secret_store': {
            'key_vault_id': key_vault_id,
        },
        'client_type': client_type or linker.get('clientType'),
    }

    # HACK: set user token to work around OBO
    target_type = get_target_resource_name(cmd)
    if target_type in TARGET_RESOURCES_USERTOKEN:
        client = set_user_token_header(client, cmd.cli_ctx)

    if key_vault_id:
        client = set_user_token_header(client, cmd.cli_ctx)
        from ._utils import create_key_vault_reference_connection_if_not_exist
        create_key_vault_reference_connection_if_not_exist(cmd, client, source_id, key_vault_id)

    parameters['v_net_solution'] = linker.get('vNetSolution')
    if service_endpoint:
        parameters['v_net_solution'] = {
            'type': 'serviceEndpoint'
        }
    elif service_endpoint is False and linker.get('vNetSolution').get('type') == 'serviceEndpoint':
        parameters['v_net_solution'] = None

    return auto_register(sdk_no_wait, no_wait,
                         client.begin_create_or_update,
                         resource_uri=source_id,
                         linker_name=connection_name,
                         parameters=parameters)


def connection_create_kafka(cmd, client,  # pylint: disable=too-many-locals
                            bootstrap_server,
                            kafka_key,
                            kafka_secret,
                            schema_registry,
                            schema_key,
                            schema_secret,
                            key_vault_id=None,
                            connection_name=None,
                            client_type=None,
                            source_resource_group=None,
                            source_id=None,
                            cluster=None,
                            site=None,                         # Resource.WebApp
                            deployment='default',
                            spring=None, app=None):            # Resource.SpringCloud

    from ._transformers import transform_linker_properties
    # validation
    if 'azure.confluent.cloud' not in bootstrap_server.lower():
        raise InvalidArgumentValueError('Kafka bootstrap server url is invalid: {}'.format(bootstrap_server))
    if 'azure.confluent.cloud' not in schema_registry.lower():
        raise InvalidArgumentValueError('Schema registry url is invalid: {}'.format(schema_registry))

    if key_vault_id:
        client = set_user_token_header(client, cmd.cli_ctx)
        from ._utils import create_key_vault_reference_connection_if_not_exist
        create_key_vault_reference_connection_if_not_exist(cmd, client, source_id, key_vault_id)

    # create bootstrap-server
    parameters = {
        'target_id': bootstrap_server,
        'auth_info': {
            'name': kafka_key,
            'secret': kafka_secret,
            'auth_type': 'secret'
        },
        'secret_store': {
            'key_vault_id': key_vault_id,
        },
        'client_type': client_type,
    }
    logger.warning('Start creating a connection for bootstrap server ...')
    server_linker = client.begin_create_or_update(resource_uri=source_id,
                                                  linker_name=connection_name,
                                                  parameters=parameters)
    # block to poll the connection
    server_linker = server_linker.result()
    logger.warning('Created')

    # create schema registry
    parameters = {
        'target_id': schema_registry,
        'auth_info': {
            'name': schema_key,
            'secret': schema_secret,
            'auth_type': 'secret'
        },
        'secret_store': {
            'key_vault_id': key_vault_id,
        },
        'client_type': client_type,
    }
    logger.warning('Start creating a connection for schema registry ...')
    registry_linker = client.begin_create_or_update(resource_uri=source_id,
                                                    linker_name='{}_schema'.format(connection_name),
                                                    parameters=parameters)
    # block to poll the connection
    registry_linker = registry_linker.result()
    logger.warning('Created')

    return [
        transform_linker_properties(server_linker),
        transform_linker_properties(registry_linker)
    ]


def connection_update_kafka(cmd, client,  # pylint: disable=too-many-locals
                            connection_name,
                            bootstrap_server=None,
                            kafka_key=None,
                            kafka_secret=None,
                            schema_registry=None,
                            schema_key=None,
                            schema_secret=None,
                            key_vault_id=None,
                            client_type=None,
                            source_resource_group=None,
                            source_id=None,
                            cluster=None,
                            site=None,                         # Resource.WebApp
                            deployment='default',
                            spring=None, app=None):            # Resource.SpringCloud

    # use the suffix to decide the connection type
    if connection_name.endswith('_schema'):  # the schema registry connection
        if schema_secret is None:
            raise ValidationError("'--schema-secret' is required to update a schema registry connection")
        if bootstrap_server or kafka_key or kafka_secret:
            raise ValidationError("The available parameters to update a schema registry connection are:"
                                  " ['--schema-registry', '--schema-key', '--schema-secret', '--client-type']")
        server_linker = todict(client.get(resource_uri=source_id, linker_name=connection_name))

        if server_linker.get('secretStore') and server_linker.get('secretStore').get('keyVaultId'):
            key_vault_id = key_vault_id or server_linker.get('secretStore').get('keyVaultId')
        if key_vault_id:
            client = set_user_token_header(client, cmd.cli_ctx)
            from ._utils import create_key_vault_reference_connection_if_not_exist
            create_key_vault_reference_connection_if_not_exist(cmd, client, source_id, key_vault_id)
        parameters = {
            'target_id': schema_registry or server_linker.get('targetId'),
            'auth_info': {
                'name': schema_key or server_linker.get('authInfo').get('name'),
                'secret': schema_secret,
                'auth_type': 'secret'
            },
            'secret_store': {
                'key_vault_id': key_vault_id,
            },
            'client_type': client_type or server_linker.get('clientType'),
        }
    else:  # the bootstrap server connection
        if kafka_secret is None:
            raise ValidationError("'--kafka-secret' is required to update a bootstrap server connection")
        if schema_registry or schema_key or schema_secret:
            raise ValidationError("The available parameters to update a bootstrap server connection are:"
                                  " ['--bootstrap-server', '--kafka-key', '--skafka-secret', '--client-type']")
        schema_linker = todict(client.get(resource_uri=source_id, linker_name=connection_name))

        if schema_linker.get('secretStore') and schema_linker.get('secretStore').get('keyVaultId'):
            key_vault_id = key_vault_id or schema_linker.get('secretStore').get('keyVaultId')
        if key_vault_id:
            client = set_user_token_header(client, cmd.cli_ctx)
            from ._utils import create_key_vault_reference_connection_if_not_exist
            create_key_vault_reference_connection_if_not_exist(cmd, client, source_id, key_vault_id)
        parameters = {
            'target_id': bootstrap_server or schema_linker.get('targetId'),
            'auth_info': {
                'name': kafka_key or schema_linker.get('authInfo').get('name'),
                'secret': kafka_secret,
                'auth_type': 'secret'
            },
            'secret_store': {
                'key_vault_id': key_vault_id,
            },
            'client_type': client_type or schema_linker.get('clientType'),
        }

    return client.begin_create_or_update(resource_uri=source_id,
                                         linker_name=connection_name,
                                         parameters=parameters)
