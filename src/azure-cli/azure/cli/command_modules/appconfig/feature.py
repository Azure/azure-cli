# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, too-many-statements, too-many-locals, too-many-branches

import json
import time
import re
import copy
import uuid

from knack.log import get_logger
from knack.util import CLIError
from ._constants import HttpHeaders
import azure.cli.core.azclierror as CLIErrors

from azure.appconfiguration import (ConfigurationSetting,
                                    ResourceReadOnlyError)
from azure.core import MatchConditions
from azure.cli.core.util import user_confirmation
from azure.core.exceptions import (HttpResponseError,
                                   ResourceNotFoundError,
                                   ResourceModifiedError)

from ._constants import (FeatureFlagConstants, SearchFilterOptions, StatusCodes)
from ._models import (KeyValue,
                      convert_configurationsetting_to_keyvalue,
                      convert_keyvalue_to_configurationsetting)
from ._utils import (get_appconfig_data_client,
                     prep_filter_for_url_encoding,
                     validate_feature_flag_name)
from ._featuremodels import (map_keyvalue_to_featureflag,
                             map_keyvalue_to_featureflagvalue,
                             FeatureFilter)


logger = get_logger(__name__)

# Feature commands #


def set_feature(cmd,
                feature=None,
                key=None,
                name=None,
                label=None,
                description=None,
                requirement_type=None,
                yes=False,
                connection_string=None,
                auth_mode="key",
                endpoint=None,
                tags=None):
    if key is None and feature is None:
        raise CLIErrors.RequiredArgumentMissingError("Please provide either `--key` or `--feature` value.")

    key = FeatureFlagConstants.FEATURE_FLAG_PREFIX + feature if key is None else key

    # If only key is indicated, ensure that the feature name derived from the key is valid.
    if feature is None:
        feature = key[len(FeatureFlagConstants.FEATURE_FLAG_PREFIX):]
        try:
            validate_feature_flag_name(feature)
        except CLIErrors.InvalidArgumentValueError as exception:
            exception.error_msg = "The feature name derived from the specified key is invalid. " + exception.error_msg
            raise exception

    # when creating a new Feature flag, these defaults will be used
    default_conditions = {FeatureFlagConstants.CLIENT_FILTERS: []}

    if requirement_type:
        default_conditions[FeatureFlagConstants.REQUIREMENT_TYPE] = (
            FeatureFlagConstants.REQUIREMENT_TYPE_ALL
            if requirement_type.lower() == FeatureFlagConstants.REQUIREMENT_TYPE_ALL.lower()
            else FeatureFlagConstants.REQUIREMENT_TYPE_ANY
        )

    default_value = {
        FeatureFlagConstants.ID: feature,
        FeatureFlagConstants.DESCRIPTION: "" if description is None else description,
        FeatureFlagConstants.ENABLED: False,
        FeatureFlagConstants.CONDITIONS: default_conditions
    }

    azconfig_client = get_appconfig_data_client(cmd, name, connection_string, auth_mode, endpoint)

    retry_times = 3
    retry_interval = 1

    label = label if label and label != SearchFilterOptions.EMPTY_LABEL else None

    # generate correlation request id for operations in the same activity
    correlation_request_id = str(uuid.uuid4())

    for i in range(0, retry_times):
        retrieved_kv = None
        set_kv = None
        set_configsetting = None
        new_kv = None

        try:
            retrieved_kv = azconfig_client.get_configuration_setting(key=key, label=label, headers={HttpHeaders.CORRELATION_REQUEST_ID: correlation_request_id})
        except ResourceNotFoundError:
            logger.debug("Feature flag '%s' with label '%s' not found. A new feature flag will be created.", feature, label)
        except HttpResponseError as exception:
            raise CLIErrors.AzureResponseError("Failed to retrieve feature flags from config store. " + str(exception))

        try:
            # if kv exists and only content-type is wrong, we can force correct it by updating the kv
            if retrieved_kv is None:
                set_kv = KeyValue(key=key,
                                  value=json.dumps(default_value, ensure_ascii=False),
                                  label=label,
                                  tags=tags,
                                  content_type=FeatureFlagConstants.FEATURE_FLAG_CONTENT_TYPE)
            else:
                if retrieved_kv.content_type != FeatureFlagConstants.FEATURE_FLAG_CONTENT_TYPE:
                    logger.warning(
                        "This feature contains invalid content-type. The feature flag will be overwritten.")
                # we make sure that value retrieved is a valid json and only has the fields supported by backend.
                # if it's invalid, we catch appropriate exception that contains
                # detailed message
                feature_flag_value = map_keyvalue_to_featureflagvalue(retrieved_kv)

                # User can only update description if the key already exists
                if description is not None:
                    feature_flag_value.description = description

                if requirement_type is not None:
                    feature_flag_value.conditions[FeatureFlagConstants.REQUIREMENT_TYPE] = (
                        FeatureFlagConstants.REQUIREMENT_TYPE_ALL
                        if requirement_type.lower() == FeatureFlagConstants.REQUIREMENT_TYPE_ALL.lower()
                        else FeatureFlagConstants.REQUIREMENT_TYPE_ANY
                    )

                set_kv = KeyValue(key=key,
                                  label=label,
                                  value=json.dumps(feature_flag_value, default=lambda o: {k: v for k, v in o.__dict__.items() if v is not None}, ensure_ascii=False),
                                  content_type=FeatureFlagConstants.FEATURE_FLAG_CONTENT_TYPE,
                                  tags=retrieved_kv.tags if tags is None else tags,
                                  etag=retrieved_kv.etag,
                                  last_modified=retrieved_kv.last_modified)

            # Convert KeyValue object to required FeatureFlag format for
            # display

            feature_flag = map_keyvalue_to_featureflag(set_kv, show_all_details=True)
            entry = json.dumps(feature_flag, default=lambda o: o.__dict__, indent=2, sort_keys=True, ensure_ascii=False)

        except Exception as exception:
            # Exceptions for ValueError and AttributeError already have customized message
            # No need to catch specific exception here and customize
            raise CLIError(str(exception))

        confirmation_message = "Are you sure you want to set the feature flag: \n" + entry + "\n"
        user_confirmation(confirmation_message, yes)
        set_configsetting = convert_keyvalue_to_configurationsetting(set_kv)

        try:
            if set_configsetting.etag is None:
                new_kv = azconfig_client.add_configuration_setting(set_configsetting, headers={HttpHeaders.CORRELATION_REQUEST_ID: correlation_request_id})
            else:
                new_kv = azconfig_client.set_configuration_setting(set_configsetting, match_condition=MatchConditions.IfNotModified, headers={HttpHeaders.CORRELATION_REQUEST_ID: correlation_request_id})
            return map_keyvalue_to_featureflag(convert_configurationsetting_to_keyvalue(new_kv))

        except ResourceReadOnlyError:
            raise CLIError("Failed to update read only feature flag. Unlock the feature flag before updating it.")
        except HttpResponseError as exception:
            if exception.status_code == StatusCodes.PRECONDITION_FAILED:
                logger.debug('Retrying setting %s times with exception: concurrent setting operations', i + 1)
                time.sleep(retry_interval)
            else:
                raise CLIErrors.AzureResponseError(str(exception))
        except Exception as exception:
            raise CLIError(str(exception))
    raise CLIError("Failed to set the feature flag '{}' due to a conflicting operation.".format(feature))


