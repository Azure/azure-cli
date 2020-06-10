# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
# pylint: disable=too-many-lines
# pylint: disable=inconsistent-return-statements
# pylint: disable=unused-variable

import re


# Namespace Region
def cli_namespace_create(client, resource_group_name, namespace_name, location=None, tags=None, sku='Standard',
                         capacity=None, default_action=None):

    from azure.mgmt.servicebus.models import SBNamespace, SBSku
    client.create_or_update(
        resource_group_name=resource_group_name,
        namespace_name=namespace_name,
        parameters=SBNamespace(
            location=location,
            tags=tags,
            sku=SBSku(
                name=sku,
                tier=sku,
                capacity=capacity)
        )
    ).result()

    if default_action:
        netwrokruleset = client.get_network_rule_set(resource_group_name, namespace_name)
        netwrokruleset.default_action = default_action
        client.create_or_update_network_rule_set(resource_group_name, namespace_name, netwrokruleset)

    return client.get(resource_group_name, namespace_name)


def cli_namespace_update(client, instance, tags=None, sku=None, capacity=None, default_action=None):
    from msrestazure.tools import parse_resource_id

    if tags is not None:
        instance.tags = tags

    if sku is not None:
        instance.sku.name = sku
        instance.sku.tier = sku

    if capacity is not None:
        instance.sku.capacity = capacity

    if default_action:
        resourcegroup = parse_resource_id(instance.id)['resource_group']
        netwrokruleset = client.get_network_rule_set(resourcegroup, instance.name)
        netwrokruleset.default_action = default_action
        client.create_or_update_network_rule_set(resourcegroup, instance.name, netwrokruleset)

    return instance


def cli_namespace_list(client, resource_group_name=None):
    if resource_group_name:
        return client.list_by_resource_group(resource_group_name=resource_group_name)

    return client.list()


# Namespace Authorization rule:
def cli_namespaceautho_create(client, resource_group_name, namespace_name, name, access_rights=None):
    from azure.cli.command_modules.servicebus._utils import accessrights_converter
    return client.create_or_update_authorization_rule(
        resource_group_name=resource_group_name,
        namespace_name=namespace_name,
        authorization_rule_name=name,
        rights=accessrights_converter(access_rights)
    )


# Namespace Authorization rule:
def cli_namespaceautho_update(instance, rights):
    from azure.cli.command_modules.servicebus._utils import accessrights_converter
    instance.rights = accessrights_converter(rights)
    return instance


# Queue Region
def cli_sbqueue_create(cmd, client, resource_group_name, namespace_name, queue_name, lock_duration=None,
                       max_size_in_megabytes=None, requires_duplicate_detection=None, requires_session=None,
                       default_message_time_to_live=None, dead_lettering_on_message_expiration=None,
                       duplicate_detection_history_time_window=None, max_delivery_count=None, status=None,
                       auto_delete_on_idle=None, enable_partitioning=None, enable_express=None,
                       forward_to=None, forward_dead_lettered_messages_to=None, enable_batched_operations=None):

    from azure.mgmt.servicebus.models import SBQueue

    if max_size_in_megabytes:
        cli_returnnsdetails(cmd, resource_group_name, namespace_name, max_size_in_megabytes)

    queue_params = SBQueue(
        lock_duration=return_valid_duration_create(lock_duration),
        max_size_in_megabytes=max_size_in_megabytes,
        requires_duplicate_detection=requires_duplicate_detection,
        requires_session=requires_session,
        default_message_time_to_live=return_valid_duration_create(default_message_time_to_live),
        dead_lettering_on_message_expiration=dead_lettering_on_message_expiration,
        duplicate_detection_history_time_window=return_valid_duration_create(duplicate_detection_history_time_window),
        max_delivery_count=max_delivery_count,
        status=status,
        auto_delete_on_idle=return_valid_duration_create(auto_delete_on_idle),
        enable_partitioning=enable_partitioning,
        enable_express=enable_express,
        forward_to=forward_to,
        forward_dead_lettered_messages_to=forward_dead_lettered_messages_to,
        enable_batched_operations=enable_batched_operations
    )
    return client.create_or_update(
        resource_group_name=resource_group_name,
        namespace_name=namespace_name,
        queue_name=queue_name,
        parameters=queue_params)


