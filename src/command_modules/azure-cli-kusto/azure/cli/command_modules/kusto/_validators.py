# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from knack.util import CLIError


def validate_database_args(namespace):
    if namespace.hot_cache_period_in_days:
        if namespace.hot_cache_period_in_days < 0:
            raise CLIError('hot_cache_period_in_days must be greater then 0')
    if namespace.soft_delete_period_in_days:
        if namespace.soft_delete_period_in_days < 0:
            raise CLIError('soft_delete_period_in_days must be greater then 0')


def validate_cluster_args(namespace):
    max_name_length = 22
    name_length = len(namespace.cluster_name)
    if name_length > max_name_length:
        raise CLIError('name can not be longer then ' + str(max_name_length) + " letters")
