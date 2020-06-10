# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
# pylint: disable=too-many-lines
# pylint: disable=inconsistent-return-statements
from azure.cli.core.profiles import ResourceType


# , resource_type = ResourceType.MGMT_EVENTHUB
# Namespace Region
def cli_namespace_create(cmd, client, resource_group_name, namespace_name, location=None, tags=None, sku='Standard', capacity=None, is_auto_inflate_enabled=None, maximum_throughput_units=None, is_kafka_enabled=None, default_action=None):
    # from azure.mgmt.eventhub.models import EHNamespace, Sku
    EHNamespace = cmd.get_models('EHNamespace', resource_type=ResourceType.MGMT_EVENTHUB)
    Sku = cmd.get_models('Sku', resource_type=ResourceType.MGMT_EVENTHUB)

    if cmd.supported_api_version(resource_type=ResourceType.MGMT_EVENTHUB, min_api='2017-04-01'):
        client.create_or_update(
            resource_group_name=resource_group_name,
            namespace_name=namespace_name,
            parameters=EHNamespace(
                location=location,
                tags=tags,
                sku=Sku(name=sku, tier=sku, capacity=capacity),
                is_auto_inflate_enabled=is_auto_inflate_enabled,
                maximum_throughput_units=maximum_throughput_units,
                kafka_enabled=is_kafka_enabled)).result()

    if default_action:
        netwrokruleset = client.get_network_rule_set(resource_group_name, namespace_name)
        netwrokruleset.default_action = default_action
        client.create_or_update_network_rule_set(resource_group_name, namespace_name, netwrokruleset)

    return client.get(resource_group_name, namespace_name)


def cli_namespace_update(cmd, client, instance, tags=None, sku=None, capacity=None, is_auto_inflate_enabled=None, maximum_throughput_units=None, is_kafka_enabled=None, default_action=None):

    if cmd.supported_api_version(resource_type=ResourceType.MGMT_EVENTHUB, min_api='2017-04-01'):
        if tags:
            instance.tags = tags

        if sku:
            instance.sku.name = sku
            instance.sku.tier = sku

        if capacity:
            instance.sku.capacity = capacity

        if is_auto_inflate_enabled:
            instance.is_auto_inflate_enabled = is_auto_inflate_enabled

        if maximum_throughput_units:
            instance.maximum_throughput_units = maximum_throughput_units

        if is_kafka_enabled:
            instance.kafka_enabled = is_kafka_enabled

        if default_action:
            resourcegroup = instance.id.split('/')[4]
            netwrokruleset = client.get_network_rule_set(resourcegroup, instance.name)
            netwrokruleset.default_action = default_action
            client.create_or_update_network_rule_set(resourcegroup, instance.name, netwrokruleset)

    return instance


def cli_namespace_list(cmd, client, resource_group_name=None):
    if cmd.supported_api_version(min_api='2017-04-01'):
        if resource_group_name:
            return client.list_by_resource_group(resource_group_name=resource_group_name)

    return client.list()


# Namespace Authorization rule:
def cli_autho_update(cmd, instance, rights):
    if cmd.supported_api_version(resource_type=ResourceType.MGMT_EVENTHUB, min_api='2017-04-01'):
        from azure.cli.command_modules.eventhubs._utils import accessrights_converter
        instance.rights = accessrights_converter(rights)
    return instance


# Eventhub Region
def cli_eheventhub_create(cmd, client, resource_group_name, namespace_name, event_hub_name, message_retention_in_days=None, partition_count=None, status=None,
                          enabled=None, skip_empty_archives=None, capture_interval_seconds=None, capture_size_limit_bytes=None, destination_name=None, storage_account_resource_id=None, blob_container=None, archive_name_format=None):
    # from azure.mgmt.eventhub.models import Eventhub, CaptureDescription, Destination, EncodingCaptureDescription
    Eventhub = cmd.get_models('Eventhub', resource_type=ResourceType.MGMT_EVENTHUB)
    CaptureDescription = cmd.get_models('CaptureDescription', resource_type=ResourceType.MGMT_EVENTHUB)
    Destination = cmd.get_models('Destination', resource_type=ResourceType.MGMT_EVENTHUB)
    EncodingCaptureDescription = cmd.get_models('EncodingCaptureDescription', resource_type=ResourceType.MGMT_EVENTHUB)

    eventhubparameter1 = Eventhub()

    if cmd.supported_api_version(resource_type=ResourceType.MGMT_EVENTHUB, min_api='2017-04-01'):
        if message_retention_in_days:
            eventhubparameter1.message_retention_in_days = message_retention_in_days

        if partition_count:
            eventhubparameter1.partition_count = partition_count

        if status:
            eventhubparameter1.status = status

        if enabled and enabled is True:
            eventhubparameter1.capture_description = CaptureDescription(
                enabled=enabled,
                skip_empty_archives=skip_empty_archives,
                encoding=EncodingCaptureDescription.avro,
                interval_in_seconds=capture_interval_seconds,
                size_limit_in_bytes=capture_size_limit_bytes,
                destination=Destination(
                    name=destination_name,
                    storage_account_resource_id=storage_account_resource_id,
                    blob_container=blob_container,
                    archive_name_format=archive_name_format)
            )
    return client.create_or_update(
        resource_group_name=resource_group_name,
        namespace_name=namespace_name,
        event_hub_name=event_hub_name,
        parameters=eventhubparameter1)


