# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, too-many-locals, too-many-statements, too-many-branches

import json
import time
import sys
import uuid

from itertools import chain

from ._kv_export_helpers import (
    __export_kvset_to_file,
    __map_to_appservice_config_reference,
    __write_kv_and_features_to_file,
    __write_kv_to_app_service,
)
from ._kv_helpers import (
    __convert_featureflag_list_to_keyvalue_list,
    __discard_features_from_retrieved_kv,
    __read_kv_from_config_store,
    __write_kv_and_features_to_config_store,
    __print_restore_preview
)
from ._kv_import_helpers import (
    __import_kvset_from_file,
    __delete_configuration_setting_from_config_store,
    __read_features_from_file,
    __read_kv_from_app_service,
    __read_kv_from_kubernetes_configmap,
    __read_kv_from_file,
)
from knack.log import get_logger
from knack.util import CLIError

from azure.appconfiguration import (ConfigurationSetting,
                                    ResourceReadOnlyError)
from azure.core import MatchConditions
from azure.cli.core.util import user_confirmation
from azure.core.exceptions import (HttpResponseError,
                                   ResourceNotFoundError,
                                   ResourceModifiedError)

import azure.cli.core.azclierror as CLIErrors

from ._constants import (FeatureFlagConstants, KeyVaultConstants,
                         SearchFilterOptions, StatusCodes,
                         ImportExportProfiles, CompareFieldsMap,
                         JsonDiff, ImportMode,
                         AIConfigConstants, HttpHeaders)
from ._featuremodels import map_keyvalue_to_featureflag
from ._json import parse_json_with_comments
from ._models import (convert_configurationsetting_to_keyvalue, convert_keyvalue_to_configurationsetting)
from ._utils import get_appconfig_data_client, prep_filter_for_url_encoding, resolve_store_metadata, get_store_endpoint_from_connection_string, is_json_content_type

from ._diff_utils import print_preview, KVComparer
from .feature import __list_features

logger = get_logger(__name__)


