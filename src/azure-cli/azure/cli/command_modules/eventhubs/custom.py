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
def cli_namespace_create(cmd, client, resource_group_name, namespace_name, location=None, tags=None, sku='Standard', capacity=None,
                         is_auto_inflate_enabled=None, maximum_throughput_units=None, is_kafka_enabled=None,
                         default_action=None, identity=None, zone_redundant=None, cluster_arm_id=None, trusted_service_access_enabled=None,
                         disable_local_auth=None):
    EHNamespace = cmd.get_models('EHNamespace', resource_type=ResourceType.MGMT_EVENTHUB)
    Sku = cmd.get_models('Sku', resource_type=ResourceType.MGMT_EVENTHUB)
    Identity = cmd.get_models('Identity', resource_type=ResourceType.MGMT_EVENTHUB)
    IdentityType = cmd.get_models('ManagedServiceIdentityType', resource_type=ResourceType.MGMT_EVENTHUB)

    if cmd.supported_api_version(resource_type=ResourceType.MGMT_EVENTHUB, min_api='2018-01-01-preview'):
        ehparam = EHNamespace()
        ehparam.location = location
        ehparam.tags = tags
        ehparam.sku = Sku(name=sku, tier=sku, capacity=capacity)
        ehparam.is_auto_inflate_enabled = is_auto_inflate_enabled
        ehparam.maximum_throughput_units = maximum_throughput_units
        ehparam.kafka_enabled = is_kafka_enabled
        ehparam.zone_redundant = zone_redundant
        ehparam.disable_local_auth = disable_local_auth
        ehparam.cluster_arm_id = cluster_arm_id
        if identity:
            ehparam.identity = Identity(type=IdentityType.SYSTEM_ASSIGNED)

        client.begin_create_or_update(
            resource_group_name=resource_group_name,
            namespace_name=namespace_name,
            parameters=ehparam).result()

    if default_action or trusted_service_access_enabled:
        netwrokruleset = client.get_network_rule_set(resource_group_name, namespace_name)
        netwrokruleset.default_action = default_action
        netwrokruleset.trusted_service_access_enabled = trusted_service_access_enabled
        client.create_or_update_network_rule_set(resource_group_name, namespace_name, netwrokruleset)

    return client.get(resource_group_name, namespace_name)


def cli_namespace_update(cmd, client, instance, tags=None, sku=None, capacity=None, is_auto_inflate_enabled=None,
                         maximum_throughput_units=None, is_kafka_enabled=None, default_action=None,
                         identity=None, key_source=None, key_name=None, key_vault_uri=None, key_version=None, trusted_service_access_enabled=None,
                         disable_local_auth=None, require_infrastructure_encryption=None):
    Encryption = cmd.get_models('Encryption', resource_type=ResourceType.MGMT_EVENTHUB)
    KeyVaultProperties = cmd.get_models('KeyVaultProperties', resource_type=ResourceType.MGMT_EVENTHUB)
    Identity = cmd.get_models('Identity', resource_type=ResourceType.MGMT_EVENTHUB)
    IdentityType = cmd.get_models('ManagedServiceIdentityType', resource_type=ResourceType.MGMT_EVENTHUB)

    if cmd.supported_api_version(resource_type=ResourceType.MGMT_EVENTHUB, min_api='2021-06-01-preview'):
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

        if identity is True and instance.identity is None:
            instance.identity = Identity(type=IdentityType.SYSTEM_ASSIGNED)
        elif instance.identity and instance.encryption is None:
            instance.encryption = Encryption()
            if key_source:
                instance.encryption.key_source = key_source
            if key_name and key_vault_uri:
                keyprop = []
                keyprop.append(KeyVaultProperties(key_name=key_name, key_vault_uri=key_vault_uri, key_version=key_version))
                instance.encryption.key_vault_properties = keyprop
            if require_infrastructure_encryption:
                instance.encryption.require_infrastructure_encryption = require_infrastructure_encryption

        if default_action:
            resourcegroup = instance.id.split('/')[4]
            netwrokruleset = client.get_network_rule_set(resourcegroup, instance.name)
            netwrokruleset.default_action = default_action
            netwrokruleset.trusted_service_access_enabled = trusted_service_access_enabled
            client.create_or_update_network_rule_set(resourcegroup, instance.name, netwrokruleset)

        if disable_local_auth:
            instance.disable_local_auth = disable_local_auth

    return instance


def cli_namespace_list(cmd, client, resource_group_name=None):
    if cmd.supported_api_version(min_api='2021-06-01-preview'):
        if resource_group_name:
            return client.list_by_resource_group(resource_group_name=resource_group_name)

    return client.list()


def cli_namespace_exists(client, name):

    return client.check_name_availability(parameters={'name': name})


# Cluster region
def cli_cluster_create(cmd, client, resource_group_name, cluster_name, location=None, tags=None, capacity=None):
    Cluster = cmd.get_models('Cluster', resource_type=ResourceType.MGMT_EVENTHUB)
    ClusterSku = cmd.get_models('ClusterSku', resource_type=ResourceType.MGMT_EVENTHUB)

    if cmd.supported_api_version(resource_type=ResourceType.MGMT_EVENTHUB, min_api='2016-06-01-preview'):
        ehparam = Cluster()
        ehparam.sku = ClusterSku(name='Dedicated')
        ehparam.location = location
        if not capacity:
            ehparam.sku.capacity = 1
        ehparam.tags = tags
        cluster_result = client.begin_create_or_update(
            resource_group_name=resource_group_name,
            cluster_name=cluster_name,
            parameters=ehparam).result()

    return cluster_result


