# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=too-many-lines

import re
from knack.log import get_logger
from knack.util import CLIError
from msrestazure.tools import parse_resource_id
from dateutil.parser import parse   # pylint: disable=import-error,relative-import

from azure.cli.core.azclierror import MutuallyExclusiveArgumentError
from azure.mgmt.eventgrid.models import (
    EventSubscription,
    EventSubscriptionUpdateParameters,
    WebHookEventSubscriptionDestination,
    Topic,
    Domain,
    JsonInputSchemaMapping,
    JsonField,
    JsonFieldWithDefault,
    RetryPolicy,
    EventHubEventSubscriptionDestination,
    StorageQueueEventSubscriptionDestination,
    HybridConnectionEventSubscriptionDestination,
    ServiceBusQueueEventSubscriptionDestination,
    ServiceBusTopicEventSubscriptionDestination,
    AzureFunctionEventSubscriptionDestination,
    StorageBlobDeadLetterDestination,
    EventSubscriptionFilter,
    TopicUpdateParameters,
    TopicRegenerateKeyRequest,
    DomainUpdateParameters,
    DomainRegenerateKeyRequest,
    ResourceSku,
    IdentityInfo,
    PartnerRegistration,
    PartnerNamespace,
    PartnerNamespaceRegenerateKeyRequest,
    EventChannel,
    PartnerTopic,
    EventChannelSource,
    EventChannelDestination,
    SystemTopic,
    SystemTopicUpdateParameters,
    EventSubscriptionIdentity,
    DeliveryWithResourceIdentity,
    DeadLetterWithResourceIdentity,
    EventChannelFilter,
    ExtendedLocation)

logger = get_logger(__name__)

EVENTGRID_NAMESPACE = "Microsoft.EventGrid"
RESOURCES_NAMESPACE = "Microsoft.Resources"
SUBSCRIPTIONS = "subscriptions"
RESOURCE_GROUPS = "resourcegroups"
EVENTGRID_DOMAINS = "domains"
EVENTGRID_TOPICS = "topics"
EVENTGRID_DOMAIN_TOPICS = "domaintopics"
EVENTGRID_SYSTEM_TOPICS = "systemtopics"
EVENTGRID_PARTNER_REGISTRATIONS = "partnerregistration"
EVENTGRID_PARTNER_NAMESPACES = "partnernamespace"
EVENTGRID_EVENT_CHANNELS = "eventchannel"
EVENTGRID_PARTNER_TOPIC = "partnertopic"
EVENTGRID_RESOURCE_SKU = "resourceSku"
SKU_BASIC = "Basic"
SKU_PREMIUM = "Premium"
IDENTITY_NO_IDENTITY = "NoIdentity"
IDENTITY_NONE = "None"
IDENTITY_SYSTEM_ASSIGNED = "SystemAssigned"
IDENTITY_USER_ASSIGNED = "UserAssigned"
IDENTITY_MIXED_MODE = "SystemAssigned, UserAssigned"

WEBHOOK_DESTINATION = "webhook"
EVENTHUB_DESTINATION = "eventhub"
STORAGEQUEUE_DESTINATION = "storagequeue"
HYBRIDCONNECTION_DESTINATION = "hybridconnection"
SERVICEBUSQUEUE_DESTINATION = "servicebusqueue"
SERVICEBUSTOPIC_DESTINATION = "servicebustopic"
AZUREFUNCTION_DESTINATION = "azurefunction"
EVENTGRID_SCHEMA = "EventGridSchema"
CLOUDEVENTV1_0_SCHEMA = "CloudEventSchemaV1_0"
CUSTOM_EVENT_SCHEMA = "CustomEventSchema"
CUSTOM_INPUT_SCHEMA = "CustomInputSchema"
GLOBAL = "global"
KIND_AZURE = "Azure"
KIND_AZUREARC = "AzureArc"
CUSTOMLOCATION = "CustomLocation"

# Deprecated event delivery schema values
INPUT_EVENT_SCHEMA = "InputEventSchema"
CLOUDEVENTV01SCHEMA = "CloudEventV01Schema"

# Constants for the target field names of the mapping
TOPIC = "topic"
SUBJECT = "subject"
ID = "id"
EVENTTIME = "eventtime"
EVENTTYPE = "eventtype"
DATAVERSION = "dataversion"

PHONE_NUMBER_REGEX = "^\\+(?:[0-9] ?){6,15}[0-9]$"
EXTENSION_NUMBER_REGEX = "^(?:[0-9] ?){1,8}[0-9]$"

DEFAULT_TOP = 100
MAX_LONG_DESCRIPTION_LEN = 2048


def cli_topic_list(
        client,
        resource_group_name=None,
        odata_query=None):

    if resource_group_name:
        return client.list_by_resource_group(resource_group_name, odata_query, DEFAULT_TOP)

    return client.list_by_subscription(odata_query, DEFAULT_TOP)


def cli_topic_create_or_update(
        client,
        resource_group_name,
        topic_name,
        location=None,
        tags=None,
        input_schema=EVENTGRID_SCHEMA,
        input_mapping_fields=None,
        input_mapping_default_values=None,
        public_network_access=None,
        inbound_ip_rules=None,
        sku=SKU_BASIC,
        identity=None,
        user_assigned=None,
        kind=KIND_AZURE,
        extended_location_name=None,
        extended_location_type=None,
        system_assigned=None):

    final_input_schema, input_schema_mapping = _get_input_schema_and_mapping(
        input_schema,
        input_mapping_fields,
        input_mapping_default_values)
    sku_name = _get_sku(sku)
    sku_info = ResourceSku(name=sku_name)
    identity_info = None

    kind_name = _get_kind(kind)
    extended_location = _get_extended_location(kind, extended_location_name, extended_location_type)
    identity_info = _get_identity_info(identity, kind, user_assigned, system_assigned)

    topic_info = Topic(
        location=location,
        tags=tags,
        input_schema=final_input_schema,
        input_schema_mapping=input_schema_mapping,
        public_network_access=public_network_access,
        inbound_ip_rules=inbound_ip_rules,
        sku=sku_info,
        identity=identity_info,
        kind=kind_name,
        extended_location=extended_location)

    return client.begin_create_or_update(
        resource_group_name,
        topic_name,
        topic_info)


def cli_topic_update(
        client,
        resource_group_name,
        topic_name,
        tags=None,
        public_network_access=None,
        inbound_ip_rules=None,
        sku=None,
        identity=None,
        user_assigned=None,
        system_assigned=None):
    sku_info = None
    if sku is not None:
        sku_name = _get_sku(sku)
        sku_info = ResourceSku(name=sku_name)

    identity_info = _get_identity_info_only_if_not_none(identity, user_assigned, system_assigned)
    topic_update_parameters = TopicUpdateParameters(
        tags=tags,
        public_network_access=public_network_access,
        inbound_ip_rules=inbound_ip_rules,
        sku=sku_info,
        identity=identity_info)

    return client.begin_update(
        resource_group_name=resource_group_name,
        topic_name=topic_name,
        topic_update_parameters=topic_update_parameters)


def cli_topic_regenerate_key(
        client,
        resource_group_name,
        topic_name,
        key_name):
    regenerate_key_request = TopicRegenerateKeyRequest(key_name=key_name)

    return client.begin_regenerate_key(
        resource_group_name=resource_group_name,
        topic_name=topic_name,
        regenerate_key_request=regenerate_key_request
    )

def cli_topic_event_subscription_create_or_update(    # pylint: disable=too-many-locals
        client,
        resource_group_name,
        topic_name,
        event_subscription_name,
        endpoint=None,
        endpoint_type=None,
        included_event_types=None,
        subject_begins_with=None,
        subject_ends_with=None,
        is_subject_case_sensitive=False,
        max_delivery_attempts=30,
        event_ttl=1440,
        max_events_per_batch=None,
        preferred_batch_size_in_kilobytes=None,
        event_delivery_schema=None,
        deadletter_endpoint=None,
        labels=None,
        expiration_date=None,
        advanced_filter=None,
        azure_active_directory_tenant_id=None,
        azure_active_directory_application_id_or_uri=None,
        storage_queue_msg_ttl=None,
        enable_advanced_filtering_on_arrays=None,
        delivery_attribute_mapping=None):

    event_subscription_info = _get_event_subscription_info(
        endpoint=endpoint,
        endpoint_type=endpoint_type,
        included_event_types=included_event_types,
        subject_begins_with=subject_begins_with,
        subject_ends_with=subject_ends_with,
        is_subject_case_sensitive=is_subject_case_sensitive,
        max_delivery_attempts=max_delivery_attempts,
        event_ttl=event_ttl,
        max_events_per_batch=max_events_per_batch,
        preferred_batch_size_in_kilobytes=preferred_batch_size_in_kilobytes,
        event_delivery_schema=event_delivery_schema,
        deadletter_endpoint=deadletter_endpoint,
        labels=labels,
        expiration_date=expiration_date,
        advanced_filter=advanced_filter,
        azure_active_directory_tenant_id=azure_active_directory_tenant_id,
        azure_active_directory_application_id_or_uri=azure_active_directory_application_id_or_uri,
        delivery_identity=None,
        delivery_identity_endpoint=None,
        delivery_identity_endpoint_type=None,
        deadletter_identity=None,
        deadletter_identity_endpoint=None,
        storage_queue_msg_ttl=storage_queue_msg_ttl,
        enable_advanced_filtering_on_arrays=enable_advanced_filtering_on_arrays,
        delivery_attribute_mapping=delivery_attribute_mapping)

    return client.begin_create_or_update(
        resource_group_name,
        topic_name,
        event_subscription_name,
        event_subscription_info)


def cli_eventgrid_topic_event_subscription_delete(
        client,
        resource_group_name,
        topic_name,
        event_subscription_name):
    return client.delete(
        resource_group_name,
        topic_name,
        event_subscription_name)


def cli_topic_event_subscription_get(
        client,
        resource_group_name,
        topic_name,
        event_subscription_name,
        include_full_endpoint_url=False,
        include_static_delivery_attribute_secret=False):

    retrieved_event_subscription = client.get(resource_group_name, topic_name, event_subscription_name)
    destination = retrieved_event_subscription.destination
    if include_full_endpoint_url and isinstance(destination, WebHookEventSubscriptionDestination):
        full_endpoint_url = client.get_full_url(resource_group_name, topic_name, event_subscription_name)
        destination.endpoint_url = full_endpoint_url.endpoint_url

    if include_static_delivery_attribute_secret and \
       not isinstance(destination, StorageQueueEventSubscriptionDestination):
        delivery_attributes = client.get_delivery_attributes(
            resource_group_name,
            topic_name,
            event_subscription_name)
        destination.delivery_attribute_mappings = delivery_attributes

    return retrieved_event_subscription


def cli_topic_event_subscription_list(   # pylint: disable=too-many-return-statements
        client,
        resource_group_name,
        topic_name,
        odata_query=None):

    return client.list_by_topic(resource_group_name, topic_name, odata_query, DEFAULT_TOP)