def import_config(cmd,
                  source,
                  name=None,
                  connection_string=None,
                  label=None,
                  tags=None,  # tags to add
                  prefix="",  # prefix to add
                  yes=False,
                  skip_features=False,
                  content_type=None,
                  auth_mode="key",
                  endpoint=None,
                  import_mode=ImportMode.IGNORE_MATCH,
                  dry_run=False,
                  # from-file parameters
                  path=None,
                  format_=None,
                  separator=None,
                  depth=None,
                  profile=ImportExportProfiles.DEFAULT,
                  strict=False,
                  # from-configstore parameters
                  src_name=None,
                  src_connection_string=None,
                  src_key=None,
                  src_label=None,
                  src_snapshot=None,
                  preserve_labels=False,
                  src_auth_mode="key",
                  src_endpoint=None,
                  src_tags=None,  # tags to filter
                  # from-appservice parameters
                  appservice_account=None,
                  # from-aks parameters
                  aks_cluster=None,
                  configmap_namespace="default",
                  configmap_name=None):

    src_features = []
    dest_features = []
    dest_kvs = []
    source = source.lower()
    profile = profile.lower()
    format_ = format_.lower() if format_ else None

    azconfig_client = get_appconfig_data_client(cmd, name, connection_string, auth_mode, endpoint)

    # generate correlation_request_id for bulk operation
    correlation_request_id = str(uuid.uuid4())

    # fetch key values from source
    if source == 'file':
        if profile == ImportExportProfiles.KVSET:
            __import_kvset_from_file(client=azconfig_client, path=path, strict=strict, yes=yes, dry_run=dry_run, import_mode=import_mode, correlation_request_id=correlation_request_id)
            return
        if format_ and content_type:
            # JSON content type is only supported with JSON format.
            # Error out if user has provided JSON content type with any other format.
            if format_ != 'json' and is_json_content_type(content_type):
                raise CLIErrors.FileOperationError("Failed to import '{}' file format with '{}' content type. Please provide JSON file format to match your content type.".format(format_, content_type))

        if separator:
            # If separator is provided, use max depth by default unless depth is specified.
            depth = sys.maxsize if depth is None else int(depth)
        else:
            if depth and int(depth) != 1:
                logger.warning("Cannot flatten hierarchical data without a separator. --depth argument will be ignored.")
            depth = 1
        src_kvs = __read_kv_from_file(file_path=path,
                                      format_=format_,
                                      separator=separator,
                                      prefix_to_add=prefix,
                                      depth=depth,
                                      content_type=content_type)

        if strict or not skip_features:
            # src_features is a list of KeyValue objects
            src_features = __read_features_from_file(file_path=path, format_=format_)

    elif source == 'appconfig':
        src_azconfig_client = get_appconfig_data_client(cmd, src_name, src_connection_string, src_auth_mode, src_endpoint)

        if label is not None and preserve_labels:
            raise CLIErrors.MutuallyExclusiveArgumentError("Import failed! Please provide only one of these arguments: '--label' or '--preserve-labels'. See 'az appconfig kv import -h' for examples.")
        if preserve_labels:
            # We need label to be the same as src_label for preview later.
            # This will have no effect on label while writing to config store
            # as we check preserve_labels again before labelling KVs.
            label = src_label

        src_kvs = __read_kv_from_config_store(src_azconfig_client,
                                              key=src_key,
                                              snapshot=src_snapshot,
                                              label=src_label if src_label else SearchFilterOptions.EMPTY_LABEL,
                                              tags=src_tags,
                                              prefix_to_add=prefix,
                                              correlation_request_id=correlation_request_id)

        if not skip_features:
            if src_snapshot:
                all_features = [kv for kv in src_kvs if kv.key.startswith(FeatureFlagConstants.FEATURE_FLAG_PREFIX)]
            else:
                # Get all Feature flags with matching label and tags
                all_features = __read_kv_from_config_store(src_azconfig_client,
                                                           key=FeatureFlagConstants.FEATURE_FLAG_PREFIX + '*',
                                                           label=src_label if src_label else SearchFilterOptions.EMPTY_LABEL,
                                                           tags=src_tags,
                                                           correlation_request_id=correlation_request_id)

            for feature in all_features:
                if feature.content_type == FeatureFlagConstants.FEATURE_FLAG_CONTENT_TYPE:
                    src_features.append(feature)

        # We need to separate KV from feature flags
        __discard_features_from_retrieved_kv(src_kvs)

    elif source == 'appservice':
        src_kvs = __read_kv_from_app_service(
            cmd, appservice_account=appservice_account, prefix_to_add=prefix, content_type=content_type)

    elif source == 'aks':
        if separator:
            # If separator is provided, use max depth by default unless depth is specified.
            depth = sys.maxsize if depth is None else int(depth)
        else:
            if depth and int(depth) != 1:
                logger.warning("Cannot flatten hierarchical data without a separator. --depth argument will be ignored.")
            depth = 1

        src_kvs = __read_kv_from_kubernetes_configmap(cmd,
                                                      aks_cluster=aks_cluster,
                                                      configmap_name=configmap_name,
                                                      namespace=configmap_namespace,
                                                      prefix_to_add=prefix,
                                                      content_type=content_type,
                                                      format_=format_,
                                                      separator=separator,
                                                      depth=depth)

    if strict or not yes or import_mode == ImportMode.IGNORE_MATCH:
        # fetch key values from user's configstore
        dest_kvs = __read_kv_from_config_store(azconfig_client,
                                               key=prefix + SearchFilterOptions.ANY_KEY if prefix else SearchFilterOptions.ANY_KEY,
                                               label=label if label else SearchFilterOptions.EMPTY_LABEL,
                                               correlation_request_id=correlation_request_id)
        __discard_features_from_retrieved_kv(dest_kvs)

    # if customer needs preview & confirmation

    # generate preview and wait for user confirmation
    kv_comparer = KVComparer(
        src_kvs=src_kvs,
        compare_fields=CompareFieldsMap[source],
        preserve_labels=source == "appconfig" and preserve_labels,
        label=label,
        content_type=content_type)

    kv_diff = kv_comparer.compare(dest_kvs=dest_kvs, strict=strict, ignore_matching_kvs=import_mode == ImportMode.IGNORE_MATCH)
    # Show indented key-value preview similar to kvset for appconfig source
    indent = 2 if source == "appconfig" else None
    need_kv_change = print_preview(kv_diff, source, yes=yes, strict=strict, title="Key Values", indent=indent)

    need_feature_change = False
    ff_diff = {}
    if strict or (src_features and not skip_features):
        all_features = __read_kv_from_config_store(azconfig_client,
                                                   key=FeatureFlagConstants.FEATURE_FLAG_PREFIX + SearchFilterOptions.ANY_KEY,
                                                   label=label if label else SearchFilterOptions.EMPTY_LABEL,
                                                   correlation_request_id=correlation_request_id)

        # Append all features to dest_features list
        for feature in all_features:
            if feature.content_type == FeatureFlagConstants.FEATURE_FLAG_CONTENT_TYPE:
                dest_features.append(feature)

        ff_comparer = KVComparer(
            src_kvs=src_features,
            compare_fields=CompareFieldsMap[source],
            preserve_labels=source == "appconfig" and preserve_labels,
            label=label)
        ff_diff = ff_comparer.compare(dest_kvs=dest_features, strict=strict, ignore_matching_kvs=import_mode == ImportMode.IGNORE_MATCH)
        need_feature_change = print_preview(ff_diff, source, yes=yes, strict=strict, title="Feature Flags")

    if (not need_kv_change and not need_feature_change) or dry_run:
        return

    if not yes:
        user_confirmation("Do you want to continue? \n")

    # append all feature flags to src_kvs list
    src_kvs.extend(src_features)

    # In strict mode, delete kvs with specific label that are missing from the imported file
    if strict:
        kvs_to_delete = chain(
            kv_diff.get(JsonDiff.DELETE, []),
            ff_diff.get(JsonDiff.DELETE, []))

        for kv in kvs_to_delete:
            __delete_configuration_setting_from_config_store(azconfig_client, kv)

    # import into configstore
    # write only added and updated kvs
    if import_mode == ImportMode.IGNORE_MATCH:
        kvs_to_write = []
        kvs_to_write.extend(kv_diff.get(JsonDiff.ADD, []))
        kvs_to_write.extend(ff_diff.get(JsonDiff.ADD, []))
        kvs_to_write.extend(update["new"] for update in kv_diff.get(JsonDiff.UPDATE, []))
        kvs_to_write.extend(update["new"] for update in ff_diff.get(JsonDiff.UPDATE, []))

    # write all kvs
    else:
        kvs_to_write = src_kvs

    __write_kv_and_features_to_config_store(azconfig_client,
                                            key_values=kvs_to_write,
                                            label=label,
                                            tags=tags,
                                            preserve_labels=preserve_labels,
                                            content_type=content_type,
                                            correlation_request_id=correlation_request_id)


