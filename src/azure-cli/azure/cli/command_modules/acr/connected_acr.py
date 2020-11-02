# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from msrest.exceptions import ValidationError
from knack.log import get_logger
from knack.util import CLIError
from azure.cli.core.commands import LongRunningOperation
from azure.cli.core.commands.client_factory import get_subscription_id
from ._utils import (
    get_registry_by_name,
    validate_managed_registry,
    parse_actions_from_repositories,
    user_confirmation,
    create_default_scope_map
)


DEFAULT_GATEWAY_SCOPE = ['config/read', 'config/write', 'messages/read', 'messages/write']
MIRROR_REPO_SCOPE = ['content/read', 'metadata/read']
REGISTRY_REPO_SCOPE = ['content/read', 'content/write', 'content/delete', 'metadata/read', 'metadata/write']

logger = get_logger(__name__)


def acr_connected_acr_create(cmd,
                             client,
                             registry_name,
                             connected_acr_name,
                             repositories,
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

    token_id = _create_default_token(cmd, resource_group_name, registry_name,
                                     connected_acr_name, repositories, mode)

    SyncProperties, ParentProperties = cmd.get_models('SyncProperties', 'ParentProperties')
    sync_properties = SyncProperties(
        TokenId=token_id,
        Schedule=sync_schedule,
        MessageTtl=sync_message_ttl,
        SyncWindow=sync_window
    )
    parent_properties = ParentProperties(
        Id=registry.id,
        SyncProperties=sync_properties
    )

    ConnectedRegistry, LoggingProperties = cmd.get_models('ConnectedRegistry', 'LoggingProperties')
    connected_acr_create_parameters = ConnectedRegistry(
        ProvisioningState=None,
        Mode=mode,
        Parent=parent_properties,
        ClientTokenIds=None,
        Logging=LoggingProperties(
            LogLevel=log_level,
            Status='Enabled' if sync_audit_logs_enabled else 'Disabled'
        )
    )

    try:
        return client.create(subscriptionId=subscription_id,
                             resourceGroupName=resource_group_name,
                             registryName=registry_name,
                             connectedRegistryName=connected_acr_name,
                             connected_registry=connected_acr_create_parameters)
    except ValidationError as e:
        raise CLIError(e)


def acr_connected_acr_update(cmd,
                             client,
                             registry_name,
                             connected_acr_name,
                             repositories,
                             resource_group_name=None,
                             mode=None,
                             sync_schedule=None,
                             sync_window=None,
                             log_level=None,
                             sync_message_ttl=None,
                             sync_audit_logs_enabled=True):

    _, resource_group_name = validate_managed_registry(
        cmd, registry_name, resource_group_name)
    subscription_id = get_subscription_id(cmd.cli_ctx)

    token_id = _create_default_token(cmd, resource_group_name, registry_name,
                                     connected_acr_name, repositories, mode)

    ConnectedRegistryUpdateProperties, SyncProperties, LoggingProperties = cmd.get_models(
        'ConnectedRegistryUpdateProperties', 'SyncProperties', 'LoggingProperties')
    sync_properties = SyncProperties(
        Schedule=sync_schedule,
        MessageTtl=sync_message_ttl,
        SyncWindow=sync_window
    )
    logging_properties = LoggingProperties(
        LogLevel=log_level,
        Status='Enabled' if sync_audit_logs_enabled else 'Disabled'
    )

    connected_acr_update_parameters = ConnectedRegistryUpdateProperties(
        SyncProperties=sync_properties,
        Logging=logging_properties,
        ClientTokenIds=token_id
    )

    try:
        return client.update(subscriptionId=subscription_id,
                             resourceGroupName=resource_group_name,
                             registryName=registry_name,
                             connectedRegistryName=connected_acr_name,
                             connected_registry=connected_acr_update_parameters)
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
    subscription_id = get_subscription_id(cmd.cli_ctx)

    #TODO Delete tokens?
    user_confirmation("Are you sure you want to delete the Connected Registry '{}' from '{}'?".format(
        connected_acr_name, registry_name), yes)
    try:
        return client.delete(subscription_id, resource_group_name, registry_name, connected_acr_name)
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
    subscription_id = get_subscription_id(cmd.cli_ctx)
    #TODO Cascading logic and different formattings.
    return client.list(subscription_id, resource_group_name, registry_name)


def acr_connected_acr_show(cmd,
                           client,
                           connected_acr_name,
                           registry_name,
                           resource_group_name=None):
    _, resource_group_name = validate_managed_registry(
        cmd, registry_name, resource_group_name)
    subscription_id = get_subscription_id(cmd.cli_ctx)
    return client.get(subscription_id, resource_group_name, registry_name, connected_acr_name)

def _create_default_token(cmd,
                          resource_group_name,
                          registry_name,
                          connected_acr_name,
                          repositories,
                          mode):
    from ._client_factory import cf_acr_tokens
    token_client = cf_acr_tokens(cmd.cli_ctx)
    if mode == 'mirror':
        repo_scope = MIRROR_REPO_SCOPE
    elif mode == 'registry':
        repo_scope = REGISTRY_REPO_SCOPE
    else:
        raise CLIError("usage error: --mode supports only 'registry' and 'mirror' values.")
    repository_actions_list = []
    for repo in repositories:
        repo_action = [repo]
        repo_action.extend(repo_scope)
        repository_actions_list.append(repo_action)

    #TODO Add gateway scopeMap
    token_name = "{}-{}-tk".format(connected_acr_name, mode)
    scope_map_id = create_default_scope_map(cmd, resource_group_name, registry_name,
                                            token_name, repository_actions_list, logger)

    Token = cmd.get_models('Token')
    poller = token_client.create(
        resource_group_name,
        registry_name,
        token_name,
        Token(
            scope_map_id=scope_map_id,
            status="enabled"
        )
    )

    token = LongRunningOperation(cmd.cli_ctx)(poller)
    return token.id