def cli_eheventhub_update(cmd, instance, message_retention_in_days=None, partition_count=None, status=None,
                          enabled=None, skip_empty_archives=None, capture_interval_seconds=None,
                          capture_size_limit_bytes=None, destination_name=None, storage_account_resource_id=None,
                          blob_container=None, archive_name_format=None):
    capturedescription, destination, encodingcapturedescription = cmd.get_models('CaptureDescription', 'Destination', 'EncodingCaptureDescription')

    if cmd.supported_api_version(resource_type=ResourceType.MGMT_EVENTHUB, min_api='2017-04-01'):
        if message_retention_in_days:
            instance.message_retention_in_days = message_retention_in_days

        if partition_count:
            instance.partition_count = partition_count

        if status:
            instance.status = status

        if enabled and not instance.capture_description:
            instance.capture_description = capturedescription()
            instance.capture_description.destination = destination()
            instance.capture_description.encoding = encodingcapturedescription.avro
            instance.capture_description.enabled = enabled

        if enabled and instance.capture_description:
            instance.capture_description.enabled = enabled
            if capture_interval_seconds:
                instance.capture_description.interval_in_seconds = capture_interval_seconds
            if capture_size_limit_bytes:
                instance.capture_description.size_limit_in_bytes = capture_size_limit_bytes
            if destination_name:
                instance.capture_description.destination.name = destination_name
            if storage_account_resource_id:
                instance.capture_description.destination.storage_account_resource_id = storage_account_resource_id
            if blob_container:
                instance.capture_description.destination.blob_container = blob_container
            if archive_name_format:
                instance.capture_description.destination.archive_name_format = archive_name_format
            if skip_empty_archives:
                instance.capture_description.skip_empty_archives = skip_empty_archives

    return instance


# NetwrokRuleSet Region
def cli_networkrule_createupdate(cmd, client, resource_group_name, namespace_name, subnet=None, ip_mask=None, ignore_missing_vnet_service_endpoint=False, action='Allow'):
    NWRuleSetVirtualNetworkRules = cmd.get_models('NWRuleSetVirtualNetworkRules', resource_type=ResourceType.MGMT_EVENTHUB)
    Subnet = cmd.get_models('Subnet', resource_type=ResourceType.MGMT_EVENTHUB)
    NWRuleSetIpRules = cmd.get_models('NWRuleSetIpRules', resource_type=ResourceType.MGMT_EVENTHUB)

    netwrokruleset = client.get_network_rule_set(resource_group_name, namespace_name)

    if cmd.supported_api_version(resource_type=ResourceType.MGMT_EVENTHUB, min_api='2017-04-01'):
        if netwrokruleset.virtual_network_rules is None:
            netwrokruleset.virtual_network_rules = [NWRuleSetVirtualNetworkRules]

        if netwrokruleset.ip_rules is None:
            netwrokruleset.ip_rules = [NWRuleSetIpRules]

        if subnet:
            netwrokruleset.virtual_network_rules.append(NWRuleSetVirtualNetworkRules(subnet=Subnet(id=subnet),
                                                                                     ignore_missing_vnet_service_endpoint=ignore_missing_vnet_service_endpoint))

        if ip_mask:
            netwrokruleset.ip_rules.append(NWRuleSetIpRules(ip_mask=ip_mask, action=action))

    return client.create_or_update_network_rule_set(resource_group_name, namespace_name, netwrokruleset)


def cli_networkrule_delete(cmd, client, resource_group_name, namespace_name, subnet=None, ip_mask=None):
    NWRuleSetVirtualNetworkRules = cmd.get_models('NWRuleSetVirtualNetworkRules', resource_type=ResourceType.MGMT_EVENTHUB)
    NWRuleSetIpRules = cmd.get_models('NWRuleSetIpRules', resource_type=ResourceType.MGMT_EVENTHUB)
    netwrokruleset = client.get_network_rule_set(resource_group_name, namespace_name)
    if cmd.supported_api_version(resource_type=ResourceType.MGMT_EVENTHUB, min_api='2017-04-01'):
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