def cli_topic_event_subscription_update(
        client,
        resource_group_name,
        topic_name,
        event_subscription_name,
        endpoint=None,
        endpoint_type=WEBHOOK_DESTINATION,
        subject_begins_with=None,
        subject_ends_with=None,
        included_event_types=None,
        advanced_filter=None,
        labels=None,
        deadletter_endpoint=None,
        storage_queue_msg_ttl=None,
        enable_advanced_filtering_on_arrays=None,
        delivery_attribute_mapping=None):

    instance = client.get(resource_group_name, topic_name, event_subscription_name)

    params = _update_event_subscription_internal(
        instance=instance,
        endpoint=endpoint,
        endpoint_type=endpoint_type,
        subject_begins_with=subject_begins_with,
        subject_ends_with=subject_ends_with,
        included_event_types=included_event_types,
        advanced_filter=advanced_filter,
        labels=labels,
        deadletter_endpoint=deadletter_endpoint,
        delivery_identity=None,
        delivery_identity_endpoint=None,
        delivery_identity_endpoint_type=None,
        deadletter_identity=None,
        deadletter_identity_endpoint=None,
        storage_queue_msg_ttl=storage_queue_msg_ttl,
        enable_advanced_filtering_on_arrays=enable_advanced_filtering_on_arrays,
        delivery_attribute_mapping=delivery_attribute_mapping)

    return client.begin_update(
        resource_group_name,
        topic_name,
        event_subscription_name,
        params)


def cli_domain_event_subscription_create_or_update(    # pylint: disable=too-many-locals
        client,
        resource_group_name,
        domain_name,
        event_subscription_name,
        endpoint=None,
        endpoint_type=None,
        included_event_types=None,
        subject_begins_with=None,
        subject_ends_with=None,
        is_subject_case_sensitive=False,
        max_delivery_attempts=30,
        event_ttl=1440,
        max_events_per_batch=None,
        preferred_batch_size_in_kilobytes=None,
        event_delivery_schema=None,
        deadletter_endpoint=None,
        labels=None,
        expiration_date=None,
        advanced_filter=None,
        azure_active_directory_tenant_id=None,
        azure_active_directory_application_id_or_uri=None,
        storage_queue_msg_ttl=None,
        enable_advanced_filtering_on_arrays=None,
        delivery_attribute_mapping=None):

    event_subscription_info = _get_event_subscription_info(
        endpoint=endpoint,
        endpoint_type=endpoint_type,
        included_event_types=included_event_types,
        subject_begins_with=subject_begins_with,
        subject_ends_with=subject_ends_with,
        is_subject_case_sensitive=is_subject_case_sensitive,
        max_delivery_attempts=max_delivery_attempts,
        event_ttl=event_ttl,
        max_events_per_batch=max_events_per_batch,
        preferred_batch_size_in_kilobytes=preferred_batch_size_in_kilobytes,
        event_delivery_schema=event_delivery_schema,
        deadletter_endpoint=deadletter_endpoint,
        labels=labels,
        expiration_date=expiration_date,
        advanced_filter=advanced_filter,
        azure_active_directory_tenant_id=azure_active_directory_tenant_id,
        azure_active_directory_application_id_or_uri=azure_active_directory_application_id_or_uri,
        delivery_identity=None,
        delivery_identity_endpoint=None,
        delivery_identity_endpoint_type=None,
        deadletter_identity=None,
        deadletter_identity_endpoint=None,
        storage_queue_msg_ttl=storage_queue_msg_ttl,
        enable_advanced_filtering_on_arrays=enable_advanced_filtering_on_arrays,
        delivery_attribute_mapping=delivery_attribute_mapping)

    return client.begin_create_or_update(
        resource_group_name,
        domain_name,
        event_subscription_name,
        event_subscription_info)


def cli_eventgrid_domain_event_subscription_delete(
        client,
        resource_group_name,
        domain_name,
        event_subscription_name):
    return client.delete(
        resource_group_name,
        domain_name,
        event_subscription_name)


def cli_domain_event_subscription_get(
        client,
        resource_group_name,
        domain_name,
        event_subscription_name,
        include_full_endpoint_url=False,
        include_static_delivery_attribute_secret=False):

    retrieved_event_subscription = client.get(resource_group_name, domain_name, event_subscription_name)
    destination = retrieved_event_subscription.destination
    if include_full_endpoint_url and isinstance(destination, WebHookEventSubscriptionDestination):
        full_endpoint_url = client.get_full_url(resource_group_name, domain_name, event_subscription_name)
        destination.endpoint_url = full_endpoint_url.endpoint_url

    if include_static_delivery_attribute_secret and \
       not isinstance(destination, StorageQueueEventSubscriptionDestination):
        delivery_attributes = client.get_delivery_attributes(
            resource_group_name,
            domain_name,
            event_subscription_name)
        destination.delivery_attribute_mappings = delivery_attributes

    return retrieved_event_subscription


def cli_domain_event_subscription_list(   # pylint: disable=too-many-return-statements
        client,
        resource_group_name,
        domain_name,
        odata_query=None):

    return client.list_by_domain(resource_group_name, domain_name, odata_query, DEFAULT_TOP)


def cli_domain_event_subscription_update(
        client,
        resource_group_name,
        domain_name,
        event_subscription_name,
        endpoint=None,
        endpoint_type=WEBHOOK_DESTINATION,
        subject_begins_with=None,
        subject_ends_with=None,
        included_event_types=None,
        advanced_filter=None,
        labels=None,
        deadletter_endpoint=None,
        storage_queue_msg_ttl=None,
        enable_advanced_filtering_on_arrays=None,
        delivery_attribute_mapping=None):

    instance = client.get(resource_group_name, domain_name, event_subscription_name)

    params = _update_event_subscription_internal(
        instance=instance,
        endpoint=endpoint,
        endpoint_type=endpoint_type,
        subject_begins_with=subject_begins_with,
        subject_ends_with=subject_ends_with,
        included_event_types=included_event_types,
        advanced_filter=advanced_filter,
        labels=labels,
        deadletter_endpoint=deadletter_endpoint,
        delivery_identity=None,
        delivery_identity_endpoint=None,
        delivery_identity_endpoint_type=None,
        deadletter_identity=None,
        deadletter_identity_endpoint=None,
        storage_queue_msg_ttl=storage_queue_msg_ttl,
        enable_advanced_filtering_on_arrays=enable_advanced_filtering_on_arrays,
        delivery_attribute_mapping=delivery_attribute_mapping)

    return client.begin_update(
        resource_group_name,
        domain_name,
        event_subscription_name,
        params)


def cli_domain_topic_event_subscription_create_or_update(    # pylint: disable=too-many-locals
        client,
        resource_group_name,
        domain_name,
        topic_name,
        event_subscription_name,
        endpoint=None,
        endpoint_type=None,
        included_event_types=None,
        subject_begins_with=None,
        subject_ends_with=None,
        is_subject_case_sensitive=False,
        max_delivery_attempts=30,
        event_ttl=1440,
        max_events_per_batch=None,
        preferred_batch_size_in_kilobytes=None,
        event_delivery_schema=None,
        deadletter_endpoint=None,
        labels=None,
        expiration_date=None,
        advanced_filter=None,
        azure_active_directory_tenant_id=None,
        azure_active_directory_application_id_or_uri=None,
        storage_queue_msg_ttl=None,
        enable_advanced_filtering_on_arrays=None,
        delivery_attribute_mapping=None):

    event_subscription_info = _get_event_subscription_info(
        endpoint=endpoint,
        endpoint_type=endpoint_type,
        included_event_types=included_event_types,
        subject_begins_with=subject_begins_with,
        subject_ends_with=subject_ends_with,
        is_subject_case_sensitive=is_subject_case_sensitive,
        max_delivery_attempts=max_delivery_attempts,
        event_ttl=event_ttl,
        max_events_per_batch=max_events_per_batch,
        preferred_batch_size_in_kilobytes=preferred_batch_size_in_kilobytes,
        event_delivery_schema=event_delivery_schema,
        deadletter_endpoint=deadletter_endpoint,
        labels=labels,
        expiration_date=expiration_date,
        advanced_filter=advanced_filter,
        azure_active_directory_tenant_id=azure_active_directory_tenant_id,
        azure_active_directory_application_id_or_uri=azure_active_directory_application_id_or_uri,
        delivery_identity=None,
        delivery_identity_endpoint=None,
        delivery_identity_endpoint_type=None,
        deadletter_identity=None,
        deadletter_identity_endpoint=None,
        storage_queue_msg_ttl=storage_queue_msg_ttl,
        enable_advanced_filtering_on_arrays=enable_advanced_filtering_on_arrays,
        delivery_attribute_mapping=delivery_attribute_mapping)

    return client.begin_create_or_update(
        resource_group_name,
        domain_name,
        topic_name,
        event_subscription_name,
        event_subscription_info)


def cli_eventgrid_domain_topic_event_subscription_delete(
        client,
        resource_group_name,
        domain_name,
        topic_name,
        event_subscription_name):
    return client.delete(
        resource_group_name,
        domain_name,
        topic_name,
        event_subscription_name)


def cli_domain_topic_event_subscription_get(
        client,
        resource_group_name,
        domain_name,
        topic_name,
        event_subscription_name,
        include_full_endpoint_url=False,
        include_static_delivery_attribute_secret=False):

    retrieved_event_subscription = client.get(resource_group_name, domain_name, topic_name, event_subscription_name)
    destination = retrieved_event_subscription.destination
    if include_full_endpoint_url and isinstance(destination, WebHookEventSubscriptionDestination):
        full_endpoint_url = client.get_full_url(resource_group_name, domain_name, topic_name, event_subscription_name)
        destination.endpoint_url = full_endpoint_url.endpoint_url

    if include_static_delivery_attribute_secret and \
       not isinstance(destination, StorageQueueEventSubscriptionDestination):
        delivery_attributes = client.get_delivery_attributes(
            resource_group_name,
            domain_name,
            topic_name,
            event_subscription_name)
        destination.delivery_attribute_mappings = delivery_attributes

    return retrieved_event_subscription


def cli_domain_topic_event_subscription_list(   # pylint: disable=too-many-return-statements
        client,
        resource_group_name,
        domain_name,
        topic_name,
        odata_query=None):

    return client.list_by_domain_topic(resource_group_name, domain_name, topic_name, odata_query, DEFAULT_TOP)


def cli_domain_topic_event_subscription_update(
        client,
        resource_group_name,
        domain_name,
        topic_name,
        event_subscription_name,
        endpoint=None,
        endpoint_type=WEBHOOK_DESTINATION,
        subject_begins_with=None,
        subject_ends_with=None,
        included_event_types=None,
        advanced_filter=None,
        labels=None,
        deadletter_endpoint=None,
        storage_queue_msg_ttl=None,
        enable_advanced_filtering_on_arrays=None,
        delivery_attribute_mapping=None):

    instance = client.get(resource_group_name, domain_name, topic_name, event_subscription_name)

    params = _update_event_subscription_internal(
        instance=instance,
        endpoint=endpoint,
        endpoint_type=endpoint_type,
        subject_begins_with=subject_begins_with,
        subject_ends_with=subject_ends_with,
        included_event_types=included_event_types,
        advanced_filter=advanced_filter,
        labels=labels,
        deadletter_endpoint=deadletter_endpoint,
        delivery_identity=None,
        delivery_identity_endpoint=None,
        delivery_identity_endpoint_type=None,
        deadletter_identity=None,
        deadletter_identity_endpoint=None,
        storage_queue_msg_ttl=storage_queue_msg_ttl,
        enable_advanced_filtering_on_arrays=enable_advanced_filtering_on_arrays,
        delivery_attribute_mapping=delivery_attribute_mapping)

    return client.begin_update(
        resource_group_name,
        domain_name,
        topic_name,
        event_subscription_name,
        params)


