# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long,too-many-nested-blocks,too-many-lines,too-many-return-statements

import json

from ._constants import HttpHeaders
from knack.log import get_logger
from knack.util import CLIError

from azure.keyvault.secrets._shared import parse_key_vault_id
from azure.appconfiguration import ResourceReadOnlyError
from azure.core.exceptions import HttpResponseError
from azure.cli.core.azclierror import (
    AzureInternalError,
    ValidationError,
    AzureResponseError,
    RequiredArgumentMissingError,
    ResourceNotFoundError,
)

from ._constants import KeyVaultConstants, StatusCodes
from ._diff_utils import __print_diff
from ._utils import prep_filter_for_url_encoding, parse_tags_to_dict
from ._models import (
    convert_configurationsetting_to_keyvalue,
    convert_keyvalue_to_configurationsetting,
    QueryFields,
)
from ._featuremodels import map_featureflag_to_keyvalue, is_feature_flag

logger = get_logger(__name__)


# Config Store <-> List of KeyValue object
def __read_kv_from_config_store(
    azconfig_client,
    key=None,
    label=None,
    tags=None,
    snapshot=None,
    datetime=None,
    fields=None,
    top=None,
    all_=True,
    cli_ctx=None,
    prefix_to_remove="",
    prefix_to_add="",
    correlation_request_id=None,
):
    # pylint: disable=too-many-branches too-many-statements

    # list_configuration_settings returns kv with null label when:
    # label = ASCII null 0x00 (or URL encoded %00)
    # In delete, import & export commands, we treat missing --label as null label
    # In list, restore & list_revision commands, we treat missing --label as all labels

    label = prep_filter_for_url_encoding(label)

    prepped_tags = [prep_filter_for_url_encoding(tag) for tag in tags] if tags else []

    query_fields = []
    if fields:
        # Create list of string field names from QueryFields list
        for field in fields:
            if field == QueryFields.ALL:
                query_fields.clear()
                break
            query_fields.append(field.name.lower())

    if snapshot:
        try:
            configsetting_iterable = azconfig_client.list_configuration_settings(
                snapshot_name=snapshot,
                fields=query_fields,
                headers={HttpHeaders.CORRELATION_REQUEST_ID: correlation_request_id},
            )

        except HttpResponseError as exception:
            raise AzureResponseError(
                "Failed to read key-values(s) from snapshot {}. ".format(snapshot) +
                str(exception)
            )

    else:
        try:
            configsetting_iterable = azconfig_client.list_configuration_settings(
                key_filter=key,
                label_filter=label,
                tags_filter=prepped_tags,
                accept_datetime=datetime,
                fields=query_fields,
                headers={HttpHeaders.CORRELATION_REQUEST_ID: correlation_request_id},
            )

        except HttpResponseError as exception:
            raise AzureResponseError(
                "Failed to read key-value(s) that match the specified key and label. " +
                str(exception)
            )

    retrieved_kvs = []
    count = 0

    if all_:
        top = float("inf")
    elif top is None:
        top = 100

    for setting in configsetting_iterable:
        kv = convert_configurationsetting_to_keyvalue(setting)

        if kv.key:
            # remove prefix if specified
            if kv.key.startswith(prefix_to_remove):
                kv.key = kv.key[len(prefix_to_remove):]

            # add prefix if specified
            kv.key = prefix_to_add + kv.key

            if kv.content_type and kv.value:
                # resolve key vault reference
                if cli_ctx and __is_key_vault_ref(kv):
                    __resolve_secret(cli_ctx, kv)

        # trim unwanted fields from kv object instead of leaving them as null.
        if fields:
            partial_kv = {}
            for field in fields:
                partial_kv[field.name.lower()] = kv.__dict__[field.name.lower()]
            retrieved_kvs.append(partial_kv)
        else:
            retrieved_kvs.append(kv)
        count += 1
        if count >= top:
            return retrieved_kvs

    # A request to list kvs of a non-existent snapshot returns an empty result.
    # We first check if the snapshot exists before returning an empty result.
    if snapshot and len(retrieved_kvs) == 0:
        try:
            _ = azconfig_client.get_snapshot(name=snapshot, headers={HttpHeaders.CORRELATION_REQUEST_ID: correlation_request_id})

        except HttpResponseError as exception:
            if exception.status_code == StatusCodes.NOT_FOUND:
                raise ResourceNotFoundError(
                    "No snapshot with name '{}' was found.".format(snapshot)
                )

    return retrieved_kvs


