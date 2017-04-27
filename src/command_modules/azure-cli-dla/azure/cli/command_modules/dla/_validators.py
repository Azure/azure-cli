# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from msrest.serialization import Deserializer
from msrest.exceptions import DeserializationError

from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.mgmt.datalake.analytics.account import DataLakeAnalyticsAccountManagementClient
from azure.cli.core.commands.arm import parse_resource_id
from azure.cli.core.util import CLIError


# Helpers
def _get_resource_group_from_account_name(client, account_name):
    """
    Fetch resource group from vault name
    :param str vault_name: name of the key vault
    :return: resource group name or None
    :rtype: str
    """
    for acct in client.list():
        id_comps = parse_resource_id(acct.id)
        if id_comps['name'] == account_name:
            return id_comps['resource_group']
    raise CLIError(
        "The Resource 'Microsoft.DataLakeAnalytics/accounts/{}'".format(account_name) +
        " not found within subscription: {}".format(client.config.subscription_id))


# COMMAND NAMESPACE VALIDATORS
def validate_resource_group_name(ns):
    if not ns.resource_group_name:
        account_name = ns.account_name
        client = get_mgmt_service_client(DataLakeAnalyticsAccountManagementClient).account
        group_name = _get_resource_group_from_account_name(client, account_name)
        ns.resource_group_name = group_name


def datetime_format(value):
    """Validate the correct format of a datetime string and deserialize."""
    try:
        datetime_obj = Deserializer.deserialize_iso(value)
    except DeserializationError:
        message = "Argument {} is not a valid ISO-8601 datetime format"
        raise ValueError(message.format(value))
    return datetime_obj
