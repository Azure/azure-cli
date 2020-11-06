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
from ._client_factory import cf_acr_registries, cf_acr_tokens, cf_acr_scope_maps
from ._utils import (
    get_registry_by_name,
    validate_managed_registry,
    user_confirmation,
    create_default_scope_map,
    get_token_from_id,
    get_scope_map_from_id,
    parse_actions_from_repositories,
    parse_repositories_from_actions
)

class ConnectedRegistryModes(Enum):
    mirror = 'mirror'
    REGISTRY = 'registry'

DEFAULT_GATEWAY_SCOPE = ['config/read', 'config/write', 'messages/read', 'messages/write']
REPO_SCOPES_BY_MODE = {
    ConnectedRegistryModes.mirror.value: ['content/read', 'metadata/read'],
    ConnectedRegistryModes.REGISTRY.value: ['content/read', 'content/write', 'content/delete',
                                            'metadata/read', 'metadata/write']
}
SYNC_SCOPE_MAP_NAME = "{}-sync-scope-map"
SYNC_TOKEN_NAME = "{}-sync-token"
REPOSITORY = "repositories/"
GATEWAY = "gateway/"

logger = get_logger(__name__)


def acr_connected_acr_create(cmd,
                             client,
                             registry_name,
                             connected_acr_name,
                             repositories,
                             client_token_ids,
                             resource_group_name=None,
                             mode=None,
                             parent=None,
                             sync_schedule=None,
                             sync_message_ttl=None,
                             sync_window=None,
                             log_level=None,
                             sync_audit_logs_enabled=True):

    registry, resource_group_name = get_registry_by_name(
        cmd.cli_ctx, registry_name, resource_group_name)
    subscription_id = get_subscription_id(cmd.cli_ctx)

    parent_id = None
    if parent:
        #TODO parent sync token
        #parent_registry, parent_resource_group_name = get_registry_by_name(
        #    cmd.cli_ctx, parent, resource_group_name)
        parent_id = "{}/connectedRegistries/{}".format(registry.id, parent)
        #sync_token_id = _create_sync_token(cmd, parent_resource_group_name, parent_registry,
        sync_token_id = _create_sync_token(cmd, resource_group_name, registry_name,
                                           connected_acr_name, repositories, mode)
    else:
        sync_token_id = _create_sync_token(cmd, resource_group_name, registry_name,
                                           connected_acr_name, repositories, mode)

    from .azure.mgmt.containerregistry.v2020_11_01_preview.models import ParentProperties, SyncProperties
#    SyncProperties, ParentProperties = cmd.get_models('SyncProperties', 'ParentProperties')
    parent_properties = ParentProperties(
        id=parent_id,
        sync_properties=SyncProperties(
            token_id=sync_token_id,
            schedule=sync_schedule,
            message_ttl=sync_message_ttl,
            sync_window=sync_window
        )
    )

    from .azure.mgmt.containerregistry.v2020_11_01_preview.models import ConnectedRegistry, LoggingProperties
#    ConnectedRegistry, LoggingProperties = cmd.get_models('ConnectedRegistry', 'LoggingProperties')
    connected_acr_create_parameters = ConnectedRegistry(
        provisioning_state=None,
        mode=mode,
        parent=parent_properties,
        client_token_ids=client_token_ids,
        logging=LoggingProperties(
            log_level=log_level,
            audit_log_status='Enabled' if sync_audit_logs_enabled else 'Disabled'
        )
    )

    try:
        if not registry.data_endpoint_enabled:
            from .custom import acr_update_custom
            acr_update_custom(cmd, cf_acr_registries(cmd.cli_ctx), data_endpoint_enabled=True)

        return client.create(subscription_id=subscription_id,
                             resource_group_name=resource_group_name,
                             registry_name=registry_name,
                             connected_registry_name=connected_acr_name,
                             connected_registry_create_parameters=connected_acr_create_parameters)
    except ValidationError as e:
        raise CLIError(e)


def acr_connected_acr_update(cmd,
                             client,
                             registry_name,
                             connected_acr_name,
                             add_client_token_ids=None,
                             remove_client_token_ids=None,
                             add_repository=None,
                             remove_repository=None,
                             resource_group_name=None,
                             mode=None,
                             sync_schedule=None,
                             sync_window=None,
                             log_level=None,
                             sync_message_ttl=None,
                             sync_audit_logs_enabled=None):

    _, resource_group_name = validate_managed_registry(
        cmd, registry_name, resource_group_name)

    current_connected_acr = acr_connected_acr_show(cmd, client, connected_acr_name, registry_name, resource_group_name)
    current_mode = current_connected_acr.mode
    client_token_ids = current_connected_acr.client_token_ids
    sync_token_id = current_connected_acr.parent.sync_properties.token_id
    sync_audit_logs_enabled = sync_audit_logs_enabled if sync_audit_logs_enabled is not None else \
                              current_connected_acr.logging.audit_log_status

    # Add or remove from the current client token id list
    add_client_token_set = set(add_client_token_ids) if add_client_token_ids else set()
    remove_client_token_set = set(remove_client_token_ids) if remove_client_token_ids else set()
    duplicate_client_token = set.intersection(add_client_token_set, remove_client_token_set)
    if duplicate_client_token:
        errors = sorted(map(lambda action: action[action.find('/') + 1:], duplicate_client_token))
        raise CLIError(
            'Update ambiguity. Duplicate client token ids were provided with ' +
            '--add-client-token-ids and --remove-client-token-ids arguments.\n{}'.format(errors))
    client_token_ids = list(set(client_token_ids).union(add_client_token_set).difference(remove_client_token_set))

    from .azure.mgmt.containerregistry.v2020_11_01_preview.models import ConnectedRegistryUpdateParameters, SyncProperties, LoggingProperties
