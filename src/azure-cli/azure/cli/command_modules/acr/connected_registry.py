# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from enum import Enum
from msrest.exceptions import ValidationError
from knack.log import get_logger
from knack.util import CLIError
from azure.cli.core.commands import LongRunningOperation
from azure.cli.core.commands.client_factory import get_subscription_id
from ._client_factory import cf_acr_tokens, cf_acr_scope_maps
from ._utils import (
    get_registry_by_name,
    validate_managed_registry,
    user_confirmation,
    create_default_scope_map,
    get_token_from_id,
    build_token_id
)


class ConnectedRegistryModes(Enum):
    MIRROR = 'mirror'
    REGISTRY = 'registry'


DEFAULT_GATEWAY_SCOPE = ['config/read', 'config/write', 'message/read', 'message/write']
REPO_SCOPES_BY_MODE = {
    ConnectedRegistryModes.MIRROR.value: ['content/read', 'metadata/read'],
    ConnectedRegistryModes.REGISTRY.value: ['content/read', 'content/write', 'content/delete',
                                            'metadata/read', 'metadata/write']
}
SYNC_SCOPE_MAP_NAME = "{}-sync-scope-map"
SYNC_TOKEN_NAME = "{}-sync-token"
REPOSITORY = "repositories/"
GATEWAY = "gateway/"

logger = get_logger(__name__)


def acr_connected_registry_create(cmd,  # pylint: disable=too-many-locals, too-many-statements
                                  client,
                                  registry_name,
                                  connected_registry_name,
                                  repositories=None,
                                  sync_token_name=None,
                                  client_token_list=None,
                                  resource_group_name=None,
                                  mode=None,
                                  parent_name=None,
                                  sync_schedule=None,
                                  sync_message_ttl=None,
                                  sync_window=None,
                                  log_level=None,
                                  sync_audit_logs_enabled=False):

    if bool(sync_token_name) == bool(repositories):
        raise CLIError("usage error: you need to provide either --sync-token-name or --repository, but not both.")
    registry, resource_group_name = get_registry_by_name(cmd.cli_ctx, registry_name, resource_group_name)
    subscription_id = get_subscription_id(cmd.cli_ctx)

    if not registry.data_endpoint_enabled:
        raise CLIError("Can't create the connected registry '{}' ".format(connected_registry_name) +
                       "because the cloud registry '{}' data endpoint is disabled. ".format(registry_name) +
                       "Enabling the data endpoint might affect your firewall rules.\nTo enable data endpoint run:" +
                       "\n\taz acr update -n {} --data-endpoint-enabled true".format(registry_name))

    ErrorResponseException = cmd.get_models('ErrorResponseException')
    parent = None
    if parent_name:
        try:
            parent = acr_connected_registry_show(cmd, client, parent_name, registry_name, resource_group_name)
        except ErrorResponseException as ex:
            if ex.response.status_code == 404:
                raise CLIError("The parent connected registry '{}' could not be found.".format(parent_name))
            raise CLIError(ex)
        if parent.mode.lower() != ConnectedRegistryModes.REGISTRY.value and parent.mode.lower() != mode.lower():
            raise CLIError("Can't create the registry '{}' with mode '{}' ".format(connected_registry_name, mode) +
                           "when the connected registry parent '{}' mode is '{}'. ".format(parent_name, parent.mode) +
                           "For more information on connected registries " +
                           "please visit https://aka.ms/acr/connected-registry.")

    if sync_token_name:
        sync_token_id = build_token_id(subscription_id, resource_group_name, registry_name, sync_token_name)
    else:
        sync_token_id = _create_sync_token(cmd, resource_group_name, registry_name,
                                           connected_registry_name, repositories, mode)

    if client_token_list is not None:
        for i, client_token_name in enumerate(client_token_list):
            client_token_list[i] = build_token_id(
                subscription_id, resource_group_name, registry_name, client_token_name)

    ConnectedRegistry, LoggingProperties, SyncProperties, ParentProperties = cmd.get_models(
        'ConnectedRegistry', 'LoggingProperties', 'SyncProperties', 'ParentProperties')
    connected_registry_create_parameters = ConnectedRegistry(
        provisioning_state=None,
        mode=mode,
        parent=ParentProperties(
            id=parent.id if parent else None,
            sync_properties=SyncProperties(
                token_id=sync_token_id,
                schedule=sync_schedule,
                message_ttl=sync_message_ttl,
                sync_window=sync_window
            )
        ),
        client_token_ids=client_token_list,
        logging=LoggingProperties(
            log_level=log_level,
            audit_log_status='Enabled' if sync_audit_logs_enabled else 'Disabled'
        )
    )

    try:
        return client.create(subscription_id=subscription_id,
                             resource_group_name=resource_group_name,
                             registry_name=registry_name,
                             connected_registry_name=connected_registry_name,
                             connected_registry_create_parameters=connected_registry_create_parameters)
    except ValidationError as e:
        raise CLIError(e)


