# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger
from knack.util import todict
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.core.util import sdk_no_wait
from azure.cli.core.azclierror import (
    CLIInternalError,
    InvalidArgumentValueError,
    RequiredArgumentMissingError,
    ValidationError,
    AzureResponseError
)
from azure.core.exceptions import ResourceNotFoundError
from ._resource_config import (
    CLIENT_TYPE,
    SUPPORTED_AUTH_TYPE,
    SUPPORTED_CLIENT_TYPE,
    TARGET_RESOURCES,
    AUTH_TYPE,
    RESOURCE,
    OPT_OUT_OPTION
)
from ._validators import (
    get_source_resource_name,
    get_target_resource_name,
    get_resource_type_by_id,
    validate_service_state
)
from ._addon_factory import AddonFactory
from ._utils import (
    compare_properties_changed,
    set_user_token_by_source_and_target,
    set_user_token_header,
    auto_register,
    get_cloud_conn_auth_info,
    get_local_conn_auth_info,
    _get_azext_module,
    _get_or_add_extension,
    springboot_migration_warning,
    get_auth_type_for_update,
    get_secret_type_for_update
)
from ._credential_free import is_passwordless_command
# pylint: disable=unused-argument,unsubscriptable-object,unsupported-membership-test,too-many-statements,too-many-locals,broad-exception-caught


logger = get_logger(__name__)
err_msg = 'Required argument is missing, please provide the arguments: {}'
PASSWORDLESS_EXTENSION_NAME = "serviceconnector-passwordless"
PASSWORDLESS_EXTENSION_MODULE = "azext_serviceconnector_passwordless.custom"


def connection_list(client,
                    source_resource_group=None,
                    source_id=None,
                    cluster=None,
                    site=None, slot=None,
                    spring=None, app=None, deployment=None):
    if not source_id:
        raise RequiredArgumentMissingError(err_msg.format('--source-id'))
    return auto_register(client.list, resource_uri=source_id)


def local_connection_list(cmd, client,
                          resource_group_name,
                          location=None):
    return auto_register(client.list,
                         subscription_id=get_subscription_id(cmd.cli_ctx),
                         resource_group_name=resource_group_name,
                         location=location)


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
        if auth_types and client_types:
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
                    site=None, slot=None,
                    spring=None, app=None, deployment=None):
    if not source_id or not connection_name:
        raise RequiredArgumentMissingError(
            err_msg.format('--source-id, --connection'))
    return auto_register(client.get, resource_uri=source_id, linker_name=connection_name)


def local_connection_show(cmd, client,
                          connection_name=None,
                          location=None,
                          resource_group_name=None,
                          id=None):  # pylint: disable=redefined-builtin
    if not connection_name:
        raise RequiredArgumentMissingError(
            err_msg.format('--id, --connection'))

    return auto_register(client.get,
                         subscription_id=get_subscription_id(cmd.cli_ctx),
                         resource_group_name=resource_group_name,
                         location=location,
                         connector_name=connection_name)


def connection_delete(client,
                      connection_name=None,
                      source_resource_group=None,
                      source_id=None,
                      indentifier=None,
                      cluster=None,
                      site=None, slot=None,
                      spring=None, app=None, deployment=None,
                      no_wait=False):
    if not source_id or not connection_name:
        raise RequiredArgumentMissingError(err_msg.format('--source-id, --connection'))

    return auto_register(sdk_no_wait, no_wait,
                         client.begin_delete,
                         resource_uri=source_id,
                         linker_name=connection_name)


def local_connection_delete(cmd, client,
                            connection_name=None,
                            location=None,
                            resource_group_name=None,
                            id=None,  # pylint: disable=redefined-builtin
                            no_wait=False):
    if not connection_name:
        raise RequiredArgumentMissingError(
            err_msg.format('--id, --connection'))

    return auto_register(sdk_no_wait, no_wait,
                         client.begin_delete,
                         subscription_id=get_subscription_id(cmd.cli_ctx),
                         resource_group_name=resource_group_name,
                         location=location,
                         connector_name=connection_name)


def connection_list_configuration(client,
                                  connection_name=None,
                                  source_resource_group=None,
                                  source_id=None,
                                  indentifier=None,
                                  cluster=None,
                                  site=None, slot=None,
                                  spring=None, app=None, deployment=None):
    if not source_id or not connection_name:
        raise RequiredArgumentMissingError(err_msg.format('--source-id, --connection'))
    configurations = auto_register(client.list_configurations,
                                   resource_uri=source_id,
                                   linker_name=connection_name)

    return configurations


def local_connection_generate_configuration(cmd, client,
                                            connection_name=None,
                                            location=None,
                                            resource_group_name=None,
                                            id=None):  # pylint: disable=redefined-builtin
    return auto_register(client.generate_configurations,
                         subscription_id=get_subscription_id(cmd.cli_ctx),
                         resource_group_name=resource_group_name,
                         location=location,
                         connector_name=connection_name)


