# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import re
import time
import uuid

from azure.cli.command_modules.acs._client_factory import (
    cf_container_registry_service,
    get_auth_management_client,
    get_resource_by_name,
)
from azure.cli.command_modules.acs._consts import (
    CONST_MANAGED_IDENTITY_OPERATOR_ROLE,
    CONST_MANAGED_IDENTITY_OPERATOR_ROLE_ID,
    CONST_NETWORK_CONTRIBUTOR_ROLE_ID,
)
from azure.cli.command_modules.acs._graph import resolve_object_id
from azure.cli.command_modules.acs._helpers import get_property_from_dict_or_object
from azure.cli.core.azclierror import AzCLIError, UnauthorizedError
from azure.cli.core.profiles import ResourceType, get_sdk
from azure.core.exceptions import HttpResponseError
from knack.log import get_logger
from knack.prompting import prompt_y_n
from msrestazure.azure_exceptions import CloudError

logger = get_logger(__name__)


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


def add_role_assignment_executor(cmd, role, assignee, resource_group_name=None, scope=None, resolve_assignee=True):
    factory = get_auth_management_client(cmd.cli_ctx, scope)
    assignments_client = factory.role_assignments
    definitions_client = factory.role_definitions

    # FIXME: is this necessary?
    if assignments_client.config is None:
        raise AzCLIError("Assignments client config is undefined.")

    scope = build_role_scope(resource_group_name, scope, assignments_client.config.subscription_id)

    # XXX: if role is uuid, this function's output cannot be used as role assignment defintion id
    # ref: https://github.com/Azure/azure-cli/issues/2458
    role_id = resolve_role_id(role, scope, definitions_client)

    # If the cluster has service principal resolve the service principal client id to get the object id,
    # if not use MSI object id.
    object_id = resolve_object_id(cmd.cli_ctx, assignee) if resolve_assignee else assignee

    assignment_name = uuid.uuid4()
    custom_headers = None

    RoleAssignmentCreateParameters = get_sdk(
        cmd.cli_ctx,
        ResourceType.MGMT_AUTHORIZATION,
        "RoleAssignmentCreateParameters",
        mod="models",
        operation_group="role_assignments",
    )
    if cmd.supported_api_version(min_api="2018-01-01-preview", resource_type=ResourceType.MGMT_AUTHORIZATION):
        parameters = RoleAssignmentCreateParameters(role_definition_id=role_id, principal_id=object_id)
        return assignments_client.create(scope, assignment_name, parameters, custom_headers=custom_headers)

    # for backward compatibility
    RoleAssignmentProperties = get_sdk(
        cmd.cli_ctx,
        ResourceType.MGMT_AUTHORIZATION,
        "RoleAssignmentProperties",
        mod="models",
        operation_group="role_assignments",
    )
    properties = RoleAssignmentProperties(role_definition_id=role_id, principal_id=object_id)
    return assignments_client.create(scope, assignment_name, properties, custom_headers=custom_headers)


def add_role_assignment(cmd, role, service_principal_msi_id, is_service_principal=True, delay=2, scope=None):
    # AAD can have delays in propagating data, so sleep and retry
    hook = cmd.cli_ctx.get_progress_controller(True)
    hook.add(message="Waiting for AAD role to propagate", value=0, total_val=1.0)
    logger.info("Waiting for AAD role to propagate")
    for x in range(0, 10):
        hook.add(message="Waiting for AAD role to propagate", value=0.1 * x, total_val=1.0)
        try:
            # TODO: break this out into a shared utility library
            add_role_assignment_executor(
                cmd,
                role,
                service_principal_msi_id,
                scope=scope,
                resolve_assignee=is_service_principal,
            )
            break
        except (CloudError, HttpResponseError) as ex:
            if ex.message == "The role assignment already exists.":
                break
            logger.info(ex.message)
        except Exception as ex:  # pylint: disable=broad-except
            logger.error(str(ex))
        time.sleep(delay + delay * x)
    else:
        return False
    hook.add(message="AAD role propagation done", value=1.0, total_val=1.0)
    logger.info("AAD role propagation done")
    return True


def search_role_assignments(
    cli_ctx,
    assignments_client,
    definitions_client,
    scope,
    assignee,
    role,
    include_inherited,
    include_groups,
    is_service_principal=True,
):
    assignee_object_id = None
    if assignee:
        if is_service_principal:
            assignee_object_id = resolve_object_id(cli_ctx, assignee)
        else:
            assignee_object_id = assignee

    # always use "scope" if provided, so we can get assignments beyond subscription e.g. management groups
    if scope:
        assignments = list(assignments_client.list_for_scope(scope=scope, filter="atScope()"))
    elif assignee_object_id:
        if include_groups:
            f = "assignedTo('{}')".format(assignee_object_id)
        else:
            f = "principalId eq '{}'".format(assignee_object_id)
        assignments = list(assignments_client.list(filter=f))
    else:
        assignments = list(assignments_client.list())

    if assignments:
        assignments = [
            a
            for a in assignments
            if (
                not scope or
                include_inherited and
                re.match(get_property_from_dict_or_object(a, "scope"), scope, re.I) or
                get_property_from_dict_or_object(a, "scope").lower() == scope.lower()
            )
        ]

        if role:
            role_id = resolve_role_id(role, scope, definitions_client)
            assignments = [
                i for i in assignments if get_property_from_dict_or_object(i, "role_definition_id") == role_id
            ]

        if assignee_object_id:
            assignments = [
                i for i in assignments if get_property_from_dict_or_object(i, "principal_id") == assignee_object_id
            ]

    return assignments


