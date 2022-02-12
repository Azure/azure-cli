# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
# pylint: disable=too-many-lines
# pylint: disable=inconsistent-return-statements
# pylint: disable=unused-variable

import re
from azure.cli.core.profiles import ResourceType
from azure.cli.core.azclierror import InvalidArgumentValueError
import argparse


# Namespace Region
def cli_namespace_create(cmd, client, resource_group_name, namespace_name, location=None, tags=None, sku='Standard',
                         capacity=None, default_action=None, mi_system_assigned=None, mi_user_assigned=None, encryption_config=None):

    from azure.mgmt.servicebus.models import SBNamespace, SBSku
    Identity = cmd.get_models('Identity', resource_type=ResourceType.MGMT_SERVICEBUS)
    IdentityType = cmd.get_models('ManagedServiceIdentityType', resource_type=ResourceType.MGMT_SERVICEBUS)
    UserAssignedIdentity = cmd.get_models('UserAssignedIdentity', resource_type=ResourceType.MGMT_SERVICEBUS)
    Encryption = cmd.get_models('Encryption', resource_type=ResourceType.MGMT_SERVICEBUS)

    parameter = SBNamespace(location=location)

    parameter.tags = tags
    parameter.sku = SBSku(name = sku, tier = sku, capacity = capacity)

    if mi_system_assigned:
        parameter.identity = Identity(type=IdentityType.SYSTEM_ASSIGNED)

    if mi_user_assigned:
        if parameter.identity:
            if parameter.identity.type == IdentityType.SYSTEM_ASSIGNED:
                parameter.identity.type = IdentityType.SYSTEM_ASSIGNED_USER_ASSIGNED
            else:
                parameter.identity.type = IdentityType.USER_ASSIGNED
        else:
            parameter.identity = Identity(type=IdentityType.USER_ASSIGNED)

        default_user_identity = UserAssignedIdentity()
        parameter.identity.user_assigned_identities = dict.fromkeys(mi_user_assigned, default_user_identity)

    if encryption_config:
        parameter.encryption = Encryption()
        parameter.encryption.key_vault_properties = encryption_config

    client.begin_create_or_update(
        resource_group_name=resource_group_name,
        namespace_name=namespace_name,
        parameters=parameter
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

def cli_namespace_exists(client, name):

    return client.check_name_availability(parameters={'name': name})


# Namespace Authorization rule:
def cli_namespaceautho_create(client, resource_group_name, namespace_name, name, rights=None):
    from azure.cli.command_modules.servicebus._utils import accessrights_converter
    return client.create_or_update_authorization_rule(
        resource_group_name=resource_group_name,
        namespace_name=namespace_name,
        authorization_rule_name=name,
        parameters={'rights': accessrights_converter(rights)}
    )


# Namespace Authorization rule:
def cli_namespaceautho_update(instance, rights):
    from azure.cli.command_modules.servicebus._utils import accessrights_converter
    instance.rights = accessrights_converter(rights)
    return instance


def cli_keys_renew(client, resource_group_name, namespace_name, name, key_type):
    return client.regenerate_keys(
        resource_group_name=resource_group_name,
        namespace_name=namespace_name,
        authorization_rule_name=name,
        parameters={'key_type': key_type}
    )


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

    instance.lock_duration = return_valid_duration(instance.lock_duration, lock_duration)

    if max_size_in_megabytes:
        instance.max_size_in_megabytes = max_size_in_megabytes

    if requires_duplicate_detection:
        instance.requires_duplicate_detection = requires_duplicate_detection

    if requires_session:
        instance.requires_session = requires_session

    instance.default_message_time_to_live = return_valid_duration(instance.default_message_time_to_live, default_message_time_to_live)

    if dead_lettering_on_message_expiration:
        instance.dead_lettering_on_message_expiration = dead_lettering_on_message_expiration

    instance.duplicate_detection_history_time_window = return_valid_duration(instance.duplicate_detection_history_time_window, duplicate_detection_history_time_window)

    if max_delivery_count:
        instance.max_delivery_count = max_delivery_count

    if status:
        instance.status = status

    instance.auto_delete_on_idle = return_valid_duration(instance.auto_delete_on_idle, auto_delete_on_idle)

    if enable_partitioning:
        instance.enable_partitioning = enable_partitioning

    if enable_express:
        instance.enable_express = enable_express

    if forward_to:
        instance.forward_to = forward_to

    if forward_dead_lettered_messages_to:
        instance.forward_dead_lettered_messages_to = forward_dead_lettered_messages_to

    if enable_batched_operations:
        instance.enable_batched_operations = enable_batched_operations

    return instance


# Queue Authorization rule:
def cli_queueautho_create(client, resource_group_name, namespace_name, queue_name, name, rights=None):
    from azure.cli.command_modules.servicebus._utils import accessrights_converter
    return client.create_or_update_authorization_rule(
        resource_group_name=resource_group_name,
        namespace_name=namespace_name,
        queue_name=queue_name,
        authorization_rule_name=name,
        parameters={'rights': accessrights_converter(rights)}
    )


def cli_queueauthokey_renew(client, resource_group_name, namespace_name, queue_name, name, key_type=None, key=None):

    return client.regenerate_keys(
        resource_group_name=resource_group_name,
        namespace_name=namespace_name,
        queue_name=queue_name,
        authorization_rule_name=name,
        parameters={'key_type': key_type, 'key': key}
    )


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

    instance.default_message_time_to_live = return_valid_duration(instance.default_message_time_to_live, default_message_time_to_live)

    if max_size_in_megabytes:
        instance.max_size_in_megabytes = max_size_in_megabytes

    if requires_duplicate_detection:
        instance.requires_duplicate_detection = requires_duplicate_detection

    instance.duplicate_detection_history_time_window = return_valid_duration(instance.duplicate_detection_history_time_window, duplicate_detection_history_time_window)

    if enable_batched_operations:
        instance.enable_batched_operations = enable_batched_operations

    if status:
        instance.status = status

    if support_ordering:
        instance.support_ordering = support_ordering

    instance.auto_delete_on_idle = return_valid_duration(instance.auto_delete_on_idle, auto_delete_on_idle)

    if enable_partitioning:
        instance.enable_partitioning = enable_partitioning

    if enable_express:
        instance.enable_express = enable_express

    return instance


# Topic Authorization rule
def cli_topicautho_create(client, resource_group_name, namespace_name, topic_name, name, rights=None):
    from azure.cli.command_modules.servicebus._utils import accessrights_converter
    return client.create_or_update_authorization_rule(
        resource_group_name=resource_group_name,
        namespace_name=namespace_name,
        topic_name=topic_name,
        authorization_rule_name=name,
        parameters={'rights': accessrights_converter(rights)}
    )


def cli_topicauthokey_renew(client, resource_group_name, namespace_name, topic_name, name, key_type=None, key=None):

    return client.regenerate_keys(
        resource_group_name=resource_group_name,
        namespace_name=namespace_name,
        topic_name=topic_name,
        authorization_rule_name=name,
        parameters={'key_type': key_type, 'key': key}
    )


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

    instance.lock_duration = return_valid_duration(instance.lock_duration, lock_duration)

    if requires_session:
        instance.requires_session = requires_session

    instance.default_message_time_to_live = return_valid_duration(instance.default_message_time_to_live, default_message_time_to_live)

    if dead_lettering_on_message_expiration:
        instance.dead_lettering_on_message_expiration = dead_lettering_on_message_expiration

    if max_delivery_count:
        instance.max_delivery_count = max_delivery_count

    if status:
        instance.status = status

    if enable_batched_operations:
        instance.enable_batched_operations = enable_batched_operations

    instance.auto_delete_on_idle = return_valid_duration(instance.auto_delete_on_idle, auto_delete_on_idle)

    if forward_to:
        instance.forward_to = forward_to

    if forward_dead_lettered_messages_to:
        instance.forward_dead_lettered_messages_to = forward_dead_lettered_messages_to

    if dead_lettering_on_filter_evaluation_exceptions is not None:
        instance.dead_lettering_on_filter_evaluation_exceptions = dead_lettering_on_filter_evaluation_exceptions

    return instance


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


# DisasterRecoveryConfigs Region
def cli_georecovery_alias_create(client, resource_group_name, namespace_name, alias,
                                 partner_namespace, alternate_name=None):

    parameters = {
        'partner_namespace': partner_namespace,
        'alternate_name': alternate_name,
    }
    return client.create_or_update(resource_group_name=resource_group_name, namespace_name=namespace_name,
                                   alias=alias, parameters=parameters)


def cli_georecovery_alias_exists(client, resource_group_name, namespace_name, name):

    return client.check_name_availability(resource_group_name=resource_group_name,
                                          namespace_name=namespace_name,
                                          parameters={'name': name})


# MigrationConfigs Region
def cli_migration_start(client, resource_group_name, namespace_name,
                        target_namespace, post_migration_name, config_name="$default"):
    import time
    parameters = {
        'target_namespace': target_namespace,
        'post_migration_name': post_migration_name
    }
    client.begin_create_and_start_migration(resource_group_name, namespace_name, config_name, parameters)
    getresponse = client.get(resource_group_name, namespace_name, config_name)

    # pool till Provisioning state is succeeded
    while getresponse.provisioning_state != 'Succeeded':
        time.sleep(30)
        getresponse = client.get(resource_group_name, namespace_name, config_name)

    # poll on the 'pendingReplicationOperationsCount' to be 0 or none
    while getresponse.pending_replication_operations_count != 0 and getresponse.pending_replication_operations_count is not None:
        time.sleep(30)
        getresponse = client.get(resource_group_name, namespace_name, config_name)

    return client.get(resource_group_name, namespace_name, config_name)


def cli_migration_show(client, resource_group_name, namespace_name, config_name="$default"):

    return client.get(resource_group_name, namespace_name, config_name)


def cli_migration_complete(client, resource_group_name, namespace_name, config_name="$default"):

    return client.complete_migration(resource_group_name, namespace_name, config_name)


iso8601pattern = re.compile("^P(?!$)(\\d+Y)?(\\d+M)?(\\d+W)?(\\d+D)?(T(?=\\d)(\\d+H)?(\\d+M)?(\\d+.)?(\\d+S)?)?$")
timedeltapattern = re.compile("^\\d+:\\d+:\\d+$")


def return_valid_duration(instance_value, update_value):
    from datetime import timedelta
    from isodate import parse_duration
    from azure.cli.command_modules.servicebus.constants import DURATION_SECS, DURATION_MIN, DURATION_DAYS
    if update_value is not None:
        value_toreturn = update_value
    else:
        value_toreturn = str(instance_value)

    if iso8601pattern.match(value_toreturn):
        if parse_duration(value_toreturn) > timedelta(days=DURATION_DAYS, minutes=DURATION_MIN, seconds=DURATION_SECS):
            return timedelta(days=DURATION_DAYS, minutes=DURATION_MIN, seconds=DURATION_SECS)
        return value_toreturn

    if timedeltapattern.match(value_toreturn):
        day, minute, seconds = value_toreturn.split(":")
        if timedelta(days=int(day), minutes=int(minute), seconds=int(seconds)) <= timedelta(days=DURATION_DAYS,
                                                                                            minutes=DURATION_MIN,
                                                                                            seconds=DURATION_SECS):
            return timedelta(days=int(day), minutes=int(minute), seconds=int(seconds))
        return timedelta(days=DURATION_DAYS, minutes=DURATION_MIN, seconds=DURATION_SECS)


# to check the timespan value
def return_valid_duration_create(update_value):
    from datetime import timedelta
    from isodate import parse_duration
    from knack.util import CLIError
    from azure.cli.command_modules.servicebus.constants import DURATION_SECS, DURATION_MIN, DURATION_DAYS
    if update_value is not None:
        if iso8601pattern.match(update_value):
            if parse_duration(update_value) > timedelta(days=DURATION_DAYS, minutes=DURATION_MIN, seconds=DURATION_SECS):
                raise CLIError(
                    'duration value should be less than (days:min:secs) 10675199:10085:477581')

        if timedeltapattern.match(update_value):
            day, minute, seconds = update_value.split(":")
            if timedelta(days=int(day), minutes=int(minute), seconds=int(seconds)) <= timedelta(days=DURATION_DAYS, minutes=DURATION_MIN, seconds=DURATION_SECS):
                update_value = timedelta(days=int(day), minutes=int(minute), seconds=int(seconds))
            else:
                raise CLIError(
                    'duration value should be less than timedelta(days=DURATION_DAYS, minutes=DURATION_MIN, seconds=DURATION_SECS)')

    return update_value


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

def cli_add_identity(cmd, client, resource_group_name, namespace_name, system_assigned=None, user_assigned=None):
    namespace = client.get(resource_group_name, namespace_name)
    IdentityType = cmd.get_models('ManagedServiceIdentityType', resource_type=ResourceType.MGMT_SERVICEBUS)
    Identity = cmd.get_models('Identity', resource_type=ResourceType.MGMT_SERVICEBUS)
    UserAssignedIdentity = cmd.get_models('UserAssignedIdentity', resource_type=ResourceType.MGMT_SERVICEBUS)

    identity_id = {}

    if namespace.identity is None:
        namespace.identity = Identity()

    if system_assigned:
        if namespace.identity.type == IdentityType.USER_ASSIGNED:
            namespace.identity.type = IdentityType.SYSTEM_ASSIGNED_USER_ASSIGNED

        elif namespace.identity.type == IdentityType.NONE or namespace.identity.type is None:
            namespace.identity.type = IdentityType.SYSTEM_ASSIGNED

    if user_assigned:
        default_user_identity = UserAssignedIdentity()
        identity_id.update(dict.fromkeys(user_assigned, default_user_identity))

        if namespace.identity.user_assigned_identities is None:
            namespace.identity.user_assigned_identities = identity_id
        else:
            namespace.identity.user_assigned_identities.update(identity_id)

        if namespace.identity.type == IdentityType.SYSTEM_ASSIGNED:
            namespace.identity.type = IdentityType.SYSTEM_ASSIGNED_USER_ASSIGNED

        elif namespace.identity.type == IdentityType.NONE or namespace.identity.type is None:
            namespace.identity.type = IdentityType.USER_ASSIGNED

    client.begin_create_or_update(
        resource_group_name=resource_group_name,
        namespace_name=namespace_name,
        parameters=namespace).result()

    get_namespace = client.get(resource_group_name, namespace_name)

    return get_namespace

def cli_remove_identity(cmd, client, resource_group_name, namespace_name, system_assigned = None, user_assigned = None):
    namespace = client.get(resource_group_name, namespace_name)
    IdentityType = cmd.get_models('ManagedServiceIdentityType', resource_type=ResourceType.MGMT_SERVICEBUS)
    Identity = cmd.get_models('Identity', resource_type=ResourceType.MGMT_SERVICEBUS)
    UserAssignedIdentity = cmd.get_models('UserAssignedIdentity', resource_type=ResourceType.MGMT_SERVICEBUS)

    from azure.cli.core import CLIError

    if namespace.identity is None:
        raise CLIError('The namespace does not have identity enabled')

    if system_assigned:
        if namespace.identity.type == IdentityType.SYSTEM_ASSIGNED:
            namespace.identity.type = IdentityType.NONE

        if namespace.identity.type == IdentityType.SYSTEM_ASSIGNED_USER_ASSIGNED:
            namespace.identity.type = IdentityType.USER_ASSIGNED

    if user_assigned:
        if namespace.identity.type == IdentityType.USER_ASSIGNED:
            if namespace.identity.user_assigned_identities:
                for x in user_assigned:
                    namespace.identity.user_assigned_identities.pop(x)
                # if all identities are popped off of the dictionary, we disable user assigned identity
                if len(namespace.identity.user_assigned_identities)==0:
                    namespace.identity.type = IdentityType.NONE
                    namespace.identity.user_assigned_identities = None

        if namespace.identity.type == IdentityType.SYSTEM_ASSIGNED_USER_ASSIGNED:
            if namespace.identity.user_assigned_identities:
                for x in user_assigned:
                    namespace.identity.user_assigned_identities.pop(x)
                # if all identities are popped off of the dictionary, we disable user assigned identity
                if len(namespace.identity.user_assigned_identities)==0:
                    namespace.identity.type = IdentityType.SYSTEM_ASSIGNED
                    namespace.identity.user_assigned_identities = None

    client.begin_create_or_update(
        resource_group_name=resource_group_name,
        namespace_name=namespace_name,
        parameters=namespace).result()

    get_namespace = client.get(resource_group_name, namespace_name)

    return get_namespace

def cli_add_encryption(cmd, client, resource_group_name, namespace_name, encryption_config):
    namespace = client.get(resource_group_name, namespace_name)
    Encryption = cmd.get_models('Encryption', resource_type=ResourceType.MGMT_SERVICEBUS)
    KeyVaultProperties = cmd.get_models('KeyVaultProperties', resource_type=ResourceType.MGMT_SERVICEBUS)

    if namespace.encryption:
        if namespace.encryption.key_vault_properties:
            namespace.encryption.key_vault_properties.extend(encryption_config)
        else:
            namespace.encryption.key_vault_properties = encryption_config

    else:
        namespace.encryption = Encryption()
        namespace.encryption.key_vault_properties = encryption_config

    client.begin_create_or_update(
        resource_group_name=resource_group_name,
        namespace_name=namespace_name,
        parameters=namespace).result()

    get_namespace = client.get(resource_group_name, namespace_name)

    return get_namespace


def cli_remove_encryption(cmd, client, resource_group_name, namespace_name, encryption_config):
    namespace = client.get(resource_group_name, namespace_name)
    Encryption = cmd.get_models('Encryption', resource_type=ResourceType.MGMT_SERVICEBUS)
    KeyVaultProperties = cmd.get_models('KeyVaultProperties', resource_type=ResourceType.MGMT_SERVICEBUS)

    if namespace.encryption is None:
        raise CLIError('The namespace does not have encryption enabled')

    else:
        if namespace.encryption.key_vault_properties:
            for property in encryption_config:
                if property in namespace.encryption.key_vault_properties:
                    namespace.encryption.key_vault_properties.remove(property)

        client.begin_create_or_update(
            resource_group_name=resource_group_name,
            namespace_name=namespace_name,
            parameters=namespace).result()

    get_namespace = client.get(resource_group_name, namespace_name)

    return get_namespace