def connection_preview_configuration(cmd, client,
                                     secret_auth_info=None, secret_auth_info_auto=None,
                                     user_identity_auth_info=None, system_identity_auth_info=None,
                                     service_principal_auth_info_secret=None,
                                     user_account_auth_info=None,
                                     client_type=None):
    param = {
        'target_service': None,
        'client_type': client_type,
        'auth_type': None
    }

    cmd_name = cmd.name.split(' ')[-1]
    resource_type = RESOURCE.value_of(cmd_name)
    if resource_type == RESOURCE.ConfluentKafka:
        param['target_service'] = 'CONFLUENT.CLOUD'
    else:
        target_id = TARGET_RESOURCES[resource_type]
        target_service_items = [i for i in target_id.split(
            '/') if i and not i.startswith('{')][3:]
        if target_service_items:
            param['target_service'] = '/'.join(target_service_items)

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
    param['auth_type'] = all_auth_info[0]['auth_type'] if len(
        all_auth_info) == 1 else None

    filter_str = "TargetService eq '{}'".format(param['target_service'])
    if param['auth_type']:
        filter_str += " and AuthType eq '{}'".format(param['auth_type'])
    if param['client_type']:
        filter_str += " and ClientType eq '{}'".format(param['client_type'])
    return auto_register(client.list,
                         filter=filter_str,
                         )


def connection_validate(cmd, client,
                        connection_name=None,
                        source_resource_group=None,
                        source_id=None,
                        indentifier=None,
                        cluster=None,
                        site=None, slot=None,
                        spring=None, app=None, deployment=None):
    if not source_id or not connection_name:
        raise RequiredArgumentMissingError(err_msg.format('--source-id, --connection'))

    # HACK: get linker first to infer target resource type so that user token can be
    # set to work around OBO
    linker = todict(client.get(resource_uri=source_id, linker_name=connection_name))
    target_id = linker.get('targetService', {}).get('id', '')
    target_type = get_resource_type_by_id(target_id)
    source_type = get_source_resource_name(cmd)
    client = set_user_token_by_source_and_target(client, cmd.cli_ctx, source_type, target_type)

    return auto_register(client.begin_validate, resource_uri=source_id, linker_name=connection_name)


def local_connection_validate(cmd, client,
                              connection_name=None,
                              resource_group_name=None,
                              location=None,
                              id=None):  # pylint: disable=redefined-builtin
    if not connection_name:
        raise RequiredArgumentMissingError(
            err_msg.format('--id, --connection'))

    # All use OBO token
    return auto_register(client.begin_validate,
                         subscription_id=get_subscription_id(cmd.cli_ctx),
                         resource_group_name=resource_group_name,
                         location=location,
                         connector_name=connection_name)


def connection_create(cmd, client,  # pylint: disable=too-many-locals,too-many-statements
                      connection_name=None, client_type=None,
                      source_resource_group=None, source_id=None,
                      target_resource_group=None, target_id=None,
                      secret_auth_info=None, secret_auth_info_auto=None,
                      user_identity_auth_info=None, system_identity_auth_info=None,
                      workload_identity_auth_info=None,                     # only used as arg
                      service_principal_auth_info_secret=None,
                      key_vault_id=None,
                      app_config_id=None,                                    # configuration store
                      service_endpoint=None,
                      private_endpoint=None,
                      store_in_connection_string=False,
                      customized_keys=None,
                      opt_out_list=None,
                      enable_appconfig_extension=False,
                      new_addon=False, no_wait=False,
                      cluster=None, scope=None, enable_csi=False,            # Resource.KubernetesCluster
                      site=None, slot=None,                                  # Resource.WebApp
                      spring=None, app=None, deployment=None,                # Resource.SpringCloud
                      server=None, database=None,                            # Resource.*Postgres, Resource.*Sql*
                      vault=None,                                            # Resource.KeyVault
                      account=None,                                          # Resource.Storage*
                      key_space=None, graph=None, table=None,                # Resource.Cosmos*,
                      config_store=None,                                     # Resource.AppConfig
                      namespace=None,                                        # Resource.EventHub
                      webpubsub=None,                                        # Resource.WebPubSub
                      signalr=None,                                          # Resource.SignalR
                      appinsights=None,                                      # Resource.AppInsights
                      target_app_name=None,                                  # Resource.ContainerApp
                      connstr_props=None,                                    # Resource.FabricSql
                      fabric_workspace_uuid=None,
                      fabric_sql_db_uuid=None,
                      no_recreate=False,
                      ):
    auth_action = 'optOutAllAuth' if (opt_out_list is not None and
                                      OPT_OUT_OPTION.AUTHENTICATION.value in opt_out_list) else None
    config_action = 'optOut' if (opt_out_list is not None and
                                 OPT_OUT_OPTION.CONFIGURATION_INFO.value in opt_out_list) else None
    target_type = get_target_resource_name(cmd)
    auth_info = get_cloud_conn_auth_info(secret_auth_info, secret_auth_info_auto, user_identity_auth_info,
                                         system_identity_auth_info, service_principal_auth_info_secret, new_addon,
                                         auth_action, config_action, target_type)
    if auth_info is not None and is_passwordless_command(cmd, auth_info) and auth_action != 'optOutAllAuth':
        if _get_or_add_extension(cmd, PASSWORDLESS_EXTENSION_NAME, PASSWORDLESS_EXTENSION_MODULE, False):
            azext_custom = _get_azext_module(
                PASSWORDLESS_EXTENSION_NAME, PASSWORDLESS_EXTENSION_MODULE)
            return azext_custom.connection_create_ext(cmd, client, connection_name, client_type,
                                                      source_resource_group, source_id,
                                                      target_resource_group, target_id,
                                                      secret_auth_info, secret_auth_info_auto,
                                                      user_identity_auth_info, system_identity_auth_info,
                                                      service_principal_auth_info_secret,
                                                      key_vault_id,
                                                      app_config_id,
                                                      service_endpoint,
                                                      private_endpoint,
                                                      store_in_connection_string,
                                                      new_addon, no_wait,
                                                      cluster=cluster, scope=scope, enable_csi=enable_csi,
                                                      customized_keys=customized_keys,
                                                      opt_out_list=opt_out_list,
                                                      connstr_props=connstr_props,
                                                      fabric_workspace_uuid=fabric_workspace_uuid,
                                                      fabric_sql_db_uuid=fabric_sql_db_uuid)
        raise CLIInternalError("Fail to install `serviceconnector-passwordless` extension. Please manually install it"
                               " with `az extension add --name serviceconnector-passwordless --upgrade`"
                               " and rerun the command")
    return connection_create_func(cmd, client, connection_name, client_type,
                                  source_resource_group, source_id,
                                  target_resource_group, target_id,
                                  secret_auth_info, secret_auth_info_auto,
                                  user_identity_auth_info, system_identity_auth_info,
                                  service_principal_auth_info_secret,
                                  key_vault_id,
                                  service_endpoint,
                                  private_endpoint,
                                  store_in_connection_string,
                                  new_addon, no_wait,
                                  # Resource.KubernetesCluster
                                  cluster, scope, enable_csi,
                                  customized_keys=customized_keys,
                                  opt_out_list=opt_out_list,
                                  app_config_id=app_config_id,
                                  enable_appconfig_extension=enable_appconfig_extension,
                                  server=server, database=database,
                                  connstr_props=connstr_props,
                                  no_recreate=no_recreate,
                                  )