def delete_feature(cmd,
                   feature=None,
                   key=None,
                   name=None,
                   label=None,
                   yes=False,
                   connection_string=None,
                   auth_mode="key",
                   endpoint=None,
                   tags=None):
    if key is None and feature is None:
        raise CLIErrors.RequiredArgumentMissingError("Please provide either `--key` or `--feature` value.")
    if key and feature:
        logger.warning("Since both `--key` and `--feature` are provided, `--feature` argument will be ignored.")

    if key is not None:
        key_filter = key
    elif feature is not None:
        key_filter = FeatureFlagConstants.FEATURE_FLAG_PREFIX + feature

    azconfig_client = get_appconfig_data_client(cmd, name, connection_string, auth_mode, endpoint)

    # generate correlation request id for operations in the same activity
    correlation_request_id = str(uuid.uuid4())

    retrieved_keyvalues = __list_all_keyvalues(azconfig_client,
                                               key_filter=key_filter,
                                               label=SearchFilterOptions.EMPTY_LABEL if label is None else label,
                                               correlation_request_id=correlation_request_id,
                                               tags=tags)

    confirmation_message = "Found '{}' feature flags matching the specified feature, label, and tags. Are you sure you want to delete these feature flags?".format(len(retrieved_keyvalues))
    user_confirmation(confirmation_message, yes)

    deleted_kvs = []
    exception_messages = []
    for entry in retrieved_keyvalues:
        feature_name = entry.key[len(FeatureFlagConstants.FEATURE_FLAG_PREFIX):]
        try:
            deleted_kv = azconfig_client.delete_configuration_setting(key=entry.key,
                                                                      label=entry.label,
                                                                      etag=entry.etag,
                                                                      match_condition=MatchConditions.IfNotModified,
                                                                      headers={HttpHeaders.CORRELATION_REQUEST_ID: correlation_request_id})
            deleted_kvs.append(convert_configurationsetting_to_keyvalue(deleted_kv))
        except ResourceReadOnlyError:
            exception = "Failed to delete read-only feature '{}' with label '{}'. Unlock the feature flag before deleting it.".format(feature_name, entry.label)
            exception_messages.append(exception)
        except ResourceModifiedError:
            exception = "Failed to delete feature '{}' with label '{}' due to a conflicting operation.".format(feature_name, entry.label)
            exception_messages.append(exception)
        except HttpResponseError as ex:
            exception_messages.append(str(ex))
            raise CLIErrors.AzureResponseError('Delete operation failed. The following error(s) occurred:\n' + json.dumps(exception_messages, indent=2, ensure_ascii=False))

    # Log errors if partially succeeded
    if exception_messages:
        if deleted_kvs:
            logger.error('Delete operation partially failed. The following error(s) occurred:\n%s\n',
                         json.dumps(exception_messages, indent=2, ensure_ascii=False))
        else:
            raise CLIErrors.AzureResponseError('Delete operation failed. \n' + json.dumps(exception_messages, indent=2, ensure_ascii=False))

    # Convert result list of KeyValue to list of FeatureFlag
    deleted_ff = []
    for success_kv in deleted_kvs:
        success_ff = map_keyvalue_to_featureflag(success_kv, show_all_details=False)
        deleted_ff.append(success_ff)

    return deleted_ff


def show_feature(cmd,
                 feature=None,
                 key=None,
                 name=None,
                 label=None,
                 fields=None,
                 connection_string=None,
                 auth_mode="key",
                 endpoint=None):
    if key is None and feature is None:
        raise CLIErrors.RequiredArgumentMissingError("Please provide either `--key` or `--feature` value.")
    if key and feature:
        logger.warning("Since both `--key` and `--feature` are provided, `--feature` argument will be ignored.")

    key = FeatureFlagConstants.FEATURE_FLAG_PREFIX + feature if key is None else key
    # Get feature name from key for logging. If users have provided a different feature name, we ignore it anyway.
    feature = key[len(FeatureFlagConstants.FEATURE_FLAG_PREFIX):]

    azconfig_client = get_appconfig_data_client(cmd, name, connection_string, auth_mode, endpoint)

    try:
        config_setting = azconfig_client.get_configuration_setting(key=key, label=label)
        if config_setting is None or config_setting.content_type != FeatureFlagConstants.FEATURE_FLAG_CONTENT_TYPE:
            raise CLIErrors.ResourceNotFoundError("The feature flag does not exist.")

        retrieved_kv = convert_configurationsetting_to_keyvalue(config_setting)
        feature_flag = map_keyvalue_to_featureflag(keyvalue=retrieved_kv, show_all_details=True)

        # If user has specified fields, we still get all the fields and then
        # filter what we need from the response.
        if fields:
            partial_featureflag = {}
            for field in fields:
                # feature_flag is guaranteed to have all the fields because
                # we validate this in map_keyvalue_to_featureflag()
                # So this line will never throw AttributeError
                partial_featureflag[field.name.lower()] = getattr(feature_flag, field.name.lower())
            return partial_featureflag
        return feature_flag
    except ResourceNotFoundError:
        raise CLIErrors.ResourceNotFoundError("Feature '{}' with label '{}' does not exist.".format(feature, label))
    except HttpResponseError as exception:
        raise CLIErrors.AzureResponseError(str(exception))
    except Exception as exception:
        raise CLIError(str(exception))


def list_feature(cmd,
                 feature=None,
                 key=None,
                 name=None,
                 label=None,
                 fields=None,
                 connection_string=None,
                 top=None,
                 all_=False,
                 auth_mode="key",
                 endpoint=None,
                 tags=None):
    return __list_features(
        cmd=cmd,
        feature=feature,
        key=key,
        name=name,
        label=label,
        fields=fields,
        connection_string=connection_string,
        top=top,
        all_=all_,
        auth_mode=auth_mode,
        endpoint=endpoint,
        tags=tags
    )