def export_config(cmd,
                  destination,
                  name=None,
                  connection_string=None,
                  label=None,
                  key=None,
                  tags=None,  # tags to filter
                  prefix="",  # prefix to remove
                  yes=False,
                  skip_features=False,
                  skip_keyvault=False,
                  auth_mode="key",
                  endpoint=None,
                  snapshot=None,
                  dry_run=False,
                  # to-file parameters
                  path=None,
                  format_=None,
                  separator=None,
                  naming_convention='pascal',
                  resolve_keyvault=False,
                  profile=ImportExportProfiles.DEFAULT,
                  # to-config-store parameters
                  dest_name=None,
                  dest_connection_string=None,
                  dest_label=None,
                  preserve_labels=False,
                  dest_auth_mode="key",
                  dest_endpoint=None,
                  dest_tags=None,  # tags to add
                  # to-app-service parameters
                  appservice_account=None,
                  export_as_reference=False):

    src_features = []
    dest_features = []
    dest_kvs = []
    destination = destination.lower()
    profile = profile.lower()
    format_ = format_.lower() if format_ else None
    naming_convention = naming_convention.lower()

    azconfig_client = get_appconfig_data_client(cmd, name, connection_string, auth_mode, endpoint)

    # generate correlation_request_id for bulk operation
    correlation_request_id = str(uuid.uuid4())

    dest_azconfig_client = None
    if destination == 'appconfig':
        if dest_label is not None and preserve_labels:
            raise CLIErrors.MutuallyExclusiveArgumentError("Export failed! Please provide only one of these arguments: '--dest-label' or '--preserve-labels'. See 'az appconfig kv export -h' for examples.")
        if preserve_labels:
            # We need dest_label to be the same as label for preview later.
            # This will have no effect on label while writing to config store
            # as we check preserve_labels again before labelling KVs.
            dest_label = label
        dest_azconfig_client = get_appconfig_data_client(cmd, dest_name, dest_connection_string, dest_auth_mode, dest_endpoint)

    # fetch key values from user's configstore
    src_kvs = __read_kv_from_config_store(azconfig_client,
                                          key=key,
                                          label=label if label else SearchFilterOptions.EMPTY_LABEL,
                                          tags=tags,
                                          prefix_to_remove=prefix if not export_as_reference else "",
                                          snapshot=snapshot,
                                          cli_ctx=cmd.cli_ctx if resolve_keyvault else None,
                                          correlation_request_id=correlation_request_id)

    if skip_keyvault:
        src_kvs = [keyvalue for keyvalue in src_kvs if keyvalue.content_type != KeyVaultConstants.KEYVAULT_CONTENT_TYPE]

    if not skip_features:
        # Get all Feature flags with matching label
        if (destination == 'file' and format_ == 'properties') or destination == 'appservice':
            skip_features = True
            logger.warning("Exporting feature flags to properties file or appservice is currently not supported.")
        else:
            if snapshot:
                src_features = [map_keyvalue_to_featureflag(
                    kv) for kv in src_kvs if kv.key.startswith(FeatureFlagConstants.FEATURE_FLAG_PREFIX)]

            # src_features is a list of FeatureFlag objects
            else:
                src_features = __list_features(
                    cmd,
                    feature="*",
                    label=label if label else SearchFilterOptions.EMPTY_LABEL,
                    tags=tags,
                    name=name,
                    connection_string=connection_string,
                    all_=True,
                    auth_mode=auth_mode,
                    endpoint=endpoint,
                    correlation_request_id=correlation_request_id,
                )

    # We need to separate KV from feature flags for the default export profile and only need to discard
    # if skip_features is true for the appconfig/kvset export profile.
    if profile == ImportExportProfiles.DEFAULT or (profile == ImportExportProfiles.KVSET and skip_features):
        __discard_features_from_retrieved_kv(src_kvs)

    if profile == ImportExportProfiles.KVSET:
        __export_kvset_to_file(file_path=path, keyvalues=src_kvs, yes=yes, dry_run=dry_run)
        return

    if destination == 'appservice' and export_as_reference:
        if endpoint is None:
            # Endpoint will not be None as it is already resolved in creating azconfig_client
            endpoint = get_store_endpoint_from_connection_string(connection_string) or resolve_store_metadata(cmd, name)[1]

        src_kvs = [__map_to_appservice_config_reference(kv, endpoint, prefix) for kv in src_kvs]

    if destination == 'appconfig':
        # dest_kvs contains features and KV that match the label
        dest_kvs = __read_kv_from_config_store(dest_azconfig_client,
                                               key=SearchFilterOptions.ANY_KEY,
                                               label=dest_label if dest_label else SearchFilterOptions.EMPTY_LABEL,
                                               correlation_request_id=correlation_request_id)
        __discard_features_from_retrieved_kv(dest_kvs)

        if not skip_features:
            # Append all features to dest_features list
            dest_features = __list_features(
                cmd,
                feature="*",
                label=dest_label if dest_label else SearchFilterOptions.EMPTY_LABEL,
                name=dest_name,
                connection_string=dest_connection_string,
                all_=True,
                auth_mode=dest_auth_mode,
                endpoint=dest_endpoint,
                correlation_request_id=correlation_request_id,
            )

    elif destination == 'appservice':
        dest_kvs = __read_kv_from_app_service(cmd, appservice_account=appservice_account)

    kv_comparer = KVComparer(
        src_kvs=src_kvs,
        compare_fields=CompareFieldsMap[destination],
        preserve_labels=destination == "appconfig" and preserve_labels,
        label=dest_label)

    kv_diff = kv_comparer.compare(dest_kvs=dest_kvs)

    # Show indented key-value preview similar to kvset for appconfig destination
    indent = 2 if destination == "appconfig" else None
    need_kv_change = print_preview(kv_diff, destination, yes=yes, title="Key Values", indent=indent)

    need_feature_change = False
    ff_diff = {}
    if src_features:
        ff_comparer = KVComparer(
            src_kvs=__convert_featureflag_list_to_keyvalue_list(src_features),
            compare_fields=CompareFieldsMap[destination],
            preserve_labels=destination == "appconfig" and preserve_labels,
            label=dest_label)

        ff_diff = ff_comparer.compare(dest_kvs=__convert_featureflag_list_to_keyvalue_list(dest_features))
        need_feature_change = print_preview(ff_diff, destination, yes=yes, title="Feature Flags")

    if (not need_feature_change and not need_kv_change) or dry_run:
        return

    # if customer needs preview & confirmation
    if not yes:
        user_confirmation("Do you want to continue? \n")

    # export to destination
    if destination == 'file':
        __write_kv_and_features_to_file(file_path=path, key_values=src_kvs, features=src_features,
                                        format_=format_, separator=separator, skip_features=skip_features,
                                        naming_convention=naming_convention)
    elif destination == 'appconfig':
        __write_kv_and_features_to_config_store(dest_azconfig_client, key_values=src_kvs, features=src_features,
                                                label=dest_label, tags=dest_tags, preserve_labels=preserve_labels,
                                                correlation_request_id=correlation_request_id)
    elif destination == 'appservice':
        __write_kv_to_app_service(cmd, key_values=src_kvs, appservice_account=appservice_account)