# The function is used in extension, new feature must be added in the end for backward compatibility
def connection_create_func(cmd, client,  # pylint: disable=too-many-locals,too-many-statements,too-many-branches
                           connection_name=None, client_type=None,
                           source_resource_group=None, source_id=None,
                           target_resource_group=None, target_id=None,
                           secret_auth_info=None, secret_auth_info_auto=None,
                           user_identity_auth_info=None, system_identity_auth_info=None,
                           service_principal_auth_info_secret=None,
                           key_vault_id=None,
                           service_endpoint=None,
                           private_endpoint=None,
                           store_in_connection_string=False,
                           new_addon=False, no_wait=False,
                           cluster=None, scope=None, enable_csi=False,            # Resource.KubernetesCluster
                           site=None, slot=None,                                  # Resource.WebApp
                           spring=None, app=None, deployment=None,                # Resource.SpringCloud
                           # Resource.*Postgres, Resource.*Sql*
                           server=None, database=None,
                           vault=None,                                            # Resource.KeyVault
                           account=None,                                          # Resource.Storage*
                           key_space=None, graph=None, table=None,                # Resource.Cosmos*,
                           config_store=None,                                     # Resource.AppConfig
                           namespace=None,                                        # Resource.EventHub
                           webpubsub=None,                                        # Resource.WebPubSub
                           signalr=None,                                          # Resource.SignalR
                           enable_mi_for_db_linker=None,
                           customized_keys=None,
                           opt_out_list=None,
                           app_config_id=None,
                           target_app_name=None,                                  # Resource.ContainerApp
                           enable_appconfig_extension=False,
                           connstr_props=None,                                    # Resource.FabricSql
                           no_recreate=False,
                           **kwargs,
                           ):
    if not source_id:
        raise RequiredArgumentMissingError(err_msg.format('--source-id'))
    if not new_addon and not target_id:
        raise RequiredArgumentMissingError(err_msg.format('--target-id'))

    auth_action = 'optOutAllAuth' if (opt_out_list is not None and
                                      OPT_OUT_OPTION.AUTHENTICATION.value in opt_out_list) else None
    config_action = 'optOut' if (opt_out_list is not None and
                                 OPT_OUT_OPTION.CONFIGURATION_INFO.value in opt_out_list) else None
    source_type = get_source_resource_name(cmd)
    target_type = get_target_resource_name(cmd)
    auth_info = get_cloud_conn_auth_info(secret_auth_info, secret_auth_info_auto, user_identity_auth_info,
                                         system_identity_auth_info, service_principal_auth_info_secret, new_addon,
                                         auth_action, config_action, target_type)

    if store_in_connection_string:
        if client_type == CLIENT_TYPE.Dotnet.value:
            client_type = CLIENT_TYPE.DotnetConnectionString.value
        else:
            logger.warning('client_type is not dotnet, ignore "--config-connstr"')

    public_network_action = 'optOut' if (opt_out_list is not None and
                                         OPT_OUT_OPTION.PUBLIC_NETWORK.value in opt_out_list) else None

    if target_type == RESOURCE.FabricSql:
        targetService = {
            "type": "FabricPlatform",
            "endpoint": target_id
        }
    else:
        targetService = {
            "type": "AzureResource",
            "id": target_id
        }

    if target_type == RESOURCE.NeonPostgres:
        if connstr_props is None:
            connstr_props = {}
        connstr_props['Database'] = database
        connstr_props['Server'] = server

    parameters = {
        'target_service': targetService,
        'auth_info': auth_info,
        'secret_store': {
            'key_vault_id': key_vault_id,
        },
        'client_type': client_type,
        'scope': scope,
        'configurationInfo': {
            'customizedKeys': customized_keys,
            'configurationStore': {
                'appConfigurationId': app_config_id,
            },
            'additionalConnectionStringProperties': connstr_props,
            'action': config_action
        },
        'publicNetworkSolution': {
            'action': public_network_action
        }
    }

    # HACK: set user token to work around OBO
    client = set_user_token_by_source_and_target(client, cmd.cli_ctx, source_type, target_type)

    if key_vault_id:
        client = set_user_token_header(client, cmd.cli_ctx)
        from ._utils import create_key_vault_reference_connection_if_not_exist
        create_key_vault_reference_connection_if_not_exist(cmd, client, source_id, key_vault_id, scope)
    elif auth_info is not None and auth_info['auth_type'] == 'secret' and 'secret_info' in auth_info \
            and auth_info['secret_info']['secret_type'] == 'keyVaultSecretReference':
        raise ValidationError('--vault-id must be provided to use secret-name')

    if app_config_id:
        from ._utils import create_app_config_connection_if_not_exist
        create_app_config_connection_if_not_exist(cmd, client, source_id, app_config_id, scope)

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

    if enable_appconfig_extension:
        parameters['target_service']['resource_properties'] = {
            'type': 'AppConfig',
            'connect_with_kubernetes_extension': enable_appconfig_extension,
        }

    if new_addon:
        addon = AddonFactory.get(target_type)(cmd, source_id)
        target_id, default_auth_info = addon.provision()
        parameters['target_service'] = {
            "type": "AzureResource",
            "id": target_id
        }
        parameters['auth_info'] = auth_info or default_auth_info
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
    if no_recreate:
        try:
            linker = todict(client.get(resource_uri=source_id, linker_name=connection_name))
            if linker is not None and linker.get('provisioningState') == 'Accepted':
                logger.warning('Connection provisioningState is Accepted, please retry later to avoid conflict.')
                return linker
            if linker is not None and linker.get('provisioningState') == 'Succeeded' and \
                    not compare_properties_changed(parameters, linker):
                logger.warning(
                    'Connection exists and no property to be updated, skip the update operation.')
                return linker
        except ResourceNotFoundError:
            logger.debug('No existing connection, continue to create it.')

    if enable_mi_for_db_linker and auth_action != 'optOutAllAuth':
        new_auth_info = enable_mi_for_db_linker(
            cmd, source_id, target_id, auth_info, client_type, connection_name, connstr_props)
        parameters['auth_info'] = new_auth_info or parameters['auth_info']

    # migration warning for Spring Azure Cloud
    if client_type == CLIENT_TYPE.SpringBoot.value and target_type == RESOURCE.CosmosSql and auth_info is not None:
        isSecretType = (auth_info['auth_type'] == AUTH_TYPE.SecretAuto.value or
                        auth_info['auth_type'] == AUTH_TYPE.Secret.value)
        logger.warning(springboot_migration_warning(require_update=False,
                                                    check_version=(not isSecretType),
                                                    both_version=isSecretType))
    return auto_register(sdk_no_wait, no_wait,
                         client.begin_create_or_update,
                         resource_uri=source_id,
                         linker_name=connection_name,
                         parameters=parameters)