def lock_feature(cmd,
                 feature=None,
                 key=None,
                 name=None,
                 label=None,
                 connection_string=None,
                 yes=False,
                 auth_mode="key",
                 endpoint=None):
    if key is None and feature is None:
        raise CLIErrors.RequiredArgumentMissingError("Please provide either `--key` or `--feature` value.")
    if key and feature:
        logger.warning("Since both `--key` and `--feature` are provided, `--feature` argument will be ignored.")

    key = FeatureFlagConstants.FEATURE_FLAG_PREFIX + feature if key is None else key
    # Get feature name from key for logging. If users have provided a different feature name, we ignore it anyway.
    feature = key[len(FeatureFlagConstants.FEATURE_FLAG_PREFIX):]

    azconfig_client = get_appconfig_data_client(cmd, name, connection_string, auth_mode, endpoint)

    # generate correlation request id for operations in the same activity
    correlation_request_id = str(uuid.uuid4())

    retry_times = 3
    retry_interval = 1
    for i in range(0, retry_times):
        try:
            retrieved_kv = azconfig_client.get_configuration_setting(key=key, label=label, headers={HttpHeaders.CORRELATION_REQUEST_ID: correlation_request_id})
        except ResourceNotFoundError:
            raise CLIErrors.ResourceNotFoundError("Feature '{}' with label '{}' does not exist.".format(feature, label))
        except HttpResponseError as exception:
            raise CLIErrors.AzureResponseError("Failed to retrieve feature flags from config store. " + str(exception))

        if retrieved_kv is None or retrieved_kv.content_type != FeatureFlagConstants.FEATURE_FLAG_CONTENT_TYPE:
            raise CLIErrors.ResourceNotFoundError("The feature '{}' you are trying to lock does not exist.".format(feature))

        confirmation_message = "Are you sure you want to lock the feature '{}' with label '{}'".format(feature, label)
        user_confirmation(confirmation_message, yes)

        try:
            new_kv = azconfig_client.set_read_only(retrieved_kv, match_condition=MatchConditions.IfNotModified, headers={HttpHeaders.CORRELATION_REQUEST_ID: correlation_request_id})
            return map_keyvalue_to_featureflag(convert_configurationsetting_to_keyvalue(new_kv),
                                               show_all_details=False)
        except HttpResponseError as exception:
            if exception.status_code == StatusCodes.PRECONDITION_FAILED:
                logger.debug('Retrying lock operation %s times with exception: concurrent setting operations', i + 1)
                time.sleep(retry_interval)
            else:
                raise CLIErrors.AzureResponseError(str(exception))
        except Exception as exception:
            raise CLIError(str(exception))
    raise CLIError("Failed to lock the feature '{}' with label '{}' due to a conflicting operation.".format(feature, label))


def unlock_feature(cmd,
                   feature=None,
                   key=None,
                   name=None,
                   label=None,
                   connection_string=None,
                   yes=False,
                   auth_mode="key",
                   endpoint=None):
    if key is None and feature is None:
        raise CLIErrors.RequiredArgumentMissingError("Please provide either `--key` or `--feature` value.")
    if key and feature:
        logger.warning("Since both `--key` and `--feature` are provided, `--feature` argument will be ignored.")

    key = FeatureFlagConstants.FEATURE_FLAG_PREFIX + feature if key is None else key
    # Get feature name from key for logging. If users have provided a different feature name, we ignore it anyway.
    feature = key[len(FeatureFlagConstants.FEATURE_FLAG_PREFIX):]

    azconfig_client = get_appconfig_data_client(cmd, name, connection_string, auth_mode, endpoint)

    # generate correlation request id for operations in the same activity
    correlation_request_id = str(uuid.uuid4())

    retry_times = 3
    retry_interval = 1
    for i in range(0, retry_times):
        try:
            retrieved_kv = azconfig_client.get_configuration_setting(key=key, label=label, headers={HttpHeaders.CORRELATION_REQUEST_ID: correlation_request_id})
        except ResourceNotFoundError:
            raise CLIErrors.ResourceNotFoundError("Feature '{}' with label '{}' does not exist.".format(feature, label))
        except HttpResponseError as exception:
            raise CLIErrors.AzureResponseError("Failed to retrieve feature flags from config store. " + str(exception))

        if retrieved_kv is None or retrieved_kv.content_type != FeatureFlagConstants.FEATURE_FLAG_CONTENT_TYPE:
            raise CLIErrors.ResourceNotFoundError("The feature '{}' you are trying to unlock does not exist.".format(feature))

        confirmation_message = "Are you sure you want to unlock the feature '{}' with label '{}'".format(feature, label)
        user_confirmation(confirmation_message, yes)

        try:
            new_kv = azconfig_client.set_read_only(retrieved_kv, read_only=False, match_condition=MatchConditions.IfNotModified, headers={HttpHeaders.CORRELATION_REQUEST_ID: correlation_request_id})
            return map_keyvalue_to_featureflag(convert_configurationsetting_to_keyvalue(new_kv),
                                               show_all_details=False)
        except HttpResponseError as exception:
            if exception.status_code == StatusCodes.PRECONDITION_FAILED:
                logger.debug('Retrying unlock operation %s times with exception: concurrent setting operations', i + 1)
                time.sleep(retry_interval)
            else:
                raise CLIErrors.AzureResponseError(str(exception))
        except Exception as exception:
            raise CLIError(str(exception))
    raise CLIError("Failed to unlock the feature '{}' with label '{}' due to a conflicting operation.".format(feature, label))