def cli_domain_update(
        client,
        resource_group_name,
        domain_name,
        tags=None,
        public_network_access=None,
        inbound_ip_rules=None,
        sku=None,
        identity=None,
        user_assigned=None,
        system_assigned=None):
    sku_info = None
    if sku is not None:
        sku_name = _get_sku(sku)
        sku_info = ResourceSku(name=sku_name)

    identity_info = _get_identity_info_only_if_not_none(identity, user_assigned, system_assigned)
    domain_update_parameters = DomainUpdateParameters(
        tags=tags,
        public_network_access=public_network_access,
        inbound_ip_rules=inbound_ip_rules,
        sku=sku_info,
        identity=identity_info)

    return client.begin_update(
        resource_group_name,
        domain_name,
        domain_update_parameters)


def cli_domain_list(
        client,
        resource_group_name=None,
        odata_query=None):

    if resource_group_name:
        return client.list_by_resource_group(resource_group_name, odata_query, DEFAULT_TOP)

    return client.list_by_subscription(odata_query, DEFAULT_TOP)


def cli_domain_regenerate_key(
        client,
        resource_group_name,
        domain_name,
        key_name):
    regenerate_key_request = DomainRegenerateKeyRequest(key_name=key_name)

    return client.regenerate_key(
        resource_group_name=resource_group_name,
        domain_name=domain_name,
        regenerate_key_request=regenerate_key_request
    )


def cli_domain_create_or_update(
        client,
        resource_group_name,
        domain_name,
        location=None,
        tags=None,
        input_schema=EVENTGRID_SCHEMA,
        input_mapping_fields=None,
        input_mapping_default_values=None,
        public_network_access=None,
        inbound_ip_rules=None,
        sku=SKU_BASIC,
        identity=None,
        user_assigned=None,
        system_assigned=None):
    final_input_schema, input_schema_mapping = _get_input_schema_and_mapping(
        input_schema,
        input_mapping_fields,
        input_mapping_default_values)
    sku_name = _get_sku(sku)
    sku_info = ResourceSku(name=sku_name)

    identity_info = None

    identity_info = _get_identity_info(identity, user_assigned, system_assigned)
    domain_info = Domain(
        location=location,
        tags=tags,
        input_schema=final_input_schema,
        input_schema_mapping=input_schema_mapping,
        public_network_access=public_network_access,
        inbound_ip_rules=inbound_ip_rules,
        sku=sku_info,
        identity=identity_info)

    return client.begin_create_or_update(
        resource_group_name,
        domain_name,
        domain_info)


def cli_domain_topic_create_or_update(
        client,
        resource_group_name,
        domain_name,
        domain_topic_name):
    return client.begin_create_or_update(
        resource_group_name,
        domain_name,
        domain_topic_name)


def cli_domain_topic_delete(
        client,
        resource_group_name,
        domain_name,
        domain_topic_name):
    return client.begin_delete(
        resource_group_name,
        domain_name,
        domain_topic_name)


def cli_domain_topic_list(
        client,
        resource_group_name,
        domain_name,
        odata_query=None):
    return client.list_by_domain(resource_group_name, domain_name, odata_query, DEFAULT_TOP)


def cli_system_topic_list(
        client,
        resource_group_name=None,
        odata_query=None):

    if resource_group_name:
        return client.list_by_resource_group(resource_group_name, odata_query, DEFAULT_TOP)

    return client.list_by_subscription(odata_query, DEFAULT_TOP)


def cli_partner_registration_list(
        client,
        resource_group_name=None,
        odata_query=None):

    if resource_group_name:
        return client.list_by_resource_group(resource_group_name, odata_query, DEFAULT_TOP)

    return client.list_by_subscription(odata_query, DEFAULT_TOP)


def cli_partner_registration_create_or_update(
        client,
        resource_group_name,
        partner_registration_name,
        partner_name,
        resource_type_name,
        display_name=None,
        description=None,
        long_description=None,
        customer_service_number=None,
        customer_service_extension=None,
        customer_service_uri=None,
        logo_uri=None,
        setup_uri=None,
        authorized_subscription_ids=None,
        tags=None):

    if long_description is not None and len(long_description) >= MAX_LONG_DESCRIPTION_LEN:
        raise CLIError('The long description cannot exceed ' + str(MAX_LONG_DESCRIPTION_LEN) + ' characters.')

    if customer_service_number is not None:
        searchObj = re.search(PHONE_NUMBER_REGEX, customer_service_number)
        if searchObj is None:
            raise CLIError('Invalid customer service phone number. The expected phone format should start with'
                           ' a \'+\' sign followed by the country code. The remaining digits are then followed.'
                           ' Only digits and spaces are allowed and its length cannot exceed 16 digits including'
                           ' country code. Examples of valid phone numbers are: +1 515 123 4567 and'
                           ' +966 7 5115 2471. Examples of invalid phone numbers are: +1 (515) 123-4567,'
                           ' 1 515 123 4567 and +966 121 5115 24 7 551 1234 43.')

    if customer_service_extension is not None:
        searchObj = re.search(EXTENSION_NUMBER_REGEX, customer_service_extension)
        if searchObj is None:
            raise CLIError('Invalid customer service extension number. Only digits are allowed'
                           ' and number of digits should not exceed 10.')

    partner_registration_info = PartnerRegistration(
        location=GLOBAL,
        partner_name=partner_name,
        partner_resource_type_name=resource_type_name,
        logo_uri=logo_uri,
        setup_uri=setup_uri,
        partner_resource_type_display_name=display_name,
        partner_resource_type_description=description,
        long_description=long_description,
        partner_customer_service_number=customer_service_number,
        partner_customer_service_extension=customer_service_extension,
        customer_service_uri=customer_service_uri,
        authorized_azure_subscription_ids=authorized_subscription_ids,
        tags=tags)

    return client.create_or_update(
        resource_group_name,
        partner_registration_name,
        partner_registration_info)


def cli_partner_namespace_list(
        client,
        resource_group_name=None,
        odata_query=None):

    if resource_group_name:
        return client.list_by_resource_group(resource_group_name, odata_query, DEFAULT_TOP)

    return client.list_by_subscription(odata_query, DEFAULT_TOP)


def cli_partner_namespace_create_or_update(
        client,
        resource_group_name,
        partner_namespace_name,
        partner_registration_id,
        location=None,
        tags=None):

    partner_namespace_info = PartnerNamespace(
        location=location,
        partner_registration_fully_qualified_id=partner_registration_id,
        tags=tags)

    return client.begin_create_or_update(
        resource_group_name,
        partner_namespace_name,
        partner_namespace_info)


def cli_partner_namespace_regenerate_key(
        client,
        resource_group_name,
        partner_namespace_name,
        key_name):
    regenerate_key_request = PartnerNamespaceRegenerateKeyRequest(key_name=key_name)

    return client.regenerate_key(
        resource_group_name=resource_group_name,
        partner_namespace_name=partner_namespace_name,
        regenerate_key_request=regenerate_key_request
    )


def cli_event_channel_list(
        client,
        resource_group_name,
        partner_namespace_name,
        odata_query=None):

    return client.list_by_partner_namespace(resource_group_name, partner_namespace_name, odata_query, DEFAULT_TOP)


def cli_event_channel_create_or_update(
        client,
        resource_group_name,
        partner_namespace_name,
        event_channel_name,
        partner_topic_source,
        destination_subscription_id,
        destination_resource_group_name,
        destination_topic_name,
        activation_expiration_date=None,
        partner_topic_description=None,
        publisher_filter=None):

    source_info = EventChannelSource(source=partner_topic_source)

    destination_info = EventChannelDestination(
        azure_subscription_id=destination_subscription_id,
        resource_group=destination_resource_group_name,
        partner_topic_name=destination_topic_name)

    event_channel_filter = None
    if publisher_filter is not None:
        event_channel_filter = EventChannelFilter(advanced_filters=publisher_filter)

    event_channel_info = EventChannel(
        source=source_info,
        destination=destination_info,
        expiration_time_if_not_activated_utc=activation_expiration_date,
        partner_topic_friendly_description=partner_topic_description,
        filter=event_channel_filter)

    return client.create_or_update(
        resource_group_name,
        partner_namespace_name,
        event_channel_name,
        event_channel_info)


def cli_partner_topic_list(
        client,
        resource_group_name=None,
        odata_query=None):

    if resource_group_name:
        return client.list_by_resource_group(resource_group_name, odata_query, DEFAULT_TOP)

    return client.list_by_subscription(odata_query, DEFAULT_TOP)


def cli_partner_topic_create_or_update(
        client,
        resource_group_name,
        partner_topic_name,
        location=None,
        tags=None):

    partner_topic_info = PartnerTopic(
        location=location,
        tags=tags)

    return client.create_or_update(
        resource_group_name,
        partner_topic_name,
        partner_topic_info)


def cli_partner_topic_event_subscription_create_or_update(    # pylint: disable=too-many-locals
        client,
        resource_group_name,
        partner_topic_name,
        event_subscription_name,
        endpoint=None,
        endpoint_type=None,
        included_event_types=None,
        subject_begins_with=None,
        subject_ends_with=None,
        is_subject_case_sensitive=False,
        max_delivery_attempts=30,
        event_ttl=1440,
        max_events_per_batch=None,
        preferred_batch_size_in_kilobytes=None,
        event_delivery_schema=None,
        deadletter_endpoint=None,
        labels=None,
        expiration_date=None,
        advanced_filter=None,
        azure_active_directory_tenant_id=None,
        azure_active_directory_application_id_or_uri=None,
        storage_queue_msg_ttl=None,
        enable_advanced_filtering_on_arrays=None,
        delivery_attribute_mapping=None):

    event_subscription_info = _get_event_subscription_info(
        endpoint=endpoint,
        endpoint_type=endpoint_type,
        included_event_types=included_event_types,
        subject_begins_with=subject_begins_with,
        subject_ends_with=subject_ends_with,
        is_subject_case_sensitive=is_subject_case_sensitive,
        max_delivery_attempts=max_delivery_attempts,
        event_ttl=event_ttl,
        max_events_per_batch=max_events_per_batch,
        preferred_batch_size_in_kilobytes=preferred_batch_size_in_kilobytes,
        event_delivery_schema=event_delivery_schema,
        deadletter_endpoint=deadletter_endpoint,
        labels=labels,
        expiration_date=expiration_date,
        advanced_filter=advanced_filter,
        azure_active_directory_tenant_id=azure_active_directory_tenant_id,
        azure_active_directory_application_id_or_uri=azure_active_directory_application_id_or_uri,
        delivery_identity=None,
        delivery_identity_endpoint=None,
        delivery_identity_endpoint_type=None,
        deadletter_identity=None,
        deadletter_identity_endpoint=None,
        storage_queue_msg_ttl=storage_queue_msg_ttl,
        enable_advanced_filtering_on_arrays=enable_advanced_filtering_on_arrays,
        delivery_attribute_mapping=delivery_attribute_mapping)

    return client.begin_create_or_update(
        resource_group_name,
        partner_topic_name,
        event_subscription_name,
        event_subscription_info)