def delete_role_assignments(cli_ctx, role, service_principal, delay=2, scope=None, is_service_principal=True):
    # AAD can have delays in propagating data, so sleep and retry
    hook = cli_ctx.get_progress_controller(True)
    hook.add(message="Waiting for AAD role to delete", value=0, total_val=1.0)
    logger.info("Waiting for AAD role to delete")
    for x in range(0, 10):
        hook.add(message="Waiting for AAD role to delete", value=0.1 * x, total_val=1.0)
        try:
            delete_role_assignments_executor(
                cli_ctx, role=role, assignee=service_principal, scope=scope, is_service_principal=is_service_principal
            )
            break
        except (CloudError, HttpResponseError) as ex:
            logger.info(ex.message)
        except Exception as ex:  # pylint: disable=broad-except
            logger.error(str(ex))
        time.sleep(delay + delay * x)
    else:
        return False
    hook.add(message="AAD role deletion done", value=1.0, total_val=1.0)
    logger.info("AAD role deletion done")
    return True


def delete_role_assignments_executor(
    cli_ctx,
    ids=None,
    assignee=None,
    role=None,
    resource_group_name=None,
    scope=None,
    include_inherited=False,
    yes=None,
    is_service_principal=True,
):
    factory = get_auth_management_client(cli_ctx, scope)
    assignments_client = factory.role_assignments
    definitions_client = factory.role_definitions
    ids = ids or []
    if ids:
        if assignee or role or resource_group_name or scope or include_inherited:
            raise AzCLIError(
                'When assignment ids are used, other parameter values are not required')
        for i in ids:
            assignments_client.delete_by_id(i)
        return
    if not any([ids, assignee, role, resource_group_name, scope, assignee, yes]):
        msg = 'This will delete all role assignments under the subscription. Are you sure?'
        if not prompt_y_n(msg, default="n"):
            return

    scope = build_role_scope(resource_group_name, scope, assignments_client.config.subscription_id)
    assignments = search_role_assignments(
        cli_ctx,
        assignments_client,
        definitions_client,
        scope,
        assignee,
        role,
        include_inherited,
        include_groups=False,
        is_service_principal=is_service_principal,
    )

    if assignments:
        for a in assignments:
            assignments_client.delete_by_id(a.id)


def subnet_role_assignment_exists(cmd, scope):
    factory = get_auth_management_client(cmd.cli_ctx, scope)
    assignments_client = factory.role_assignments

    if cmd.supported_api_version(min_api='2018-01-01-preview', resource_type=ResourceType.MGMT_AUTHORIZATION):
        for i in assignments_client.list_for_scope(scope=scope, filter='atScope()'):
            if i.scope == scope and i.role_definition_id.endswith(CONST_NETWORK_CONTRIBUTOR_ROLE_ID):
                return True
    return False


def ensure_cluster_identity_permission_on_kubelet_identity(cmd, cluster_identity_object_id, scope):
    factory = get_auth_management_client(cmd.cli_ctx, scope)
    assignments_client = factory.role_assignments

    for i in assignments_client.list_for_scope(scope=scope, filter="atScope()"):
        if i.scope.lower() != scope.lower():
            continue
        if not i.role_definition_id.lower().endswith(CONST_MANAGED_IDENTITY_OPERATOR_ROLE_ID):
            continue
        if i.principal_id.lower() != cluster_identity_object_id.lower():
            continue
        # already assigned
        return

    if not add_role_assignment(
        cmd, CONST_MANAGED_IDENTITY_OPERATOR_ROLE, cluster_identity_object_id, is_service_principal=False, scope=scope
    ):
        raise UnauthorizedError(
            "Could not grant Managed Identity Operator " "permission to cluster identity at scope {}".format(scope)
        )


def ensure_aks_acr_role_assignment(cmd, assignee, registry_id, detach=False, is_service_principal=True):
    if detach:
        if not delete_role_assignments(
            cmd.cli_ctx, "acrpull", assignee, scope=registry_id, is_service_principal=is_service_principal
        ):
            raise AzCLIError("Could not delete role assignments for ACR. " "Are you an Owner on this subscription?")
        return

    if not add_role_assignment(cmd, "acrpull", assignee, scope=registry_id, is_service_principal=is_service_principal):
        raise AzCLIError("Could not create a role assignment for ACR. " "Are you an Owner on this subscription?")
    return


# pylint: disable=unused-argument
def ensure_aks_acr(cmd, assignee, acr_name_or_id, subscription_id, detach=False, is_service_principal=True):
    from msrestazure.tools import is_valid_resource_id, parse_resource_id

    # Check if the ACR exists by resource ID.
    if is_valid_resource_id(acr_name_or_id):
        try:
            parsed_registry = parse_resource_id(acr_name_or_id)
            acr_client = cf_container_registry_service(cmd.cli_ctx, subscription_id=parsed_registry["subscription"])
            registry = acr_client.registries.get(parsed_registry["resource_group"], parsed_registry["name"])
        except (CloudError, HttpResponseError) as ex:
            raise AzCLIError(ex.message)
        ensure_aks_acr_role_assignment(cmd, assignee, registry.id, detach, is_service_principal)
        return

    # Check if the ACR exists by name accross all resource groups.
    registry_name = acr_name_or_id
    registry_resource = "Microsoft.ContainerRegistry/registries"
    try:
        registry = get_resource_by_name(cmd.cli_ctx, registry_name, registry_resource)
    except (CloudError, HttpResponseError) as ex:
        if "was not found" in ex.message:
            raise AzCLIError("ACR {} not found. Have you provided the right ACR name?".format(registry_name))
        raise AzCLIError(ex.message)
    ensure_aks_acr_role_assignment(cmd, assignee, registry.id, detach, is_service_principal)
    return