def cli_sbqueue_update(instance, lock_duration=None,
                       max_size_in_megabytes=None, requires_duplicate_detection=None, requires_session=None,
                       default_message_time_to_live=None, dead_lettering_on_message_expiration=None,
                       duplicate_detection_history_time_window=None, max_delivery_count=None, status=None,
                       auto_delete_on_idle=None, enable_partitioning=None, enable_express=None,
                       forward_to=None, forward_dead_lettered_messages_to=None, enable_batched_operations=None):

    from azure.mgmt.servicebus.models import SBQueue
    returnobj = SBQueue()

    if lock_duration:
        returnobj.lock_duration = return_valid_duration(instance, 'lock_duration', lock_duration)

    if max_size_in_megabytes:
        returnobj.max_size_in_megabytes = max_size_in_megabytes

    if requires_duplicate_detection:
        returnobj.requires_duplicate_detection = requires_duplicate_detection

    if requires_session:
        returnobj.requires_session = requires_session

    if default_message_time_to_live:
        returnobj.default_message_time_to_live = return_valid_duration(instance, 'default_message_time_to_live', default_message_time_to_live)

    if dead_lettering_on_message_expiration:
        returnobj.dead_lettering_on_message_expiration = dead_lettering_on_message_expiration

    if duplicate_detection_history_time_window:
        returnobj.duplicate_detection_history_time_window = return_valid_duration(instance, 'duplicate_detection_history_time_window', duplicate_detection_history_time_window)

    if max_delivery_count:
        returnobj.max_delivery_count = max_delivery_count

    if status:
        returnobj.status = status

    if auto_delete_on_idle:
        returnobj.auto_delete_on_idle = return_valid_duration(instance, 'auto_delete_on_idle', auto_delete_on_idle)

    if enable_partitioning:
        returnobj.enable_partitioning = enable_partitioning

    if enable_express:
        returnobj.enable_express = enable_express

    if forward_to:
        returnobj.forward_to = forward_to

    if forward_dead_lettered_messages_to:
        returnobj.forward_dead_lettered_messages_to = forward_dead_lettered_messages_to

    if enable_batched_operations:
        returnobj.enable_batched_operations = enable_batched_operations

    return returnobj


# Topic Region
def cli_sbtopic_create(cmd, client, resource_group_name, namespace_name, topic_name, default_message_time_to_live=None,
                       max_size_in_megabytes=None, requires_duplicate_detection=None,
                       duplicate_detection_history_time_window=None,
                       enable_batched_operations=None, status=None, support_ordering=None, auto_delete_on_idle=None,
                       enable_partitioning=None, enable_express=None):
    from azure.mgmt.servicebus.models import SBTopic

    if max_size_in_megabytes:
        cli_returnnsdetails(cmd, resource_group_name, namespace_name, max_size_in_megabytes)

    topic_params = SBTopic(
        default_message_time_to_live=return_valid_duration_create(default_message_time_to_live),
        max_size_in_megabytes=max_size_in_megabytes,
        requires_duplicate_detection=requires_duplicate_detection,
        duplicate_detection_history_time_window=return_valid_duration_create(duplicate_detection_history_time_window),
        enable_batched_operations=enable_batched_operations,
        status=status,
        support_ordering=support_ordering,
        auto_delete_on_idle=return_valid_duration_create(auto_delete_on_idle),
        enable_partitioning=enable_partitioning,
        enable_express=enable_express
    )
    return client.create_or_update(
        resource_group_name=resource_group_name,
        namespace_name=namespace_name,
        topic_name=topic_name,
        parameters=topic_params)


def cli_sbtopic_update(instance, default_message_time_to_live=None,
                       max_size_in_megabytes=None, requires_duplicate_detection=None,
                       duplicate_detection_history_time_window=None,
                       enable_batched_operations=None, status=None, support_ordering=None, auto_delete_on_idle=None,
                       enable_partitioning=None, enable_express=None):

    from azure.mgmt.servicebus.models import SBTopic
    topic_params = SBTopic()

    if default_message_time_to_live:
        topic_params.default_message_time_to_live = return_valid_duration(instance, 'default_message_time_to_live', default_message_time_to_live)

    if max_size_in_megabytes:
        topic_params.max_size_in_megabytes = max_size_in_megabytes

    if requires_duplicate_detection:
        topic_params.requires_duplicate_detection = requires_duplicate_detection

    if duplicate_detection_history_time_window:
        topic_params.duplicate_detection_history_time_window = return_valid_duration(instance, 'duplicate_detection_history_time_window', duplicate_detection_history_time_window)

    if enable_batched_operations:
        topic_params.enable_batched_operations = enable_batched_operations

    if status:
        topic_params.status = status

    if support_ordering:
        topic_params.support_ordering = support_ordering

    if auto_delete_on_idle:
        topic_params.auto_delete_on_idle = return_valid_duration(instance, 'auto_delete_on_idle', auto_delete_on_idle)

    if enable_partitioning:
        topic_params.enable_partitioning = enable_partitioning

    if enable_express:
        topic_params.enable_express = enable_express

    return topic_params


