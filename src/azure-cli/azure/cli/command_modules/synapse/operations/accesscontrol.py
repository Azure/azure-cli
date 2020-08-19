# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError
from azure.synapse.accesscontrol.models import RoleAssignmentOptions
from azure.cli.core.util import is_guid
from azure.graphrbac.models import GraphErrorException
from msrestazure.azure_exceptions import CloudError
from .._client_factory import cf_synapse_client_accesscontrol_factory, cf_graph_client_factory


# List Synapse Role Assignment
def list_role_assignments(cmd, workspace_name, role=None, assignee=None):
    # get role id
    role_id = _resolve_role_id(cmd, role, workspace_name)
    # get object_id
    object_id = _resolve_object_id(cmd, assignee, fallback_to_object_id=True)

    client = cf_synapse_client_accesscontrol_factory(cmd.cli_ctx, workspace_name)
    role_assignments = client.get_role_assignments(role_id, object_id)

    # TODO:
    # Currently, when only `ObjectId` is specified, the cmdlet returns incorrect result.
    # Filter from client side as a workaround
    if object_id:
        role_assignments = [x for x in role_assignments if x.principal_id == object_id]
    return role_assignments


# Show Synapse Role Assignment By Id
def get_role_assignment_by_id(cmd, workspace_name, role_assignment_id):
    client = cf_synapse_client_accesscontrol_factory(cmd.cli_ctx, workspace_name)
    return client.get_role_assignment_by_id(role_assignment_id)


# Delete Synapse Role Assignment
def delete_role_assignment_by_id(cmd, workspace_name, ids=None, assignee=None, role=None, delete_all=None):
    client = cf_synapse_client_accesscontrol_factory(cmd.cli_ctx, workspace_name)
    ids = ids or []
    if ids:
        if assignee or role or delete_all:
            raise CLIError('When assignment --ids are used, other parameter values are not required')
        role_assignments = list_role_assignments(cmd, workspace_name, None, None)
        assignment_id_list = [x.id for x in role_assignments]
        # check role assignment id
        for i in ids:
            if i not in assignment_id_list:
                raise CLIError("role assigment id:'{}' doesn't exist.".format(i))
        # delete all ids when check pass
        for i in ids:
            client.delete_role_assignment_by_id(i)
        return

    if delete_all:
        if ids or role or delete_all:
            raise CLIError('When assignment --all are used, other parameter values are not required')

    if not any([ids, assignee, role, delete_all]):
        from knack.prompting import prompt_y_n
        msg = 'This will delete all role assignments under the workspace. Are you sure?'
        if not prompt_y_n(msg, default="n"):
            return

    role_assignments = list_role_assignments(cmd, workspace_name, role, assignee)
    if role_assignments:
        for a in role_assignments:
            client.delete_role_assignment_by_id(a.id)
    else:
        raise CLIError('No matched assignments were found to delete')


# Create Synapse Role Assignment
def create_role_assignment(cmd, workspace_name, role, assignee):
    # get role id
    role_id = _resolve_role_id(cmd, role, workspace_name)
    # get object_id
    object_id = _resolve_object_id(cmd, assignee, fallback_to_object_id=True)

    create_role_assignment_options = RoleAssignmentOptions(
        role_id=role_id,
        principal_id=object_id
    )
    assignment_client = cf_synapse_client_accesscontrol_factory(cmd.cli_ctx, workspace_name)
    return assignment_client.create_role_assignment(create_role_assignment_options)


# List Synapse Role Definitions
def list_role_definitions(cmd, workspace_name):
    client = cf_synapse_client_accesscontrol_factory(cmd.cli_ctx, workspace_name)
    return client.get_role_definitions()


# Get Synapse Role Definition
def get_role_definition(cmd, workspace_name, role):
    role_id = _resolve_role_id(cmd, role, workspace_name)
    client = cf_synapse_client_accesscontrol_factory(cmd.cli_ctx, workspace_name)
    return client.get_role_definition_by_id(role_id)


def _resolve_role_id(cmd, role, workspace_name):
    role_id = None
    if not role:
        return role_id
    if is_guid(role):
        role_id = role
    else:
        role_definition_client = cf_synapse_client_accesscontrol_factory(cmd.cli_ctx, workspace_name)
        role_definition = role_definition_client.get_role_definitions()
        role_dict = {x.name.lower(): x.id for x in role_definition if x.name}
        if role.lower() not in role_dict:
            raise CLIError("Role '{}' doesn't exist.".format(role))
        role_id = role_dict[role.lower()]
    return role_id


def _resolve_object_id(cmd, assignee, fallback_to_object_id=False):
    if not assignee:
        return None
    client = cf_graph_client_factory(cmd.cli_ctx)
    result = None
    try:
        if assignee.find('@') >= 0:  # looks like a user principal name
            result = list(client.users.list(filter="userPrincipalName eq '{}'".format(assignee)))
        if not result:
            result = list(client.service_principals.list(
                filter="servicePrincipalNames/any(c:c eq '{}')".format(assignee)))
        if not result and is_guid(assignee):
            return assignee

        # 2+ matches should never happen, so we only check 'no match' here
        if not result:
            raise CLIError("Cannot find user or service principal in graph database for '{assignee}'. "
                           "If the assignee is an appId, make sure the corresponding service principal is created "
                           "with 'az ad sp create --id {assignee}'.".format(assignee=assignee))

        return result[0].object_id
    except (CloudError, GraphErrorException):
        if fallback_to_object_id and is_guid(assignee):
            return assignee
        raise
