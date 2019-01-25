# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from knack.util import CLIError


def validate_database_args(namespace):
    if namespace.hot_cache_period:
        hot_cache_period_in_days = round_hot_cache_to_days(namespace.hot_cache_period)
        if hot_cache_period_in_days < 0:
            raise CLIError('hot_cache_period must be a valid time')
    if namespace.soft_delete_period:
        soft_delete_period_in_days = round_soft_delete_to_days(namespace.soft_delete_period)
        if soft_delete_period_in_days < 0:
            raise CLIError('soft_delete_period must be a valid time')


def validate_cluster_args(namespace):
    max_name_length = 22
    name_length = len(namespace.cluster_name)
    if name_length > max_name_length:
        raise CLIError('name can not be longer then ' + str(max_name_length) + " letters")


def round_hot_cache_to_days(time):
    return round_timedelta_to_days(time, 'hot_cache_period')


def round_soft_delete_to_days(time):
    return round_timedelta_to_days(time, 'soft_delete_period')


def round_timedelta_to_days(time, parameter_name):
    try:
        splitted = time.split(":")
        numberOfDays = int(splitted[0])
        if int(splitted[1]) > 0:
            numberOfDays += 1
        return numberOfDays
    except:
        raise CLIError(parameter_name + ' must be a valid time format')
