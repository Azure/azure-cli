# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError
from azure.cli.core.azclierror import InvalidArgumentValueError, ArgumentUsageError
from azure.cli.core.util import is_guid
from azure.cli.command_modules.role import GraphError
from .._client_factory import cf_synapse_role_assignments, cf_synapse_role_definitions, cf_graph_client_factory
from ..constant import ITEM_NAME_MAPPING
import azure.cli.command_modules.synapse.custom_help as cust_help


# List Synapse Role Assignment
def list_role_assignments(cmd, workspace_name, role=None, assignee=None, assignee_object_id=None,
                          scope=None, item=None, item_type=None):
    if bool(assignee) and bool(assignee_object_id):
        raise ArgumentUsageError('usage error: --assignee STRING | --assignee-object-id GUID')

    if bool(item) != bool(item_type):
        raise ArgumentUsageError('usage error: --item-type STRING --item STRING')

    return _list_role_assignments(cmd, workspace_name, role, assignee or assignee_object_id,
                                  scope, resolve_assignee=(not assignee_object_id), item=item, item_type=item_type)


def _list_role_assignments(cmd, workspace_name, role=None, assignee=None, scope=None,
                           resolve_assignee=True, item=None, item_type=None):
    """Prepare scope, role ID and resolve object ID from Graph API."""
    if any([scope, item, item_type]):
        scope = _build_role_scope(workspace_name, scope, item, item_type)
    role_id = _resolve_role_id(cmd, role, workspace_name)
    object_id = _resolve_object_id(cmd, assignee, fallback_to_object_id=True) if resolve_assignee else assignee
    client = cf_synapse_role_assignments(cmd.cli_ctx, workspace_name)
    token = ""
    result = []
    while True:
        request = client.list_role_assignments(role_id, object_id, scope, continuation_token_parameter=token,
                                               cls=cust_help.get_deserialized_and_headers)
        token = request[1]['x-ms-continuation']
        result += request[0].value
        if not token:
            break
    return result


# Show Synapse Role Assignment By Id
def get_role_assignment_by_id(cmd, workspace_name, role_assignment_id):
    client = cf_synapse_role_assignments(cmd.cli_ctx, workspace_name)
    return client.get_role_assignment_by_id(role_assignment_id)


# Delete Synapse Role Assignment
def delete_role_assignment(cmd, workspace_name, ids=None, assignee=None, assignee_object_id=None, role=None,
                           scope=None, item=None, item_type=None):
    client = cf_synapse_role_assignments(cmd.cli_ctx, workspace_name)
    if not any([ids, assignee, assignee_object_id, role, scope, item, item_type]):
        raise ArgumentUsageError('usage error: No argument are provided. --assignee STRING | --ids GUID')

    if ids:
        if any([assignee, assignee_object_id, role, scope, item, item_type]):
            raise ArgumentUsageError('You should not provide --role or --assignee or --assignee_object_id '
                                     'or --scope or --principal-type when --ids is provided.')
        role_assignments = list_role_assignments(cmd, workspace_name, None, None, None, None, None, None)
        assignment_id_list = [x.id for x in role_assignments]
        # check role assignment id
        for assignment_id in ids:
            if assignment_id not in assignment_id_list:
                raise ArgumentUsageError("role assignment id:'{}' doesn't exist.".format(assignment_id))
        # delete when all ids check pass
        for assignment_id in ids:
            client.delete_role_assignment_by_id(assignment_id)
        return

    role_assignments = list_role_assignments(cmd, workspace_name, role, assignee, assignee_object_id,
                                             scope, item, item_type)
    if any([scope, item, item_type]):
        scope = _build_role_scope(workspace_name, scope, item, item_type)
        role_assignments = [x for x in role_assignments if x.scope == scope]

    if role_assignments:
        for assignment in role_assignments:
            client.delete_role_assignment_by_id(assignment.id)
    else:
        raise CLIError('No matched assignments were found to delete, please provide correct --role or --assignee.'
                       'Use `az synapse role assignment list` to get role assignments.')


def create_role_assignment(cmd, workspace_name, role, assignee=None, assignee_object_id=None,
                           scope=None, assignee_principal_type=None, item_type=None, item=None, assignment_id=None):
    """Check parameters are provided correctly, then call _create_role_assignment."""
    if assignment_id and not is_guid(assignment_id):
        raise InvalidArgumentValueError('usage error: --id GUID')

    if bool(assignee) == bool(assignee_object_id):
        raise ArgumentUsageError('usage error: --assignee STRING | --assignee-object-id GUID')

    if assignee_principal_type and not assignee_object_id:
        raise ArgumentUsageError('usage error: --assignee-object-id GUID [--assignee-principal-type]')

    if bool(item) != bool(item_type):
        raise ArgumentUsageError('usage error: --item-type STRING --item STRING')

    try:
        return _create_role_assignment(cmd, workspace_name, role, assignee or assignee_object_id, scope, item,
                                       item_type, resolve_assignee=(not assignee_object_id),
                                       assignee_principal_type=assignee_principal_type, assignment_id=assignment_id)
    except Exception as ex:  # pylint: disable=broad-except
        if _error_caused_by_role_assignment_exists(ex):  # for idempotent
            return list_role_assignments(cmd, workspace_name, role=role,
                                         assignee=assignee, assignee_object_id=assignee_object_id,
                                         scope=scope, item=item, item_type=item_type)
        raise