def set_key(cmd,
            key,
            name=None,
            label=None,
            content_type=None,
            tags=None,
            value=None,
            yes=False,
            connection_string=None,
            auth_mode="key",
            endpoint=None):
    azconfig_client = get_appconfig_data_client(cmd, name, connection_string, auth_mode, endpoint)

    if content_type:
        if content_type.lower() == KeyVaultConstants.KEYVAULT_CONTENT_TYPE:
            logger.warning("There is a dedicated command to set key vault reference. 'appconfig kv set-keyvault -h'")
        elif content_type.lower() == FeatureFlagConstants.FEATURE_FLAG_CONTENT_TYPE:
            logger.warning("There is a dedicated command to set feature flag. 'appconfig feature set -h'")

    retry_times = 3
    retry_interval = 1

    label = label if label and label != SearchFilterOptions.EMPTY_LABEL else None

    # generate correlation request id for operations in the same activity
    correlation_request_id = str(uuid.uuid4())

    for i in range(0, retry_times):
        retrieved_kv = None
        set_kv = None
        new_kv = None

        try:
            retrieved_kv = azconfig_client.get_configuration_setting(key=key, label=label, headers={HttpHeaders.CORRELATION_REQUEST_ID: correlation_request_id})
        except ResourceNotFoundError:
            logger.debug("Key '%s' with label '%s' not found. A new key-value will be created.", key, label)
        except HttpResponseError as exception:
            raise CLIErrors.AzureResponseError("Failed to retrieve key-values from config store. " + str(exception))

        if retrieved_kv is None:
            if is_json_content_type(content_type):
                try:
                    # Ensure that provided value is valid JSON and strip comments if needed.
                    value = 'null' if value is None else value

                    __validate_json_value(value, content_type)
                except ValueError:
                    raise CLIErrors.ValidationError('Value "{}" is not a valid JSON object, which conflicts with the content type "{}".'.format(value, content_type))

            set_kv = ConfigurationSetting(key=key,
                                          label=label,
                                          value="" if value is None else value,
                                          content_type="" if content_type is None else content_type,
                                          tags=tags)
        else:
            value = retrieved_kv.value if value is None else value
            content_type = retrieved_kv.content_type if content_type is None else content_type
            if is_json_content_type(content_type):
                try:
                    # Ensure that provided value is valid JSON and strip comments if needed.
                    __validate_json_value(value, content_type)
                except (TypeError, ValueError):
                    raise CLIErrors.ValidationError('Value "{}" is not a valid JSON object, which conflicts with the content type "{}". Set the value again in valid JSON format.'.format(value, content_type))
            set_kv = ConfigurationSetting(key=key,
                                          label=label,
                                          value=value,
                                          content_type=content_type,
                                          tags=retrieved_kv.tags if tags is None else tags,
                                          read_only=retrieved_kv.read_only,
                                          etag=retrieved_kv.etag)

        verification_kv = {
            "key": set_kv.key,
            "label": set_kv.label,
            "content_type": set_kv.content_type,
            "value": set_kv.value,
            "tags": set_kv.tags
        }

        entry = json.dumps(verification_kv, indent=2, sort_keys=True, ensure_ascii=False)
        confirmation_message = "Are you sure you want to set the key: \n" + entry + "\n"
        user_confirmation(confirmation_message, yes)

        try:
            if set_kv.etag is None:
                new_kv = azconfig_client.add_configuration_setting(set_kv, headers={HttpHeaders.CORRELATION_REQUEST_ID: correlation_request_id})
            else:
                new_kv = azconfig_client.set_configuration_setting(set_kv, match_condition=MatchConditions.IfNotModified, headers={HttpHeaders.CORRELATION_REQUEST_ID: correlation_request_id})
            return convert_configurationsetting_to_keyvalue(new_kv)

        except ResourceReadOnlyError:
            raise CLIError("Failed to update read only key-value. Unlock the key-value before updating it.")
        except HttpResponseError as exception:
            if exception.status_code == StatusCodes.PRECONDITION_FAILED:
                logger.debug('Retrying setting %s times with exception: concurrent setting operations', i + 1)
                time.sleep(retry_interval)
            else:
                raise CLIError("Failed to set the key-value due to an exception: " + str(exception))
        except Exception as exception:
            raise CLIError("Failed to set the key-value due to an exception: " + str(exception))
    raise CLIError("Failed to set the key '{}' due to a conflicting operation.".format(key))


