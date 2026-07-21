# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.decorators import Completer
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.command_modules.resource._client_factory import _resource_policy_client_factory

from ._client_factory import cf_policy_insights


@Completer
def get_policy_remediation_completion_list(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
    client = cf_policy_insights(cmd.cli_ctx)
    sub = get_subscription_id(cmd.cli_ctx)
    rg = getattr(namespace, 'resource_group_name', None)
    management_group = getattr(namespace, 'management_group_name', None)
    if rg:
        result = client.remediations.list_for_resource_group(subscription_id=sub, resource_group_name=rg)
    elif management_group:
        result = client.remediations.list_for_management_group(management_group_id=management_group)
    else:
        result = client.remediations.list_for_subscription(subscription_id=sub)

    return [i.name for i in result]


@Completer
def get_policy_metadata_completion_list(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
    client = cf_policy_insights(cmd.cli_ctx).policy_metadata

    from azure.mgmt.policyinsights.models import QueryOptions
    query_options = QueryOptions(top=2000)

    return [metadata.name for metadata in client.list(query_options) if metadata.name.startswith(prefix)]


@Completer
def get_policy_completion_list(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
    policy_client = _resource_policy_client_factory(cmd.cli_ctx)
    result = policy_client.policy_definitions.list()
    return [i.name for i in result]


@Completer
def get_policy_set_completion_list(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
    policy_client = _resource_policy_client_factory(cmd.cli_ctx)
    result = policy_client.policy_set_definitions.list()
    return [i.name for i in result]


@Completer
def get_policy_assignment_completion_list(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
    policy_client = _resource_policy_client_factory(cmd.cli_ctx)
    result = policy_client.policy_assignments.list()
    return [i.name for i in result]


@Completer
def get_policy_exemption_completion_list(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
    policy_client = _resource_policy_client_factory(cmd.cli_ctx)
    result = policy_client.policy_exemptions.list()
    return [i.name for i in result]