def local_connection_create(cmd, client,  # pylint: disable=too-many-locals,too-many-statements
                            resource_group_name,
                            connection_name=None,
                            location=None,
                            client_type=None,
                            target_resource_group=None, target_id=None,
                            secret_auth_info=None, secret_auth_info_auto=None,
                            user_account_auth_info=None,                      # new auth info
                            service_principal_auth_info_secret=None,
                            customized_keys=None,
                            no_wait=False,
                            server=None, database=None,                            # Resource.*Postgres, Resource.*Sql*
                            vault=None,                                            # Resource.KeyVault
                            account=None,                                          # Resource.Storage*
                            key_space=None, graph=None, table=None,                # Resource.Cosmos*,
                            config_store=None,                                     # Resource.AppConfig
                            namespace=None,                                        # Resource.EventHub
                            webpubsub=None,                                        # Resource.WebPubSub
                            signalr=None,                                          # Resource.SignalR
                            appinsights=None,                                      # Resource.AppInsights
                            ):
    auth_info = get_local_conn_auth_info(secret_auth_info, secret_auth_info_auto,
                                         user_account_auth_info, service_principal_auth_info_secret)
    if is_passwordless_command(cmd, auth_info):
        if _get_or_add_extension(cmd, PASSWORDLESS_EXTENSION_NAME, PASSWORDLESS_EXTENSION_MODULE, False):
            azext_custom = _get_azext_module(
                PASSWORDLESS_EXTENSION_NAME, PASSWORDLESS_EXTENSION_MODULE)
            return azext_custom.local_connection_create_ext(cmd, client, resource_group_name,
                                                            connection_name,
                                                            location,
                                                            client_type,
                                                            target_resource_group, target_id,
                                                            secret_auth_info, secret_auth_info_auto,
                                                            user_account_auth_info,                      # new auth info
                                                            service_principal_auth_info_secret,
                                                            no_wait,
                                                            customized_keys=customized_keys)
        raise CLIInternalError("Fail to install `serviceconnector-passwordless` extension. Please manually install it"
                               " with `az extension add --name serviceconnector-passwordless --upgrade`"
                               " and rerun the command")

    return local_connection_create_func(cmd, client, resource_group_name,
                                        connection_name,
                                        location,
                                        client_type,
                                        target_resource_group, target_id,
                                        secret_auth_info, secret_auth_info_auto,
                                        user_account_auth_info,                      # new auth info
                                        service_principal_auth_info_secret,
                                        no_wait,
                                        customized_keys=customized_keys)