def acr_connected_registry_update(cmd,  # pylint: disable=too-many-locals, too-many-statements
                                  client,
                                  registry_name,
                                  connected_registry_name,
                                  add_client_token_list=None,
                                  remove_client_token_list=None,
                                  resource_group_name=None,
                                  sync_schedule=None,
                                  sync_window=None,
                                  log_level=None,
                                  sync_message_ttl=None,
                                  sync_audit_logs_enabled=None):
    _, resource_group_name = validate_managed_registry(
        cmd, registry_name, resource_group_name)
    subscription_id = get_subscription_id(cmd.cli_ctx)
    current_connected_registry = acr_connected_registry_show(
        cmd, client, connected_registry_name, registry_name, resource_group_name)

    # Add or remove from the current client token id list
    if add_client_token_list is not None:
        for i, client_token_name in enumerate(add_client_token_list):
            add_client_token_list[i] = build_token_id(
                subscription_id, resource_group_name, registry_name, client_token_name)
        add_client_token_set = set(add_client_token_list)
    else:
        add_client_token_set = set()
    if remove_client_token_list is not None:
        for i, client_token_name in enumerate(remove_client_token_list):
            remove_client_token_list[i] = build_token_id(
                subscription_id, resource_group_name, registry_name, client_token_name)
        remove_client_token_set = set(remove_client_token_list)
    else:
        remove_client_token_set = set()

    duplicate_client_token = set.intersection(add_client_token_set, remove_client_token_set)
    if duplicate_client_token:
        errors = sorted(map(lambda action: action[action.rfind('/') + 1:], duplicate_client_token))
        raise CLIError(
            'Update ambiguity. Duplicate client token ids were provided with ' +
            '--add-client-tokens and --remove-client-tokens arguments.\n{}'.format(errors))

    current_client_token_set = set(current_connected_registry.client_token_ids) \
        if current_connected_registry.client_token_ids else set()
    client_token_set = current_client_token_set.union(add_client_token_set).difference(remove_client_token_set)

    client_token_list = list(client_token_set) if client_token_set != current_client_token_set else None

    ConnectedRegistryUpdateParameters, SyncUpdateProperties, LoggingProperties = cmd.get_models(
        'ConnectedRegistryUpdateParameters', 'SyncUpdateProperties', 'LoggingProperties')
    connected_registry_update_parameters = ConnectedRegistryUpdateParameters(
        sync_properties=SyncUpdateProperties(
            token_id=current_connected_registry.parent.sync_properties.token_id,
            schedule=sync_schedule,
            message_ttl=sync_message_ttl,
            sync_window=sync_window
        ),
        logging=LoggingProperties(
            log_level=log_level,
            audit_log_status=sync_audit_logs_enabled
        ),
        client_token_ids=client_token_list
    )

    try:
        return client.update(resource_group_name=resource_group_name,
                             registry_name=registry_name,
                             connected_registry_name=connected_registry_name,
                             connected_registry_update_parameters=connected_registry_update_parameters)
    except ValidationError as e:
        raise CLIError(e)