def enable_feature(cmd,
                   feature=None,
                   key=None,
                   name=None,
                   label=None,
                   connection_string=None,
                   yes=False,
                   auth_mode="key",
                   endpoint=None):
    if key is None and feature is None:
        raise CLIErrors.RequiredArgumentMissingError("Please provide either `--key` or `--feature` value.")
    if key and feature:
        logger.warning("Since both `--key` and `--feature` are provided, `--feature` argument will be ignored.")

    key = FeatureFlagConstants.FEATURE_FLAG_PREFIX + feature if key is None else key
    # Get feature name from key for logging. If users have provided a different feature name, we ignore it anyway.
    feature = key[len(FeatureFlagConstants.FEATURE_FLAG_PREFIX):]

    azconfig_client = get_appconfig_data_client(cmd, name, connection_string, auth_mode, endpoint)

    # generate correlation request id for operations in the same activity
    correlation_request_id = str(uuid.uuid4())

    retry_times = 3
    retry_interval = 1
    for i in range(0, retry_times):
        try:
            retrieved_kv = azconfig_client.get_configuration_setting(key=key, label=label, headers={HttpHeaders.CORRELATION_REQUEST_ID: correlation_request_id})
        except ResourceNotFoundError:
            raise CLIErrors.ResourceNotFoundError("Feature flag '{}' with label '{}' not found.".format(feature, label))
        except HttpResponseError as exception:
            raise CLIErrors.AzureResponseError("Failed to retrieve feature flags from config store. " + str(exception))

        try:
            if retrieved_kv is None or retrieved_kv.content_type != FeatureFlagConstants.FEATURE_FLAG_CONTENT_TYPE:
                raise CLIErrors.ResourceNotFoundError("The feature flag {} does not exist.".format(feature))

            # we make sure that value retrieved is a valid json and only has the fields supported by backend.
            # if it's invalid, we catch appropriate exception that contains
            # detailed message
            feature_flag_value = map_keyvalue_to_featureflagvalue(retrieved_kv)

            feature_flag_value.enabled = True
            confirmation_message = "Are you sure you want to enable this feature '{}'?".format(feature)
            user_confirmation(confirmation_message, yes)

            updated_key_value = __update_existing_key_value(azconfig_client=azconfig_client,
                                                            retrieved_kv=retrieved_kv,
                                                            updated_value=json.dumps(feature_flag_value,
                                                                                     default=lambda o: {k: v for k, v in o.__dict__.items() if v is not None},
                                                                                     ensure_ascii=False),
                                                            correlation_request_id=correlation_request_id)

            return map_keyvalue_to_featureflag(keyvalue=updated_key_value, show_all_details=False)

        except HttpResponseError as exception:
            if exception.status_code == StatusCodes.PRECONDITION_FAILED:
                logger.debug('Retrying feature enable operation %s times with exception: concurrent setting operations', i + 1)
                time.sleep(retry_interval)
            else:
                raise CLIErrors.AzureResponseError(str(exception))
        except Exception as exception:
            raise CLIError(str(exception))
    raise CLIError("Failed to enable the feature flag '{}' due to a conflicting operation.".format(feature))


def disable_feature(cmd,
                    feature=None,
                    key=None,
                    name=None,
                    label=None,
                    connection_string=None,
                    yes=False,
                    auth_mode="key",
                    endpoint=None):
    if key is None and feature is None:
        raise CLIErrors.RequiredArgumentMissingError("Please provide either `--key` or `--feature` value.")
    if key and feature:
        logger.warning("Since both `--key` and `--feature` are provided, `--feature` argument will be ignored.")

    key = FeatureFlagConstants.FEATURE_FLAG_PREFIX + feature if key is None else key
    # Get feature name from key for logging. If users have provided a different feature name, we ignore it anyway.
    feature = key[len(FeatureFlagConstants.FEATURE_FLAG_PREFIX):]

    azconfig_client = get_appconfig_data_client(cmd, name, connection_string, auth_mode, endpoint)

    # generate correlation request id for operations in the same activity
    correlation_request_id = str(uuid.uuid4())

    retry_times = 3
    retry_interval = 1
    for i in range(0, retry_times):
        try:
            retrieved_kv = azconfig_client.get_configuration_setting(key=key, label=label, headers={HttpHeaders.CORRELATION_REQUEST_ID: correlation_request_id})
        except ResourceNotFoundError:
            raise CLIErrors.ResourceNotFoundError("Feature flag '{}' with label '{}' not found.".format(feature, label))
        except HttpResponseError as exception:
            raise CLIErrors.AzureResponseError("Failed to retrieve feature flags from config store. " + str(exception))

        try:
            if retrieved_kv is None or retrieved_kv.content_type != FeatureFlagConstants.FEATURE_FLAG_CONTENT_TYPE:
                raise CLIErrors.ResourceNotFoundError("The feature flag {} does not exist.".format(feature))

            # we make sure that value retrieved is a valid json and only has the fields supported by backend.
            # if it's invalid, we catch appropriate exception that contains
            # detailed message
            feature_flag_value = map_keyvalue_to_featureflagvalue(retrieved_kv)

            feature_flag_value.enabled = False
            confirmation_message = "Are you sure you want to disable this feature '{}'?".format(feature)
            user_confirmation(confirmation_message, yes)

            updated_key_value = __update_existing_key_value(azconfig_client=azconfig_client,
                                                            retrieved_kv=retrieved_kv,
                                                            updated_value=json.dumps(feature_flag_value,
                                                                                     default=lambda o: {k: v for k, v in o.__dict__.items() if v is not None},
                                                                                     ensure_ascii=False),
                                                            correlation_request_id=correlation_request_id)

            return map_keyvalue_to_featureflag(keyvalue=updated_key_value, show_all_details=False)

        except HttpResponseError as exception:
            if exception.status_code == StatusCodes.PRECONDITION_FAILED:
                logger.debug('Retrying feature disable operation %s times with exception: concurrent setting operations', i + 1)
                time.sleep(retry_interval)
            else:
                raise CLIErrors.AzureResponseError(str(exception))
        except Exception as exception:
            raise CLIError(str(exception))
    raise CLIError("Failed to disable the feature flag '{}' due to a conflicting operation.".format(feature))


# Feature Filter commands #