# The function is used in extension, new feature must be added in the end for backward compatibility
def local_connection_create_func(cmd, client,  # pylint: disable=too-many-locals,too-many-statements
                                 resource_group_name,
                                 connection_name=None,
                                 location=None,
                                 client_type=None,
                                 target_resource_group=None, target_id=None,
                                 secret_auth_info=None, secret_auth_info_auto=None,
                                 user_account_auth_info=None,                      # new auth info
                                 service_principal_auth_info_secret=None,
                                 no_wait=False,
                                 # Resource.*Postgres, Resource.*Sql*
                                 server=None, database=None,
                                 vault=None,                                            # Resource.KeyVault
                                 account=None,                                          # Resource.Storage*
                                 key_space=None, graph=None, table=None,                # Resource.Cosmos*,
                                 config_store=None,                                     # Resource.AppConfig
                                 namespace=None,                                        # Resource.EventHub
                                 webpubsub=None,                                        # Resource.WebPubSub
                                 signalr=None,                                          # Resource.SignalR
                                 enable_mi_for_db_linker=None,
                                 customized_keys=None,
                                 **kwargs,
                                 ):
    auth_info = get_local_conn_auth_info(secret_auth_info, secret_auth_info_auto,
                                         user_account_auth_info, service_principal_auth_info_secret)
    parameters = {
        'target_service': {
            "type": "AzureResource",
            "id": target_id
        },
        'auth_info': auth_info,
        'client_type': client_type,
        'public_network_solution': {
            'firewall_rules': {
                'caller_client_iP': 'true'
            }
        },
        'configurationInfo': {
            'customizedKeys': customized_keys
        }
    }

    # HACK: set user token to work around OBO
    source_type = get_source_resource_name(cmd)
    target_type = get_target_resource_name(cmd)
    client = set_user_token_by_source_and_target(
        client, cmd.cli_ctx, source_type, target_type)

    validate_service_state(parameters)
    if enable_mi_for_db_linker:
        new_auth_info = enable_mi_for_db_linker(
            cmd, None, target_id, auth_info, client_type, connection_name)
        parameters['auth_info'] = new_auth_info or parameters['auth_info']
    return auto_register(sdk_no_wait, no_wait,
                         client.begin_create_or_update,
                         subscription_id=get_subscription_id(cmd.cli_ctx),
                         resource_group_name=resource_group_name,
                         location=location,
                         connector_name=connection_name,
                         parameters=parameters)