def set_keyvault(cmd,
                 key,
                 secret_identifier,
                 name=None,
                 label=None,
                 tags=None,
                 yes=False,
                 connection_string=None,
                 auth_mode="key",
                 endpoint=None):
    azconfig_client = get_appconfig_data_client(cmd, name, connection_string, auth_mode, endpoint)

    keyvault_ref_value = json.dumps({"uri": secret_identifier}, ensure_ascii=False)
    retry_times = 3
    retry_interval = 1

    label = label if label and label != SearchFilterOptions.EMPTY_LABEL else None

    # generate correlation request id for operations in the same activity
    correlation_request_id = str(uuid.uuid4())

    for i in range(0, retry_times):
        retrieved_kv = None
        set_kv = None
        new_kv = None

        try:
            retrieved_kv = azconfig_client.get_configuration_setting(key=key, label=label, headers={HttpHeaders.CORRELATION_REQUEST_ID: correlation_request_id})
        except ResourceNotFoundError:
            logger.debug("Key '%s' with label '%s' not found. A new key-vault reference will be created.", key, label)
        except HttpResponseError as exception:
            raise CLIErrors.AzureResponseError("Failed to retrieve key-values from config store. " + str(exception))

        if retrieved_kv is None:
            set_kv = ConfigurationSetting(key=key,
                                          label=label,
                                          value=keyvault_ref_value,
                                          content_type=KeyVaultConstants.KEYVAULT_CONTENT_TYPE,
                                          tags=tags)
        else:
            set_kv = ConfigurationSetting(key=key,
                                          label=label,
                                          value=keyvault_ref_value,
                                          content_type=KeyVaultConstants.KEYVAULT_CONTENT_TYPE,
                                          tags=retrieved_kv.tags if tags is None else tags,
                                          read_only=retrieved_kv.read_only,
                                          etag=retrieved_kv.etag)

        verification_kv = {
            "key": set_kv.key,
            "label": set_kv.label,
            "content_type": set_kv.content_type,
            "value": set_kv.value,
            "tags": set_kv.tags
        }
        entry = json.dumps(verification_kv, indent=2, sort_keys=True, ensure_ascii=False)
        confirmation_message = "Are you sure you want to set the keyvault reference: \n" + entry + "\n"
        user_confirmation(confirmation_message, yes)

        try:
            if set_kv.etag is None:
                new_kv = azconfig_client.add_configuration_setting(set_kv, headers={HttpHeaders.CORRELATION_REQUEST_ID: correlation_request_id})
            else:
                new_kv = azconfig_client.set_configuration_setting(set_kv, match_condition=MatchConditions.IfNotModified, headers={HttpHeaders.CORRELATION_REQUEST_ID: correlation_request_id})
            return convert_configurationsetting_to_keyvalue(new_kv)

        except ResourceReadOnlyError:
            raise CLIError("Failed to update read only key vault reference. Unlock the key vault reference before updating it.")
        except HttpResponseError as exception:
            if exception.status_code == StatusCodes.PRECONDITION_FAILED:
                logger.debug('Retrying setting %s times with exception: concurrent setting operations', i + 1)
                time.sleep(retry_interval)
            else:
                raise CLIErrors.AzureResponseError("Failed to set the keyvault reference due to an exception: " + str(exception))
        except Exception as exception:
            raise CLIError("Failed to set the keyvault reference due to an exception: " + str(exception))
    raise CLIError("Failed to set the keyvault reference '{}' due to a conflicting operation.".format(key))


