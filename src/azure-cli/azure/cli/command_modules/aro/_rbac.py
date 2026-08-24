# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import typing
import uuid

from azure.cli.command_modules.aro.aaz.latest.identity import Create as _create_identity
from azure.cli.command_modules.aro.aaz.latest.role.assignment import Create as _role_assignment_create
from azure.cli.core.commands.client_factory import (
    get_mgmt_service_client,
    get_subscription_id
)
from azure.cli.core.profiles import ResourceType
from azure.core.exceptions import ResourceExistsError
from azure.mgmt.core.tools import resource_id
from knack.log import get_logger

ROLE_NETWORK_CONTRIBUTOR = '4d97b98b-1d4f-4787-a291-c67834d212e7'
ROLE_READER = 'acdd72a7-3385-48ef-bd42-f606fba81ae7'

logger = get_logger(__name__)


# UUID/GUID generation is extracted into a function to aid in testing.
def _gen_uuid() -> uuid.UUID:
    return uuid.uuid4()


def create_identity(cmd, location, group, name) -> typing.Any:
    create = _create_identity(cli_ctx=cmd.cli_ctx)

    # idempotent
    return create(command_args={
        "location": location,
        "resource_group": group,
        "resource_name": name,
    })


def create_role_assignment(cli_ctx, principal_id, role_definition_id, scope) -> typing.Any | None:
    create = _role_assignment_create(cli_ctx=cli_ctx)
    try:
        return create(command_args={
            "principal_id": principal_id,
            "principal_type": "ServicePrincipal",
            "role_definition_id": role_definition_id,
            "scope": scope,
            "role_assignment_name": str(_gen_uuid()),
        })
    except ResourceExistsError:
        logger.warning("Role Assignment already exists for "
                       "{ principal: %s, role definition: %s, scope: %s }.",
                       principal_id, role_definition_id, scope)
        return None


def has_role_assignment_on_resource(cli_ctx, resource, object_id, role_name) -> bool:
    auth_client = get_mgmt_service_client(cli_ctx, ResourceType.MGMT_AUTHORIZATION)

    role_definition_id = resource_id(
        subscription=get_subscription_id(cli_ctx),
        namespace='Microsoft.Authorization',
        type='roleDefinitions',
        name=role_name,
    )

    for assignment in auth_client.role_assignments.list_for_scope(resource):
        if assignment.role_definition_id.lower() == role_definition_id.lower() and \
                assignment.principal_id.lower() == object_id.lower():
            return True

    return False


def print_identity_create_cmd(group, name, location) -> None:
    msg = f"    az identity create -g '{group}' -n '{name}' -l '{location}'"
    logger.warning(msg)


def print_role_assignment_create_cmd(assignee, role, scope) -> None:
    msg = [
        "    az role assignment create",
        f'--assignee-object-id "{assignee}"',
        "--assignee-principal-type ServicePrincipal",
        f"--role '{role}'",
        f'--scope "{scope}"',
    ]
    logger.warning(" ".join(msg))