def cli_eventgrid_partner_topic_event_subscription_delete(
        client,
        resource_group_name,
        partner_topic_name,
        event_subscription_name):
    return client.delete(
        resource_group_name,
        partner_topic_name,
        event_subscription_name)


def cli_partner_topic_event_subscription_get(
        client,
        resource_group_name,
        partner_topic_name,
        event_subscription_name,
        include_full_endpoint_url=False,
        include_static_delivery_attribute_secret=False):

    retrieved_event_subscription = client.get(resource_group_name, partner_topic_name, event_subscription_name)
    destination = retrieved_event_subscription.destination
    if include_full_endpoint_url and isinstance(destination, WebHookEventSubscriptionDestination):
        full_endpoint_url = client.get_full_url(resource_group_name, partner_topic_name, event_subscription_name)
        destination.endpoint_url = full_endpoint_url.endpoint_url

    if include_static_delivery_attribute_secret and \
       not isinstance(destination, StorageQueueEventSubscriptionDestination):
        delivery_attributes = client.get_delivery_attributes(
            resource_group_name,
            partner_topic_name,
            event_subscription_name)
        destination.delivery_attribute_mappings = delivery_attributes
    return retrieved_event_subscription


def cli_partner_topic_event_subscription_list(   # pylint: disable=too-many-return-statements
        client,
        resource_group_name,
        partner_topic_name,
        odata_query=None):

    return client.list_by_partner_topic(resource_group_name, partner_topic_name, odata_query, DEFAULT_TOP)


def cli_system_topic_create_or_update(
        client,
        resource_group_name,
        system_topic_name,
        topic_type,
        source,
        location=None,
        tags=None,
        identity=None,
        user_assigned=None,
        system_assigned=None):

    identity_info = _get_identity_info_only_if_not_none(identity, user_assigned, system_assigned)

    system_topic_info = SystemTopic(
        location=location,
        tags=tags,
        topic_type=topic_type,
        source=source,
        identity=identity_info)

    return client.begin_create_or_update(
        resource_group_name,
        system_topic_name,
        system_topic_info)


def cli_system_topic_update(
        client,
        resource_group_name,
        system_topic_name,
        tags=None,
        identity=None,
        user_assigned=None,
        system_assigned=None):

    identity_info = _get_identity_info_only_if_not_none(identity, user_assigned, system_assigned)

    system_topic_update_parameters = SystemTopicUpdateParameters(
        tags=tags,
        identity=identity_info)

    return client.begin_update(
        resource_group_name=resource_group_name,
        system_topic_name=system_topic_name,
        system_topic_update_parameters=system_topic_update_parameters)


def cli_system_topic_event_subscription_create_or_update(    # pylint: disable=too-many-locals
        client,
        resource_group_name,
        system_topic_name,
        event_subscription_name,
        endpoint=None,
        endpoint_type=None,
        included_event_types=None,
        subject_begins_with=None,
        subject_ends_with=None,
        is_subject_case_sensitive=False,
        max_delivery_attempts=30,
        event_ttl=1440,
        max_events_per_batch=None,
        preferred_batch_size_in_kilobytes=None,
        event_delivery_schema=None,
        deadletter_endpoint=None,
        labels=None,
        expiration_date=None,
        advanced_filter=None,
        azure_active_directory_tenant_id=None,
        azure_active_directory_application_id_or_uri=None,
        storage_queue_msg_ttl=None,
        enable_advanced_filtering_on_arrays=None,
        delivery_attribute_mapping=None):

    event_subscription_info = _get_event_subscription_info(
        endpoint=endpoint,
        endpoint_type=endpoint_type,
        included_event_types=included_event_types,
        subject_begins_with=subject_begins_with,
        subject_ends_with=subject_ends_with,
        is_subject_case_sensitive=is_subject_case_sensitive,
        max_delivery_attempts=max_delivery_attempts,
        event_ttl=event_ttl,
        max_events_per_batch=max_events_per_batch,
        preferred_batch_size_in_kilobytes=preferred_batch_size_in_kilobytes,
        event_delivery_schema=event_delivery_schema,
        deadletter_endpoint=deadletter_endpoint,
        labels=labels,
        expiration_date=expiration_date,
        advanced_filter=advanced_filter,
        azure_active_directory_tenant_id=azure_active_directory_tenant_id,
        azure_active_directory_application_id_or_uri=azure_active_directory_application_id_or_uri,
        delivery_identity=None,
        delivery_identity_endpoint=None,
        delivery_identity_endpoint_type=None,
        deadletter_identity=None,
        deadletter_identity_endpoint=None,
        storage_queue_msg_ttl=storage_queue_msg_ttl,
        enable_advanced_filtering_on_arrays=enable_advanced_filtering_on_arrays,
        delivery_attribute_mapping=delivery_attribute_mapping)

    return client.begin_create_or_update(
        resource_group_name,
        system_topic_name,
        event_subscription_name,
        event_subscription_info)


def cli_eventgrid_system_topic_event_subscription_delete(
        client,
        resource_group_name,
        system_topic_name,
        event_subscription_name):
    return client.delete(
        resource_group_name,
        system_topic_name,
        event_subscription_name)


def cli_system_topic_event_subscription_get(
        client,
        resource_group_name,
        system_topic_name,
        event_subscription_name,
        include_full_endpoint_url=False,
        include_static_delivery_attribute_secret=False):

    retrieved_event_subscription = client.get(resource_group_name, system_topic_name, event_subscription_name)
    destination = retrieved_event_subscription.destination
    if include_full_endpoint_url and isinstance(destination, WebHookEventSubscriptionDestination):
        full_endpoint_url = client.get_full_url(resource_group_name, system_topic_name, event_subscription_name)
        destination.endpoint_url = full_endpoint_url.endpoint_url

    if include_static_delivery_attribute_secret and \
       not isinstance(destination, StorageQueueEventSubscriptionDestination):
        delivery_attributes = client.get_delivery_attributes(
            resource_group_name,
            system_topic_name,
            event_subscription_name)
        destination.delivery_attribute_mappings = delivery_attributes

    return retrieved_event_subscription


def cli_system_topic_event_subscription_list(   # pylint: disable=too-many-return-statements
        client,
        resource_group_name,
        system_topic_name,
        odata_query=None):

    return client.list_by_system_topic(resource_group_name, system_topic_name, odata_query, DEFAULT_TOP)


def cli_eventgrid_event_subscription_create(   # pylint: disable=too-many-locals
        client,
        event_subscription_name,
        endpoint=None,
        source_resource_id=None,
        endpoint_type=WEBHOOK_DESTINATION,
        included_event_types=None,
        subject_begins_with=None,
        subject_ends_with=None,
        is_subject_case_sensitive=False,
        max_delivery_attempts=30,
        event_ttl=1440,
        max_events_per_batch=None,
        preferred_batch_size_in_kilobytes=None,
        event_delivery_schema=None,
        deadletter_endpoint=None,
        labels=None,
        expiration_date=None,
        advanced_filter=None,
        azure_active_directory_tenant_id=None,
        azure_active_directory_application_id_or_uri=None,
        delivery_identity=None,
        delivery_identity_endpoint=None,
        delivery_identity_endpoint_type=None,
        deadletter_identity=None,
        deadletter_identity_endpoint=None,
        storage_queue_msg_ttl=None,
        enable_advanced_filtering_on_arrays=None,
        delivery_attribute_mapping=None):

    event_subscription_info = _get_event_subscription_info(
        endpoint=endpoint,
        endpoint_type=endpoint_type,
        included_event_types=included_event_types,
        subject_begins_with=subject_begins_with,
        subject_ends_with=subject_ends_with,
        is_subject_case_sensitive=is_subject_case_sensitive,
        max_delivery_attempts=max_delivery_attempts,
        event_ttl=event_ttl,
        max_events_per_batch=max_events_per_batch,
        preferred_batch_size_in_kilobytes=preferred_batch_size_in_kilobytes,
        event_delivery_schema=event_delivery_schema,
        deadletter_endpoint=deadletter_endpoint,
        labels=labels,
        expiration_date=expiration_date,
        advanced_filter=advanced_filter,
        azure_active_directory_tenant_id=azure_active_directory_tenant_id,
        azure_active_directory_application_id_or_uri=azure_active_directory_application_id_or_uri,
        delivery_identity=delivery_identity,
        delivery_identity_endpoint=delivery_identity_endpoint,
        delivery_identity_endpoint_type=delivery_identity_endpoint_type,
        deadletter_identity=deadletter_identity,
        deadletter_identity_endpoint=deadletter_identity_endpoint,
        storage_queue_msg_ttl=storage_queue_msg_ttl,
        enable_advanced_filtering_on_arrays=enable_advanced_filtering_on_arrays,
        delivery_attribute_mapping=delivery_attribute_mapping)

    return client.begin_create_or_update(
        source_resource_id,
        event_subscription_name,
        event_subscription_info)


def cli_eventgrid_event_subscription_delete(
        client,
        event_subscription_name,
        source_resource_id=None):
    return client.begin_delete(
        source_resource_id,
        event_subscription_name)


def event_subscription_setter(
        client,
        parameters,
        event_subscription_name,
        source_resource_id=None):

    return client.begin_update(
        source_resource_id,
        event_subscription_name,
        parameters)


def cli_eventgrid_event_subscription_get(
        client,
        event_subscription_name,
        source_resource_id=None,
        include_full_endpoint_url=False,
        include_static_delivery_attribute_secret=False):

    retrieved_event_subscription = client.get(source_resource_id, event_subscription_name)
    destination = retrieved_event_subscription.destination
    if include_full_endpoint_url and isinstance(destination, WebHookEventSubscriptionDestination):
        full_endpoint_url = client.get_full_url(source_resource_id, event_subscription_name)
        destination.endpoint_url = full_endpoint_url.endpoint_url

    if include_static_delivery_attribute_secret and \
       not isinstance(destination, StorageQueueEventSubscriptionDestination):
        delivery_attributes = client.get_delivery_attributes(source_resource_id, event_subscription_name)
        destination.delivery_attribute_mappings = delivery_attributes

    return retrieved_event_subscription