def cli_cluster_update(cmd, instance, tags=None):
    if cmd.supported_api_version(resource_type=ResourceType.MGMT_EVENTHUB, min_api='2016-06-01-preview'):
        if tags:
            instance.tags = tags
    return instance


# Namespace Authorization rule:
def cli_namespaceautho_create(client, resource_group_name, namespace_name, name, rights=None):
    from azure.cli.command_modules.eventhubs._utils import accessrights_converter
    return client.create_or_update_authorization_rule(
        resource_group_name=resource_group_name,
        namespace_name=namespace_name,
        authorization_rule_name=name,
        parameters={'rights': accessrights_converter(rights)}
    )


def cli_autho_update(cmd, instance, rights):
    if cmd.supported_api_version(resource_type=ResourceType.MGMT_EVENTHUB, min_api='2021-06-01-preview'):
        from azure.cli.command_modules.eventhubs._utils import accessrights_converter
        instance.rights = accessrights_converter(rights)
    return instance


def cli_keys_renew(client, resource_group_name, namespace_name, name, key_type, key=None):
    return client.regenerate_keys(
        resource_group_name=resource_group_name,
        namespace_name=namespace_name,
        authorization_rule_name=name,
        parameters={'key_type': key_type, 'key': key}
    )


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

        if instance.capture_description:
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


# Eventhub Authorizationrule
def cli_eventhubautho_create(client, resource_group_name, namespace_name, event_hub_name, name, rights=None):
    from azure.cli.command_modules.eventhubs._utils import accessrights_converter
    return client.create_or_update_authorization_rule(
        resource_group_name=resource_group_name,
        namespace_name=namespace_name,
        event_hub_name=event_hub_name,
        authorization_rule_name=name,
        parameters={'rights': accessrights_converter(rights)}
    )


def cli_eventhub_keys_renew(client, resource_group_name, namespace_name, event_hub_name, name, key_type, key=None):
    return client.regenerate_keys(
        resource_group_name=resource_group_name,
        namespace_name=namespace_name,
        event_hub_name=event_hub_name,
        authorization_rule_name=name,
        parameters={'key_type': key_type, 'key': key}
    )


# ConsumerGroup region
def cli_consumergroup_create(client, resource_group_name, namespace_name, event_hub_name, name, user_metadata=None):
    return client.create_or_update(
        resource_group_name=resource_group_name,
        namespace_name=namespace_name,
        event_hub_name=event_hub_name,
        consumer_group_name=name,
        parameters={'user_metadata': user_metadata}
    )


def cli_consumergroup_update(cmd, instance, user_metadata=None):
    if cmd.supported_api_version(resource_type=ResourceType.MGMT_EVENTHUB, min_api='2017-04-01'):
        if user_metadata:
            instance.user_metadata = user_metadata

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


# GeoDR region
def cli_geodr_name_exists(client, resource_group_name, namespace_name, name):

    return client.check_name_availability(resource_group_name, namespace_name, parameters={'name': name})


def cli_geodr_create(client, resource_group_name, namespace_name, alias, partner_namespace=None, alternate_name=None):

    return client.create_or_update(resource_group_name,
                                   namespace_name,
                                   alias,
                                   parameters={'partner_namespace': partner_namespace, 'alternate_name': alternate_name})


# Private Endpoint
def _update_private_endpoint_connection_status(cmd, client, resource_group_name, namespace_name,
                                               private_endpoint_connection_name, is_approved=True, description=None):
    from azure.core.exceptions import HttpResponseError
    import time

    PrivateEndpointServiceConnectionStatus = cmd.get_models('PrivateLinkConnectionStatus')

    private_endpoint_connection = client.get(resource_group_name=resource_group_name, namespace_name=namespace_name,
                                             private_endpoint_connection_name=private_endpoint_connection_name)

    old_status = private_endpoint_connection.private_link_service_connection_state.status
    if old_status != "Approved" or not is_approved:
        private_endpoint_connection.private_link_service_connection_state.status = PrivateEndpointServiceConnectionStatus.APPROVED\
            if is_approved else PrivateEndpointServiceConnectionStatus.REJECTED
        private_endpoint_connection.private_link_service_connection_state.description = description
        try:
            private_endpoint_connection = client.create_or_update(resource_group_name=resource_group_name,
                                                                  namespace_name=namespace_name,
                                                                  private_endpoint_connection_name=private_endpoint_connection_name,
                                                                  parameters=private_endpoint_connection)
        except HttpResponseError as ex:
            if 'Operation returned an invalid status ''Accepted''' in ex.message:
                time.sleep(30)
                private_endpoint_connection = client.get(resource_group_name=resource_group_name,
                                                         namespace_name=namespace_name,
                                                         private_endpoint_connection_name=private_endpoint_connection_name)
    return private_endpoint_connection


def approve_private_endpoint_connection(cmd, client, resource_group_name, namespace_name,
                                        private_endpoint_connection_name, description=None):

    return _update_private_endpoint_connection_status(
        cmd, client, resource_group_name=resource_group_name, namespace_name=namespace_name, is_approved=True,
        private_endpoint_connection_name=private_endpoint_connection_name, description=description
    )


def reject_private_endpoint_connection(cmd, client, resource_group_name, namespace_name, private_endpoint_connection_name,
                                       description=None):
    return _update_private_endpoint_connection_status(
        cmd, client, resource_group_name=resource_group_name, namespace_name=namespace_name, is_approved=False,
        private_endpoint_connection_name=private_endpoint_connection_name, description=description
    )