def connection_update(cmd, client,  # pylint: disable=too-many-locals, too-many-branches
                      connection_name=None, client_type=None,
                      source_resource_group=None, source_id=None, indentifier=None,
                      secret_auth_info=None, secret_auth_info_auto=None,
                      user_identity_auth_info=None, system_identity_auth_info=None,
                      workload_identity_auth_info=None,
                      service_principal_auth_info_secret=None,
                      key_vault_id=None,
                      app_config_id=None,
                      service_endpoint=None,
                      private_endpoint=None,
                      store_in_connection_string=False,
                      no_wait=False,
                      scope=None,
                      cluster=None, enable_csi=False,                         # Resource.Kubernetes
                      site=None, slot=None,                                   # Resource.WebApp
                      spring=None, app=None, deployment=None,                 # Resource.SpringCloud
                      customized_keys=None,
                      connstr_props=None,           # Resource.FabricSql
                      opt_out_list=None,
                      ):

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
    elif not all_auth_info and (linker.get('authInfo') is None or
                                linker.get('authInfo').get('authType') != 'secret' or
                                not linker.get('authInfo').get('name')):
        auth_info = linker.get('authInfo')
    else:
        raise ValidationError('Auth info argument should be provided when '
                              'updating the connection: {}'.format(linker.get('name')))
    # validate the properties to be updated
    if client_type is None and not all_auth_info:
        raise ValidationError(
            'Either client type or auth info should be specified to update')
    auth_action = 'optOutAllAuth' if (opt_out_list is not None and
                                      OPT_OUT_OPTION.AUTHENTICATION.value in opt_out_list) else None
    if auth_info is not None:
        auth_info["auth_mode"] = auth_action

    if linker.get('secretStore') and linker.get('secretStore').get('keyVaultId'):
        key_vault_id = key_vault_id or linker.get('secretStore').get('keyVaultId')

    client_type = client_type or linker.get('clientType')
    if store_in_connection_string:
        if client_type == CLIENT_TYPE.Dotnet.value:
            client_type = CLIENT_TYPE.DotnetConnectionString.value
        else:
            logger.warning('client_type is not dotnet, ignore "--config-connstr"')

    if linker.get('configurationInfo') and linker.get('configurationInfo').get('customizedKeys'):
        customized_keys = customized_keys or linker.get('configurationInfo').get('customizedKeys')

    if linker.get('configurationInfo') and linker.get('configurationInfo').get('additionalConnectionStringProperties'):
        connstr_props = connstr_props or linker.get(
            'configurationInfo').get('additionalConnectionStringProperties')

    config_action = 'optOut' if (opt_out_list is not None and
                                 OPT_OUT_OPTION.CONFIGURATION_INFO.value in opt_out_list) else None
    public_network_action = 'optOut' if (opt_out_list is not None and
                                         OPT_OUT_OPTION.PUBLIC_NETWORK.value in opt_out_list) else None

    parameters = {
        'target_service': linker.get('targetService'),
        'auth_info': auth_info,
        'secret_store': {
            'key_vault_id': key_vault_id,
        },
        'client_type': client_type,
        # scope can be updated in container app while cannot be updated in aks due to some limitations
        'scope': scope or linker.get('scope'),
        'configurationInfo': {
            'customizedKeys': customized_keys,
            'configurationStore': {
                'appConfigurationId': app_config_id
            },
            'additionalConnectionStringProperties': connstr_props,
            'action': config_action
        },
        'publicNetworkSolution': {
            'action': public_network_action
        }
    }

    # HACK: set user token to work around OBO
    source_type = get_source_resource_name(cmd)
    target_type = get_target_resource_name(cmd)
    client = set_user_token_by_source_and_target(client, cmd.cli_ctx, source_type, target_type)

    if key_vault_id:
        client = set_user_token_header(client, cmd.cli_ctx)
        from ._utils import create_key_vault_reference_connection_if_not_exist
        create_key_vault_reference_connection_if_not_exist(cmd, client, source_id, key_vault_id, scope)
    elif get_auth_type_for_update(auth_info) == 'secret' and \
            get_secret_type_for_update(auth_info) == 'keyVaultSecretReference':
        raise ValidationError('--vault-id must be provided to use secret-name')

    if app_config_id:
        from ._utils import create_app_config_connection_if_not_exist
        create_app_config_connection_if_not_exist(cmd, client, source_id, app_config_id, scope)

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

    # migration warning for Spring Azure Cloud
    if client_type == CLIENT_TYPE.SpringBoot.value and target_type == RESOURCE.CosmosSql:
        isSecretType = (get_auth_type_for_update(auth_info) == AUTH_TYPE.SecretAuto.value or
                        get_auth_type_for_update(auth_info) == AUTH_TYPE.Secret.value)
        logger.warning(springboot_migration_warning(require_update=False,
                                                    check_version=(not isSecretType),
                                                    both_version=isSecretType))

    return auto_register(sdk_no_wait, no_wait,
                         client.begin_create_or_update,
                         resource_uri=source_id,
                         linker_name=connection_name,
                         parameters=parameters)


def local_connection_update(cmd, client,  # pylint: disable=too-many-locals
                            connection_name=None,
                            location=None,
                            resource_group_name=None,
                            id=None,  # pylint: disable=redefined-builtin
                            client_type=None,
                            secret_auth_info=None, secret_auth_info_auto=None,
                            user_account_auth_info=None,                      # new auth info
                            service_principal_auth_info_secret=None,
                            no_wait=False,
                            customized_keys=None,
                            ):

    linker = todict(client.get(subscription_id=get_subscription_id(cmd.cli_ctx),
                               resource_group_name=resource_group_name,
                               location=location,
                               connector_name=connection_name))

    all_auth_info = []
    if secret_auth_info is not None:
        all_auth_info.append(secret_auth_info)
    if secret_auth_info_auto is not None:
        all_auth_info.append(secret_auth_info_auto)
    if user_account_auth_info is not None:
        all_auth_info.append(user_account_auth_info)
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
        raise ValidationError(
            'Either client type or auth info should be specified to update')

    client_type = client_type or linker.get('clientType')
    if linker.get('configurationInfo') and linker.get('configurationInfo').get('customizedKeys'):
        customized_keys = customized_keys or linker.get('configurationInfo').get('customizedKeys')

    parameters = {
        'target_service': linker.get('targetService'),
        'auth_info': auth_info,
        'client_type': client_type,
        'public_network_solution': linker.get('publicNetworkSolution') or {
            'firewall_rules': {
                'caller_client_iP': 'true'
            }
        },
        'configurationInfo': {
            'customizedKeys': customized_keys
        }
    }

    return auto_register(sdk_no_wait, no_wait,
                         client.begin_create_or_update,
                         subscription_id=get_subscription_id(cmd.cli_ctx),
                         resource_group_name=resource_group_name,
                         location=location,
                         connector_name=connection_name,
                         parameters=parameters)