#    ConnectedRegistryUpdateParameters, SyncProperties, LoggingProperties = cmd.get_models(
#                'ConnectedRegistryUpdateParameters', 'SyncProperties', 'LoggingProperties')
    sync_properties = SyncProperties(
        token_id=sync_token_id,
        schedule=sync_schedule,
        message_ttl=sync_message_ttl,
        sync_window=sync_window
    )
    logging_properties = LoggingProperties(
        log_level=log_level,
        audit_log_status=sync_audit_logs_enabled
    )
    connected_acr_update_parameters = ConnectedRegistryUpdateParameters(
        sync_properties=sync_properties,
        logging=logging_properties,
        client_token_ids=client_token_ids
    )

    # Add or remove the repo permissions from the sync token scope map id
    if add_repository or remove_repository or mode:
        mode = mode if mode else current_mode
        _ = _update_sync_token_scope_map(cmd, resource_group_name, registry_name, connected_acr_name,
                                         sync_token_id, add_repository, remove_repository, mode)
    try:
        return client.update(resource_group_name=resource_group_name,
                             registry_name=registry_name,
                             connected_registry_name=connected_acr_name,
                             connected_registry_update_parameters=connected_acr_update_parameters)
    except ValidationError as e:
        raise CLIError(e)


def acr_connected_acr_delete(cmd,
                             client,
                             connected_acr_name,
                             registry_name,
                             yes=False,
                             resource_group_name=None):

    _, resource_group_name = validate_managed_registry(
        cmd, registry_name, resource_group_name)

    #TODO disable tokens
    user_confirmation("Are you sure you want to delete the Connected Registry '{}' from '{}'?".format(
        connected_acr_name, registry_name), yes)
    try:
        return client.delete(resource_group_name, registry_name, connected_acr_name)
    except ValidationError as e:
        raise CLIError(e)


def acr_connected_acr_list(cmd,
                           client,
                           registry_name,
                           parent=None,
                           cascading=False,
                           resource_group_name=None):
    _, resource_group_name = validate_managed_registry(
        cmd, registry_name, resource_group_name)
    #TODO Cascading logic and different formattings.
    return client.list(resource_group_name, registry_name)


def acr_connected_acr_show(cmd,
                           client,
                           connected_acr_name,
                           registry_name,
                           resource_group_name=None):
    _, resource_group_name = validate_managed_registry(
        cmd, registry_name, resource_group_name)
    return client.get(resource_group_name, registry_name, connected_acr_name)


def _create_sync_token(cmd,
                       resource_group_name,
                       registry_name,
                       connected_acr_name,
                       repositories,
                       mode):
    token_client = cf_acr_tokens(cmd.cli_ctx)

    mode = mode.lower()
    if not any(option for option in ConnectedRegistryModes if option.value == mode):
        raise CLIError("usage error: --mode supports only 'registry' and 'mirror' values.")
    repository_actions_list = [[repo] + REPO_SCOPES_BY_MODE[mode] for repo in repositories]
    gateway_actions_list = [[connected_acr_name] + DEFAULT_GATEWAY_SCOPE]

    try:
        scope_map_id = create_default_scope_map(cmd, resource_group_name, registry_name,
                                                SYNC_SCOPE_MAP_NAME.format(connected_acr_name),
                                                repository_actions_list, gateway_actions_list,
                                                "Created by connected registry: {}".format(connected_acr_name))

        Token = cmd.get_models('Token')
        poller = token_client.create(
            resource_group_name,
            registry_name,
            SYNC_TOKEN_NAME.format(connected_acr_name),
            Token(
                scope_map_id=scope_map_id,
                status="enabled"
            )
        )

        token = LongRunningOperation(cmd.cli_ctx)(poller)
        return token.id
    except ValidationError as e:
        raise CLIError(e)


def _update_sync_token_scope_map(cmd,
                                 resource_group_name,
                                 registry_name,
                                 connected_acr_name,
                                 sync_token_id,
                                 add_repository=None,
                                 remove_repository=None,
                                 mode=None):
    scope_map_client = cf_acr_scope_maps(cmd.cli_ctx)
    sync_token = get_token_from_id(cmd, sync_token_id)
    current_scope_map = get_scope_map_from_id(cmd, sync_token.scope_map_id)
    current_actions = current_scope_map.actions
    add_repo_set = set(add_repository) if add_repository else set()
    remove_repo_set = set(remove_repository) if remove_repository else set()
    duplicate_repos = set.intersection(add_repo_set, remove_repo_set)
    if duplicate_repos:
        errors = sorted(map(lambda action: action[action.find('/') + 1:], duplicate_repos))
        raise CLIError(
            'Update ambiguity. Duplicate repositories were provided with ' +
            '--add-repository and --remove-repository arguments.\n{}'.format(errors))

    repositories = parse_repositories_from_actions(current_actions)
    repositories = list(set(repositories).union(add_repo_set).difference(remove_repo_set))
    if not repositories:
        raise CLIError("Update blocked: all repository would be removed from the connected" +
                       "registry '{}'.The connected registry needs to ".format(connected_acr_name) +
                       "have access to at least one repository")
    repository_actions_list = [[repo] + REPO_SCOPES_BY_MODE[mode] for repo in repositories]
    actions_list = [repo for repo in current_actions if repo.startswith(GATEWAY)]
    actions_list += parse_actions_from_repositories(repository_actions_list)

    try:
        return scope_map_client.update(
            resource_group_name,
            registry_name,
            current_scope_map.name,
            current_scope_map.description,
            actions_list
        )
    except ValidationError as e:
        raise CLIError(e)