def _resolve_object_id(cmd, assignee, fallback_to_object_id=False):
    if assignee is None:
        return None
    client = cf_graph_client_factory(cmd.cli_ctx)
    result = None
    try:
        result = list(client.user_list(filter="userPrincipalName eq '{0}' or mail eq '{0}' or displayName eq '{0}'"
                                       .format(assignee)))
        if not result:
            result = list(client.service_principal_list(filter="displayName eq '{}'".format(assignee)))
        if not result:
            result = list(client.group_list(filter="mail eq '{}'".format(assignee)))
        if not result and is_guid(assignee):  # assume an object id, let us verify it
            result = _get_object_stubs(client, [assignee])

        # 2+ matches should never happen, so we only check 'no match' here
        if not result:
            raise CLIError("Cannot find user or group or service principal in graph database for '{assignee}'. "
                           "If the assignee is a principal id, make sure the corresponding principal is created "
                           "with 'az ad sp create --id {assignee}'.".format(assignee=assignee))

        if len(result) > 1:
            raise CLIError("Find more than one user or group or service principal in graph database for '{assignee}'. "
                           "Please using --assignee-object-id GUID to specify assignee accurately"
                           .format(assignee=assignee))

        return result[0]["id"]
    except GraphError:
        if fallback_to_object_id and is_guid(assignee):
            return assignee
        raise


def _get_object_stubs(graph_client, assignees):
    result = []
    assignees = list(assignees)  # callers could pass in a set
    for i in range(0, len(assignees), 1000):
        body = {"ids": assignees[i:i + 1000],
                "types": ['user', 'group', 'servicePrincipal', 'directoryObjectPartnerReference']}
        result.extend(list(graph_client.directory_object_get_by_ids(body)))
    return result


def _error_caused_by_role_assignment_exists(ex):
    return getattr(ex, 'status_code', None) == 409 and ex.error.code == 'RoleAssignmentExists'


def _create_role_assignment(cmd, workspace_name, role, assignee, scope=None, item=None, item_type=None,
                            resolve_assignee=True, assignee_principal_type=None, assignment_id=None):
    """Prepare scope, role ID and resolve object ID from Graph API."""
    scope = _build_role_scope(workspace_name, scope, item, item_type)
    role_id = _resolve_role_id(cmd, role, workspace_name)
    object_id = _resolve_object_id(cmd, assignee, fallback_to_object_id=True) if resolve_assignee else assignee

    assignment_client = cf_synapse_role_assignments(cmd.cli_ctx, workspace_name)
    return assignment_client.create_role_assignment(assignment_id if assignment_id is not None else _gen_guid(),
                                                    role_id, object_id, scope, assignee_principal_type)


def _build_role_scope(workspace_name, scope, item, item_type):
    if scope:
        return scope

    if item and item_type:
        # workspaces/{workspaceName}/bigDataPools/{bigDataPoolName}
        scope = "workspaces/" + workspace_name + "/" + item_type + "/" + item
    else:
        scope = "workspaces/" + workspace_name

    return scope


def _resolve_role_id(cmd, role, workspace_name):
    role_id = None
    if not role:
        return role_id
    if is_guid(role):
        role_id = role
    else:
        role_definition_client = cf_synapse_role_definitions(cmd.cli_ctx, workspace_name)
        role_definition = role_definition_client.list_role_definitions()
        role_dict = {x.name.lower(): x.id for x in role_definition if x.name}
        if role.lower() not in role_dict:
            raise CLIError("Role '{}' doesn't exist.".format(role))
        role_id = role_dict[role.lower()]
    return role_id


def _gen_guid():
    import uuid
    return uuid.uuid4()


# List Synapse Role Definitions Scope
def list_scopes(cmd, workspace_name):
    client = cf_synapse_role_definitions(cmd.cli_ctx, workspace_name)
    return client.list_scopes()


# List Synapse Role Definitions
def list_role_definitions(cmd, workspace_name, is_built_in=None):
    client = cf_synapse_role_definitions(cmd.cli_ctx, workspace_name)
    role_definitions = client.list_role_definitions(is_built_in)
    return role_definitions


def _build_role_scope_format(scope, item_type):
    if scope:
        return scope

    if item_type:
        scope = "workspaces/{workspaceName}/" + item_type + "/" + ITEM_NAME_MAPPING[item_type]
    else:
        scope = "workspaces/{workspaceName}"

    return scope


# Get Synapse Role Definition
def get_role_definition(cmd, workspace_name, role):
    role_id = _resolve_role_id(cmd, role, workspace_name)
    client = cf_synapse_role_definitions(cmd.cli_ctx, workspace_name)
    return client.get_role_definition_by_id(role_id)
