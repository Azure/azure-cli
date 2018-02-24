# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError


def validate_include_or_exclude(namespace):
    if namespace.include and namespace.exclude:
        raise CLIError('usage error: --include | --exclude')


def validate_ids_or_names(namespace):
    if namespace.ids and (namespace.recommendation_name or namespace.resource_group_name):
        raise CLIError('usage error: --ids | --name [--resource-group]')


def validate_ids_or_resource_group(namespace):
    if namespace.ids and namespace.resource_group_name:
        raise CLIError('usage error: --ids | --resource-group')


def validate_threshold_or_resource_group(namespace):
    if namespace.low_cpu_threshold and namespace.resource_group_name:
        raise CLIError('usage error: --low-cpu-threshold | --resource-group')