# Subscription Region
def cli_sbsubscription_create(client, resource_group_name, namespace_name, topic_name, subscription_name, lock_duration=None,
                              requires_session=None, default_message_time_to_live=None, dead_lettering_on_message_expiration=None,
                              max_delivery_count=None, status=None, enable_batched_operations=None,
                              auto_delete_on_idle=None, forward_to=None, forward_dead_lettered_messages_to=None, dead_lettering_on_filter_evaluation_exceptions=None):

    from azure.mgmt.servicebus.models import SBSubscription
    subscription_params = SBSubscription(
        lock_duration=return_valid_duration_create(lock_duration),
        requires_session=requires_session,
        default_message_time_to_live=return_valid_duration_create(default_message_time_to_live),
        dead_lettering_on_message_expiration=dead_lettering_on_message_expiration,
        max_delivery_count=max_delivery_count,
        status=status,
        enable_batched_operations=enable_batched_operations,
        auto_delete_on_idle=return_valid_duration_create(auto_delete_on_idle),
        forward_to=forward_to,
        forward_dead_lettered_messages_to=forward_dead_lettered_messages_to,
        dead_lettering_on_filter_evaluation_exceptions=dead_lettering_on_filter_evaluation_exceptions
    )

    return client.create_or_update(
        resource_group_name=resource_group_name,
        namespace_name=namespace_name,
        topic_name=topic_name,
        subscription_name=subscription_name,
        parameters=subscription_params)


def cli_sbsubscription_update(instance, lock_duration=None,
                              requires_session=None, default_message_time_to_live=None,
                              dead_lettering_on_message_expiration=None,
                              max_delivery_count=None, status=None, enable_batched_operations=None,
                              auto_delete_on_idle=None, forward_to=None, forward_dead_lettered_messages_to=None, dead_lettering_on_filter_evaluation_exceptions=None):
    from azure.mgmt.servicebus.models import SBSubscription
    subscription_params = SBSubscription()

    if lock_duration:
        subscription_params.lock_duration = return_valid_duration(instance, 'lock_duration', lock_duration)

    if requires_session:
        subscription_params.requires_session = requires_session

    if default_message_time_to_live:
        subscription_params.default_message_time_to_live = return_valid_duration(instance, 'default_message_time_to_live', default_message_time_to_live)

    if dead_lettering_on_message_expiration:
        subscription_params.dead_lettering_on_message_expiration = dead_lettering_on_message_expiration

    if max_delivery_count:
        subscription_params.max_delivery_count = max_delivery_count

    if status:
        subscription_params.status = status

    if lock_duration:
        subscription_params.enable_batched_operations = enable_batched_operations

    subscription_params.auto_delete_on_idle = return_valid_duration(instance, 'auto_delete_on_idle', auto_delete_on_idle)

    if forward_to:
        subscription_params.forward_to = forward_to

    if forward_dead_lettered_messages_to:
        subscription_params.forward_dead_lettered_messages_to = forward_dead_lettered_messages_to

    if dead_lettering_on_filter_evaluation_exceptions:
        subscription_params.dead_lettering_on_filter_evaluation_exceptions = dead_lettering_on_filter_evaluation_exceptions

    return subscription_params