def delete_key(cmd,
               key,
               name=None,
               label=None,
               tags=None,
               yes=False,
               connection_string=None,
               auth_mode="key",
               endpoint=None):
    azconfig_client = get_appconfig_data_client(cmd, name, connection_string, auth_mode, endpoint)

    # list_configuration_settings returns kv with null label when:
    # label = ASCII null 0x00, or URL encoded %00
    # In delete, import and export commands, we treat missing --label as null label
    # In list, restore and revision commands, we treat missing --label as all labels

    # generate correlation request id for operations in the same activity
    correlation_request_id = str(uuid.uuid4())

    entries = __read_kv_from_config_store(azconfig_client,
                                          key=key,
                                          label=label if label else SearchFilterOptions.EMPTY_LABEL,
                                          tags=tags,
                                          correlation_request_id=correlation_request_id)
    confirmation_message = "Found '{}' key-values matching the specified key, label and tags. Are you sure you want to delete these key-values?".format(len(entries))
    user_confirmation(confirmation_message, yes)

    deleted_entries = []
    exception_messages = []
    for entry in entries:
        try:
            deleted_kv = azconfig_client.delete_configuration_setting(key=entry.key,
                                                                      label=entry.label,
                                                                      etag=entry.etag,
                                                                      match_condition=MatchConditions.IfNotModified,
                                                                      headers={HttpHeaders.CORRELATION_REQUEST_ID: correlation_request_id})
            deleted_entries.append(convert_configurationsetting_to_keyvalue(deleted_kv))

        except ResourceReadOnlyError:
            exception = "Failed to delete read-only key-value with key '{}' and label '{}'. Unlock the key-value before deleting it.".format(entry.key, entry.label)
            exception_messages.append(exception)
        except ResourceModifiedError:
            exception = "Failed to delete key-value with key '{}' and label '{}' due to a conflicting operation.".format(entry.key, entry.label)
            exception_messages.append(exception)
        except HttpResponseError as ex:
            exception_messages.append(str(ex))
            raise CLIErrors.AzureResponseError('Delete operation failed. The following error(s) occurred:\n' + json.dumps(exception_messages, indent=2, ensure_ascii=False))

    # Log errors if partially succeeded
    if exception_messages:
        if deleted_entries:
            logger.error('Delete operation partially failed. The following error(s) occurred:\n%s\n',
                         json.dumps(exception_messages, indent=2, ensure_ascii=False))
        else:
            raise CLIError('Delete operation failed. \n' + json.dumps(exception_messages, indent=2, ensure_ascii=False))

    return deleted_entries


def lock_key(cmd,
             key,
             label=None,
             name=None,
             connection_string=None,
             yes=False,
             auth_mode="key",
             endpoint=None):
    azconfig_client = get_appconfig_data_client(cmd, name, connection_string, auth_mode, endpoint)

    # generate correlation request id for operations in the same activity
    correlation_request_id = str(uuid.uuid4())

    retry_times = 3
    retry_interval = 1
    for i in range(0, retry_times):
        try:
            retrieved_kv = azconfig_client.get_configuration_setting(key=key, label=label, headers={HttpHeaders.CORRELATION_REQUEST_ID: correlation_request_id})
        except ResourceNotFoundError:
            raise CLIErrors.ResourceNotFoundError("Key '{}' with label '{}' does not exist.".format(key, label))
        except HttpResponseError as exception:
            raise CLIErrors.AzureResponseError("Failed to retrieve key-values from config store. " + str(exception))

        confirmation_message = "Are you sure you want to lock the key '{}' with label '{}'".format(key, label)
        user_confirmation(confirmation_message, yes)

        try:
            new_kv = azconfig_client.set_read_only(retrieved_kv, match_condition=MatchConditions.IfNotModified, headers={HttpHeaders.CORRELATION_REQUEST_ID: correlation_request_id})
            return convert_configurationsetting_to_keyvalue(new_kv)
        except HttpResponseError as exception:
            if exception.status_code == StatusCodes.PRECONDITION_FAILED:
                logger.debug('Retrying lock operation %s times with exception: concurrent setting operations', i + 1)
                time.sleep(retry_interval)
            else:
                raise CLIErrors.AzureResponseError("Failed to lock the key-value due to an exception: " + str(exception))
        except Exception as exception:
            raise CLIError("Failed to lock the key-value due to an exception: " + str(exception))
    raise CLIError("Failed to lock the key '{}' with label '{}' due to a conflicting operation.".format(key, label))