def add_filter(cmd,
               filter_name,
               feature=None,
               key=None,
               name=None,
               label=None,
               filter_parameters=None,
               yes=False,
               index=None,
               connection_string=None,
               auth_mode="key",
               endpoint=None):
    if key is None and feature is None:
        raise CLIErrors.RequiredArgumentMissingError("Please provide either `--key` or `--feature` value.")
    if key and feature:
        logger.warning("Since both `--key` and `--feature` are provided, `--feature` argument will be ignored.")

    key = FeatureFlagConstants.FEATURE_FLAG_PREFIX + feature if key is None else key
    # Get feature name from key for logging. If users have provided a different feature name, we ignore it anyway.
    feature = key[len(FeatureFlagConstants.FEATURE_FLAG_PREFIX):]

    azconfig_client = get_appconfig_data_client(cmd, name, connection_string, auth_mode, endpoint)

    if index is None:
        index = float("-inf")

    # Construct feature filter to be added
    if filter_parameters is None:
        filter_parameters = {}
    new_filter = FeatureFilter(filter_name, filter_parameters)

    # generate correlation request id for operations in the same activity
    correlation_request_id = str(uuid.uuid4())

    retry_times = 3
    retry_interval = 1
    for i in range(0, retry_times):
        try:
            retrieved_kv = azconfig_client.get_configuration_setting(key=key, label=label, headers={HttpHeaders.CORRELATION_REQUEST_ID: correlation_request_id})
        except ResourceNotFoundError:
            raise CLIErrors.ResourceNotFoundError("Feature flag '{}' with label '{}' not found.".format(feature, label))
        except HttpResponseError as exception:
            raise CLIErrors.AzureResponseError("Failed to retrieve feature flags from config store. " + str(exception))

        try:
            if retrieved_kv is None or retrieved_kv.content_type != FeatureFlagConstants.FEATURE_FLAG_CONTENT_TYPE:
                raise CLIErrors.ResourceNotFoundError(
                    "The feature flag {} does not exist.".format(feature))

            # we make sure that value retrieved is a valid json and only has the fields supported by backend.
            # if it's invalid, we catch appropriate exception that contains
            # detailed message
            feature_flag_value = map_keyvalue_to_featureflagvalue(retrieved_kv)
            feature_filters = feature_flag_value.conditions[FeatureFlagConstants.CLIENT_FILTERS]

            entry = json.dumps(new_filter.__dict__, indent=2, ensure_ascii=False)
            confirmation_message = "Are you sure you want to add this filter?\n" + entry
            user_confirmation(confirmation_message, yes)

            # If user has specified index, we insert at that index
            if 0 <= index <= len(feature_filters):
                logger.debug("Adding new filter at index '%s'.\n", index)
                feature_filters.insert(index, new_filter)
            else:
                if index != float("-inf"):
                    logger.debug(
                        "Ignoring the provided index '%s' because it is out of range or invalid.\n", index)
                logger.debug("Adding new filter to the end of list.\n")
                feature_filters.append(new_filter)

            __update_existing_key_value(azconfig_client=azconfig_client,
                                        retrieved_kv=retrieved_kv,
                                        updated_value=json.dumps(feature_flag_value,
                                                                 default=lambda o: {k: v for k, v in o.__dict__.items() if v is not None},
                                                                 ensure_ascii=False),
                                        correlation_request_id=correlation_request_id)

            return new_filter

        except HttpResponseError as exception:
            if exception.status_code == StatusCodes.PRECONDITION_FAILED:
                logger.debug('Retrying filter add operation %s times with exception: concurrent setting operations', i + 1)
                time.sleep(retry_interval)
            else:
                raise CLIErrors.AzureResponseError(str(exception))
        except Exception as exception:
            raise CLIError(str(exception))
    raise CLIError(
        "Failed to add filter for the feature flag '{}' due to a conflicting operation.".format(feature))


def update_filter(cmd,
                  filter_name,
                  feature=None,
                  key=None,
                  name=None,
                  label=None,
                  filter_parameters=None,
                  yes=False,
                  index=None,
                  connection_string=None,
                  auth_mode=None,
                  endpoint=None):
    if auth_mode is None:
        auth_mode = "key"
    if key is None and feature is None:
        raise CLIErrors.RequiredArgumentMissingError(
            "Please provide either `--key` or `--feature` value.")
    if key and feature:
        logger.warning(
            "Since both `--key` and `--feature` are provided, `--feature` argument will be ignored.")

    key = FeatureFlagConstants.FEATURE_FLAG_PREFIX + feature if key is None else key
    # Get feature name from key for logging. If users have provided a different feature name, we ignore it anyway.
    feature = key[len(FeatureFlagConstants.FEATURE_FLAG_PREFIX):]

    azconfig_client = get_appconfig_data_client(
        cmd, name, connection_string, auth_mode, endpoint)

    if index is None:
        index = float("-inf")

    # Construct feature filter
    if filter_parameters is None:
        filter_parameters = {}
    new_filter = FeatureFilter(filter_name, filter_parameters)

    # generate correlation request id for operations in the same activity
    correlation_request_id = str(uuid.uuid4())

    retry_times = 3
    retry_interval = 1
    for i in range(0, retry_times):
        try:
            retrieved_kv = azconfig_client.get_configuration_setting(
                key=key, label=label,
                headers={HttpHeaders.CORRELATION_REQUEST_ID: correlation_request_id})
        except ResourceNotFoundError:
            raise CLIErrors.ResourceNotFoundError(
                "Feature flag '{}' with label '{}' not found.".format(feature, label))
        except HttpResponseError as exception:
            raise CLIErrors.AzureResponseError(
                "Failed to retrieve feature flags from config store. " + str(exception))

        try:
            if retrieved_kv is None or retrieved_kv.content_type != FeatureFlagConstants.FEATURE_FLAG_CONTENT_TYPE:
                raise CLIErrors.ResourceNotFoundError(
                    "The feature flag {} does not exist.".format(feature))

            # we make sure that value retrieved is a valid json and only has the fields supported by backend.
            # if it's invalid, we catch appropriate exception that contains
            # detailed message
            feature_flag_value = map_keyvalue_to_featureflagvalue(retrieved_kv)
            feature_filters = feature_flag_value.conditions[FeatureFlagConstants.CLIENT_FILTERS]

            entry = json.dumps(new_filter.__dict__,
                               indent=2, ensure_ascii=False)

            current_filter = {}
            match_index = []

            # get all filters where name matches filter_name provided by user
            for idx, feature_filter in enumerate(feature_filters):
                if feature_filter.name == filter_name:
                    if idx == index:
                        current_filter = copy.deepcopy(feature_filters[index])

                        confirmation_message = "Current filter:\n" + \
                            json.dumps(current_filter.__dict__, indent=2, ensure_ascii=False) + \
                            "\nAre you sure you want to update it with this filter?\n" + \
                            entry

                        user_confirmation(confirmation_message, yes)

                        feature_filters[index] = new_filter
                        break

                    match_index.append(idx)

            if not current_filter:
                # If one match was found at a different index from the given one, we ignore it
                if len(match_index) == 1:
                    if index != float("-inf"):
                        logger.warning(
                            "Found filter '%s' at index '%s'. Invalidating provided index '%s'", filter_name, match_index[0], index)

                    current_filter = copy.deepcopy(feature_filters[match_index[0]])

                    confirmation_message = "Current filter:\n" + \
                        json.dumps(current_filter.__dict__, indent=2, ensure_ascii=False) + \
                        "\nAre you sure you want to update it with this filter?\n" + \
                        entry

                    user_confirmation(confirmation_message, yes)

                    feature_filters[match_index[0]] = new_filter

                elif len(match_index) > 1:
                    error_msg = "Feature '{0}' contains multiple instances of filter '{1}'. ".format(feature, filter_name) +\
                                "For resolving this conflict run the command again with the filter name and correct zero-based index of the filter you want to update.\n"
                    raise CLIError(str(error_msg))

                else:
                    raise CLIError(
                        "No filter named '{0}' was found for feature '{1}'".format(filter_name, feature))

            __update_existing_key_value(azconfig_client=azconfig_client,
                                        retrieved_kv=retrieved_kv,
                                        updated_value=json.dumps(feature_flag_value,
                                                                 default=lambda o: {k: v for k, v in o.__dict__.items() if v is not None},
                                                                 ensure_ascii=False),
                                        correlation_request_id=correlation_request_id)

            return new_filter

        except HttpResponseError as exception:
            if exception.status_code == StatusCodes.PRECONDITION_FAILED:
                logger.debug(
                    'Retrying filter update operation %s times with exception: concurrent setting operations', i + 1)
                time.sleep(retry_interval)
            else:
                raise CLIErrors.AzureResponseError(str(exception))
        except Exception as exception:
            raise CLIError(str(exception))
    raise CLIError(
        "Failed to update filter for the feature flag '{}' due to a conflicting operation.".format(feature))


