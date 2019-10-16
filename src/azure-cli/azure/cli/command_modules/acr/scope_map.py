# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.util import CLIError
from ._utils import get_resource_group_name_by_registry_name, validate_premium_registry

REPOSITORIES = 'repositories'


def _parse_actions_from_repositories(allow_or_remove_repository):
    actions = []
    for rule in allow_or_remove_repository:
        repository = rule[0]
        if len(rule) < 2:
            raise CLIError('At least one action must be specified with the repository {}.'.format(repository))
        for action in rule[1:]:
            actions.append('{}/{}/{}'.format(REPOSITORIES, repository, action))

    return actions


def acr_scope_map_create(cmd,
                         client,
                         registry_name,
                         scope_map_name,
                         add_repository,
                         resource_group_name=None,
                         description=None):

    validate_premium_registry(cmd, registry_name, resource_group_name)

    actions = _parse_actions_from_repositories(add_repository)

    resource_group_name = get_resource_group_name_by_registry_name(cmd.cli_ctx, registry_name, resource_group_name)

    return client.create(
        resource_group_name,
        registry_name,
        scope_map_name,
        actions,
        description
    )


def acr_scope_map_delete(cmd,
                         client,
                         registry_name,
                         scope_map_name,
                         yes=None,
                         resource_group_name=None):

    if not yes:
        from knack.prompting import prompt_y_n
        confirmation = prompt_y_n("Deleting the scope map '{}' will remove its permissions with associated tokens. "
                                  "Proceed?".format(scope_map_name))

        if not confirmation:
            return None

    resource_group_name = get_resource_group_name_by_registry_name(cmd.cli_ctx, registry_name, resource_group_name)
    return client.delete(resource_group_name, registry_name, scope_map_name)


def acr_scope_map_update(cmd,
                         client,
                         registry_name,
                         scope_map_name,
                         add_repository=None,
                         remove_repository=None,
                         resource_group_name=None,
                         description=None):

    resource_group_name = get_resource_group_name_by_registry_name(cmd.cli_ctx, registry_name, resource_group_name)
    current_scope_map = acr_scope_map_show(cmd, client, registry_name, scope_map_name, resource_group_name)
    current_actions = current_scope_map.actions

    if remove_repository:
        removed_actions = _parse_actions_from_repositories(remove_repository)
        # We have to treat actions case-insensitively but list them case-sensitively
        lower_current_actions = {action.lower() for action in current_actions}
        lower_removed_actions = {action.lower() for action in removed_actions}
        current_actions = [action for action in current_actions
                           if action.lower() in lower_current_actions - lower_removed_actions]

    if add_repository:
        added_actions = _parse_actions_from_repositories(add_repository)
        # We have to avoid duplicates and give preference to user input casing
        lower_action_to_action = {}
        for action in current_actions:
            lower_action_to_action[action.lower()] = action
        for action in added_actions:
            lower_action_to_action[action.lower()] = action
        current_actions = [lower_action_to_action[action] for action in lower_action_to_action]

    return client.update(
        resource_group_name,
        registry_name,
        scope_map_name,
        description,
        current_actions
    )


def acr_scope_map_show(cmd,
                       client,
                       registry_name,
                       scope_map_name,
                       resource_group_name=None):

    resource_group_name = get_resource_group_name_by_registry_name(cmd.cli_ctx, registry_name, resource_group_name)

    return client.get(
        resource_group_name,
        registry_name,
        scope_map_name
    )


def acr_scope_map_list(cmd,
                       client,
                       registry_name,
                       resource_group_name=None):

    resource_group_name = get_resource_group_name_by_registry_name(cmd.cli_ctx, registry_name, resource_group_name)

    return client.list(
        resource_group_name,
        registry_name
    )
