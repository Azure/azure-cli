# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from enum import Enum
import re
from msrest.exceptions import ValidationError
from knack.log import get_logger
from knack.util import CLIError
from azure.cli.core.azclierror import ArgumentUsageError, InvalidArgumentValueError
from azure.cli.core.commands import LongRunningOperation
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.core.util import user_confirmation
from ._client_factory import cf_acr_tokens, cf_acr_scope_maps
from ._utils import (
    build_token_id,
    create_default_scope_map,
    get_registry_by_name,
    get_scope_map_from_id,
    get_token_from_id,
    parse_scope_map_actions,
    validate_managed_registry
)


class ConnectedRegistryModes(Enum):
    READONLY = 'readonly'
    READWRITE = 'readwrite'


DEFAULT_GATEWAY_SCOPE = ['config/read', 'config/write', 'message/read', 'message/write']
REPO_SCOPES_BY_MODE = {
    ConnectedRegistryModes.READONLY.value: ['content/read', 'metadata/read'],
    ConnectedRegistryModes.READWRITE.value: ['content/read', 'content/write', 'content/delete',
                                             'metadata/read', 'metadata/write'],
    # Remove next release
    "mirror": ['content/read', 'metadata/read'],
    "registry": ['content/read', 'content/write', 'content/delete', 'metadata/read', 'metadata/write'],
}
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
                                  sync_audit_logs_enabled=False,
                                  notifications=None):

    if bool(sync_token_name) == bool(repositories):
        raise CLIError("usage error: you must provide either --sync-token-name or --repository, but not both.")
    # Check needed since the sync token gateway actions must be at least 5 characters long.
    if len(connected_registry_name) < 5:
        raise InvalidArgumentValueError("argument error: Connected registry name must be at least 5 characters long.")
    if re.match(r'\w*[A-Z]\w*', connected_registry_name):
        raise InvalidArgumentValueError("argument error: Connected registry name must use only lowercase.")
    registry, resource_group_name = get_registry_by_name(cmd.cli_ctx, registry_name, resource_group_name)
    subscription_id = get_subscription_id(cmd.cli_ctx)

    if not registry.data_endpoint_enabled:
        raise CLIError("Can't create the connected registry '{}' ".format(connected_registry_name) +
                       "because the cloud registry '{}' data endpoint is disabled. ".format(registry_name) +
                       "Enabling the data endpoint might affect your firewall rules.\nTo enable data endpoint run:" +
                       "\n\taz acr update -n {} --data-endpoint-enabled true".format(registry_name))

    from azure.core.exceptions import HttpResponseError as ErrorResponseException
    parent = None
    mode = mode.lower()
    if parent_name:
        try:
            parent = acr_connected_registry_show(cmd, client, parent_name, registry_name, resource_group_name)
            connected_registry_list = list(client.list(resource_group_name, registry_name))
            family_tree, _ = _get_family_tree(connected_registry_list, None)
        except ErrorResponseException as ex:
            if ex.response.status_code == 404:
                raise CLIError("The parent connected registry '{}' could not be found.".format(parent_name))
            raise CLIError(ex)

        if parent.mode.lower() not in (ConnectedRegistryModes.READWRITE.value, mode):
            raise CLIError("Can't create the registry '{}' with mode '{}' ".format(connected_registry_name, mode) +
                           "when the connected registry parent '{}' mode is '{}'. ".format(parent_name, parent.mode) +
                           "For more information on connected registries " +
                           "please visit https://aka.ms/acr/connected-registry.")
        _update_ancestor_permissions(cmd, family_tree, resource_group_name, registry_name, parent.id,
                                     connected_registry_name, repositories, mode, False)

    if sync_token_name:
        sync_token_id = build_token_id(subscription_id, resource_group_name, registry_name, sync_token_name)
    else:
        sync_token_id = _create_sync_token(cmd, resource_group_name, registry_name,
                                           connected_registry_name, repositories, mode)

    if client_token_list is not None:
        for i, client_token_name in enumerate(client_token_list):
            client_token_list[i] = build_token_id(
                subscription_id, resource_group_name, registry_name, client_token_name)

    notifications_set = set(list(notifications)) \
        if notifications else set()

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
        ),
        notifications_list=list(notifications_set) if notifications_set else None
    )

    try:
        return client.begin_create(resource_group_name=resource_group_name,
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
                                  sync_audit_logs_enabled=None,
                                  add_notifications=None,
                                  remove_notifications=None):
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

    # Add or remove from the current notifications list
    add_notifications_set = set(list(add_notifications)) \
        if add_notifications else set()

    remove_notifications_set = set(list(remove_notifications)) \
        if remove_notifications else set()

    duplicate_notifications = set.intersection(add_notifications_set, remove_notifications_set)
    if duplicate_notifications:
        errors = sorted(duplicate_notifications)
        raise ArgumentUsageError(
            'Update ambiguity. Duplicate notifications list were provided with ' +
            '--add-notifications and --remove-notifications arguments.\n{}'.format(errors))

    current_notifications_set = set(current_connected_registry.notifications_list) \
        if current_connected_registry.notifications_list else set()
    notifications_set = current_notifications_set.union(add_notifications_set).difference(remove_notifications_set)

    notifications_list = list(notifications_set) if notifications_set != current_notifications_set else None

    ConnectedRegistryUpdateParameters, SyncUpdateProperties, LoggingProperties = cmd.get_models(
        'ConnectedRegistryUpdateParameters', 'SyncUpdateProperties', 'LoggingProperties')
    connected_registry_update_parameters = ConnectedRegistryUpdateParameters(
        sync_properties=SyncUpdateProperties(
            schedule=sync_schedule,
            message_ttl=sync_message_ttl,
            sync_window=sync_window
        ),
        logging=LoggingProperties(
            log_level=log_level,
            audit_log_status=sync_audit_logs_enabled
        ),
        client_token_ids=client_token_list,
        notifications_list=notifications_list
    )

    try:
        return client.begin_update(resource_group_name=resource_group_name,
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
    extraMsg = ""
    if not cleanup:
        extraMsg = " without cleanup flag enabled"
    user_confirmation("Are you sure you want to delete the connected registry '{}' in '{}'{}?".format(
        connected_registry_name, registry_name, extraMsg), yes)
    try:
        connected_registry = acr_connected_registry_show(
            cmd, client, connected_registry_name, registry_name, resource_group_name)
        result = client.begin_delete(resource_group_name, registry_name, connected_registry_name)
        sync_token = get_token_from_id(cmd, connected_registry.parent.sync_properties.token_id)
        sync_token_name = sync_token.name
        sync_scope_map_name = sync_token.scope_map_id.split('/scopeMaps/')[1]
        if cleanup:
            from .token import acr_token_delete
            from .scope_map import acr_scope_map_delete
            token_client = cf_acr_tokens(cmd.cli_ctx)
            scope_map_client = cf_acr_scope_maps(cmd.cli_ctx)

            # Delete target sync scope map and token.
            acr_token_delete(cmd, token_client, registry_name, sync_token_name, yes, resource_group_name)
            acr_scope_map_delete(cmd, scope_map_client, registry_name, sync_scope_map_name, yes, resource_group_name)
            # Cleanup gateway permissions from ancestors
            connected_registry_list = list(client.list(resource_group_name, registry_name))
            family_tree, _ = _get_family_tree(connected_registry_list, None)
            _update_ancestor_permissions(cmd, family_tree, resource_group_name, registry_name,
                                         connected_registry.parent.id, connected_registry_name, remove_access=True)
        else:
            msg = "Connected registry successfully deleted. Please cleanup your sync tokens and scope maps. " + \
                "Run the following commands for cleanup: \n\t" + \
                "az acr token delete -n {} -r {} --yes\n\t".format(sync_token_name, registry_name) + \
                "az acr scope-map delete -n {} -r {} --yes\n".format(sync_scope_map_name, registry_name) + \
                "Run the following command on all ascendency to remove the deleted registry gateway access: \n\t" + \
                "az acr scope-map update -n <scope-map-name> -r {} --remove-gateway {}".format(
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

    user_confirmation("Are you sure you want to deactivate the connected registry '{}' in '{}'?".format(
        connected_registry_name, registry_name), yes)
    return client.begin_deactivate(resource_group_name=resource_group_name,
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
        family_tree, parent = _get_family_tree(connected_registry_list, parent_name)
        if parent is None:
            raise CLIError("Parent connected registry '{}' doesn't exist.".format(parent_name))
        result = _get_descendants(family_tree, parent.id)
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

    result = []
    if current_connected_registry.client_token_ids is None:
        return result

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

    if not any(option for option in ConnectedRegistryModes if option.value == mode):
        raise CLIError("usage error: --mode supports only 'ReadWrite' and 'ReadOnly' values.")
    repository_actions_list = [[repo] + REPO_SCOPES_BY_MODE[mode] for repo in repositories]
    gateway_actions_list = [[connected_registry_name.lower()] + DEFAULT_GATEWAY_SCOPE]
    try:
        message = "Created by connected registry sync token: {}"
        sync_scope_map_name = connected_registry_name
        logger.warning("If sync scope map '%s' already exists, its actions will be overwritten", sync_scope_map_name)
        sync_scope_map = create_default_scope_map(cmd, resource_group_name, registry_name, sync_scope_map_name,
                                                  repository_actions_list, gateway_actions_list,
                                                  scope_map_description=message.format(connected_registry_name),
                                                  force=True)

        sync_token_name = connected_registry_name
        logger.warning("If sync token '%s' already exists, it properties will be overwritten", sync_token_name)
        Token = cmd.get_models('Token')
        poller = token_client.begin_create(
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


def _get_family_tree(connected_registry_list, target_connected_registry_name):
    family_tree = {}
    targetConnectedRegistry = None
    # Populate the dictionary
    for ConnectedRegistry in connected_registry_list:
        family_tree[ConnectedRegistry.id] = {
            "connectedRegistry": ConnectedRegistry,
            "children": []
        }
        if ConnectedRegistry.name == target_connected_registry_name:
            targetConnectedRegistry = ConnectedRegistry

    # Populate Children dependencies
    for ConnectedRegistry in connected_registry_list:
        parent_id = ConnectedRegistry.parent.id
        if parent_id and not parent_id.isspace():
            family_tree[parent_id]["children"].append(ConnectedRegistry.id)
    return family_tree, targetConnectedRegistry


def _get_descendants(family_tree, parent_id):
    children = family_tree[parent_id]['children']
    result = []
    for child_id in children:
        result = [family_tree[child_id]["connectedRegistry"]]
        descendants = _get_descendants(family_tree, child_id)
        if descendants:
            result.extend(descendants)
    return result


# region connected-registry install subgroup
def acr_connected_registry_install_info(cmd,
                                        client,
                                        connected_registry_name,
                                        registry_name,
                                        parent_protocol,
                                        resource_group_name=None):
    return acr_connected_registry_get_settings(cmd, client, connected_registry_name, registry_name, parent_protocol,
                                               None, False, resource_group_name)


def acr_connected_registry_install_renew_credentials(cmd,
                                                     client,
                                                     connected_registry_name,
                                                     registry_name,
                                                     parent_protocol,
                                                     yes=False,
                                                     resource_group_name=None):
    return acr_connected_registry_get_settings(cmd, client, connected_registry_name, registry_name, parent_protocol,
                                               '1', yes, resource_group_name)


def acr_connected_registry_get_settings(cmd,
                                        client,
                                        connected_registry_name,
                                        registry_name,
                                        parent_protocol,
                                        generate_password=None,
                                        yes=False,
                                        resource_group_name=None):
    _, resource_group_name = validate_managed_registry(
        cmd, registry_name, resource_group_name)
    connected_registry = acr_connected_registry_show(
        cmd, client, connected_registry_name, registry_name, resource_group_name)

    sync_token_name = connected_registry.parent.sync_properties.token_id.split('/tokens/')[1]
    if generate_password:
        user_confirmation("Are you sure you want to generate a new sync token '{}' password{}?".format(
                          sync_token_name, generate_password), yes)
        from ._client_factory import cf_acr_token_credentials
        from .token import acr_token_credential_generate
        cred_client = cf_acr_token_credentials(cmd.cli_ctx)
        if generate_password == '1':
            password1 = True
            password2 = False
        else:
            password1 = False
            password2 = True

        poller = acr_token_credential_generate(
            cmd, cred_client, registry_name, sync_token_name,
            password1=password1, password2=password2, resource_group_name=resource_group_name)
        credentials = LongRunningOperation(cmd.cli_ctx)(poller)
        sync_username = credentials.username
        if credentials.passwords[0].name.endswith(generate_password):
            sync_password = credentials.passwords[0].value
        else:
            sync_password = credentials.passwords[1].value
        logger.warning('Please store your generated credentials safely.')
    else:
        sync_username = sync_token_name
        sync_password = "<use --generate-password to generate a new password>"

    parent_gateway_endpoint = connected_registry.parent.sync_properties.gateway_endpoint
    if parent_gateway_endpoint is None or parent_gateway_endpoint == '':
        parent_gateway_endpoint = "<parent gateway endpoint>"
    parent_id = connected_registry.parent.id
    # if parent_id is not none, parent is a connected registry
    if parent_id:
        parent_endpoint_protocol = parent_protocol
    # if parent_id is none, parent is a cloud registry
    else:
        if parent_protocol != "https":
            logger.warning("Parent endpoint protocol must be 'https' when parent is a cloud registry.")
        parent_endpoint_protocol = "https"
    connected_registry_login_server = "<Optional: connected registry login server. " + \
        "More info at https://aka.ms/acr/connected-registry>"
    connection_string = "ConnectedRegistryName=%s;" % connected_registry_name + \
        "SyncTokenName=%s;SyncTokenPassword=%s;" % (sync_username, sync_password) + \
        "ParentGatewayEndpoint=%s;ParentEndpointProtocol=%s" % (parent_gateway_endpoint, parent_endpoint_protocol)
    return {
        "SYNC_TOKEN_USER": sync_username,
        "SYNC_TOKEN_PASSWORD": sync_password,
        "ACR_REGISTRY_CERTIFICATE_VOLUME": "/var/acr/certs",
        "ACR_REGISTRY_DATA_VOLUME": "/var/acr/data",
        "ACR_REGISTRY_CONNECTION_STRING": connection_string,
        "ACR_REGISTRY_LOGIN_SERVER": connected_registry_login_server
    }
# endregion


def _update_ancestor_permissions(cmd,
                                 family_tree,
                                 resource_group_name,
                                 registry_name,
                                 parent_id,
                                 gateway,
                                 repositories=None,
                                 mode=None,
                                 remove_access=False):
    gateway_actions_list = [[gateway.lower()] + DEFAULT_GATEWAY_SCOPE]
    repo_msg = ""
    if repositories is not None:
        repository_actions_list = [[repo] + REPO_SCOPES_BY_MODE[mode] for repo in repositories]
        repo_msg = ", ".join(repositories)
        repo_msg = " and repo(s) '{}' {} permissions".format(repo_msg, mode)
    if remove_access:
        action_txt = "Removing"
        add_actions_set = set()
        remove_actions_set = set(parse_scope_map_actions(gateway_actions_list=gateway_actions_list))
    else:
        action_txt = "Adding"
        add_actions_set = set(parse_scope_map_actions(repository_actions_list, gateway_actions_list))
        remove_actions_set = set()

    while parent_id and not parent_id.isspace():
        ancestor = family_tree[parent_id]["connectedRegistry"]
        msg = "{} '{}' gateway permissions{} to connected registry '{}' sync scope map.".format(
            action_txt, gateway, repo_msg, ancestor.name)
        _update_repo_permissions(cmd, resource_group_name, registry_name,
                                 ancestor, add_actions_set, remove_actions_set, msg=msg)
        parent_id = ancestor.parent.id


# region connected-registry repo update
def _update_repo_permissions(cmd,
                             resource_group_name,
                             registry_name,
                             connected_registry,
                             add_actions_set,
                             remove_actions_set,
                             msg=None,
                             description=None):
    scope_map_client = cf_acr_scope_maps(cmd.cli_ctx)
    sync_token = get_token_from_id(cmd, connected_registry.parent.sync_properties.token_id)
    sync_scope_map = get_scope_map_from_id(cmd, sync_token.scope_map_id)
    sync_scope_map_name = sync_scope_map.name
    current_actions_set = set(sync_scope_map.actions)
    final_actions_set = current_actions_set.union(add_actions_set).difference(remove_actions_set)
    if final_actions_set == current_actions_set:
        return None
    current_actions = list(final_actions_set)
    logger.warning(msg)

    ScopeMapUpdateParameters = cmd.get_models('ScopeMapUpdateParameters')
    scope_map_update_parameters = ScopeMapUpdateParameters(
        description=description,
        actions=current_actions
    )

    poller = scope_map_client.begin_update(
        resource_group_name,
        registry_name,
        sync_scope_map_name,
        scope_map_update_parameters
    )
    return LongRunningOperation(cmd.cli_ctx)(poller)


def _get_scope_map_actions_set(repos, actions):
    for i, repo_name in enumerate(repos):
        repos[i] = [repo_name] + actions
    return set(parse_scope_map_actions(repos))


def acr_connected_registry_permissions_show(cmd,
                                            client,
                                            connected_registry_name,
                                            registry_name,
                                            resource_group_name=None):
    _, resource_group_name = validate_managed_registry(
        cmd, registry_name, resource_group_name)
    connected_registry = acr_connected_registry_show(
        cmd, client, connected_registry_name, registry_name, resource_group_name)
    sync_token = get_token_from_id(cmd, connected_registry.parent.sync_properties.token_id)
    return get_scope_map_from_id(cmd, sync_token.scope_map_id)


def acr_connected_registry_permissions_update(cmd,
                                              client,
                                              connected_registry_name,
                                              registry_name,
                                              add_repos=None,
                                              remove_repos=None,
                                              resource_group_name=None):
    if not (add_repos or remove_repos):
        raise CLIError('No repository permissions to update.')
    _, resource_group_name = validate_managed_registry(
        cmd, registry_name, resource_group_name)

    add_repos_set = set(add_repos) if add_repos is not None else set()
    remove_repos_set = set(remove_repos) if remove_repos is not None else set()
    duplicate_repos = set.intersection(add_repos_set, remove_repos_set)
    if duplicate_repos:
        errors = sorted(map(lambda action: action[action.rfind('/') + 1:], duplicate_repos))
        raise CLIError(
            'Update ambiguity. Duplicate repository names were provided with ' +
            '--add and --remove arguments.\n{}'.format(errors))

    connected_registry_list = list(client.list(resource_group_name, registry_name))
    family_tree, target_connected_registry = _get_family_tree(connected_registry_list, connected_registry_name)
    if target_connected_registry is None:
        raise CLIError("Connected registry '{}' doesn't exist.".format(connected_registry_name))

    # remove repo permissions from connected registry descendants.
    remove_actions = REPO_SCOPES_BY_MODE[ConnectedRegistryModes.READWRITE.value]
    if remove_repos is not None:
        remove_repos_txt = ", ".join(remove_repos)
        remove_repos_set = _get_scope_map_actions_set(remove_repos, remove_actions)
        descendants = _get_descendants(family_tree, target_connected_registry.id)
        for connected_registry in descendants:
            msg = "Removing '{}' repository permissions from {}".format(remove_repos_txt, connected_registry.name)
            _update_repo_permissions(cmd, resource_group_name, registry_name,
                                     connected_registry, set(), remove_repos_set, msg=msg)
    else:
        remove_repos_set = set()

    # add repo permissions to ancestors.
    add_actions = REPO_SCOPES_BY_MODE[target_connected_registry.mode.lower()]
    if add_repos is not None:
        add_repos_txt = ", ".join(add_repos)
        add_repos_set = _get_scope_map_actions_set(add_repos, add_actions)
        parent_id = target_connected_registry.parent.id
        while parent_id and not parent_id.isspace():
            connected_registry = family_tree[parent_id]["connectedRegistry"]
            msg = "Adding '{}' repository permissions to {}".format(add_repos_txt, connected_registry.name)
            _update_repo_permissions(cmd, resource_group_name, registry_name,
                                     connected_registry, add_repos_set, set(), msg=msg)
            parent_id = connected_registry.parent.id
    else:
        add_repos_set = set()

    # update target connected registry repo permissions.
    if add_repos and remove_repos:
        msg = "Adding '{}' and removing '{}' repository permissions in {}".format(
            add_repos_txt, remove_repos_txt, target_connected_registry.name)
    elif add_repos:
        msg = "Adding '{}' repository permissions to {}".format(add_repos_txt, target_connected_registry.name)
    else:
        msg = "Removing '{}' repository permissions from {}".format(remove_repos_txt, target_connected_registry.name)
    _update_repo_permissions(cmd, resource_group_name, registry_name,
                             target_connected_registry, add_repos_set, remove_repos_set, msg=msg)
# endregion