def delete_filter(cmd,
                  feature=None,
                  key=None,
                  filter_name=None,
                  name=None,
                  label=None,
                  index=None,
                  yes=False,
                  connection_string=None,
                  all_=False,
                  auth_mode="key",
                  endpoint=None):
    if key is None and feature is None:
        raise CLIErrors.RequiredArgumentMissingError("Please provide either `--key` or `--feature` value.")
    if key and feature:
        logger.warning("Since both `--key` and `--feature` are provided, `--feature` argument will be ignored.")

    key = FeatureFlagConstants.FEATURE_FLAG_PREFIX + feature if key is None else key
    # Get feature name from key for logging. If users have provided a different feature name, we ignore it anyway.
    feature = key[len(FeatureFlagConstants.FEATURE_FLAG_PREFIX):]

    # generate correlation request id for operations in the same activity
    correlation_request_id = str(uuid.uuid4())

    azconfig_client = get_appconfig_data_client(cmd, name, connection_string, auth_mode, endpoint)

    if index is None:
        index = float("-inf")

    if all_:
        return __clear_filter(azconfig_client, feature, label, yes)

    if filter_name is None:
        raise CLIErrors.RequiredArgumentMissingError("Cannot delete filters because filter name is missing. To delete all filters, run the command again with --all option.")

    retry_times = 3
    retry_interval = 1
    for i in range(0, retry_times):
        try:
            retrieved_kv = azconfig_client.get_configuration_setting(key=key, label=label, headers={HttpHeaders.CORRELATION_REQUEST_ID: correlation_request_id})
        except ResourceNotFoundError:
            raise CLIErrors.ResourceNotFoundError("Feature flag '{}' with label '{}' not found.".format(feature, label))
        except HttpResponseError as exception:
            raise CLIErrors.AzureResponseError("Failed to retrieve feature flags from config store. " + str(exception))

        try:
            if retrieved_kv is None or retrieved_kv.content_type != FeatureFlagConstants.FEATURE_FLAG_CONTENT_TYPE:
                raise CLIErrors.ResourceNotFoundError(
                    "The feature flag {} does not exist.".format(feature))

            # we make sure that value retrieved is a valid json and only has the fields supported by backend.
            # if it's invalid, we catch appropriate exception that contains
            # detailed message
            feature_flag_value = map_keyvalue_to_featureflagvalue(retrieved_kv)
            feature_filters = feature_flag_value.conditions[FeatureFlagConstants.CLIENT_FILTERS]

            display_filter = {}
            match_index = []

            # get all filters where name matches filter_name provided by user
            for idx, feature_filter in enumerate(feature_filters):
                if feature_filter.name == filter_name:
                    if idx == index:
                        # name and index both match this filter - delete it.
                        # create a deep copy of the filter to display to the
                        # user after deletion
                        display_filter = copy.deepcopy(feature_filters[index])

                        confirmation_message = "Are you sure you want to delete this filter?\n" + \
                            json.dumps(display_filter.__dict__, indent=2, ensure_ascii=False)
                        user_confirmation(confirmation_message, yes)

                        del feature_filters[index]
                        break

                    match_index.append(idx)

            if not display_filter:
                # this means we have not deleted the filter yet
                if len(match_index) == 1:
                    if index != float("-inf"):
                        logger.warning("Found filter '%s' at index '%s'. Invalidating provided index '%s'", filter_name, match_index[0], index)

                    display_filter = copy.deepcopy(
                        feature_filters[match_index[0]])

                    confirmation_message = "Are you sure you want to delete this filter?\n" + \
                        json.dumps(display_filter.__dict__, indent=2, ensure_ascii=False)
                    user_confirmation(confirmation_message, yes)

                    del feature_filters[match_index[0]]

                elif len(match_index) > 1:
                    error_msg = "Feature '{0}' contains multiple instances of filter '{1}'. ".format(feature, filter_name) +\
                                "For resolving this conflict run the command again with the filter name and correct zero-based index of the filter you want to delete.\n"
                    raise CLIError(str(error_msg))

                else:
                    raise CLIError(
                        "No filter named '{0}' was found for feature '{1}'".format(filter_name, feature))

            __update_existing_key_value(azconfig_client=azconfig_client,
                                        retrieved_kv=retrieved_kv,
                                        updated_value=json.dumps(feature_flag_value,
                                                                 default=lambda o: {k: v for k, v in o.__dict__.items() if v is not None},
                                                                 ensure_ascii=False),
                                        correlation_request_id=correlation_request_id)

            return display_filter

        except HttpResponseError as exception:
            if exception.status_code == StatusCodes.PRECONDITION_FAILED:
                logger.debug('Retrying deleting feature filter operation %s times with exception: concurrent setting operations', i + 1)
                time.sleep(retry_interval)
            else:
                raise CLIErrors.AzureResponseError(str(exception))
        except Exception as exception:
            raise CLIError(str(exception))
    raise CLIError(
        "Failed to delete filter '{}' for the feature flag '{}' due to a conflicting operation.".format(
            filter_name,
            feature))


