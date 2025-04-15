# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands.validators import validate_tag


def validate_storage_account_id(cmd, namespace):
    """Validate storage account name"""
    from azure.cli.core.commands.client_factory import get_subscription_id
    from azure.mgmt.core.tools import is_valid_resource_id, resource_id

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


def validate_archive_window_length(ns):
    """Validate the correct format of a datetime string and the range."""
    if ns.archive_window_length is not None:
        from msrest.serialization import Deserializer
        from msrest.exceptions import DeserializationError

        try:
            datetime_obj = Deserializer.deserialize_duration(ns.archive_window_length)
        except DeserializationError:
            message = "archive-window-length {} is not a valid ISO-8601 duration format"
            raise ValueError(message.format(ns.archive_window_length))

        minwindow = Deserializer.deserialize_duration("PT5M")
        maxwindow = Deserializer.deserialize_duration("PT25H")

        if datetime_obj < minwindow or datetime_obj > maxwindow:
            message = "archive-window-length '{}' is not in the range of PT5M and PT25H"\
                .format(ns.archive_window_length)
            raise ValueError(message)


def validate_key_frame_interval_duration(ns):
    """Validate the correct format of a datetime string and the range."""
    if ns.key_frame_interval_duration is not None:
        from msrest.serialization import Deserializer
        from msrest.exceptions import DeserializationError

        try:
            datetime_obj = Deserializer.deserialize_duration(ns.key_frame_interval_duration)
        except DeserializationError:
            message = "key-frame-interval-duration {} is not a valid ISO-8601 duration format"
            raise ValueError(message.format(ns.key_frame_interval_duration))

        minwindow = Deserializer.deserialize_duration("PT1S")
        maxwindow = Deserializer.deserialize_duration("PT30S")

        if datetime_obj < minwindow or datetime_obj > maxwindow:
            message = "key-frame-interval-duration '{}' is not in the range of PT1S and PT30S"\
                .format(ns.key_frame_interval_duration)
            raise ValueError(message)


def validate_correlation_data(ns):
    """ Extracts multiple space-separated correlation data in key[=value] format """
    if isinstance(ns.correlation_data, list):
        correlation_data_dict = {}
        for item in ns.correlation_data:
            correlation_data_dict.update(validate_tag(item))
        ns.correlation_data = correlation_data_dict


def validate_token_claim(ns):
    """ Extracts multiple space-separated token claims in key[=value] format """
    if isinstance(ns.token_claims, list):
        token_claims_dict = {}
        for item in ns.token_claims:
            token_claims_dict.update(validate_tag(item))
        ns.token_claims = token_claims_dict


def validate_output_assets(ns):
    """ Extracts multiple space-separated output assets in key[=value] format """
    def _get_asset(asset_string):
        from azure.mgmt.media.models import JobOutputAsset

        name_and_label = asset_string.split('=')
        if len(name_and_label) <= 1:
            message = "Output assets are not in correct format. Output assets should be in 'assetName=label'" \
                      " format. An asset without label can be sent like this: 'assetName='"
            raise ValueError(message)
        name = name_and_label[0]
        label = name_and_label[1]
        return JobOutputAsset(asset_name=name, label=label)

    if isinstance(ns.output_assets, list):
        ns.output_assets = list(map(_get_asset, ns.output_assets))