def unlock_key(cmd,
               key,
               label=None,
               name=None,
               connection_string=None,
               yes=False,
               auth_mode="key",
               endpoint=None):
    azconfig_client = get_appconfig_data_client(cmd, name, connection_string, auth_mode, endpoint)

    # generate correlation request id for operations in the same activity
    correlation_request_id = str(uuid.uuid4())

    retry_times = 3
    retry_interval = 1
    for i in range(0, retry_times):
        try:
            retrieved_kv = azconfig_client.get_configuration_setting(key=key, label=label, headers={HttpHeaders.CORRELATION_REQUEST_ID: correlation_request_id})
        except ResourceNotFoundError:
            raise CLIErrors.ResourceNotFoundError("Key '{}' with label '{}' does not exist.".format(key, label))
        except HttpResponseError as exception:
            raise CLIErrors.AzureResponseError("Failed to retrieve key-values from config store. " + str(exception))

        confirmation_message = "Are you sure you want to unlock the key '{}' with label '{}'".format(key, label)
        user_confirmation(confirmation_message, yes)

        try:
            new_kv = azconfig_client.set_read_only(retrieved_kv, read_only=False, match_condition=MatchConditions.IfNotModified, headers={HttpHeaders.CORRELATION_REQUEST_ID: correlation_request_id})
            return convert_configurationsetting_to_keyvalue(new_kv)
        except HttpResponseError as exception:
            if exception.status_code == StatusCodes.PRECONDITION_FAILED:
                logger.debug('Retrying unlock operation %s times with exception: concurrent setting operations', i + 1)
                time.sleep(retry_interval)
            else:
                raise CLIErrors.AzureResponseError("Failed to unlock the key-value due to an exception: " + str(exception))
        except Exception as exception:
            raise CLIError("Failed to unlock the key-value due to an exception: " + str(exception))
    raise CLIError("Failed to unlock the key '{}' with label '{}' due to a conflicting operation.".format(key, label))


def show_key(cmd,
             key,
             name=None,
             label=None,
             datetime=None,
             connection_string=None,
             auth_mode="key",
             endpoint=None):
    azconfig_client = get_appconfig_data_client(cmd, name, connection_string, auth_mode, endpoint)
    try:
        key_value = azconfig_client.get_configuration_setting(key=key, label=label, accept_datetime=datetime)
        if key_value is None:
            raise CLIErrors.ResourceNotFoundError("The key-value does not exist.")
        return convert_configurationsetting_to_keyvalue(key_value)
    except ResourceNotFoundError:
        raise CLIErrors.ResourceNotFoundError("Key '{}' with label '{}' does not exist.".format(key, label))
    except HttpResponseError as exception:
        raise CLIErrors.AzureResponseError('Failed to retrieve key-values from config store. ' + str(exception))

    raise CLIError("Failed to get the key '{}' with label '{}'.".format(key, label))


def list_key(cmd,
             key=None,
             fields=None,
             name=None,
             label=None,
             tags=None,
             datetime=None,
             snapshot=None,
             connection_string=None,
             top=None,
             all_=False,
             resolve_keyvault=False,
             auth_mode="key",
             endpoint=None):
    if fields and resolve_keyvault:
        raise CLIErrors.MutuallyExclusiveArgumentError("Please provide only one of these arguments: '--fields' or '--resolve-keyvault'. See 'az appconfig kv list -h' for examples.")

    if snapshot and (key or label or datetime):
        raise CLIErrors.MutuallyExclusiveArgumentError("'snapshot' cannot be specified with 'key', 'label', or 'datetime' filters.")

    azconfig_client = get_appconfig_data_client(cmd, name, connection_string, auth_mode, endpoint)

    keyvalues = __read_kv_from_config_store(azconfig_client,
                                            key=key if key else SearchFilterOptions.ANY_KEY,
                                            label=label if label else SearchFilterOptions.ANY_LABEL,
                                            tags=tags,
                                            datetime=datetime,
                                            snapshot=snapshot,
                                            fields=fields,
                                            top=top,
                                            all_=all_,
                                            cli_ctx=cmd.cli_ctx if resolve_keyvault else None)
    return keyvalues


