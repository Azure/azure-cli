# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.decorators import Completer
from azure.cli.core.commands.client_factory import get_subscription_id

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