def show_filter(cmd,
                filter_name,
                feature=None,
                key=None,
                index=None,
                name=None,
                label=None,
                connection_string=None,
                auth_mode="key",
                endpoint=None):
    if key is None and feature is None:
        raise CLIErrors.RequiredArgumentMissingError("Please provide either `--key` or `--feature` value.")
    if key and feature:
        logger.warning("Since both `--key` and `--feature` are provided, `--feature` argument will be ignored.")

    key = FeatureFlagConstants.FEATURE_FLAG_PREFIX + feature if key is None else key
    # Get feature name from key for logging. If users have provided a different feature name, we ignore it anyway.
    feature = key[len(FeatureFlagConstants.FEATURE_FLAG_PREFIX):]

    azconfig_client = get_appconfig_data_client(cmd, name, connection_string, auth_mode, endpoint)

    if index is None:
        index = float("-inf")

    try:
        retrieved_kv = azconfig_client.get_configuration_setting(key=key, label=label)
    except ResourceNotFoundError:
        raise CLIErrors.ResourceNotFoundError("Feature flag '{}' with label '{}' not found.".format(feature, label))
    except HttpResponseError as exception:
        raise CLIErrors.AzureResponseError("Failed to retrieve feature flags from config store. " + str(exception))

    try:
        if retrieved_kv is None or retrieved_kv.content_type != FeatureFlagConstants.FEATURE_FLAG_CONTENT_TYPE:
            raise CLIErrors.ResourceNotFoundError(
                "The feature flag {} does not exist.".format(feature))

        # we make sure that value retrieved is a valid json and only has the fields supported by backend.
        # if it's invalid, we catch appropriate exception that contains
        # detailed message
        feature_flag_value = map_keyvalue_to_featureflagvalue(retrieved_kv)
        feature_filters = feature_flag_value.conditions[FeatureFlagConstants.CLIENT_FILTERS]
        display_filters = []

        # If user has specified index, we use it as secondary check to display
        # a unique filter
        if 0 <= index < len(feature_filters):
            if feature_filters[index].name == filter_name:
                return feature_filters[index]
        if index != float("-inf"):
            logger.warning(
                "Could not find filter with the index provided. Ignoring index and trying to find the filter by name.")

        # get all filters where name matches filter_name provided by user
        display_filters = [
            featurefilter for featurefilter in feature_filters if featurefilter.name == filter_name]

        if not display_filters:
            raise CLIError(
                "No filter named '{0}' was found for feature '{1}'".format(filter_name, feature))
        return display_filters

    except Exception as exception:
        raise CLIError(str(exception))


def list_filter(cmd,
                feature=None,
                key=None,
                name=None,
                label=None,
                connection_string=None,
                top=None,
                all_=False,
                auth_mode="key",
                endpoint=None):
    if key is None and feature is None:
        raise CLIErrors.RequiredArgumentMissingError("Please provide either `--key` or `--feature` value.")
    if key and feature:
        logger.warning("Since both `--key` and `--feature` are provided, `--feature` argument will be ignored.")

    key = FeatureFlagConstants.FEATURE_FLAG_PREFIX + feature if key is None else key
    # Get feature name from key for logging. If users have provided a different feature name, we ignore it anyway.
    feature = key[len(FeatureFlagConstants.FEATURE_FLAG_PREFIX):]

    azconfig_client = get_appconfig_data_client(cmd, name, connection_string, auth_mode, endpoint)

    try:
        retrieved_kv = azconfig_client.get_configuration_setting(key=key, label=label)
    except ResourceNotFoundError:
        raise CLIErrors.ResourceNotFoundError("Feature flag '{}' with label '{}' not found.".format(feature, label))
    except HttpResponseError as exception:
        raise CLIErrors.AzureResponseError("Failed to retrieve feature flags from config store. " + str(exception))

    try:
        if retrieved_kv is None or retrieved_kv.content_type != FeatureFlagConstants.FEATURE_FLAG_CONTENT_TYPE:
            raise CLIErrors.ResourceNotFoundError(
                "The feature flag {} does not exist.".format(feature))

        # we make sure that value retrieved is a valid json and only has the fields supported by backend.
        # if it's invalid, we catch appropriate exception that contains
        # detailed message
        feature_flag_value = map_keyvalue_to_featureflagvalue(retrieved_kv)
        feature_filters = feature_flag_value.conditions[FeatureFlagConstants.CLIENT_FILTERS]

        if all_:
            top = len(feature_filters)
        elif top is None:
            top = 100

        return feature_filters[:top]

    except Exception as exception:
        raise CLIError(str(exception))


# Helper functions #


def __list_features(
    cmd,
    feature=None,
    key=None,
    name=None,
    label=None,
    tags=None,
    fields=None,
    connection_string=None,
    top=None,
    all_=False,
    auth_mode="key",
    endpoint=None,
    correlation_request_id=None,
):
    if key and feature:
        logger.warning(
            "Since both `--key` and `--feature` are provided, `--feature` argument will be ignored."
        )

    if key is not None:
        key_filter = key
    elif feature is not None:
        key_filter = FeatureFlagConstants.FEATURE_FLAG_PREFIX + feature
    else:
        key_filter = (
            FeatureFlagConstants.FEATURE_FLAG_PREFIX + SearchFilterOptions.ANY_KEY
        )

    azconfig_client = get_appconfig_data_client(
        cmd, name, connection_string, auth_mode, endpoint
    )
    try:
        retrieved_keyvalues = __list_all_keyvalues(
            azconfig_client,
            key_filter=key_filter,
            label=label if label else SearchFilterOptions.ANY_LABEL,
            tags=tags,
            correlation_request_id=correlation_request_id,
        )
        retrieved_featureflags = []

        invalid_ffs = 0
        for kv in retrieved_keyvalues:
            try:
                retrieved_featureflags.append(
                    map_keyvalue_to_featureflag(keyvalue=kv, show_all_details=True)
                )
            except ValueError as exception:
                logger.warning("%s\n", exception)
                invalid_ffs += 1
                continue

        if invalid_ffs > 0:
            logger.warning(
                "Found %s invalid feature flags. These feature flags will be skipped.",
                invalid_ffs,
            )

        filtered_featureflags = []
        count = 0

        if all_:
            top = len(retrieved_featureflags)
        elif top is None:
            top = 100

        for featureflag in retrieved_featureflags:
            if fields:
                partial_featureflags = {}
                for field in fields:
                    # featureflag is guaranteed to have all the fields because
                    # we validate this in map_keyvalue_to_featureflag()
                    # So this line will never throw AttributeError
                    partial_featureflags[field.name.lower()] = getattr(
                        featureflag, field.name.lower()
                    )
                filtered_featureflags.append(partial_featureflags)
            else:
                filtered_featureflags.append(featureflag)
            count += 1
            if count >= top:
                break
        return filtered_featureflags

    except Exception as exception:
        raise CLIError(str(exception))