def local_connection_create_kafka(cmd, client,  # pylint: disable=too-many-locals
                                  resource_group_name,
                                  bootstrap_server,
                                  kafka_key,
                                  kafka_secret,
                                  schema_registry,
                                  schema_key,
                                  schema_secret,
                                  connection_name=None,
                                  location=None,
                                  client_type=None,
                                  customized_keys=None):

    from ._transformers import transform_linker_properties
    # validation
    if 'azure.confluent.cloud' not in bootstrap_server.lower():
        raise InvalidArgumentValueError(
            'Kafka bootstrap server url is invalid: {}'.format(bootstrap_server))
    if 'azure.confluent.cloud' not in schema_registry.lower():
        raise InvalidArgumentValueError(
            'Schema registry url is invalid: {}'.format(schema_registry))

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
        'client_type': client_type,
        'public_network_solution': {
            'firewall_rules': {
                'caller_client_iP': 'true'
            }
        },
        'configurationInfo': {
            'customizedKeys': customized_keys
        },
    }
    logger.warning('Start creating a connection for bootstrap server ...')
    server_linker = client.begin_create_or_update(
        subscription_id=get_subscription_id(cmd.cli_ctx),
        resource_group_name=resource_group_name,
        location=location,
        connector_name=connection_name,
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
        'client_type': client_type,
        'public_network_solution': {
            'firewall_rules': {
                'caller_client_iP': 'true'
            }
        },
        'configurationInfo': {
            'customizedKeys': customized_keys
        },
    }
    logger.warning('Start creating a connection for schema registry ...')
    registry_linker = client.begin_create_or_update(
        subscription_id=get_subscription_id(cmd.cli_ctx),
        resource_group_name=resource_group_name,
        location=location,
        connector_name='{}_schema'.format(connection_name),
        parameters=parameters)
    # block to poll the connection
    registry_linker = registry_linker.result()
    logger.warning('Created')

    return [
        transform_linker_properties(server_linker),
        transform_linker_properties(registry_linker)
    ]


def local_connection_update_kafka(cmd, client,  # pylint: disable=too-many-locals
                                  connection_name,
                                  location=None,
                                  resource_group_name=None,
                                  bootstrap_server=None,
                                  kafka_key=None,
                                  kafka_secret=None,
                                  schema_registry=None,
                                  schema_key=None,
                                  schema_secret=None,
                                  client_type=None,
                                  customized_keys=None):

    # use the suffix to decide the connection type
    if connection_name.endswith('_schema'):  # the schema registry connection
        if schema_secret is None:
            raise ValidationError(
                "'--schema-secret' is required to update a schema registry connection")
        if bootstrap_server or kafka_key or kafka_secret:
            raise ValidationError("The available parameters to update a schema registry connection are:"
                                  " ['--schema-registry', '--schema-key', '--schema-secret', '--client-type']")
        server_linker = todict(client.get(subscription_id=get_subscription_id(cmd.cli_ctx),
                                          resource_group_name=resource_group_name,
                                          location=location,
                                          connector_name=connection_name))
        if server_linker.get('configurationInfo') and server_linker.get('configurationInfo').get('customizedKeys'):
            customized_keys = customized_keys or server_linker.get('configurationInfo').get('customizedKeys')

        parameters = {
            'targetService': server_linker.get('targetService'),
            'auth_info': {
                'name': schema_key or server_linker.get('authInfo').get('name'),
                'secret': schema_secret,
                'auth_type': 'secret'
            },

            'client_type': client_type or server_linker.get('clientType'),
            'public_network_solution': server_linker.get('publicNetworkSolution') or {
                'firewall_rules': {
                    'caller_client_iP': 'true'
                }
            },
            'configurationInfo': {
                'customizedKeys': customized_keys
            },
        }
        if schema_registry:
            parameters['targetService'] = {
                "type": "ConfluentSchemaRegistry",
                "endpoint": schema_registry
            }
    else:  # the bootstrap server connection
        if kafka_secret is None:
            raise ValidationError(
                "'--kafka-secret' is required to update a bootstrap server connection")
        if schema_registry or schema_key or schema_secret:
            raise ValidationError("The available parameters to update a bootstrap server connection are:"
                                  " ['--bootstrap-server', '--kafka-key', '--kafka-secret', '--client-type']")
        schema_linker = todict(client.get(subscription_id=get_subscription_id(cmd.cli_ctx),
                                          resource_group_name=resource_group_name,
                                          location=location,
                                          connector_name=connection_name))
        if schema_linker.get('configurationInfo') and schema_linker.get('configurationInfo').get('customizedKeys'):
            customized_keys = customized_keys or schema_linker.get('configurationInfo').get('customizedKeys')

        parameters = {
            'targetService': schema_linker.get('targetService'),
            'auth_info': {
                'name': kafka_key or schema_linker.get('authInfo').get('name'),
                'secret': kafka_secret,
                'auth_type': 'secret'
            },
            'client_type': client_type or schema_linker.get('clientType'),
            'public_network_solution': schema_linker.get('publicNetworkSolution') or {
                'firewall_rules': {
                    'caller_client_iP': 'true'
                }
            },
            'configurationInfo': {
                'customizedKeys': customized_keys
            },
        }
        if bootstrap_server:
            parameters['targetService'] = {
                "type": "ConfluentBootstrapServer",
                "endpoint": bootstrap_server
            }

    return client.begin_create_or_update(subscription_id=get_subscription_id(cmd.cli_ctx),
                                         resource_group_name=resource_group_name,
                                         location=location,
                                         connector_name=connection_name,
                                         parameters=parameters)


