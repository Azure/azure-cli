# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.mgmt.core.tools import is_valid_resource_id
from knack.util import CLIError


def validate_resource(cmd, namespace):  # pylint: disable=unused-argument
    if namespace.resource:
        if not is_valid_resource_id(namespace.resource):
            if not namespace.namespace:
                raise CLIError('--namespace is required if --resource is not a resource ID.')
            if not namespace.resource_type:
                raise CLIError('--resource-type is required if --resource is not a resource ID.')


def validate_resource_required(cmd, namespace):
    if not namespace.resource:
        raise CLIError('--resource is required for the operation.')

    validate_resource(cmd, namespace)


def validate_expand(cmd, namespace):
    if namespace.expand_clause is not None:
        validate_resource_required(cmd, namespace)
