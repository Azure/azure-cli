# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def validate_storage_account_id(cmd, namespace):
    """Validate storage account name"""
    from azure.cli.core.commands.client_factory import get_subscription_id
    from msrestazure.tools import is_valid_resource_id, resource_id

    if namespace.storage_account:
        if not is_valid_resource_id(namespace.storage_account):
            namespace.storage_account = resource_id(
                subscription=get_subscription_id(cmd.cli_ctx),
                resource_group=namespace.resource_group_name,
                namespace='Microsoft.Storage', type='storageAccounts',
                name=namespace.storage_account
            )


def datetime_format(value):
    """Validate the correct format of a datetime string and deserialize."""
    from msrest.serialization import Deserializer
    from msrest.exceptions import DeserializationError

    try:
        datetime_obj = Deserializer.deserialize_iso(value)
    except DeserializationError:
        message = "Argument {} is not a valid ISO-8601 datetime format"
        raise ValueError(message.format(value))
    return datetime_obj