def __write_kv_and_features_to_config_store(
    azconfig_client,
    key_values,
    features=None,
    tags=None,
    label=None,
    preserve_labels=False,
    content_type=None,
    correlation_request_id=None,
):
    if not key_values and not features:
        logger.warning("\nSource configuration is empty. No changes will be made.")
        return

    # write all keyvalues to target store
    if features:
        key_values.extend(__convert_featureflag_list_to_keyvalue_list(features))

    for kv in key_values:
        set_kv = convert_keyvalue_to_configurationsetting(kv)
        if not preserve_labels:
            set_kv.label = label
        if tags is not None:
            if tags == "":  # Empty string explicitly clears existing tags
                set_kv.tags = {}
            else:
                set_kv.tags = parse_tags_to_dict(tags)

        # Don't overwrite the content type of feature flags or key vault references
        if (
            content_type and not
            is_feature_flag(set_kv) and not
            __is_key_vault_ref(set_kv)
        ):
            set_kv.content_type = content_type

        __write_configuration_setting_to_config_store(
            azconfig_client, set_kv, correlation_request_id
        )


def __is_key_vault_ref(kv):
    return (
        kv and
        kv.content_type and
        isinstance(kv.content_type, str) and
        kv.content_type.lower() == KeyVaultConstants.KEYVAULT_CONTENT_TYPE
    )


def __discard_features_from_retrieved_kv(src_kvs):
    try:
        src_kvs[:] = [kv for kv in src_kvs if not is_feature_flag(kv)]
    except Exception as exception:
        raise CLIError(str(exception))


def __print_restore_preview(diff, yes):
    if not yes:
        logger.warning("\n---------------- Restore Preview ----------------")

    if not diff or not any(diff.values()):
        logger.warning(
            "\nNo matching records found to be restored. No changes will be made."
        )
        return False

    if not yes:
        __print_diff(diff, "restore", indent=2, show_update_diff=False)

    logger.warning("")  # printing an empty line for formatting purpose

    return True


def __flatten_json_key_value(key, value, flattened_data, depth, separator):
    if depth > 1:
        depth = depth - 1
        if value and isinstance(value, dict):
            if separator is None or not separator:
                raise RequiredArgumentMissingError(
                    "A non-empty separator is required for importing hierarchical configurations."
                )
            for nested_key in value:
                __flatten_json_key_value(
                    key + separator + nested_key,
                    value[nested_key],
                    flattened_data,
                    depth,
                    separator,
                )
        else:
            if key in flattened_data:
                logger.debug(
                    "The key %s already exist, value has been overwritten.", key
                )
            flattened_data[key] = json.dumps(value)
    else:
        flattened_data[key] = json.dumps(value)


def __convert_featureflag_list_to_keyvalue_list(featureflags):
    kv_list = []
    for feature in featureflags:
        try:
            kv = map_featureflag_to_keyvalue(feature)
        except ValueError as exception:
            # If we failed to convert FatureFlag to KeyValue, log warning and continue parsing other features
            logger.warning(exception)
            continue

        kv_list.append(kv)

    return kv_list


def __resolve_secret(cli_ctx, keyvault_reference):
    try:
        secret_id = json.loads(keyvault_reference.value)["uri"]
        kv_identifier = parse_key_vault_id(source_id=secret_id)
        from azure.cli.command_modules.keyvault._client_factory import (
            data_plane_azure_keyvault_secret_client,
        )

        command_args = {"vault_base_url": kv_identifier.vault_url}
        keyvault_client = data_plane_azure_keyvault_secret_client(cli_ctx, command_args)

        secret = keyvault_client.get_secret(
            name=kv_identifier.name, version=kv_identifier.version
        )
        keyvault_reference.value = secret.value
        return keyvault_reference
    except (TypeError, ValueError):
        raise ValidationError(
            "Invalid key vault reference for key {} value:{}.".format(
                keyvault_reference.key, keyvault_reference.value
            )
        )
    except Exception as exception:
        raise CLIError(str(exception))


def __write_configuration_setting_to_config_store(
    azconfig_client, configuration_setting, correlation_request_id=None
):
    try:
        azconfig_client.set_configuration_setting(
            configuration_setting,
            headers={HttpHeaders.CORRELATION_REQUEST_ID: correlation_request_id},
        )
    except ResourceReadOnlyError:
        logger.warning(
            "Failed to set read only key-value with key '%s' and label '%s'. Unlock the key-value before updating it.",
            configuration_setting.key,
            configuration_setting.label,
        )
    except HttpResponseError as exception:
        logger.warning(
            "Failed to set key-value with key '%s' and label '%s'. %s",
            configuration_setting.key,
            configuration_setting.label,
            str(exception),
        )
    except Exception as exception:
        raise AzureInternalError(str(exception))
