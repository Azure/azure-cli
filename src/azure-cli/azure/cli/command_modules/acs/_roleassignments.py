# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import time
import uuid

from azure.cli.command_modules.acs._client_factory import get_auth_management_client, get_graph_rbac_management_client
from azure.cli.core.azclierror import AzCLIError
from azure.cli.core.profiles import ResourceType, get_sdk
from azure.core.exceptions import HttpResponseError
from azure.graphrbac.models import GetObjectsParameters
from knack.log import get_logger
from msrestazure.azure_exceptions import CloudError

logger = get_logger(__name__)


def _get_object_stubs(graph_client, assignees):
    params = GetObjectsParameters(include_directory_object_references=True,
                                  object_ids=assignees)
    return list(graph_client.objects.get_objects_by_object_ids(params))


def resolve_object_id(cli_ctx, assignee):
    client = get_graph_rbac_management_client(cli_ctx)
    result = None
    if assignee is None:
        raise AzCLIError('Inputted parameter "assignee" is None.')
    if assignee.find('@') >= 0:  # looks like a user principal name
        result = list(client.users.list(
            filter="userPrincipalName eq '{}'".format(assignee)))
    if not result:
        result = list(client.service_principals.list(
            filter="servicePrincipalNames/any(c:c eq '{}')".format(assignee)))
    if not result:  # assume an object id, let us verify it
        result = _get_object_stubs(client, [assignee])

    # 2+ matches should never happen, so we only check 'no match' here
    if not result:
        raise AzCLIError(
            "No matches in graph database for '{}'".format(assignee))

    return result[0].object_id


def resolve_role_id(role, scope, definitions_client):
    role_id = None
    try:
        uuid.UUID(role)
        role_id = role
    except ValueError:
        pass
    if not role_id:  # retrieve role id
        role_defs = list(definitions_client.list(
            scope, "roleName eq '{}'".format(role)))
        if len(role_defs) == 0:
            raise AzCLIError("Role '{}' doesn't exist.".format(role))
        if len(role_defs) > 1:
            ids = [r.id for r in role_defs]
            err = "More than one role matches the given name '{}'. Please pick a value from '{}'"
            raise AzCLIError(err.format(role, ids))
        role_id = role_defs[0].id
    return role_id


def build_role_scope(resource_group_name: str, scope: str, subscription_id: str):
    subscription_scope = '/subscriptions/' + subscription_id
    if scope is not None:
        if resource_group_name:
            err = 'Resource group "{}" is redundant because scope is supplied'
            raise AzCLIError(err.format(resource_group_name))
    elif resource_group_name:
        scope = subscription_scope + '/resourceGroups/' + resource_group_name
    else:
        scope = subscription_scope
    return scope


def create_role_assignment(
    cmd,
    role,
    assignee,
    is_service_principal,
    resource_group_name=None,
    scope=None,
    resolve_assignee=True,
):
    return _create_role_assignment(
        cmd,
        role,
        assignee,
        resource_group_name,
        scope,
        resolve_assignee=(is_service_principal and resolve_assignee),
    )


def _create_role_assignment(cmd, role, assignee,
                            resource_group_name=None, scope=None, resolve_assignee=True):
    factory = get_auth_management_client(cmd.cli_ctx, scope)
    assignments_client = factory.role_assignments
    definitions_client = factory.role_definitions

    # FIXME: is this necessary?
    if assignments_client.config is None:
        raise AzCLIError("Assignments client config is undefined.")

    scope = build_role_scope(
        resource_group_name, scope, assignments_client.config.subscription_id)

    # XXX: if role is uuid, this function's output cannot be used as role assignment defintion id
    # ref: https://github.com/Azure/azure-cli/issues/2458
    role_id = resolve_role_id(role, scope, definitions_client)

    # If the cluster has service principal resolve the service principal client id to get the object id,
    # if not use MSI object id.
    object_id = resolve_object_id(
        cmd.cli_ctx, assignee) if resolve_assignee else assignee

    assignment_name = uuid.uuid4()
    custom_headers = None

    RoleAssignmentCreateParameters = get_sdk(cmd.cli_ctx, ResourceType.MGMT_AUTHORIZATION,
                                             'RoleAssignmentCreateParameters', mod='models',
                                             operation_group='role_assignments')
    if cmd.supported_api_version(min_api='2018-01-01-preview', resource_type=ResourceType.MGMT_AUTHORIZATION):
        parameters = RoleAssignmentCreateParameters(
            role_definition_id=role_id, principal_id=object_id)
        return assignments_client.create(scope, assignment_name, parameters, custom_headers=custom_headers)

    # for backward compatibility
    RoleAssignmentProperties = get_sdk(cmd.cli_ctx, ResourceType.MGMT_AUTHORIZATION,
                                       'RoleAssignmentProperties', mod='models',
                                       operation_group='role_assignments')
    properties = RoleAssignmentProperties(role_definition_id=role_id, principal_id=object_id)
    return assignments_client.create(scope, assignment_name, properties, custom_headers=custom_headers)


def add_role_assignment(cmd, role, service_principal_msi_id, is_service_principal=True, delay=2, scope=None):
    # AAD can have delays in propagating data, so sleep and retry
    hook = cmd.cli_ctx.get_progress_controller(True)
    hook.add(message='Waiting for AAD role to propagate',
             value=0, total_val=1.0)
    logger.info('Waiting for AAD role to propagate')
    for x in range(0, 10):
        hook.add(message='Waiting for AAD role to propagate',
                 value=0.1 * x, total_val=1.0)
        try:
            # TODO: break this out into a shared utility library
            create_role_assignment(
                cmd, role, service_principal_msi_id, is_service_principal, scope=scope)
            break
        except (CloudError, HttpResponseError) as ex:
            if ex.message == 'The role assignment already exists.':
                break
            logger.info(ex.message)
        except Exception as ex:     # pylint: disable=broad-except
            logger.error(str(ex))
        time.sleep(delay + delay * x)
    else:
        return False
    hook.add(message='AAD role propagation done', value=1.0, total_val=1.0)
    logger.info('AAD role propagation done')
    return True
