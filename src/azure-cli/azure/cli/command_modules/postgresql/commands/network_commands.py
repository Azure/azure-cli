# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-argument, line-too-long, import-outside-toplevel
from azure.cli.core.util import sdk_no_wait

from ..utils.validators import validate_resource_group


def flexible_server_migrate_network(client, resource_group_name, server_name, no_wait=False):
    validate_resource_group(resource_group_name)

    return sdk_no_wait(no_wait, client.begin_migrate_network_mode, resource_group_name, server_name)