def cli_event_subscription_list(   # pylint: disable=too-many-return-statements
        cmd,
        client,
        source_resource_id=None,
        location=None,
        resource_group_name=None,
        topic_type_name=None,
        odata_query=None):
    if source_resource_id is not None:
        # If Source Resource ID is specified, we need to list event subscriptions for that particular resource.
        # Since a full resource ID is specified, it should override all other defaults such as default location and RG
        # No other parameters must be specified
        if topic_type_name is not None:
            raise CLIError('usage error: Since --source-resource-id is specified, none of the other parameters must '
                           'be specified.')

        return _list_event_subscriptions_by_resource_id(cmd, client, source_resource_id, odata_query, DEFAULT_TOP)

    if location is None:
        # Since resource-id was not specified, location must be specified: e.g. "westus2" or "global". If not error
        # OUT.
        raise CLIError('usage error: --source-resource-id ID | --location LOCATION'
                       ' [--resource-group RG] [--topic-type-name TOPIC_TYPE_NAME]')

    if topic_type_name is None:
        # No topic-type is specified: return event subscriptions across all topic types for this location.
        if location.lower() == GLOBAL.lower():
            if resource_group_name:
                return client.list_global_by_resource_group(resource_group_name, odata_query, DEFAULT_TOP)
            return client.list_global_by_subscription(odata_query, DEFAULT_TOP)

        if resource_group_name:
            return client.list_regional_by_resource_group(resource_group_name, location, odata_query, DEFAULT_TOP)
        return client.list_regional_by_subscription(location, odata_query, DEFAULT_TOP)

    # Topic type name is specified
    if location.lower() == GLOBAL.lower():
        if not _is_topic_type_global_resource(topic_type_name):
            raise CLIError('Invalid usage: Global cannot be specified for the location '
                           'as the specified topic type is a regional topic type with '
                           'regional event subscriptions. Specify a location value such '
                           'as westus. Global can be used only for global topic types: '
                           'Microsoft.Resources.Subscriptions and Microsoft.Resources.ResourceGroups.')
        if resource_group_name:
            return client.list_global_by_resource_group_for_topic_type(
                resource_group_name,
                topic_type_name,
                odata_query,
                DEFAULT_TOP)
        return client.list_global_by_subscription_for_topic_type(topic_type_name, odata_query, DEFAULT_TOP)

    if resource_group_name:
        return client.list_regional_by_resource_group_for_topic_type(
            resource_group_name,
            location,
            topic_type_name,
            odata_query,
            DEFAULT_TOP)
    return client.list_regional_by_subscription_for_topic_type(
        location,
        topic_type_name,
        odata_query,
        DEFAULT_TOP)


def _get_event_subscription_info(    # pylint: disable=too-many-locals,too-many-statements,too-many-branches
        endpoint=None,
        endpoint_type=WEBHOOK_DESTINATION,
        included_event_types=None,
        subject_begins_with=None,
        subject_ends_with=None,
        is_subject_case_sensitive=False,
        max_delivery_attempts=30,
        event_ttl=1440,
        max_events_per_batch=None,
        preferred_batch_size_in_kilobytes=None,
        event_delivery_schema=None,
        deadletter_endpoint=None,
        labels=None,
        expiration_date=None,
        advanced_filter=None,
        azure_active_directory_tenant_id=None,
        azure_active_directory_application_id_or_uri=None,
        delivery_identity=None,
        delivery_identity_endpoint=None,
        delivery_identity_endpoint_type=None,
        deadletter_identity=None,
        deadletter_identity_endpoint=None,
        storage_queue_msg_ttl=None,
        enable_advanced_filtering_on_arrays=None,
        delivery_attribute_mapping=None):

    _validate_delivery_identity_args(
        endpoint,
        delivery_identity,
        delivery_identity_endpoint,
        delivery_identity_endpoint_type)

    if deadletter_endpoint is not None and deadletter_identity_endpoint is not None:
        raise CLIError('usage error: either --deadletter_endpoint or --deadletter_identity_endpoint '
                       'should be specified at one time, not both')

    if included_event_types is not None and len(included_event_types) == 1 and included_event_types[0].lower() == 'all':
        logger.warning('The usage of \"All\" for --included-event-types is not allowed starting from Azure Event Grid'
                       ' API Version 2019-02-01-preview. However, the call here is still permitted by replacing'
                       ' \"All\" with None in order to return all the event types (for the custom topics and'
                       ' domains case) or default event types (for other topic types case). In any future calls,'
                       ' please consider leaving --included-event-types unspecified or use None instead.')
        included_event_types = None

    # Construct RetryPolicy based on max_delivery_attempts and event_ttl
    _validate_retry_policy(max_delivery_attempts, event_ttl)
    retry_policy = RetryPolicy(max_delivery_attempts=max_delivery_attempts, event_time_to_live_in_minutes=event_ttl)

    if max_events_per_batch is not None:
        if endpoint_type not in (WEBHOOK_DESTINATION, AZUREFUNCTION_DESTINATION):
            raise CLIError('usage error: max-events-per-batch is applicable only for '
                           'endpoint types WebHook and AzureFunction.')
        if max_events_per_batch > 5000:
            raise CLIError('usage error: max-events-per-batch must be a number between 1 and 5000.')

    if preferred_batch_size_in_kilobytes is not None:
        if endpoint_type not in (WEBHOOK_DESTINATION, AZUREFUNCTION_DESTINATION):
            raise CLIError('usage error: preferred-batch-size-in-kilobytes is applicable only for '
                           'endpoint types WebHook and AzureFunction.')
        if preferred_batch_size_in_kilobytes > 1024:
            raise CLIError('usage error: preferred-batch-size-in-kilobytes must be a number '
                           'between 1 and 1024.')

    if azure_active_directory_tenant_id is not None:
        if endpoint_type is not WEBHOOK_DESTINATION:
            raise CLIError('usage error: azure-active-directory-tenant-id is applicable only for '
                           'endpoint types WebHook.')
        if azure_active_directory_application_id_or_uri is None:
            raise CLIError('usage error: azure-active-directory-application-id-or-uri is missing. '
                           'It should include an Azure Active Directory Application Id or Uri.')

    if azure_active_directory_application_id_or_uri is not None:
        if endpoint_type is not WEBHOOK_DESTINATION:
            raise CLIError('usage error: azure-active-directory-application-id-or-uri is applicable only for '
                           'endpoint types WebHook.')
        if azure_active_directory_tenant_id is None:
            raise CLIError('usage error: azure-active-directory-tenant-id is missing. '
                           'It should include an Azure Active Directory Tenant Id.')

    condition1 = deadletter_identity is not None and deadletter_identity_endpoint is None
    condition2 = deadletter_identity is None and deadletter_identity_endpoint is not None
    if condition1 or condition2:
        raise CLIError('usage error: one or more deadletter identity information is missing. If '
                       'deadletter_identity is specified, deadletter_identity_endpoint should be specified.')

    tennant_id = None
    application_id = None

    condition1 = endpoint_type is not None and endpoint_type.lower() == WEBHOOK_DESTINATION.lower()
    condition2 = delivery_identity_endpoint_type is not None and \
        delivery_identity_endpoint_type.lower() == WEBHOOK_DESTINATION.lower()
    if condition1 or condition2:
        tennant_id = azure_active_directory_tenant_id
        application_id = azure_active_directory_application_id_or_uri

    destination = None
    delivery_with_resource_identity = None
    if endpoint is not None:
        _validate_destination_attribute(endpoint_type, storage_queue_msg_ttl, delivery_attribute_mapping)
        destination = _get_endpoint_destination(
            endpoint_type,
            endpoint,
            max_events_per_batch,
            preferred_batch_size_in_kilobytes,
            tennant_id,
            application_id,
            storage_queue_msg_ttl,
            delivery_attribute_mapping)
    elif delivery_identity_endpoint is not None:
        identity_type_name = _get_event_subscription_identity_type(delivery_identity)
        delivery_identity_info = EventSubscriptionIdentity(type=identity_type_name)
        _validate_destination_attribute(
            delivery_identity_endpoint_type,
            storage_queue_msg_ttl,
            delivery_attribute_mapping)
        destination_with_identity = _get_endpoint_destination(
            delivery_identity_endpoint_type,
            delivery_identity_endpoint,
            max_events_per_batch,
            preferred_batch_size_in_kilobytes,
            tennant_id,
            application_id,
            storage_queue_msg_ttl,
            delivery_attribute_mapping)
        delivery_with_resource_identity = DeliveryWithResourceIdentity(
            identity=delivery_identity_info,
            destination=destination_with_identity)

    event_subscription_filter = EventSubscriptionFilter(
        subject_begins_with=subject_begins_with,
        subject_ends_with=subject_ends_with,
        included_event_types=included_event_types,
        is_subject_case_sensitive=is_subject_case_sensitive,
        enable_advanced_filtering_on_arrays=enable_advanced_filtering_on_arrays,
        advanced_filters=advanced_filter)

    deadletter_destination = None
    if deadletter_endpoint is not None:
        deadletter_destination = _get_deadletter_destination(deadletter_endpoint)

    deadletter_with_resource_identity = None

    if deadletter_identity_endpoint is not None:
        deadletter_destination_with_identity = _get_deadletter_destination(deadletter_identity_endpoint)
        deadletter_identity_type_name = _get_event_subscription_identity_type(deadletter_identity)
        deadletter_delivery_identity_info = EventSubscriptionIdentity(type=deadletter_identity_type_name)
        deadletter_with_resource_identity = DeadLetterWithResourceIdentity(
            identity=deadletter_delivery_identity_info,
            dead_letter_destination=deadletter_destination_with_identity)

    if expiration_date is not None:
        expiration_date = parse(expiration_date)

    event_subscription_info = EventSubscription(
        destination=destination,
        filter=event_subscription_filter,
        labels=labels,
        event_delivery_schema=_get_event_delivery_schema(event_delivery_schema),
        retry_policy=retry_policy,
        expiration_time_utc=expiration_date,
        dead_letter_destination=deadletter_destination,
        delivery_with_resource_identity=delivery_with_resource_identity,
        dead_letter_with_resource_identity=deadletter_with_resource_identity)

    _warn_if_manual_handshake_needed(endpoint_type, endpoint)

    return event_subscription_info


def event_subscription_getter(
        client,
        event_subscription_name,
        source_resource_id=None):
    return client.get(source_resource_id, event_subscription_name)


def get_input_schema_mapping(
        input_mapping_fields=None,
        input_mapping_default_values=None):
    input_schema_mapping = None

    if input_mapping_fields is not None or input_mapping_default_values is not None:
        input_schema_mapping = JsonInputSchemaMapping()

        input_schema_mapping.id = JsonField()
        input_schema_mapping.topic = JsonField()
        input_schema_mapping.event_time = JsonField()
        input_schema_mapping.subject = JsonFieldWithDefault()
        input_schema_mapping.event_type = JsonFieldWithDefault()
        input_schema_mapping.data_version = JsonFieldWithDefault()

        if input_mapping_fields is not None:
            for field_mapping_pair in input_mapping_fields:
                field_mapping = field_mapping_pair.split("=")
                target = field_mapping[0]
                source = field_mapping[1]

                if target.lower() == ID.lower():
                    input_schema_mapping.id.source_field = source
                elif target.lower() == EVENTTIME.lower():
                    input_schema_mapping.event_time.source_field = source
                elif target.lower() == TOPIC.lower():
                    input_schema_mapping.topic.source_field = source
                elif target.lower() == SUBJECT.lower():
                    input_schema_mapping.subject.source_field = source
                elif target.lower() == DATAVERSION.lower():
                    input_schema_mapping.data_version.source_field = source
                elif target.lower() == EVENTTYPE.lower():
                    input_schema_mapping.event_type.source_field = source

        if input_mapping_default_values is not None:
            for default_value_mapping_pair in input_mapping_default_values:
                default_value_mapping = default_value_mapping_pair.split("=")
                target = default_value_mapping[0]
                source = default_value_mapping[1]

                if target.lower() == SUBJECT.lower():
                    input_schema_mapping.subject.default_value = source
                elif target.lower() == DATAVERSION.lower():
                    input_schema_mapping.data_version.default_value = source
                elif target.lower() == EVENTTYPE.lower():
                    input_schema_mapping.event_type.default_value = source

    return input_schema_mapping