def acr_connected_registry_delete(cmd,
                                  client,
                                  connected_registry_name,
                                  registry_name,
                                  cleanup=False,
                                  yes=False,
                                  resource_group_name=None):

    _, resource_group_name = validate_managed_registry(
        cmd, registry_name, resource_group_name)
    user_confirmation("Are you sure you want to delete the connected registry '{}' in '{}'?".format(
        connected_registry_name, registry_name), yes)
    try:
        connected_registry = acr_connected_registry_show(
            cmd, client, connected_registry_name, registry_name, resource_group_name)
        result = client.delete(resource_group_name, registry_name, connected_registry_name)
        sync_token = get_token_from_id(cmd, connected_registry.parent.sync_properties.token_id)
        sync_token_name = sync_token.name
        sync_scope_map_name = sync_token.scope_map_id.split('/scopeMaps/')[1]
        if cleanup:
            from .token import acr_token_delete
            from .scope_map import acr_scope_map_delete
            token_client = cf_acr_tokens(cmd.cli_ctx)
            scope_map_client = cf_acr_scope_maps(cmd.cli_ctx)

            acr_token_delete(cmd, token_client, registry_name, sync_token_name, yes, resource_group_name)
            acr_scope_map_delete(cmd, scope_map_client, registry_name, sync_scope_map_name, yes, resource_group_name)
        else:
            msg = "Connected registry successfully deleted. Please cleanup your sync tokens and scope maps. " + \
                "Run the following commands for cleanup: \n\t" + \
                "az acr token delete -n {} -r {} --yes\n\t".format(sync_token_name, registry_name) + \
                "az acr scope-map delete -n {} -r {} --yes\n".format(sync_scope_map_name, registry_name) + \
                "Run the following command on all ascendency to remove the deleted registry gateway access: \n\t" + \
                "az acr scope-map update -n <scope-map-name> -r {} --remove-gateway {} --yes".format(
                    registry_name, " ".join([connected_registry_name] + DEFAULT_GATEWAY_SCOPE))
            logger.warning(msg)
        return result
    except ValidationError as e:
        raise CLIError(e)


def acr_connected_registry_deactivate(cmd,
                                      client,
                                      connected_registry_name,
                                      registry_name,
                                      yes=False,
                                      resource_group_name=None):
    _, resource_group_name = validate_managed_registry(
        cmd, registry_name, resource_group_name)
    subscription_id = get_subscription_id(cmd.cli_ctx)

    user_confirmation("Are you sure you want to deactivate the connected registry '{}' in '{}'?".format(
        connected_registry_name, registry_name), yes)
    return client.deactivate(subscription_id=subscription_id,
                             resource_group_name=resource_group_name,
                             registry_name=registry_name,
                             connected_registry_name=connected_registry_name)


def acr_connected_registry_list(cmd,
                                client,
                                registry_name,
                                parent_name=None,
                                no_children=False,
                                resource_group_name=None):
    _, resource_group_name = validate_managed_registry(
        cmd, registry_name, resource_group_name)
    connected_registry_list = list(client.list(resource_group_name, registry_name))
    result = []
    if no_children:
        if parent_name:
            result = [registry for registry in connected_registry_list
                      if registry.parent.id is not None and registry.parent.id.endswith(parent_name)]
        else:
            result = [registry for registry in connected_registry_list if not registry.parent.id]
    elif parent_name:
        family_tree = {}
        for registry in connected_registry_list:
            family_tree[registry.id] = {
                "registry": registry,
                "childs": []
            }
            if registry.name == parent_name:
                root_parent_id = registry.id
        for registry in connected_registry_list:
            parent_id = registry.parent.id
            if parent_id and not parent_id.isspace():
                family_tree[parent_id]["childs"].append(registry.id)
        result = _get_descendancy(family_tree, root_parent_id)
    else:
        result = connected_registry_list
    return result


def acr_connected_registry_show(cmd,
                                client,
                                connected_registry_name,
                                registry_name,
                                resource_group_name=None):
    _, resource_group_name = validate_managed_registry(
        cmd, registry_name, resource_group_name)
    return client.get(resource_group_name, registry_name, connected_registry_name)


def acr_connected_registry_list_client_tokens(cmd,
                                              client,
                                              connected_registry_name,
                                              registry_name,
                                              resource_group_name=None):
    _, resource_group_name = validate_managed_registry(
        cmd, registry_name, resource_group_name)
    current_connected_registry = acr_connected_registry_show(
        cmd, client, connected_registry_name, registry_name, resource_group_name)
    if current_connected_registry.client_token_ids is None:
        raise CLIError("No client tokens found: You can update your connected registry to add client tokens.")

    result = []
    for token_id in current_connected_registry.client_token_ids:
        token = get_token_from_id(cmd, token_id)
        result.append(token)
    return result


