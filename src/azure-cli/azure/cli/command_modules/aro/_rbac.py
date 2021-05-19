# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import uuid

from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.core.profiles import get_sdk
from azure.cli.core.profiles import ResourceType
from knack.log import get_logger
from msrest.exceptions import ValidationError
from msrestazure.tools import resource_id

NETWORK_CONTRIBUTOR = '4d97b98b-1d4f-4787-a291-c67834d212e7'

logger = get_logger(__name__)


def _gen_uuid():
    return uuid.uuid4()


def _create_role_assignment(auth_client, resource, params):
    # retry "ValidationError: A hash conflict was encountered for the role Assignment ID. Please use a new Guid."
    max_retries = 3
    retries = 0
    while True:
        try:
            return auth_client.role_assignments.create(resource, _gen_uuid(), params)
        except ValidationError as ex:
            if retries >= max_retries:
                raise
            retries += 1
            logger.warning("%s; retry %d of %d", ex, retries, max_retries)


def assign_network_contributor_to_resource(cli_ctx, resource, object_id):
    auth_client = get_mgmt_service_client(cli_ctx, ResourceType.MGMT_AUTHORIZATION)

    RoleAssignmentCreateParameters = get_sdk(cli_ctx, ResourceType.MGMT_AUTHORIZATION,
                                             'RoleAssignmentCreateParameters', mod='models',
                                             operation_group='role_assignments')

    role_definition_id = resource_id(
        subscription=get_subscription_id(cli_ctx),
        namespace='Microsoft.Authorization',
        type='roleDefinitions',
        name=NETWORK_CONTRIBUTOR,
    )

    _create_role_assignment(auth_client, resource, RoleAssignmentCreateParameters(
        role_definition_id=role_definition_id,
        principal_id=object_id,
        principal_type='ServicePrincipal',
    ))


def has_network_contributor_on_resource(cli_ctx, resource, object_id):
    auth_client = get_mgmt_service_client(cli_ctx, ResourceType.MGMT_AUTHORIZATION)

    role_definition_id = resource_id(
        subscription=get_subscription_id(cli_ctx),
        namespace='Microsoft.Authorization',
        type='roleDefinitions',
        name=NETWORK_CONTRIBUTOR,
    )

    for assignment in auth_client.role_assignments.list_for_scope(resource):
        if assignment.role_definition_id.lower() == role_definition_id.lower() and \
                assignment.principal_id.lower() == object_id.lower():
            return True

    return False