def cli_system_topic_event_subscription_update(
        client,
        resource_group_name,
        system_topic_name,
        event_subscription_name,
        endpoint=None,
        endpoint_type=WEBHOOK_DESTINATION,
        subject_begins_with=None,
        subject_ends_with=None,
        included_event_types=None,
        advanced_filter=None,
        labels=None,
        deadletter_endpoint=None,
        storage_queue_msg_ttl=None,
        enable_advanced_filtering_on_arrays=None,
        delivery_attribute_mapping=None):

    instance = client.get(resource_group_name, system_topic_name, event_subscription_name)

    params = _update_event_subscription_internal(
        instance=instance,
        endpoint=endpoint,
        endpoint_type=endpoint_type,
        subject_begins_with=subject_begins_with,
        subject_ends_with=subject_ends_with,
        included_event_types=included_event_types,
        advanced_filter=advanced_filter,
        labels=labels,
        deadletter_endpoint=deadletter_endpoint,
        delivery_identity=None,
        delivery_identity_endpoint=None,
        delivery_identity_endpoint_type=None,
        deadletter_identity=None,
        deadletter_identity_endpoint=None,
        storage_queue_msg_ttl=storage_queue_msg_ttl,
        enable_advanced_filtering_on_arrays=enable_advanced_filtering_on_arrays,
        delivery_attribute_mapping=delivery_attribute_mapping)

    return client.begin_update(
        resource_group_name,
        system_topic_name,
        event_subscription_name,
        params)


def cli_partner_topic_event_subscription_update(
        client,
        resource_group_name,
        partner_topic_name,
        event_subscription_name,
        endpoint=None,
        endpoint_type=WEBHOOK_DESTINATION,
        subject_begins_with=None,
        subject_ends_with=None,
        included_event_types=None,
        advanced_filter=None,
        labels=None,
        deadletter_endpoint=None,
        storage_queue_msg_ttl=None,
        enable_advanced_filtering_on_arrays=None,
        delivery_attribute_mapping=None):

    instance = client.get(resource_group_name, partner_topic_name, event_subscription_name)

    params = _update_event_subscription_internal(
        instance=instance,
        endpoint=endpoint,
        endpoint_type=endpoint_type,
        subject_begins_with=subject_begins_with,
        subject_ends_with=subject_ends_with,
        included_event_types=included_event_types,
        advanced_filter=advanced_filter,
        labels=labels,
        deadletter_endpoint=deadletter_endpoint,
        delivery_identity=None,
        delivery_identity_endpoint=None,
        delivery_identity_endpoint_type=None,
        deadletter_identity=None,
        deadletter_identity_endpoint=None,
        storage_queue_msg_ttl=storage_queue_msg_ttl,
        enable_advanced_filtering_on_arrays=enable_advanced_filtering_on_arrays,
        delivery_attribute_mapping=delivery_attribute_mapping)

    return client.begin_update(
        resource_group_name,
        partner_topic_name,
        event_subscription_name,
        params)


def update_event_subscription(
        instance,
        endpoint=None,
        endpoint_type=WEBHOOK_DESTINATION,
        subject_begins_with=None,
        subject_ends_with=None,
        included_event_types=None,
        advanced_filter=None,
        labels=None,
        deadletter_endpoint=None,
        delivery_identity=None,
        delivery_identity_endpoint=None,
        delivery_identity_endpoint_type=None,
        deadletter_identity=None,
        deadletter_identity_endpoint=None,
        storage_queue_msg_ttl=None,
        enable_advanced_filtering_on_arrays=None,
        delivery_attribute_mapping=None):
    return _update_event_subscription_internal(
        instance=instance,
        endpoint=endpoint,
        endpoint_type=endpoint_type,
        subject_begins_with=subject_begins_with,
        subject_ends_with=subject_ends_with,
        included_event_types=included_event_types,
        advanced_filter=advanced_filter,
        labels=labels,
        deadletter_endpoint=deadletter_endpoint,
        delivery_identity=delivery_identity,
        delivery_identity_endpoint=delivery_identity_endpoint,
        delivery_identity_endpoint_type=delivery_identity_endpoint_type,
        deadletter_identity=deadletter_identity,
        deadletter_identity_endpoint=deadletter_identity_endpoint,
        storage_queue_msg_ttl=storage_queue_msg_ttl,
        enable_advanced_filtering_on_arrays=enable_advanced_filtering_on_arrays,
        delivery_attribute_mapping=delivery_attribute_mapping)


def _update_event_subscription_internal(  # pylint: disable=too-many-locals,too-many-statements
        instance,
        endpoint=None,
        endpoint_type=WEBHOOK_DESTINATION,
        subject_begins_with=None,
        subject_ends_with=None,
        included_event_types=None,
        advanced_filter=None,
        labels=None,
        deadletter_endpoint=None,
        delivery_identity=None,
        delivery_identity_endpoint=None,
        delivery_identity_endpoint_type=None,
        deadletter_identity=None,
        deadletter_identity_endpoint=None,
        storage_queue_msg_ttl=None,
        enable_advanced_filtering_on_arrays=None,
        delivery_attribute_mapping=None):

    _validate_delivery_identity_args(
        endpoint,
        delivery_identity,
        delivery_identity_endpoint,
        delivery_identity_endpoint_type)

    _validate_deadletter_identity_args(
        deadletter_identity,
        deadletter_endpoint)

    if endpoint_type.lower() != WEBHOOK_DESTINATION.lower() and endpoint is None:
        raise CLIError('Invalid usage: Since --endpoint-type is specified, a valid endpoint must also be specified.')

    current_destination = instance.destination
    current_filter = instance.filter
    current_event_delivery_schema = instance.event_delivery_schema
    current_retry_policy = instance.retry_policy
    current_destination_with_resource_identity = None
    current_destination2 = None

    if instance.delivery_with_resource_identity is not None:
        current_destination2 = instance.delivery_with_resource_identity
        current_destination_with_resource_identity = instance.delivery_with_resource_identity.destination

    tenant_id = _get_tenant_id(current_destination, current_destination_with_resource_identity)
    application_id = _get_application_id(current_destination, current_destination_with_resource_identity)

    # for the update path, endpoint_type can be None but it does not mean that this is webhook,
    # as it can be other types too.
    current_max_events_per_batch = 0
    current_preferred_batch_size_in_kilobytes = 0

    if current_destination is not None and (current_destination.endpoint_type.lower() == WEBHOOK_DESTINATION.lower() or current_destination.endpoint_type.lower() == AZUREFUNCTION_DESTINATION.lower()):  # pylint: disable=line-too-long
        current_max_events_per_batch = current_destination.max_events_per_batch
        current_preferred_batch_size_in_kilobytes = current_destination.preferred_batch_size_in_kilobytes
    elif current_destination_with_resource_identity is not None and (current_destination_with_resource_identity.endpoint_type.lower() == WEBHOOK_DESTINATION.lower() or current_destination_with_resource_identity.endpoint_type.lower() == AZUREFUNCTION_DESTINATION.lower()):  # pylint: disable=line-too-long
        current_max_events_per_batch = current_destination_with_resource_identity.max_events_per_batch
        current_preferred_batch_size_in_kilobytes = current_destination_with_resource_identity.preferred_batch_size_in_kilobytes   # pylint: disable=line-too-long

    updated_destination = None
    updated_delivery_with_resource_identity = None

    # if endpoint and delivery_identity_endpoint is not specified then use the instance value
    if endpoint is None and delivery_identity_endpoint is None:
        if current_destination is not None:
            _validate_and_update_destination(
                current_destination.endpoint_type,
                current_destination,
                storage_queue_msg_ttl,
                delivery_attribute_mapping)
            updated_destination = current_destination
        elif current_destination_with_resource_identity is not None:
            _validate_and_update_destination(
                current_destination_with_resource_identity.endpoint_type,
                current_destination_with_resource_identity,
                storage_queue_msg_ttl,
                delivery_attribute_mapping)
            updated_delivery_with_resource_identity = current_destination2
    elif endpoint is not None:
        _validate_destination_attribute(
            endpoint_type,
            storage_queue_msg_ttl,
            delivery_attribute_mapping)
        updated_destination = _get_endpoint_destination(
            endpoint_type,
            endpoint,
            current_max_events_per_batch,
            current_preferred_batch_size_in_kilobytes,
            tenant_id,
            application_id,
            storage_queue_msg_ttl,
            delivery_attribute_mapping)
    elif delivery_identity_endpoint is not None:
        destination_with_identity = _get_endpoint_destination(
            delivery_identity_endpoint_type,
            delivery_identity_endpoint,
            0,
            0,
            tenant_id,
            application_id,
            storage_queue_msg_ttl,
            delivery_attribute_mapping)

        identity_type_name = _get_event_subscription_identity_type(delivery_identity)
        delivery_identity_info = EventSubscriptionIdentity(type=identity_type_name)

        updated_delivery_with_resource_identity = DeliveryWithResourceIdentity(
            identity=delivery_identity_info,
            destination=destination_with_identity)

    updated_deadletter_destination = None
    if deadletter_endpoint is not None:
        updated_deadletter_destination = _get_deadletter_destination(deadletter_endpoint)

    updated_deadletter_with_resource_identity = None
    if deadletter_identity_endpoint is not None:
        deadletter_destination_with_identity = _get_deadletter_destination(deadletter_identity_endpoint)
        deadletter_identity_type_name = _get_event_subscription_identity_type(deadletter_identity)
        deadletter_delivery_identity_info = EventSubscriptionIdentity(type=deadletter_identity_type_name)
        updated_deadletter_with_resource_identity = DeadLetterWithResourceIdentity(
            identity=deadletter_delivery_identity_info,
            dead_letter_destination=deadletter_destination_with_identity)

    _update_event_subscription_filter(
        current_filter,
        subject_begins_with,
        subject_ends_with,
        included_event_types,
        enable_advanced_filtering_on_arrays,
        advanced_filter)
    updated_filter = current_filter

    updated_labels = None
    if labels is not None:
        updated_labels = labels

    params = EventSubscriptionUpdateParameters(
        destination=updated_destination,
        filter=updated_filter,
        labels=updated_labels,
        retry_policy=current_retry_policy,
        dead_letter_destination=updated_deadletter_destination,
        event_delivery_schema=current_event_delivery_schema,
        delivery_with_resource_identity=updated_delivery_with_resource_identity,
        dead_letter_with_resource_identity=updated_deadletter_with_resource_identity)

    return params