# Rule Region
def cli_rules_create(client, resource_group_name, namespace_name, topic_name, subscription_name, rule_name,
                     action_sql_expression=None, action_compatibility_level=None, action_requires_preprocessing=None,
                     filter_sql_expression=None, filter_requires_preprocessing=None, correlation_id=None,
                     message_id=None, to=None, reply_to=None, label=None, session_id=None, reply_to_session_id=None,
                     content_type=None, requires_preprocessing=None):

    from azure.mgmt.servicebus.models import Rule, Action, SqlFilter, CorrelationFilter
    parameters = Rule()
    parameters.action = Action(
        sql_expression=action_sql_expression,
        compatibility_level=action_compatibility_level,
        requires_preprocessing=action_requires_preprocessing
    )
    parameters.sql_filter = SqlFilter(
        sql_expression=filter_sql_expression,
        requires_preprocessing=filter_requires_preprocessing
    )
    parameters.correlation_filter = CorrelationFilter(
        correlation_id=correlation_id,
        to=to,
        message_id=message_id,
        reply_to=reply_to,
        label=label,
        session_id=session_id,
        reply_to_session_id=reply_to_session_id,
        content_type=content_type,
        requires_preprocessing=requires_preprocessing
    )
    return client.create_or_update(
        resource_group_name=resource_group_name,
        namespace_name=namespace_name,
        topic_name=topic_name,
        subscription_name=subscription_name,
        rule_name=rule_name,
        parameters=parameters)


# Rule Region
def cli_rules_update(instance,
                     action_sql_expression=None, action_compatibility_level=None, action_requires_preprocessing=None,
                     filter_sql_expression=None, filter_requires_preprocessing=None, correlation_id=None,
                     message_id=None, to=None, reply_to=None, label=None, session_id=None, reply_to_session_id=None,
                     content_type=None, requires_preprocessing=None):

    if action_sql_expression:
        instance.action.sql_expression = action_sql_expression

    if action_compatibility_level:
        instance.action.compatibility_level = action_compatibility_level

    if action_requires_preprocessing:
        instance.action.requires_preprocessing = action_requires_preprocessing

    if filter_sql_expression:
        instance.sql_filter.sql_expression = filter_sql_expression

    if filter_requires_preprocessing:
        instance.sql_filter.requires_preprocessing = filter_requires_preprocessing

    if correlation_id:
        instance.correlation_filter.correlation_id = correlation_id

    if to:
        instance.correlation_filter.to = to

    if message_id:
        instance.correlation_filter.message_id = message_id

    if reply_to:
        instance.correlation_filter.reply_to = reply_to

    if label:
        instance.correlation_filter.label = label

    if session_id:
        instance.correlation_filter.session_id = session_id

    if reply_to_session_id:
        instance.correlation_filter.reply_to_session_id = reply_to_session_id

    if content_type:
        instance.correlation_filter.content_type = content_type

    if requires_preprocessing:
        instance.correlation_filter.requires_preprocessing = requires_preprocessing

    return instance


def cli_migration_start(client, resource_group_name, namespace_name, target_namespace, post_migration_name):
    import time

    client.create_and_start_migration(resource_group_name, namespace_name, target_namespace, post_migration_name)
    getresponse = client.get(resource_group_name, namespace_name)

    # pool till Provisioning state is succeeded
    while getresponse.provisioning_state != 'Succeeded':
        time.sleep(30)
        getresponse = client.get(resource_group_name, namespace_name)

    # poll on the 'pendingReplicationOperationsCount' to be 0 or none
    while getresponse.pending_replication_operations_count != 0 and getresponse.pending_replication_operations_count is not None:
        time.sleep(30)
        getresponse = client.get(resource_group_name, namespace_name)

    return client.get(resource_group_name, namespace_name)


iso8601pattern = re.compile("^P(?!$)(\\d+Y)?(\\d+M)?(\\d+W)?(\\d+D)?(T(?=\\d)(\\d+H)?(\\d+M)?(\\d+.)?(\\d+S)?)?$")
timedeltapattern = re.compile("^\\d+:\\d+:\\d+$")


def return_valid_duration(objinstance, duration_property, update_value):
    from datetime import timedelta
    from isodate import parse_duration
    if update_value is not None:
        if iso8601pattern.match(update_value):
            for attr, value in vars(objinstance).items():
                if attr == duration_property:
                    if parse_duration(update_value) < timedelta(days=10675199, minutes=10085, seconds=477581):
                        return update_value

                    if parse_duration(update_value) > timedelta(days=10675199, minutes=10085, seconds=477581):
                        return None

        if timedeltapattern.match(update_value):
            day, minute, seconds = update_value.split(":")
            for attr, value in vars(objinstance).items():
                if attr == duration_property:
                    if timedelta(days=int(day), minutes=int(minute), seconds=int(seconds)) < timedelta(days=10675199, minutes=10085, seconds=477581):
                        return timedelta(days=int(day), minutes=int(minute), seconds=int(seconds))

                    if timedelta(days=int(day), minutes=int(minute), seconds=int(seconds)) > timedelta(days=10675198, minutes=10085, seconds=477581):
                        return None


