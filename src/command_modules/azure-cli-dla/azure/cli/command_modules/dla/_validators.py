# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError

from azure.cli.core.commands.client_factory import get_mgmt_service_client


# Helpers
def _get_resource_group_from_account_name(client, account_name):
    """
    Fetch resource group from vault name
    :param str vault_name: name of the key vault
    :return: resource group name or None
    :rtype: str
    """
    from msrestazure.tools import parse_resource_id
    for acct in client.list():
        id_comps = parse_resource_id(acct.id)
        if id_comps['name'] == account_name:
            return id_comps['resource_group']
    raise CLIError(
        "The Resource 'Microsoft.DataLakeAnalytics/accounts/{}'".format(account_name) +
        " not found within subscription: {}".format(client.config.subscription_id))


# COMMAND NAMESPACE VALIDATORS
def validate_resource_group_name(cmd, ns):
    from azure.mgmt.datalake.analytics.account import DataLakeAnalyticsAccountManagementClient
    if not ns.resource_group_name:
        account_name = ns.account_name
        client = get_mgmt_service_client(cmd.cli_ctx, DataLakeAnalyticsAccountManagementClient).account
        group_name = _get_resource_group_from_account_name(client, account_name)
        ns.resource_group_name = group_name


def datetime_format(value):
    """Validate the correct format of a datetime string and deserialize."""
    from msrest.serialization import Deserializer
    from msrest.exceptions import DeserializationError
    try:
        datetime_obj = Deserializer.deserialize_iso(value)
    except DeserializationError:
        message = "Argument {} is not a valid ISO-8601 datetime format"
        raise ValueError(message.format(value))
    return datetime_obj


# pylint: disable=too-many-boolean-expressions
def process_dla_job_submit_namespace(ns):
    if (not ns.recurrence_id and
            (ns.pipeline_name or
             ns.pipeline_uri or
             ns.recurrence_id or
             ns.recurrence_name or
             ns.run_id)):
        raise CLIError("--recurrence-id is required if any of the following are specified: " +
                       "--pipeline-uri, --pipeline-name, --recurrence-id, --recurrence-name, --run-id")
    if not ns.pipeline_id and (ns.pipeline_name or ns.pipeline_uri or ns.run_id):
        raise CLIError("--pipeline-id and --recurrence-id are required if any of the following are specified: " +
                       "--pipeline-uri, --pipeline-name, --run-id")