def _create_sync_token(cmd,
                       resource_group_name,
                       registry_name,
                       connected_registry_name,
                       repositories,
                       mode):
    token_client = cf_acr_tokens(cmd.cli_ctx)

    mode = mode.lower()
    if not any(option for option in ConnectedRegistryModes if option.value == mode):
        raise CLIError("usage error: --mode supports only 'registry' and 'mirror' values.")
    repository_actions_list = [[repo] + REPO_SCOPES_BY_MODE[mode] for repo in repositories]
    gateway_actions_list = [[connected_registry_name.lower()] + DEFAULT_GATEWAY_SCOPE]
    try:
        message = "Created by connected registry sync token: {}"
        sync_scope_map_name = SYNC_SCOPE_MAP_NAME.format(connected_registry_name)
        logger.warning("If sync scope map '%s' already exists, its actions will be overwritten", sync_scope_map_name)
        sync_scope_map = create_default_scope_map(cmd, resource_group_name, registry_name, sync_scope_map_name,
                                                  repository_actions_list, gateway_actions_list,
                                                  scope_map_description=message.format(connected_registry_name),
                                                  force=True)

        sync_token_name = SYNC_TOKEN_NAME.format(connected_registry_name)
        logger.warning("If sync token '%s' already exists, it properties will be overwritten", sync_token_name)
        Token = cmd.get_models('Token')
        poller = token_client.create(
            resource_group_name,
            registry_name,
            sync_token_name,
            Token(
                scope_map_id=sync_scope_map.id,
                status="enabled"
            )
        )

        token = LongRunningOperation(cmd.cli_ctx)(poller)
        return token.id
    except ValidationError as e:
        raise CLIError(e)


def _get_descendancy(family_tree, parent_id):
    childs = family_tree[parent_id]['childs']
    result = []
    for child_id in childs:
        result = [family_tree[child_id]["registry"]]
        descendancy = _get_descendancy(family_tree, child_id)
        if descendancy:
            result.extend(descendancy)
    return result


# region connected-registry install subgroup
def acr_connected_registry_install_info(cmd,
                                        client,
                                        connected_registry_name,
                                        registry_name,
                                        resource_group_name=None):
    return _get_install_info(cmd, client, connected_registry_name, registry_name, False, resource_group_name)


def acr_connected_registry_install_renew_credentials(cmd,
                                                     client,
                                                     connected_registry_name,
                                                     registry_name,
                                                     resource_group_name=None):
    return _get_install_info(cmd, client, connected_registry_name, registry_name, True, resource_group_name)


def _get_install_info(cmd,
                      client,
                      connected_registry_name,
                      registry_name,
                      regenerate_credentials,
                      resource_group_name=None):
    registry, resource_group_name = validate_managed_registry(
        cmd, registry_name, resource_group_name)
    connected_registry = acr_connected_registry_show(
        cmd, client, connected_registry_name, registry_name, resource_group_name)
    parent_gateway_endpoint = connected_registry.parent.sync_properties.gateway_endpoint
    parent_id = connected_registry.parent.id
    sync_token_name = connected_registry.parent.sync_properties.token_id.split('/tokens/')[1]
    if parent_id:
        parent = parent_id.split('/connectedRegistries/')[1]
        parent = acr_connected_registry_show(
            cmd, client, parent, registry_name, resource_group_name)
        parent_registry_endpoint = parent.login_server.host
    else:
        parent_registry_endpoint = registry.login_server

    connected_registry_login_server = "<connected registry login server. " + \
        "More info at https://aka.ms/acr/connected-registry>"

    if regenerate_credentials:
        from ._client_factory import cf_acr_token_credentials
        from .token import acr_token_credential_generate
        cred_client = cf_acr_token_credentials(cmd.cli_ctx)
        poller = acr_token_credential_generate(
            cmd, cred_client, registry_name, sync_token_name,
            password1=True, password2=True, resource_group_name=resource_group_name)
        credentials = LongRunningOperation(cmd.cli_ctx)(poller)
        sync_username = credentials.username
        sync_password = {
            "password1": credentials.passwords[0].value,
            "password2": credentials.passwords[1].value
        }
        logger.warning('Please store your generated credentials safely.')
    else:
        sync_username = sync_token_name
        sync_password = "<sync token password>"

    return {
        "ACR_REGISTRY_NAME": connected_registry_name,
        "ACR_REGISTRY_LOGIN_SERVER": connected_registry_login_server,
        "ACR_SYNC_TOKEN_USERNAME": sync_username,
        "ACR_SYNC_TOKEN_PASSWORD": sync_password,
        "ACR_PARENT_GATEWAY_ENDPOINT": parent_gateway_endpoint,
        "ACR_PARENT_LOGIN_SERVER": parent_registry_endpoint,
        "ACR_PARENT_PROTOCOL": "https"
    }
# endregion
