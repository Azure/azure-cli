# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=unused-argument
# pylint: disable=line-too-long
# pylint: disable=no-value-for-parameter

from azure.cli.core.decorators import Completer


@Completer
def get_eventhubs_command_completion_list(cmd, prefix, namespace):
    from ._client_factory import event_hub_mgmt_client_factory
    resource_group_name = namespace.resource_group_name
    namespace_name = namespace.name
    result = event_hub_mgmt_client_factory(cmd.cli_ctx).list_by_namespace(resource_group_name, namespace_name)
    return [r.name for r in result]


@Completer
def get_consumergroup_command_completion_list(cmd, prefix, namespace):
    from ._client_factory import consumer_groups_mgmt_client_factory
    resource_group_name = namespace.resource_group_name
    namespace_name = namespace.namespace_name
    eventhub_name = namespace.name
    result = consumer_groups_mgmt_client_factory(cmd.cli_ctx).list_by_event_hub(resource_group_name, namespace_name, eventhub_name)
    return [r.name for r in result]