def connection_create_kafka(cmd, client,  # pylint: disable=too-many-locals
                            bootstrap_server,
                            kafka_key,
                            kafka_secret,
                            schema_registry,
                            schema_key,
                            schema_secret,
                            key_vault_id=None,
                            app_config_id=None,
                            connection_name=None,
                            client_type=None,
                            source_resource_group=None,
                            source_id=None,
                            customized_keys=None,
                            opt_out_list=None,
                            cluster=None, scope=None,          # Resource.Kubernetes
                            site=None, slot=None,              # Resource.WebApp
                            deployment=None,
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

    if app_config_id:
        from ._utils import create_app_config_connection_if_not_exist
        create_app_config_connection_if_not_exist(cmd, client, source_id, app_config_id, scope)
    config_action = 'optOut' if (opt_out_list is not None and
                                 OPT_OUT_OPTION.CONFIGURATION_INFO.value in opt_out_list) else None
    public_network_action = 'optOut' if (opt_out_list is not None and
                                         OPT_OUT_OPTION.PUBLIC_NETWORK.value in opt_out_list) else None
    auth_action = 'optOutAllAuth' if (opt_out_list is not None and
                                      OPT_OUT_OPTION.AUTHENTICATION.value in opt_out_list) else None

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
            'auth_type': 'secret',
            'auth_mode': auth_action
        },
        'secret_store': {
            'key_vault_id': key_vault_id,
        },
        'client_type': client_type,
        'scope': scope,
        'configurationInfo': {
            'customizedKeys': customized_keys,
            'configurationStore': {
                'appConfigurationId': app_config_id,
            },
            'action': config_action
        },
        'publicNetworkSolution': {
            'action': public_network_action
        }
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
            'auth_type': 'secret',
            'auth_mode': auth_action
        },
        'secret_store': {
            'key_vault_id': key_vault_id,
        },
        'client_type': client_type,
        'scope': scope,
        'configurationInfo': {
            'configurationStore': {
                'appConfigurationId': app_config_id,
            },
            'action': config_action
        }
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
                            app_config_id=None,
                            client_type=None,
                            source_resource_group=None,
                            source_id=None,
                            customized_keys=None,
                            opt_out_list=None,
                            cluster=None,
                            site=None, slot=None,              # Resource.WebApp
                            deployment=None,
                            spring=None, app=None):            # Resource.SpringCloud

    config_action = 'optOut' if (opt_out_list is not None and
                                 OPT_OUT_OPTION.CONFIGURATION_INFO.value in opt_out_list) else None
    public_network_action = 'optOut' if (opt_out_list is not None and
                                         OPT_OUT_OPTION.PUBLIC_NETWORK.value in opt_out_list) else None
    auth_action = 'optOutAllAuth' if (opt_out_list is not None and
                                      OPT_OUT_OPTION.AUTHENTICATION.value in opt_out_list) else None

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
        if server_linker.get('configurationInfo') and server_linker.get('configurationInfo').get('customizedKeys'):
            customized_keys = customized_keys or server_linker.get('configurationInfo').get('customizedKeys')

        if app_config_id:
            from ._utils import create_app_config_connection_if_not_exist
            create_app_config_connection_if_not_exist(cmd, client, source_id, app_config_id)

        parameters = {
            'targetService': server_linker.get('targetService'),
            'auth_info': {
                'name': schema_key or server_linker.get('authInfo').get('name'),
                'secret': schema_secret,
                'auth_type': 'secret',
                'auth_mode': auth_action
            },
            'secret_store': {
                'key_vault_id': key_vault_id,
            },
            'client_type': client_type or server_linker.get('clientType'),
            # scope does not support update due to aks solution's limitation
            'scope': server_linker.get('scope'),
            'configurationInfo': {
                'customizedKeys': customized_keys,
                'configurationStore': {
                    'appConfigurationId': app_config_id,
                },
                'action': config_action,
            },
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
                                  " ['--bootstrap-server', '--kafka-key', '--kafka-secret', '--client-type']")
        schema_linker = todict(client.get(resource_uri=source_id, linker_name=connection_name))

        if schema_linker.get('secretStore') and schema_linker.get('secretStore').get('keyVaultId'):
            key_vault_id = key_vault_id or schema_linker.get('secretStore').get('keyVaultId')
        if key_vault_id:
            client = set_user_token_header(client, cmd.cli_ctx)
            from ._utils import create_key_vault_reference_connection_if_not_exist
            create_key_vault_reference_connection_if_not_exist(cmd, client, source_id, key_vault_id)
        if schema_linker.get('configurationInfo') and schema_linker.get('configurationInfo').get('customizedKeys'):
            customized_keys = customized_keys or schema_linker.get('configurationInfo').get('customizedKeys')

        if app_config_id:
            from ._utils import create_app_config_connection_if_not_exist
            create_app_config_connection_if_not_exist(cmd, client, source_id, app_config_id)

        parameters = {
            'targetService': schema_linker.get('targetService'),
            'auth_info': {
                'name': kafka_key or schema_linker.get('authInfo').get('name'),
                'secret': kafka_secret,
                'auth_type': 'secret',
                'auth_mode': auth_action
            },
            'secret_store': {
                'key_vault_id': key_vault_id,
            },
            'client_type': client_type or schema_linker.get('clientType'),
            'configurationInfo': {
                'customizedKeys': customized_keys,
                'configurationStore': {
                    'appConfigurationId': app_config_id,
                },
                'action': config_action
            },
            'publicNetworkSolution': {
                'action': public_network_action
            }
        }
        if bootstrap_server:
            parameters['targetService'] = {
                "type": "ConfluentBootstrapServer",
                "endpoint": bootstrap_server
            }

    return client.begin_create_or_update(resource_uri=source_id,
                                         linker_name=connection_name,
                                         parameters=parameters)
