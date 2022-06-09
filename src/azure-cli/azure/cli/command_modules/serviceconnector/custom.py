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
    TARGET_RESOURCES
)
from ._validators import (
    get_source_resource_name,
    get_target_resource_name,
    get_resource_type_by_id,
    validate_service_state
)
from ._addon_factory import AddonFactory
from ._utils import (
    set_user_token_by_source_and_target,
    set_user_token_header,
    auto_register
)
# pylint: disable=unused-argument,unsubscriptable-object,unsupported-membership-test


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
    if not source_id or not connection_name:
        raise RequiredArgumentMissingError(err_msg.format('--source-id, --connection'))

    # HACK: get linker first to infer target resource type so that user token can be
    # set to work around OBO
    linker = todict(client.get(resource_uri=source_id, linker_name=connection_name))
    target_id = linker.get('targetService', dict()).get('id', '')
    target_type = get_resource_type_by_id(target_id)
    source_type = get_source_resource_name(cmd)
    client = set_user_token_by_source_and_target(client, cmd.cli_ctx, source_type, target_type)

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
                      private_endpoint=None,
                      new_addon=False, no_wait=False,
                      cluster=None, scope=None, enable_csi=False,            # Resource.KubernetesCluster
                      site=None,                                             # Resource.WebApp
                      spring=None, app=None, deployment='default',           # Resource.SpringCloud
                      server=None, database=None,                            # Resource.*Postgres, Resource.*Sql*
                      vault=None,                                            # Resource.KeyVault
                      account=None,                                          # Resource.Storage*
                      key_space=None, graph=None, table=None,                # Resource.Cosmos*,
                      config_store=None,                                     # Resource.AppConfig
                      namespace=None,                                        # Resource.EventHub
                      webpubsub=None,                                        # Resource.WebPubSub
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
        'target_service': {
            "type": "AzureResource",
            "id": target_id
        },
        'auth_info': auth_info,
        'secret_store': {
            'key_vault_id': key_vault_id,
        },
        'client_type': client_type,
        'scope': scope
    }

    # HACK: set user token to work around OBO
    source_type = get_source_resource_name(cmd)
    target_type = get_target_resource_name(cmd)
    client = set_user_token_by_source_and_target(client, cmd.cli_ctx, source_type, target_type)

    if key_vault_id:
        client = set_user_token_header(client, cmd.cli_ctx)
        from ._utils import create_key_vault_reference_connection_if_not_exist
        create_key_vault_reference_connection_if_not_exist(cmd, client, source_id, key_vault_id)
    elif auth_info['auth_type'] == 'secret' and 'secret_info' in auth_info \
            and auth_info['secret_info']['secret_type'] == 'keyVaultSecretReference':
        raise ValidationError('--vault-id must be provided to use secret-name')

    if service_endpoint:
        client = set_user_token_header(client, cmd.cli_ctx)
        parameters['v_net_solution'] = {
            'type': 'serviceEndpoint'
        }
    if private_endpoint:
        client = set_user_token_header(client, cmd.cli_ctx)
        parameters['v_net_solution'] = {
            'type': 'privateLink'
        }

    if enable_csi:
        parameters['target_service']['resource_properties'] = {
            'type': 'KeyVault',
            'connect_as_kubernetes_csi_driver': enable_csi,
        }

    if new_addon:
        addon = AddonFactory.get(target_type)(cmd, source_id)
        target_id, auth_info = addon.provision()
        parameters['target_service'] = {
            "type": "AzureResource",
            "id": target_id
        }
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
                      private_endpoint=None,
                      no_wait=False,
                      scope=None,
                      cluster=None, enable_csi=False,                         # Resource.Kubernetes
                      site=None,                                              # Resource.WebApp
                      spring=None, app=None, deployment='default'):           # Resource.SpringCloud

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
        'target_service': linker.get('targetService'),
        'auth_info': auth_info,
        'secret_store': {
            'key_vault_id': key_vault_id,
        },
        'client_type': client_type or linker.get('clientType'),
        # scope can be updated in container app while cannot be updated in aks due to some limitations
        'scope': scope or linker.get('scope')
    }

    # HACK: set user token to work around OBO
    source_type = get_source_resource_name(cmd)
    target_type = get_target_resource_name(cmd)
    client = set_user_token_by_source_and_target(client, cmd.cli_ctx, source_type, target_type)

    if key_vault_id:
        client = set_user_token_header(client, cmd.cli_ctx)
        from ._utils import create_key_vault_reference_connection_if_not_exist
        create_key_vault_reference_connection_if_not_exist(cmd, client, source_id, key_vault_id)
    elif auth_info['auth_type'] == 'secret' and 'secret_info' in auth_info \
            and auth_info['secret_info']['secret_type'] == 'keyVaultSecretReference':
        raise ValidationError('--vault-id must be provided to use secret-name')

    parameters['v_net_solution'] = linker.get('vNetSolution')
    if service_endpoint:
        parameters['v_net_solution'] = {
            'type': 'serviceEndpoint'
        }
    if private_endpoint:
        parameters['v_net_solution'] = {
            'type': 'privateLink'
        }
    elif service_endpoint is False and linker.get('vNetSolution').get('type') == 'serviceEndpoint':
        parameters['v_net_solution'] = None
    elif private_endpoint is False and linker.get('vNetSolution').get('type') == 'privateLink':
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
                            cluster=None, scope=None,          # Resource.Kubernetes
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
        'target_service': {
            "type": "ConfluentBootstrapServer",
            "endpoint": bootstrap_server
        },
        'auth_info': {
            'name': kafka_key,
            'secret_info': {
                'secret_type': 'rawValue',
                'value': kafka_secret
            },
            'auth_type': 'secret'
        },
        'secret_store': {
            'key_vault_id': key_vault_id,
        },
        'client_type': client_type,
        'scope': scope
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
        'target_service': {
            "type": "ConfluentSchemaRegistry",
            "endpoint": schema_registry
        },
        'auth_info': {
            'name': schema_key,
            'secret_info': {
                'secret_type': 'rawValue',
                'value': schema_secret
            },
            'auth_type': 'secret'
        },
        'secret_store': {
            'key_vault_id': key_vault_id,
        },
        'client_type': client_type,
        'scope': scope
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
            'targetService': server_linker.get('targetService'),
            'auth_info': {
                'name': schema_key or server_linker.get('authInfo').get('name'),
                'secret': schema_secret,
                'auth_type': 'secret'
            },
            'secret_store': {
                'key_vault_id': key_vault_id,
            },
            'client_type': client_type or server_linker.get('clientType'),
            # scope does not support update due to aks solution's limitation
            'scope': server_linker.get('scope')
        }
        if schema_registry:
            parameters['targetService'] = {
                "type": "ConfluentSchemaRegistry",
                "endpoint": schema_registry
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
            'targetService': schema_linker.get('targetService'),
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
        if bootstrap_server:
            parameters['targetService'] = {
                "type": "ConfluentBootstrapServer",
                "endpoint": bootstrap_server
            }

    return client.begin_create_or_update(resource_uri=source_id,
                                         linker_name=connection_name,
                                         parameters=parameters)
