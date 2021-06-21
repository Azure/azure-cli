# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=unused-argument
from azure.cli.core.util import sdk_no_wait
from azure.mgmt.synapse.models import TransparentDataEncryption


def create_or_update(cmd, client, sql_pool_name, workspace_name, resource_group_name,
                     transparent_data_encryption_name, status, no_wait=False):
    tde_parameters = TransparentDataEncryption(status=status)
    return sdk_no_wait(no_wait, client.create_or_update, resource_group_name, workspace_name, sql_pool_name,
                       transparent_data_encryption_name, tde_parameters)
