# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands.validators import validate_tag


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
        name = name_and_label[0]
        label = name_and_label[1]
        return JobOutputAsset(asset_name=name, label=label)

    if isinstance(ns.output_assets, list):
        ns.output_assets = list(map(_get_asset, ns.output_assets))
