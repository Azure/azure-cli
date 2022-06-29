# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
# pylint: disable=too-many-lines
# pylint: disable=inconsistent-return-statements
# pylint: disable=too-many-locals

from azure.cli.core.profiles import ResourceType


# , resource_type = ResourceType.MGMT_EVENTHUB
# Namespace Region
def cli_namespace_create(cmd, client, resource_group_name, namespace_name, location=None, tags=None, sku='Standard', capacity=None,
                         is_auto_inflate_enabled=None, maximum_throughput_units=None, is_kafka_enabled=None,
                         default_action=None, identity=None, zone_redundant=None, cluster_arm_id=None, trusted_service_access_enabled=None,
                         disable_local_auth=None, mi_system_assigned=None, mi_user_assigned=None, encryption_config=None):
    EHNamespace = cmd.get_models('EHNamespace', resource_type=ResourceType.MGMT_EVENTHUB)
    Sku = cmd.get_models('Sku', resource_type=ResourceType.MGMT_EVENTHUB)
    Identity = cmd.get_models('Identity', resource_type=ResourceType.MGMT_EVENTHUB)
    IdentityType = cmd.get_models('ManagedServiceIdentityType', resource_type=ResourceType.MGMT_EVENTHUB)
    UserAssignedIdentity = cmd.get_models('UserAssignedIdentity', resource_type=ResourceType.MGMT_EVENTHUB)
    Encryption = cmd.get_models('Encryption', resource_type=ResourceType.MGMT_EVENTHUB)

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

        if identity or mi_system_assigned:
            ehparam.identity = Identity(type=IdentityType.SYSTEM_ASSIGNED)

        if mi_user_assigned:
            if ehparam.identity:
                if ehparam.identity.type == IdentityType.SYSTEM_ASSIGNED:
                    ehparam.identity.type = IdentityType.SYSTEM_ASSIGNED_USER_ASSIGNED
                else:
                    ehparam.identity.type = IdentityType.USER_ASSIGNED
            else:
                ehparam.identity = Identity(type=IdentityType.USER_ASSIGNED)

            default_user_identity = UserAssignedIdentity()
            ehparam.identity.user_assigned_identities = dict.fromkeys(mi_user_assigned, default_user_identity)

        if encryption_config:
            ehparam.encryption = Encryption()
            ehparam.encryption.key_vault_properties = encryption_config

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

        if is_auto_inflate_enabled is not None:
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

        if enabled is not None and not instance.capture_description:
            instance.capture_description = capturedescription()
            instance.capture_description.destination = destination()
            instance.capture_description.encoding = encodingcapturedescription.avro
            instance.capture_description.enabled = enabled

        if instance.capture_description:
            if enabled is not None:
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


def cli_networkrule_update(cmd, client, resource_group_name, namespace_name, public_network_access=None, trusted_service_access_enabled=None,
                           default_action=None):
    networkruleset = client.get_network_rule_set(resource_group_name, namespace_name)

    if trusted_service_access_enabled is not None:
        networkruleset.trusted_service_access_enabled = trusted_service_access_enabled

    if public_network_access:
        networkruleset.public_network_access = public_network_access

    if default_action:
        networkruleset.default_action = default_action

    return client.create_or_update_network_rule_set(resource_group_name, namespace_name, networkruleset)


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


def cli_add_identity(cmd, client, resource_group_name, namespace_name, system_assigned=None, user_assigned=None):
    namespace = client.get(resource_group_name, namespace_name)
    IdentityType = cmd.get_models('ManagedServiceIdentityType', resource_type=ResourceType.MGMT_EVENTHUB)
    Identity = cmd.get_models('Identity', resource_type=ResourceType.MGMT_EVENTHUB)
    UserAssignedIdentity = cmd.get_models('UserAssignedIdentity', resource_type=ResourceType.MGMT_EVENTHUB)

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