def __clear_filter(azconfig_client, feature, label=None, yes=False):
    key = FeatureFlagConstants.FEATURE_FLAG_PREFIX + feature

    # generate correlation request id for operations in the same activity
    correlation_request_id = str(uuid.uuid4())

    retry_times = 3
    retry_interval = 1
    for i in range(0, retry_times):
        try:
            retrieved_kv = azconfig_client.get_configuration_setting(
                key=key, label=label,
                headers={HttpHeaders.CORRELATION_REQUEST_ID: correlation_request_id}
            )
        except ResourceNotFoundError:
            raise CLIErrors.ResourceNotFoundError(
                "Feature flag '{}' with label '{}' not found.".format(feature, label)
            )
        except HttpResponseError as exception:
            raise CLIErrors.AzureResponseError(
                "Failed to retrieve feature flags from config store. " + str(exception)
            )

        try:
            if (
                retrieved_kv is None or retrieved_kv.content_type != FeatureFlagConstants.FEATURE_FLAG_CONTENT_TYPE
            ):
                raise CLIErrors.ResourceNotFoundError(
                    "The feature flag {} does not exist.".format(feature)
                )

            # we make sure that value retrieved is a valid json and only has the fields supported by backend.
            # if it's invalid, we catch appropriate exception that contains
            # detailed message
            feature_flag_value = map_keyvalue_to_featureflagvalue(retrieved_kv)

            # These fields will never be missing because we validate that
            # in map_keyvalue_to_featureflagvalue
            feature_filters = feature_flag_value.conditions[FeatureFlagConstants.CLIENT_FILTERS]

            # create a deep copy of the filters to display to the user
            # after deletion
            display_filters = []
            if feature_filters:
                confirmation_message = "Are you sure you want to delete all filters for feature '{0}'?\n".format(
                    feature
                )
                user_confirmation(confirmation_message, yes)

                display_filters = copy.deepcopy(feature_filters)
                # clearing feature_filters list for python 2.7 compatibility
                del feature_filters[:]

                __update_existing_key_value(
                    azconfig_client=azconfig_client,
                    retrieved_kv=retrieved_kv,
                    updated_value=json.dumps(
                        feature_flag_value,
                        default=lambda o: {k: v for k, v in o.__dict__.items() if v is not None},
                        ensure_ascii=False,
                    ),
                )

            return display_filters

        except HttpResponseError as exception:
            if exception.status_code == StatusCodes.PRECONDITION_FAILED:
                logger.debug(
                    "Retrying feature enable operation %s times with exception: concurrent setting operations",
                    i + 1,
                )
                time.sleep(retry_interval)
            else:
                raise CLIErrors.AzureResponseError(str(exception))
        except Exception as exception:
            raise CLIError(str(exception))
    raise CLIError(
        "Failed to delete filters for the feature flag '{}' due to a conflicting operation.".format(
            feature
        )
    )


def __update_existing_key_value(azconfig_client,
                                retrieved_kv,
                                updated_value,
                                correlation_request_id=None):
    '''
        To update the value of a pre-existing KeyValue

        Args:
            azconfig_client - AppConfig client making calls to the service
            retrieved_kv - Pre-existing ConfigurationSetting object
            updated_value - Value string to be updated

        Return:
            KeyValue object
    '''
    set_kv = ConfigurationSetting(key=retrieved_kv.key,
                                  value=updated_value,
                                  label=retrieved_kv.label,
                                  tags=retrieved_kv.tags,
                                  content_type=FeatureFlagConstants.FEATURE_FLAG_CONTENT_TYPE,
                                  read_only=retrieved_kv.read_only,
                                  etag=retrieved_kv.etag,
                                  last_modified=retrieved_kv.last_modified)

    try:
        new_kv = azconfig_client.set_configuration_setting(set_kv, match_condition=MatchConditions.IfNotModified, headers={HttpHeaders.CORRELATION_REQUEST_ID: correlation_request_id})
        return convert_configurationsetting_to_keyvalue(new_kv)
    except ResourceReadOnlyError:
        raise CLIError("Failed to update read only feature flag. Unlock the feature flag before updating it.")
    # We don't catch HttpResponseError here because some calling functions want to retry on transient exceptions


def __list_all_keyvalues(azconfig_client,
                         key_filter,
                         label=None,
                         tags=None,
                         correlation_request_id=None):
    '''
        To get all keys by name or pattern

        Args:
            azconfig_client - AppConfig client making calls to the service
            key_filter - Filter for the key of the feature flag
            label - Feature label or pattern
            tags - Tags to filter the feature flags

        Return:
            List of KeyValue objects
    '''

    # We dont support listing comma separated keys and ned to fail with appropriate error
    # (?<!\\)    Matches if the preceding character is not a backslash
    # (?:\\\\)*  Matches any number of occurrences of two backslashes
    # ,          Matches a comma
    unescaped_comma_regex = re.compile(r'(?<!\\)(?:\\\\)*,')
    if unescaped_comma_regex.search(key_filter):
        raise CLIError("Comma separated feature names are not supported. Please provide escaped string if your feature name contains comma. \nSee \"az appconfig feature list -h\" for correct usage.")

    label = prep_filter_for_url_encoding(label)
    prepped_tags = [prep_filter_for_url_encoding(tag) for tag in tags] if tags else []

    try:
        configsetting_iterable = azconfig_client.list_configuration_settings(key_filter=key_filter, label_filter=label, tags_filter=prepped_tags, headers={HttpHeaders.CORRELATION_REQUEST_ID: correlation_request_id})
    except HttpResponseError as exception:
        raise CLIErrors.AzureResponseError('Failed to read feature flag(s) that match the specified feature and label. ' + str(exception))

    try:
        retrieved_kv = [convert_configurationsetting_to_keyvalue(x) for x in configsetting_iterable]
        valid_features = []
        for kv in retrieved_kv:
            if kv.content_type == FeatureFlagConstants.FEATURE_FLAG_CONTENT_TYPE:
                valid_features.append(kv)
        return valid_features
    except Exception as exception:
        raise CLIError(str(exception))