def restore_key(cmd,
                datetime,
                key=None,
                name=None,
                label=None,
                tags=None,
                connection_string=None,
                yes=False,
                auth_mode="key",
                dry_run=False,
                endpoint=None):
    azconfig_client = get_appconfig_data_client(cmd, name, connection_string, auth_mode, endpoint)

    # generate correlation_request_id for bulk operation
    correlation_request_id = str(uuid.uuid4())

    exception_messages = []
    restore_keyvalues = __read_kv_from_config_store(azconfig_client,
                                                    key=key if key else SearchFilterOptions.ANY_KEY,
                                                    label=label if label else SearchFilterOptions.ANY_LABEL,
                                                    tags=tags,
                                                    datetime=datetime,
                                                    correlation_request_id=correlation_request_id)
    current_keyvalues = __read_kv_from_config_store(azconfig_client,
                                                    key=key if key else SearchFilterOptions.ANY_KEY,
                                                    label=label if label else SearchFilterOptions.ANY_LABEL,
                                                    tags=tags,
                                                    correlation_request_id=correlation_request_id)

    try:
        comparer = KVComparer(restore_keyvalues, CompareFieldsMap["restore"])
        restore_diff = comparer.compare(current_keyvalues, strict=True)

        need_change = __print_restore_preview(restore_diff, yes=yes)

        if dry_run or not need_change:
            return

        if not yes:
            user_confirmation("Do you want to continue? \n")

        kvs_to_restore = restore_diff.get(JsonDiff.ADD, [])
        kvs_to_modify = [update["new"] for update in restore_diff.get(JsonDiff.UPDATE, [])]
        kvs_to_delete = restore_diff.get(JsonDiff.DELETE, [])

        keys_to_restore = len(kvs_to_restore) + len(kvs_to_modify) + len(kvs_to_delete)
        restored_so_far = 0

        for kv in chain(kvs_to_restore, kvs_to_modify):
            set_kv = convert_keyvalue_to_configurationsetting(kv)
            try:
                azconfig_client.set_configuration_setting(set_kv, headers={HttpHeaders.CORRELATION_REQUEST_ID: correlation_request_id})
                restored_so_far += 1
            except ResourceReadOnlyError:
                exception = "Failed to update read-only key-value with key '{}' and label '{}'. Unlock the key-value before updating it.".format(set_kv.key, set_kv.label)
                exception_messages.append(exception)
            except ResourceModifiedError:
                exception = "Failed to update key-value with key '{}' and label '{}' due to a conflicting operation.".format(set_kv.key, set_kv.label)
                exception_messages.append(exception)

        for kv in kvs_to_delete:
            try:
                azconfig_client.delete_configuration_setting(key=kv.key,
                                                             label=kv.label,
                                                             etag=kv.etag,
                                                             match_condition=MatchConditions.IfNotModified,
                                                             headers={HttpHeaders.CORRELATION_REQUEST_ID: correlation_request_id})
                restored_so_far += 1
            except ResourceReadOnlyError:
                exception = "Failed to delete read-only key-value with key '{}' and label '{}'. Unlock the key-value before deleting it.".format(kv.key, kv.label)
                exception_messages.append(exception)
            except ResourceModifiedError:
                exception = "Failed to delete key-value with key '{}' and label '{}' due to a conflicting operation.".format(kv.key, kv.label)
                exception_messages.append(exception)

        if restored_so_far != keys_to_restore:
            logger.error('Failed after restoring %d out of %d keys. The following error(s) occurred:\n%s\n',
                         restored_so_far, keys_to_restore, json.dumps(exception_messages, indent=2, ensure_ascii=False))
        else:
            logger.debug('Successfully restored %d out of %d keys', restored_so_far, keys_to_restore)
        return

    except HttpResponseError as ex:
        exception_messages.append(str(ex))

    raise CLIError('Restore operation failed. The following error(s) occurred:\n' + json.dumps(exception_messages, indent=2, ensure_ascii=False))


def list_revision(cmd,
                  key=None,
                  fields=None,
                  name=None,
                  label=None,
                  tags=None,
                  datetime=None,
                  connection_string=None,
                  top=None,
                  all_=False,
                  auth_mode="key",
                  endpoint=None):
    azconfig_client = get_appconfig_data_client(cmd, name, connection_string, auth_mode, endpoint)

    key = key if key else SearchFilterOptions.ANY_KEY
    label = label if label else SearchFilterOptions.ANY_LABEL
    label = prep_filter_for_url_encoding(label)
    prepped_tags = [prep_filter_for_url_encoding(tag) for tag in tags] if tags else []

    try:
        query_fields = None
        if fields:
            query_fields = []
            for field in fields:
                query_fields.append(field.name.lower())

        revisions_iterable = azconfig_client.list_revisions(key_filter=key,
                                                            label_filter=label,
                                                            tags_filter=prepped_tags,
                                                            accept_datetime=datetime,
                                                            fields=query_fields)
        retrieved_revisions = []
        count = 0

        if all_:
            top = float('inf')
        elif top is None:
            top = 100

        for revision in revisions_iterable:
            kv_revision = convert_configurationsetting_to_keyvalue(revision)
            if fields:
                partial_revision = {}
                for field in fields:
                    partial_revision[field.name.lower()] = kv_revision.__dict__[field.name.lower()]
                retrieved_revisions.append(partial_revision)
            else:
                retrieved_revisions.append(kv_revision)
            count += 1
            if count >= top:
                return retrieved_revisions
        return retrieved_revisions
    except HttpResponseError as ex:
        raise CLIErrors.AzureResponseError('List revision operation failed.\n' + str(ex))


def __validate_json_value(json_string, content_type):
    # We do not allow comments in keyvault references, feature flags, and AI chat completion configs
    if content_type in (FeatureFlagConstants.FEATURE_FLAG_CONTENT_TYPE, KeyVaultConstants.KEYVAULT_CONTENT_TYPE, AIConfigConstants.AI_CHAT_COMPLETION_CONTENT_TYPE):
        json.loads(json_string)

    else:
        parse_json_with_comments(json_string)