def _validate_destination_attribute(endpoint_type, storage_queue_msg_ttl=None, delivery_attribute_mapping=None):
    isStorageQueueDestination = endpoint_type is not None and endpoint_type.lower() == STORAGEQUEUE_DESTINATION.lower()

    if not isStorageQueueDestination and storage_queue_msg_ttl is not None:
        raise CLIError('usage error: --storage-queue-msg-ttl is only applicable for endpoint type StorageQueue.')

    if isStorageQueueDestination and delivery_attribute_mapping is not None:
        raise CLIError('usage error: --delivery-attribute-mapping is not applicable for endpoint type StorageQueue.')


def _set_event_subscription_destination(
        destination,
        storage_queue_msg_ttl=None,
        delivery_attribute_mapping=None):

    endpoint_type = destination.endpoint_type
    if endpoint_type.lower() == WEBHOOK_DESTINATION.lower():
        if delivery_attribute_mapping is not None:
            destination.delivery_attribute_mappings = delivery_attribute_mapping
    elif endpoint_type.lower() == EVENTHUB_DESTINATION.lower():
        if delivery_attribute_mapping is not None:
            destination.delivery_attribute_mappings = delivery_attribute_mapping
    elif endpoint_type.lower() == HYBRIDCONNECTION_DESTINATION.lower():
        if delivery_attribute_mapping is not None:
            destination.delivery_attribute_mappings = delivery_attribute_mapping
    elif endpoint_type.lower() == STORAGEQUEUE_DESTINATION.lower():
        if storage_queue_msg_ttl is not None:
            destination.queue_message_time_to_live_in_seconds = storage_queue_msg_ttl
    elif endpoint_type.lower() == SERVICEBUSQUEUE_DESTINATION.lower():
        if delivery_attribute_mapping is not None:
            destination.delivery_attribute_mappings = delivery_attribute_mapping
    elif endpoint_type.lower() == SERVICEBUSTOPIC_DESTINATION.lower():
        if delivery_attribute_mapping is not None:
            destination.delivery_attribute_mappings = delivery_attribute_mapping
    elif endpoint_type.lower() == AZUREFUNCTION_DESTINATION.lower():
        if delivery_attribute_mapping is not None:
            destination.delivery_attribute_mappings = delivery_attribute_mapping
    return destination


def _get_endpoint_destination(
        endpoint_type,
        endpoint,
        max_events_per_batch,
        preferred_batch_size_in_kilobytes,
        azure_active_directory_tenant_id,
        azure_active_directory_application_id_or_uri,
        storage_queue_msg_ttl,
        delivery_attribute_mapping):

    if endpoint_type.lower() == WEBHOOK_DESTINATION.lower():
        destination = WebHookEventSubscriptionDestination(
            endpoint_url=endpoint,
            max_events_per_batch=max_events_per_batch,
            preferred_batch_size_in_kilobytes=preferred_batch_size_in_kilobytes,
            azure_active_directory_tenant_id=azure_active_directory_tenant_id,
            azure_active_directory_application_id_or_uri=azure_active_directory_application_id_or_uri,
            delivery_attribute_mappings=delivery_attribute_mapping)
    elif endpoint_type.lower() == EVENTHUB_DESTINATION.lower():
        destination = EventHubEventSubscriptionDestination(
            resource_id=endpoint,
            delivery_attribute_mappings=delivery_attribute_mapping)
    elif endpoint_type.lower() == HYBRIDCONNECTION_DESTINATION.lower():
        destination = HybridConnectionEventSubscriptionDestination(
            resource_id=endpoint,
            delivery_attribute_mappings=delivery_attribute_mapping)
    elif endpoint_type.lower() == STORAGEQUEUE_DESTINATION.lower():
        destination = _get_storage_queue_destination(endpoint, storage_queue_msg_ttl)
    elif endpoint_type.lower() == SERVICEBUSQUEUE_DESTINATION.lower():
        destination = ServiceBusQueueEventSubscriptionDestination(
            resource_id=endpoint,
            delivery_attribute_mappings=delivery_attribute_mapping)
    elif endpoint_type.lower() == SERVICEBUSTOPIC_DESTINATION.lower():
        destination = ServiceBusTopicEventSubscriptionDestination(
            resource_id=endpoint,
            delivery_attribute_mappings=delivery_attribute_mapping)
    elif endpoint_type.lower() == AZUREFUNCTION_DESTINATION.lower():
        destination = AzureFunctionEventSubscriptionDestination(
            resource_id=endpoint,
            max_events_per_batch=max_events_per_batch,
            preferred_batch_size_in_kilobytes=preferred_batch_size_in_kilobytes,
            delivery_attribute_mappings=delivery_attribute_mapping)
    return destination


def _get_storage_queue_destination(endpoint, storage_queue_msg_ttl):
    # Supplied endpoint would be in the following format:
    # /subscriptions/.../storageAccounts/sa1/queueServices/default/queues/{queueName}))
    # and we need to break it up into:
    # /subscriptions/.../storageAccounts/sa1 and queueName
    queue_items = re.split(
        "/queueServices/default/queues/", endpoint, flags=re.IGNORECASE)

    if len(queue_items) != 2 or queue_items[0] is None or queue_items[1] is None:
        raise CLIError('Argument Error: Expected format of --endpoint for storage queue is:' +
                       '/subscriptions/id/resourceGroups/rg/providers/Microsoft.Storage/' +
                       'storageAccounts/sa1/queueServices/default/queues/queueName')

    if storage_queue_msg_ttl is not None:
        destination = StorageQueueEventSubscriptionDestination(
            resource_id=queue_items[0],
            queue_name=queue_items[1],
            queue_message_time_to_live_in_seconds=storage_queue_msg_ttl)
    else:
        destination = StorageQueueEventSubscriptionDestination(
            resource_id=queue_items[0],
            queue_name=queue_items[1])
    return destination


def _get_deadletter_destination(deadletter_endpoint):
    blob_items = re.split(
        "/blobServices/default/containers/", deadletter_endpoint, flags=re.IGNORECASE)

    if len(blob_items) != 2 or blob_items[0] is None or blob_items[1] is None:
        raise CLIError('Argument Error: Expected format of --deadletter-endpoint is:' +
                       '/subscriptions/id/resourceGroups/rg/providers/Microsoft.Storage/' +
                       'storageAccounts/sa1/blobServices/default/containers/containerName')

    return StorageBlobDeadLetterDestination(resource_id=blob_items[0], blob_container_name=blob_items[1])


def _validate_retry_policy(max_delivery_attempts, event_ttl):
    if max_delivery_attempts < 1 or max_delivery_attempts > 30:
        raise CLIError('--max-delivery-attempts should be a number between 1 and 30.')

    if event_ttl < 1 or event_ttl > 1440:
        raise CLIError('--event-ttl should be a number between 1 and 1440.')


def _get_event_delivery_schema(event_delivery_schema):
    if event_delivery_schema is None:
        return None
    if event_delivery_schema.lower() == EVENTGRID_SCHEMA.lower():
        event_delivery_schema = EVENTGRID_SCHEMA
    elif event_delivery_schema.lower() == CUSTOM_INPUT_SCHEMA.lower():
        event_delivery_schema = CUSTOM_INPUT_SCHEMA
    elif event_delivery_schema.lower() == CLOUDEVENTV1_0_SCHEMA.lower():
        event_delivery_schema = CLOUDEVENTV1_0_SCHEMA
    else:
        raise CLIError('usage error: --event-delivery-schema supported values are'
                       ' :' + EVENTGRID_SCHEMA + ',' + CUSTOM_INPUT_SCHEMA +
                       ',' + CLOUDEVENTV1_0_SCHEMA)

    return event_delivery_schema


def _warn_if_manual_handshake_needed(endpoint_type, endpoint):
    # If the endpoint belongs to a service that we know implements the subscription validation
    # handshake, there's no need to show this message, hence we check for those services
    # before showing this message. This list includes Azure Automation, EventGrid Trigger based
    # Azure functions, and Azure Logic Apps.
    if endpoint is not None and endpoint_type.lower() == WEBHOOK_DESTINATION.lower() and \
       "azure-automation" not in endpoint.lower() and \
       "eventgridextension" not in endpoint.lower() and \
       "logic.azure" not in endpoint.lower():

        logger.warning('If you are creating an event subscription from a topic that has “Azure” as the value for its '
                       '“kind” property, you must validate your webhook endpoint by following the steps described in '
                       'https://aka.ms/eg-webhook-endpoint-validation.')


def _get_sku(sku_name):
    if sku_name.lower() == 'basic':
        result = SKU_BASIC
    elif sku_name.lower() == 'premium':
        result = SKU_PREMIUM

    return result


def _get_identity_type_with_checks(
        identity_type_name=IDENTITY_NONE,
        user_identity_properties=None,
        mi_system_assigned=None):
    if identity_type_name is not None and user_identity_properties is None and mi_system_assigned is None:
        result = _get_identity_type(identity_type_name)
    elif identity_type_name is None and user_identity_properties is None and mi_system_assigned is not None:
        result = IDENTITY_SYSTEM_ASSIGNED
    elif identity_type_name is None and user_identity_properties is not None and mi_system_assigned is None:
        result = IDENTITY_USER_ASSIGNED
    elif identity_type_name is None and user_identity_properties is not None and mi_system_assigned is not None:
        result = IDENTITY_MIXED_MODE
    elif identity_type_name is not None and (user_identity_properties is not None or mi_system_assigned is not None):
        raise MutuallyExclusiveArgumentError(
            'usage error: cannot use --identity together with --mi-system-assigned or --mi-user-assigned')

    return result


def _get_identity_type(identity_type_name=IDENTITY_NONE):
    if identity_type_name.lower() == IDENTITY_NO_IDENTITY.lower():
        result = IDENTITY_NONE
    elif identity_type_name.lower() == IDENTITY_SYSTEM_ASSIGNED.lower():
        result = IDENTITY_SYSTEM_ASSIGNED

    return result


def _get_event_subscription_identity_type(identity_type_name):
    result = None
    if identity_type_name.lower() == IDENTITY_SYSTEM_ASSIGNED.lower():
        result = IDENTITY_SYSTEM_ASSIGNED

    return result


def _get_tenant_id(destination, destination_with_resource_identity):
    tenant_id = None

    if destination is not None and hasattr(destination, 'azure_active_directory_tenant_id'):
        tenant_id = destination.azure_active_directory_tenant_id
    elif destination_with_resource_identity is not None and hasattr(destination_with_resource_identity, 'azure_active_directory_tenant_id'):  # pylint: disable=line-too-long
        tenant_id = destination_with_resource_identity.azure_active_directory_tenant_id

    return tenant_id


def _get_application_id(destination, destination_with_resource_identity):
    application_id = None

    if destination is not None and hasattr(destination, 'azure_active_directory_application_id_or_uri'):
        application_id = destination.azure_active_directory_application_id_or_uri
    elif destination_with_resource_identity is not None and hasattr(destination_with_resource_identity, 'azure_active_directory_application_id_or_uri'):  # pylint: disable=line-too-long
        application_id = destination_with_resource_identity.azure_active_directory_application_id_or_uri
    return application_id


