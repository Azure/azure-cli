# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import uuid

from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.core.profiles import get_sdk
from azure.cli.core.profiles import ResourceType
from msrestazure.tools import resource_id


CONTRIBUTOR = 'b24988ac-6180-42a0-ab88-20f7382dd24c'
DEVELOPMENT_CONTRIBUTOR = 'f3fe7bc1-0ef9-4681-a68c-c1fa285d6128'


def assign_contributor_to_vnet(cli_ctx, vnet, object_id):
    client = get_mgmt_service_client(cli_ctx, ResourceType.MGMT_AUTHORIZATION)

    RoleAssignmentCreateParameters = get_sdk(cli_ctx, ResourceType.MGMT_AUTHORIZATION,
                                             'RoleAssignmentCreateParameters', mod='models',
                                             operation_group='role_assignments')

    role_definition_id = resource_id(
        subscription=get_subscription_id(cli_ctx),
        namespace='Microsoft.Authorization',
        type='roleDefinitions',
        name=DEVELOPMENT_CONTRIBUTOR if rp_mode_development() else CONTRIBUTOR,
    )

    for assignment in list(client.role_assignments.list_for_scope(vnet)):
        if assignment.role_definition_id.lower() == role_definition_id.lower() and \
                assignment.principal_id.lower() == object_id.lower():
            return

    client.role_assignments.create(vnet, uuid.uuid4(), RoleAssignmentCreateParameters(
        role_definition_id=role_definition_id,
        principal_id=object_id,
        principal_type='ServicePrincipal',
    ))


def rp_mode_development():
    return os.environ.get('RP_MODE', '').lower() == 'development'