def cli_remove_identity(cmd, client, resource_group_name, namespace_name, system_assigned=None, user_assigned=None):
    namespace = client.get(resource_group_name, namespace_name)
    IdentityType = cmd.get_models('ManagedServiceIdentityType', resource_type=ResourceType.MGMT_EVENTHUB)

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
                if len(namespace.identity.user_assigned_identities) == 0:
                    namespace.identity.type = IdentityType.NONE
                    namespace.identity.user_assigned_identities = None

        if namespace.identity.type == IdentityType.SYSTEM_ASSIGNED_USER_ASSIGNED:
            if namespace.identity.user_assigned_identities:
                for x in user_assigned:
                    namespace.identity.user_assigned_identities.pop(x)
                # if all identities are popped off of the dictionary, we disable user assigned identity
                if len(namespace.identity.user_assigned_identities) == 0:
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
    Encryption = cmd.get_models('Encryption', resource_type=ResourceType.MGMT_EVENTHUB)

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


def cli_remove_encryption(client, resource_group_name, namespace_name, encryption_config):
    namespace = client.get(resource_group_name, namespace_name)

    from azure.cli.core import CLIError

    if namespace.encryption is None:
        raise CLIError('The namespace does not have encryption enabled')

    if namespace.encryption.key_vault_properties:
        for encryption_property in encryption_config:
            if encryption_property in namespace.encryption.key_vault_properties:
                namespace.encryption.key_vault_properties.remove(encryption_property)

    client.begin_create_or_update(
        resource_group_name=resource_group_name,
        namespace_name=namespace_name,
        parameters=namespace).result()

    get_namespace = client.get(resource_group_name, namespace_name)

    return get_namespace


def cli_schemaregistry_createupdate(cmd, client, resource_group_name, namespace_name, schema_group_name,
                                    schema_compatibility, schema_type, tags=None):
    SchemaGroup = cmd.get_models('SchemaGroup', resource_type=ResourceType.MGMT_EVENTHUB)
    ehSchemaGroup = SchemaGroup(schema_compatibility=schema_compatibility, schema_type=schema_type, group_properties=tags)

    return client.create_or_update(resource_group_name, namespace_name, schema_group_name, ehSchemaGroup)


def cli_appgroup_create(cmd, client, resource_group_name, namespace_name, application_group_name, client_app_group_identifier,
                        throttling_policy_config, is_enabled=None):
    ApplicationGroup = cmd.get_models('ApplicationGroup', resource_type=ResourceType.MGMT_EVENTHUB)
    appGroup = ApplicationGroup(policies=throttling_policy_config, client_app_group_identifier=client_app_group_identifier)

    if is_enabled is not None:
        ApplicationGroup.is_enabled = is_enabled

    return client.create_or_update_application_group(resource_group_name, namespace_name, application_group_name, appGroup)


def cli_appgroup_update(client, resource_group_name, namespace_name, application_group_name, is_enabled=None):
    appGroup = client.get(resource_group_name, namespace_name, application_group_name)

    if is_enabled is not None:
        appGroup.is_enabled = is_enabled

    return client.create_or_update_application_group(resource_group_name, namespace_name, application_group_name, appGroup)


def cli_add_appgroup_policy(client, resource_group_name, namespace_name, application_group_name, throttling_policy_config):
    appGroup = client.get(resource_group_name, namespace_name, application_group_name)
    appGroup.policies.extend(throttling_policy_config)
    return client.create_or_update_application_group(resource_group_name, namespace_name, application_group_name, appGroup)


def cli_remove_appgroup_policy(client, resource_group_name, namespace_name, application_group_name, throttling_policy_config):
    from azure.cli.core import CLIError

    appGroup = client.get(resource_group_name, namespace_name, application_group_name)

    if appGroup.policies:
        for policy_object in throttling_policy_config:
            if policy_object in appGroup.policies:
                appGroup.policies.remove(policy_object)
            else:
                raise CLIError('The following policy was not found: Name: ' + policy_object.name + ', RateLimitThreshold: ' + str(policy_object.rate_limit_threshold) + ', MetricId: ' + policy_object.metric_id)

    return client.create_or_update_application_group(resource_group_name, namespace_name, application_group_name, appGroup)
