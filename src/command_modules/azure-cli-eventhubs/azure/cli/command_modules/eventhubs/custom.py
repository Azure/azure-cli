# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
# pylint: disable=too-many-lines
# pylint: disable=inconsistent-return-statements


# Namespace Region
def cli_namespace_create(client, resource_group_name, namespace_name, location=None, tags=None, sku='Standard', capacity=None, is_auto_inflate_enabled=None, maximum_throughput_units=None):
    from azure.mgmt.eventhub.models import EHNamespace, Sku
    return client.create_or_update(
        resource_group_name=resource_group_name,
        namespace_name=namespace_name,
        parameters=EHNamespace(
            location=location,
            tags=tags,
            sku=Sku(sku, sku, capacity),
            is_auto_inflate_enabled=is_auto_inflate_enabled,
            maximum_throughput_units=maximum_throughput_units))


def cli_namespace_update(instance, tags=None, sku=None, capacity=None, is_auto_inflate_enabled=None, maximum_throughput_units=None):

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

    return instance


def cli_namespace_list(client, resource_group_name=None):
    if resource_group_name:
        return client.list_by_resource_group(resource_group_name=resource_group_name)

    return client.list()


# Namespace Authorization rule:
def cli_autho_update(instance, rights):
    from azure.cli.command_modules.eventhubs._utils import accessrights_converter
    instance.rights = accessrights_converter(rights)
    return instance


# Eventhub Region
def cli_eheventhub_create(client, resource_group_name, namespace_name, event_hub_name, message_retention_in_days=None, partition_count=None, status=None,
                          enabled=None, capture_interval_seconds=None, capture_size_limit_bytes=None, destination_name=None, storage_account_resource_id=None, blob_container=None, archive_name_format=None):
    from azure.mgmt.eventhub.models import Eventhub, CaptureDescription, Destination
    from azure.mgmt.eventhub.models.event_hub_management_client_enums import EncodingCaptureDescription
    eventhubparameter1 = Eventhub()
    if message_retention_in_days:
        eventhubparameter1.message_retention_in_days = message_retention_in_days

    if partition_count:
        eventhubparameter1.partition_count = partition_count

    if status:
        eventhubparameter1.status = status

    if enabled and enabled is True:
        eventhubparameter1.capture_description = CaptureDescription(
            enabled=enabled,
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


def cli_eheventhub_update(instance, message_retention_in_days=None, partition_count=None, status=None,
                          enabled=None, capture_interval_seconds=None,
                          capture_size_limit_bytes=None, destination_name=None, storage_account_resource_id=None,
                          blob_container=None, archive_name_format=None):

    if message_retention_in_days:
        instance.message_retention_in_days = message_retention_in_days

    if partition_count:
        instance.partition_count = partition_count

    if status:
        instance.status = status

    if instance.enabled is True or enabled is True:
        if enabled:
            instance.capture_description.enabled = enabled
        if capture_interval_seconds:
            instance.interval_in_seconds = capture_interval_seconds
        if capture_size_limit_bytes:
            instance.size_limit_in_bytes = capture_size_limit_bytes
        if destination_name:
            instance.destination = destination_name
        if storage_account_resource_id:
            instance.storage_account_resource_id = storage_account_resource_id
        if blob_container:
            instance.blob_container = blob_container
        if archive_name_format:
            instance.archive_name_format = archive_name_format

    return instance


# pylint: disable=inconsistent-return-statements
def empty_on_404(ex):
    from azure.mgmt.eventhub.models import ErrorResponseException
    if isinstance(ex, ErrorResponseException) and ex.response.status_code == 404:
        return None
    raise ex
