# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=unused-argument
# pylint: disable=line-too-long
# pylint: disable=no-value-for-parameter

from azure.cli.core.decorators import Completer


@Completer
def get_queue_command_completion_list(cmd, prefix, namespace):
    from ._client_factory import queues_mgmt_client_factory
    resource_group_name = namespace.resource_group_name
    namespace_name = namespace.namespace_name
    result = queues_mgmt_client_factory(cmd.cli_ctx).list_by_namespace(resource_group_name, namespace_name)
    return [r.name for r in result]


@Completer
def get_topic_command_completion_list(cmd, prefix, namespace):
    from ._client_factory import topics_mgmt_client_factory
    resource_group_name = namespace.resource_group_name
    namespace_name = namespace.namespace_name
    result = topics_mgmt_client_factory(cmd.cli_ctx).list_by_namespace(resource_group_name, namespace_name)
    return [r.name for r in result]


@Completer
def get_subscriptions_command_completion_list(cmd, prefix, namespace):
    from ._client_factory import subscriptions_mgmt_client_factory
    resource_group_name = namespace.resource_group_name
    namespace_name = namespace.namespace_name
    topic_name = namespace.topic_name
    result = subscriptions_mgmt_client_factory(cmd.cli_ctx).list_by_topic(resource_group_name, namespace_name, topic_name)
    return [r.name for r in result]


@Completer
def get_rules_command_completion_list(cmd, prefix, namespace):
    from ._client_factory import rules_mgmt_client_factory
    resource_group_name = namespace.resource_group_name
    namespace_name = namespace.namespace_name
    topic_name = namespace.topic_name
    subscription_name = namespace.subscription_name
    result = rules_mgmt_client_factory(cmd.cli_ctx).list_by_subscriptions(resource_group_name, namespace_name, topic_name, subscription_name)
    return [r.name for r in result]
