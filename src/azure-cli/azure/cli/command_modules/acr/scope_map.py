# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from enum import Enum
from azure.cli.core.util import CLIError
from ._utils import get_resource_group_name_by_registry_name, parse_actions_from_repositories


class ScopeMapActions(Enum):
    CONTENT_DELETE = 'content/delete'
    CONTENT_READ = 'content/read'
    CONTENT_WRITE = 'content/write'
    METADATA_READ = 'metadata/read'
    METADATA_WRITE = 'metadata/write'


def acr_scope_map_create(cmd,
                         client,
                         registry_name,
                         scope_map_name,
                         repository_actions_list,
                         resource_group_name=None,
                         description=None):

    resource_group_name = get_resource_group_name_by_registry_name(cmd.cli_ctx, registry_name, resource_group_name)

    actions = parse_actions_from_repositories(repository_actions_list)

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

    if not (add_repository or remove_repository or description):
        raise CLIError('No scope map properties to update.')

    resource_group_name = get_resource_group_name_by_registry_name(cmd.cli_ctx, registry_name, resource_group_name)

    current_scope_map = acr_scope_map_show(cmd, client, registry_name, scope_map_name, resource_group_name)
    current_actions = current_scope_map.actions

    if add_repository or remove_repository:
        add_actions_set = set(parse_actions_from_repositories(add_repository)) if add_repository else set()
        remove_actions_set = set(parse_actions_from_repositories(remove_repository)) if remove_repository else set()

        # Duplicate actions can lead to inconsistency based on order of operations (set subtraction isn't associative).
        # Eg: ({A, B} - {B}) U {B, C} = {A, B, C},  ({A, B} U {B, C}) - {B}  = {A, C}
        duplicate_actions = set.intersection(add_actions_set, remove_actions_set)
        if duplicate_actions:
            # Display these actions to users: remove 'repositories/' prefix from 'repositories/<repo>/<action>'
            errors = sorted(map(lambda action: action[action.find('/') + 1:], duplicate_actions))
            raise CLIError(
                'Update ambiguity. Duplicate actions were provided with --add and --remove arguments.\n{}'
                .format(errors))

        final_actions_set = set(current_scope_map.actions).union(add_actions_set).difference(remove_actions_set)
        current_actions = list(final_actions_set)

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