def return_valid_duration_create(update_value):
    from datetime import timedelta
    from isodate import parse_duration
    if update_value is not None:
        if iso8601pattern.match(update_value):
            if parse_duration(update_value) < timedelta(days=10675199, minutes=10085, seconds=477581):
                return update_value

            if parse_duration(update_value) > timedelta(days=10675199, minutes=10085, seconds=477581):
                return None

        if timedeltapattern.match(update_value):
            day, minute, seconds = update_value.split(":")
            if timedelta(days=int(day), minutes=int(minute), seconds=int(seconds)) < timedelta(days=10675199, minutes=10085, seconds=477581):
                return timedelta(days=int(day), minutes=int(minute), seconds=int(seconds))

            if timedelta(days=int(day), minutes=int(minute), seconds=int(seconds)) > timedelta(days=10675198, minutes=10085, seconds=477581):
                return None
    else:
        return None


# NetwrokRuleSet Region
def cli_networkrule_createupdate(client, resource_group_name, namespace_name, subnet=None, ip_mask=None, ignore_missing_vnet_service_endpoint=False, action='Allow'):
    from azure.mgmt.servicebus.models import NWRuleSetVirtualNetworkRules, Subnet, NWRuleSetIpRules
    netwrokruleset = client.get_network_rule_set(resource_group_name, namespace_name)

    if netwrokruleset.virtual_network_rules is None:
        netwrokruleset.virtual_network_rules = []

    if netwrokruleset.ip_rules is None:
        netwrokruleset.ip_rules = []

    if subnet:
        netwrokruleset.virtual_network_rules.append(NWRuleSetVirtualNetworkRules(subnet=Subnet(id=subnet),
                                                                                 ignore_missing_vnet_service_endpoint=ignore_missing_vnet_service_endpoint))

    if ip_mask:
        netwrokruleset.ip_rules.append(NWRuleSetIpRules(ip_mask=ip_mask, action=action))

    return client.create_or_update_network_rule_set(resource_group_name, namespace_name, netwrokruleset)


def cli_networkrule_delete(client, resource_group_name, namespace_name, subnet=None, ip_mask=None):
    from azure.mgmt.servicebus.models import NWRuleSetVirtualNetworkRules, NWRuleSetIpRules
    netwrokruleset = client.get_network_rule_set(resource_group_name, namespace_name)

    if subnet:
        virtualnetworkrule = NWRuleSetVirtualNetworkRules()
        virtualnetworkrule.subnet = subnet

        for vnetruletodelete in netwrokruleset.virtual_network_rules:
            if vnetruletodelete.subnet.id.lower() == subnet.lower():
                virtualnetworkrule.ignore_missing_vnet_service_endpoint = vnetruletodelete.ignore_missing_vnet_service_endpoint
                netwrokruleset.virtual_network_rules.remove(vnetruletodelete)
                break

    if ip_mask:
        ipruletodelete = NWRuleSetIpRules()
        ipruletodelete.ip_mask = ip_mask
        ipruletodelete.action = "Allow"

        if ipruletodelete in netwrokruleset.ip_rules:
            netwrokruleset.ip_rules.remove(ipruletodelete)

    return client.create_or_update_network_rule_set(resource_group_name, namespace_name, netwrokruleset)


def cli_returnnsdetails(cmd, resource_group_name, namespace_name, max_size_in_megabytes):
    from knack.util import CLIError
    from azure.mgmt.servicebus import ServiceBusManagementClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    nsclient = get_mgmt_service_client(cmd.cli_ctx, ServiceBusManagementClient).namespaces
    getnamespace = nsclient.get(resource_group_name=resource_group_name, namespace_name=namespace_name)
    if getnamespace.sku.name == 'Standard' and max_size_in_megabytes not in [1024, 2048, 3072, 4096, 5120]:
        raise CLIError('--max-size on Standard sku namespace only supports upto [1024, 2048, 3072, 4096, 5120] GB')

    if getnamespace.sku.name == 'Premium' and max_size_in_megabytes not in [1024, 2048, 3072, 4096, 5120, 10240, 20480,
                                                                            40960, 81920]:
        raise CLIError(
            '--max-size on Premium sku namespace only supports upto [1024, 2048, 3072, 4096, 5120, 10240, 20480, 40960, 81920] GB')
