# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long
# pylint: disable=unused-variable

import re

from knack.util import CLIError

# PARAMETER VALIDATORS

def validate_partner_namespace(cmd, namespace):
    from azure.cli.core.commands.client_factory import get_subscription_id
    from msrestazure.tools import is_valid_resource_id, resource_id
    if namespace.partner_namespace:
        if not is_valid_resource_id(namespace.partner_namespace):
            namespace.partner_namespace = resource_id(
                subscription=get_subscription_id(cmd.cli_ctx),
                resource_group=namespace.resource_group_name,
                namespace='Microsoft.Relay',
                type='namespaces',
                name=namespace.partner_namespace)