def _get_input_schema_and_mapping(
        input_schema=EVENTGRID_SCHEMA,
        input_mapping_fields=None,
        input_mapping_default_values=None):
    if input_schema.lower() == EVENTGRID_SCHEMA.lower():
        input_schema = EVENTGRID_SCHEMA
    elif input_schema.lower() == CUSTOM_EVENT_SCHEMA.lower():
        input_schema = CUSTOM_EVENT_SCHEMA
    elif input_schema.lower() == CLOUDEVENTV1_0_SCHEMA.lower():
        input_schema = CLOUDEVENTV1_0_SCHEMA
    else:
        raise CLIError('The provided --input-schema is not valid. The supported values are: ' +
                       EVENTGRID_SCHEMA + ',' + CUSTOM_EVENT_SCHEMA + ',' + CLOUDEVENTV1_0_SCHEMA)

    if input_schema == EVENTGRID_SCHEMA:
        # Ensure that custom input mappings are not specified
        if input_mapping_fields is not None or input_mapping_default_values is not None:
            raise CLIError('--input-mapping-default-values and --input-mapping-fields should not be ' +
                           'specified when --input-schema is set to eventgridschema.')

    if input_schema == CLOUDEVENTV1_0_SCHEMA:
        # Ensure that input_mapping_default_values is not specified.
        if input_mapping_default_values is not None:
            raise CLIError('--input-mapping-default-values should be ' +
                           'specified only when --input-schema is set to customeventschema.')

    if input_schema == CUSTOM_EVENT_SCHEMA:
        # Ensure that custom input mappings are specified
        if input_mapping_fields is None and input_mapping_default_values is None:
            raise CLIError('Either --input-mapping-default-values or --input-mapping-fields must be ' +
                           'specified when --input-schema is set to customeventschema.')

    input_schema_mapping = get_input_schema_mapping(
        input_mapping_fields,
        input_mapping_default_values)

    return input_schema, input_schema_mapping


def _list_event_subscriptions_by_resource_id(cmd, client, resource_id, oDataQuery, top):
    # parse_resource_id doesn't handle resource_ids for Azure subscriptions and RGs
    # so, first try to look for those two patterns.
    from azure.cli.core.commands.client_factory import get_subscription_id
    default_subscription_id = get_subscription_id(cmd.cli_ctx)

    if resource_id is not None:
        id_parts = list(filter(None, resource_id.split('/')))
        if len(id_parts) < 5:
            # Azure subscriptions or Resource group
            if id_parts[0].lower() != "subscriptions":
                raise CLIError('The specified value for resource-id is not in the'
                               ' expected format. It should start with /subscriptions.')

            subscription_id = id_parts[1]
            _validate_subscription_id_matches_default_subscription_id(
                default_subscription_id=default_subscription_id,
                provided_subscription_id=subscription_id)

            if len(id_parts) == 2:
                return client.list_global_by_subscription_for_topic_type(
                    "Microsoft.Resources.Subscriptions",
                    oDataQuery,
                    top)

            if len(id_parts) == 4 and id_parts[2].lower() == "resourcegroups":
                resource_group_name = id_parts[3]
                if resource_group_name is None:
                    raise CLIError('The specified value for resource-id is not'
                                   ' in the expected format. A valid value for'
                                   ' resource group must be provided.')
                return client.list_global_by_resource_group_for_topic_type(
                    resource_group_name,
                    "Microsoft.Resources.ResourceGroups",
                    oDataQuery,
                    top)

    id_parts = parse_resource_id(resource_id)
    subscription_id = id_parts.get('subscription')
    _validate_subscription_id_matches_default_subscription_id(
        default_subscription_id=default_subscription_id,
        provided_subscription_id=subscription_id)

    rg_name = id_parts.get('resource_group')
    resource_name = id_parts.get('name')
    namespace = id_parts.get('namespace')
    resource_type = id_parts.get('type')

    if (subscription_id is None or rg_name is None or resource_name is None or
            namespace is None or resource_type is None):
        raise CLIError('The specified value for resource-id is not'
                       ' in the expected format.')

    # If this is for a domain topic, invoke the appropriate operation
    if (namespace.lower() == EVENTGRID_NAMESPACE.lower() and resource_type.lower() == EVENTGRID_DOMAINS.lower()):
        child_resource_type = id_parts.get('child_type_1')
        child_resource_name = id_parts.get('child_name_1')

        if (child_resource_type is not None and child_resource_type.lower() == EVENTGRID_TOPICS.lower() and
                child_resource_name is not None):
            return client.list_by_domain_topic(rg_name, resource_name, child_resource_name, oDataQuery, top)

    # Not a domain topic, invoke the standard list_by_resource
    return client.list_by_resource(
        rg_name,
        namespace,
        resource_type,
        resource_name,
        oDataQuery,
        top)


def _is_topic_type_global_resource(topic_type_name):
    # TODO: Add here if any other global topic types get added in the future.
    TOPIC_TYPE_AZURE_SUBSCRIPTIONS = "Microsoft.Resources.Subscriptions"
    TOPIC_TYPE_AZURE_RESOURCE_GROUP = "Microsoft.Resources.ResourceGroups"
    TOPIC_TYPE_MAPS_ACCOUNTS = "Microsoft.Maps.Accounts"

    if (topic_type_name.lower() == TOPIC_TYPE_AZURE_SUBSCRIPTIONS.lower() or
            topic_type_name.lower() == TOPIC_TYPE_MAPS_ACCOUNTS or
            topic_type_name.lower() == TOPIC_TYPE_AZURE_RESOURCE_GROUP.lower()):
        return True

    return False


def _validate_subscription_id_matches_default_subscription_id(
        default_subscription_id,
        provided_subscription_id):
    # The CLI/SDK infrastructure doesn't support overriding the subscription ID.
    # Hence, we validate that the provided subscription ID is the same as the default
    # configured subscription.
    if provided_subscription_id.lower() != default_subscription_id.lower():
        raise CLIError('The subscription ID in the specified resource-id'
                       ' does not match the default subscription ID. To set the default subscription ID,'
                       ' use az account set ID_OR_NAME, or use the global argument --subscription ')


def _get_identity_info(identity=None, kind=None, user_identity_properties=None, mi_system_assigned=None):
    if (identity is not None and identity.lower() != IDENTITY_NONE.lower()):
        identity_type_name = _get_identity_type_with_checks(identity, user_identity_properties, mi_system_assigned)
        identity_info = IdentityInfo(type=identity_type_name, user_assigned_identities=user_identity_properties)
    else:
        if kind is None or kind.lower() == KIND_AZURE.lower():
            identity_info = IdentityInfo(type=IDENTITY_NONE)
        else:
            identity_info = None
    return identity_info


def _get_identity_info_only_if_not_none(identity=None, user_identity_properties=None, mi_system_assigned=None):
    identity_info = None
    if (identity is not None and identity.lower() != IDENTITY_NONE.lower()):
        identity_type_name = _get_identity_type_with_checks(identity, user_identity_properties, mi_system_assigned)
        identity_info = IdentityInfo(type=identity_type_name, user_assigned_identities=user_identity_properties)
    return identity_info


def _update_event_subscription_filter(
        event_subscription_filter,
        subject_begins_with=None,
        subject_ends_with=None,
        included_event_types=None,
        enable_advanced_filtering_on_arrays=None,
        advanced_filter=None):

    if subject_begins_with is not None:
        event_subscription_filter.subject_begins_with = subject_begins_with

    if subject_ends_with is not None:
        event_subscription_filter.subject_ends_with = subject_ends_with

    if included_event_types is not None:
        event_subscription_filter.included_event_types = included_event_types

    if enable_advanced_filtering_on_arrays is not None:
        event_subscription_filter.enable_advanced_filtering_on_arrays = enable_advanced_filtering_on_arrays

    if advanced_filter is not None:
        event_subscription_filter.advanced_filters = advanced_filter


def _get_kind(kind_name):
    if kind_name.lower() == KIND_AZURE.lower():
        result = KIND_AZURE
    elif kind_name.lower() == KIND_AZUREARC.lower():
        result = KIND_AZUREARC

    return result


def _get_extended_location(kind_name=None, extended_location_name=None, extended_location_type=None):
    result = None

    if kind_name is None:
        _ensure_extended_location_is_none(extended_location_name, extended_location_type)
    elif kind_name.lower() == KIND_AZURE.lower():
        _ensure_extended_location_is_none(extended_location_name, extended_location_type)
    elif kind_name.lower() == KIND_AZUREARC.lower():
        _ensure_extended_location_is_valid(extended_location_name, extended_location_type)
        result = ExtendedLocation(name=extended_location_name, type=extended_location_type)
    else:
        raise CLIError("--kind: The specified kind '{}' is not valid."
                       " Supported values are ".format(kind_name) +
                       KIND_AZURE + "," + KIND_AZUREARC + ".")
    return result


def _ensure_extended_location_is_none(extended_location_name=None, extended_location_type=None):

    if extended_location_name is not None or extended_location_type is not None:
        raise CLIError('Cannot specify extended-location-name or extended-location-type when targetting Azure.')


def _ensure_extended_location_is_valid(extended_location_name=None, extended_location_type=None):
    if extended_location_name is None or extended_location_type is None or \
       extended_location_type.lower() != CUSTOMLOCATION.lower():
        raise CLIError("Must specify extended-location-name and extended-location-type"
                       " and extended-location-type value must be 'customLocation'.")


def _validate_delivery_identity_args(
        endpoint,
        delivery_identity,
        delivery_identity_endpoint,
        delivery_identity_endpoint_type):

    condition1 = delivery_identity is not None and \
        (delivery_identity_endpoint is None or delivery_identity_endpoint_type is None)

    condition2 = delivery_identity is None and \
        (delivery_identity_endpoint is not None or delivery_identity_endpoint_type is not None)

    if endpoint is None and (condition1 or condition2):
        raise CLIError('usage error: one or more delivery identity information is missing. '
                       'If --delivery-identity is specified, both --delivery-identity-endpoint and '
                       '--delivery-identity-endpoint-type should be specified.')

    if endpoint is not None and (condition1 or condition2):
        raise CLIError('usage error: Cannot specify both --delivery-identity and --endpoint.'
                       ' If --endpoint is specified then none of the --delivery-identity properties can be specified.')


def _validate_deadletter_identity_args(deadletter_identity, deadletter_identity_endpoint):
    condition1 = deadletter_identity is not None and deadletter_identity_endpoint is None
    condition2 = deadletter_identity is None and deadletter_identity_endpoint is not None
    if condition1 or condition2:
        raise CLIError('usage error: one or more deadletter identity information is missing. If '
                       'deadletter_identity is specified, deadletter_identity_endpoint should be specified.')


def _validate_and_update_destination(endpoint_type, destination, storage_queue_msg_ttl, delivery_attribute_mapping):
    _validate_destination_attribute(
        endpoint_type,
        storage_queue_msg_ttl,
        delivery_attribute_mapping)

    _set_event_subscription_destination(
        destination,
        storage_queue_msg_ttl,
        delivery_attribute_mapping)
