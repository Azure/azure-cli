# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

import json
import time
import re
import copy

from knack.log import get_logger
from knack.util import CLIError

from ._constants import FeatureFlagConstants
from ._utils import resolve_connection_string, user_confirmation
from ._azconfig.azconfig_client import AzconfigClient
from ._azconfig.constants import StatusCodes
from ._azconfig.exceptions import HTTPException
from ._azconfig.models import (KeyValue,
                               ModifyKeyValueOptions,
                               QueryKeyValueCollectionOptions,
                               QueryKeyValueOptions)
from ._featuremodels import (map_keyvalue_to_featureflag,
                             map_keyvalue_to_featureflagvalue,
                             FeatureFilter)


logger = get_logger(__name__)

# Feature commands #


def set_feature(cmd,
                feature,
                name=None,
                label=None,
                description=None,
                yes=False,
                connection_string=None):
    key = FeatureFlagConstants.FEATURE_FLAG_PREFIX + feature

    # when creating a new Feature flag, these defaults will be used
    tags = {}
    default_conditions = {'client_filters': []}

    default_value = {
        "id": feature,
        "description": description,
        "enabled": False,
        "conditions": default_conditions
    }

    connection_string = resolve_connection_string(cmd, name, connection_string)
    azconfig_client = AzconfigClient(connection_string)
    retry_times = 3
    retry_interval = 1

    label = label if label and label != ModifyKeyValueOptions.empty_label else None
    query_options = QueryKeyValueOptions(label=label)

    for i in range(0, retry_times):
        try:
            retrieved_kv = azconfig_client.get_keyvalue(key, query_options)
        except HTTPException as exception:
            raise CLIError(str(exception))

        try:
            # if kv exists and only content-type is wrong, we can force correct it by updating the kv
            if retrieved_kv is None:
                set_kv = KeyValue(
                    key,
                    json.dumps(default_value, ensure_ascii=False),
                    label,
                    tags,
                    FeatureFlagConstants.FEATURE_FLAG_CONTENT_TYPE)
            else:
                if retrieved_kv.content_type != FeatureFlagConstants.FEATURE_FLAG_CONTENT_TYPE:
                    logger.warning(
                        "This feature contains invalid content-type. The feature flag will be overwritten.")
                # we make sure that value retrieved is a valid json and only has the fields supported by backend.
                # if it's invalid, we catch appropriate exception that contains
                # detailed message
                feature_flag_value = map_keyvalue_to_featureflagvalue(
                    retrieved_kv)

                # User can only update description if the key already exists
                feature_flag_value.description = description
                set_kv = KeyValue(
                    key=key,
                    label=label,
                    value=json.dumps(
                        feature_flag_value,
                        default=lambda o: o.__dict__,
                        ensure_ascii=False),
                    content_type=FeatureFlagConstants.FEATURE_FLAG_CONTENT_TYPE,
                    tags=retrieved_kv.tags if retrieved_kv.tags else tags)
                set_kv.etag = retrieved_kv.etag
                set_kv.last_modified = retrieved_kv.last_modified

            # Convert KeyValue object to required FeatureFlag format for
            # display
            feature_flag = map_keyvalue_to_featureflag(
                set_kv, show_conditions=True)
            entry = json.dumps(feature_flag, default=lambda o: o.__dict__, indent=2, sort_keys=True, ensure_ascii=False)

        except Exception as exception:
            # Exceptions for ValueError and AttributeError already have customized message
            # No need to catch specific exception here and customize
            raise CLIError(str(exception))

        confirmation_message = "Are you sure you want to set the feature flag: \n" + entry + "\n"
        user_confirmation(confirmation_message, yes)

        try:
            updated_key_value = azconfig_client.add_keyvalue(
                set_kv,
                ModifyKeyValueOptions()) if set_kv.etag is None else azconfig_client.update_keyvalue(
                    set_kv,
                    ModifyKeyValueOptions())
            return map_keyvalue_to_featureflag(
                keyvalue=updated_key_value, show_conditions=True)
        except HTTPException as exception:
            if exception.status == StatusCodes.PRECONDITION_FAILED:
                logger.debug(
                    'Retrying setting %s times with exception: concurrent setting operations',
                    i + 1)
                time.sleep(retry_interval)
            else:
                raise CLIError(str(exception))
        except Exception as exception:
            raise CLIError(str(exception))
    raise CLIError(
        "Failed to set the feature flag '{}' due to a conflicting operation.".format(feature))


def delete_feature(cmd,
                   feature,
                   name=None,
                   label=None,
                   yes=False,
                   connection_string=None):
    connection_string = resolve_connection_string(cmd, name, connection_string)
    azconfig_client = AzconfigClient(connection_string)

    delete_one_version_message = "Are you sure you want to delete the feature '{}'".format(
        feature)
    confirmation_message = delete_one_version_message
    user_confirmation(confirmation_message, yes)

    try:
        retrieved_keyvalues = __list_all_keyvalues(azconfig_client,
                                                   feature=feature,
                                                   label=QueryKeyValueCollectionOptions.empty_label if label is None else label)
    except HTTPException as exception:
        raise CLIError('Delete operation failed. ' + str(exception))

    deleted_kv = []
    not_deleted_kv = []
    http_exception = None
    for entry in retrieved_keyvalues:
        try:
            deleted_kv.append(
                azconfig_client.delete_keyvalue(
                    entry, ModifyKeyValueOptions()))
        except HTTPException as exception:
            not_deleted_kv.append(entry)
            http_exception = exception
        except Exception as exception:
            raise CLIError(str(exception))

    if not_deleted_kv:
        if deleted_kv:
            # Log partial success - display feature flags that failed to be
            # deleted
            logger.error(
                'Delete operation partially succeeded. Unable to delete the following keys: \n')
            not_deleted_ff = []
            for failed_kv in not_deleted_kv:
                failed_ff = map_keyvalue_to_featureflag(
                    failed_kv, show_conditions=False)
                not_deleted_ff.append(failed_ff)
                logger.error(
                    json.dumps(
                        failed_ff,
                        default=lambda o: o.__dict__,
                        indent=2,
                        sort_keys=True,
                        ensure_ascii=False))
        else:
            raise CLIError('Delete operation failed.' + str(http_exception))

    # Convert result list of KeyValue to ist of FeatureFlag
    deleted_ff = []
    for success_kv in deleted_kv:
        success_ff = map_keyvalue_to_featureflag(
            success_kv, show_conditions=False)
        deleted_ff.append(success_ff)

    return deleted_ff


def show_feature(cmd,
                 feature,
                 name=None,
                 label=None,
                 fields=None,
                 connection_string=None):
    key = FeatureFlagConstants.FEATURE_FLAG_PREFIX + feature
    connection_string = resolve_connection_string(cmd, name, connection_string)
    azconfig_client = AzconfigClient(connection_string)

    try:
        query_options = QueryKeyValueOptions(label=label)
        retrieved_kv = azconfig_client.get_keyvalue(key, query_options)

        if retrieved_kv is None or retrieved_kv.content_type != FeatureFlagConstants.FEATURE_FLAG_CONTENT_TYPE:
            raise CLIError(
                "The feature flag '{}' does not exist.".format(feature))

        feature_flag = map_keyvalue_to_featureflag(
            keyvalue=retrieved_kv, show_conditions=True)

        # If user has specified fields, we still get all the fields and then
        # filter what we need from the response.
        if fields:
            partial_featureflag = {}
            for field in fields:
                # feature_flag is guaranteed to have all the fields because
                # we validate this in map_keyvalue_to_featureflag()
                # So this line will never throw AttributeError
                partial_featureflag[field.name.lower()] = getattr(
                    feature_flag, field.name.lower())
            return partial_featureflag
        return feature_flag

    except Exception as exception:
        raise CLIError(str(exception))


def list_feature(cmd,
                 feature=None,
                 name=None,
                 label=None,
                 fields=None,
                 connection_string=None,
                 top=None,
                 all_=False):
    connection_string = resolve_connection_string(cmd, name, connection_string)
    azconfig_client = AzconfigClient(connection_string)

    try:
        feature = '*' if feature is None else feature
        retrieved_keyvalues = __list_all_keyvalues(azconfig_client,
                                                   feature=feature,
                                                   label=label)
        retrieved_featureflags = []
        for kv in retrieved_keyvalues:
            retrieved_featureflags.append(
                map_keyvalue_to_featureflag(
                    keyvalue=kv, show_conditions=True))
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
                        featureflag, field.name.lower())
                filtered_featureflags.append(partial_featureflags)
            else:
                filtered_featureflags.append(featureflag)
            count += 1
            if count >= top:
                break
        return filtered_featureflags

    except Exception as exception:
        raise CLIError(str(exception))


def lock_feature(cmd,
                 feature,
                 name=None,
                 label=None,
                 connection_string=None,
                 yes=False):
    key = FeatureFlagConstants.FEATURE_FLAG_PREFIX + feature
    connection_string = resolve_connection_string(cmd, name, connection_string)
    azconfig_client = AzconfigClient(connection_string)

    retry_times = 3
    retry_interval = 1
    for i in range(0, retry_times):
        try:
            retrieved_kv = azconfig_client.get_keyvalue(key, QueryKeyValueOptions(label))
        except HTTPException as exception:
            raise CLIError(str(exception))

        if retrieved_kv is None or retrieved_kv.content_type != FeatureFlagConstants.FEATURE_FLAG_CONTENT_TYPE:
            raise CLIError(
                "The feature '{}' you are trying to lock does not exist.".format(feature))

        confirmation_message = "Are you sure you want to lock the feature '{}'".format(feature)
        user_confirmation(confirmation_message, yes)

        try:
            updated_key_value = azconfig_client.lock_keyvalue(
                retrieved_kv, ModifyKeyValueOptions())
            return map_keyvalue_to_featureflag(
                updated_key_value, show_conditions=False)

        except HTTPException as exception:
            if exception.status == StatusCodes.PRECONDITION_FAILED:
                logger.debug(
                    'Retrying locking %s times with exception: concurrent setting operations',
                    i + 1)
                time.sleep(retry_interval)
            else:
                raise CLIError(str(exception))
        except Exception as exception:
            raise CLIError(str(exception))
    raise CLIError(
        "Failed to lock the feature '{}' due to a conflicting operation.".format(feature))


def unlock_feature(cmd,
                   feature,
                   name=None,
                   label=None,
                   connection_string=None,
                   yes=False):
    key = FeatureFlagConstants.FEATURE_FLAG_PREFIX + feature
    connection_string = resolve_connection_string(cmd, name, connection_string)
    azconfig_client = AzconfigClient(connection_string)

    retry_times = 3
    retry_interval = 1
    for i in range(0, retry_times):
        try:
            retrieved_kv = azconfig_client.get_keyvalue(key, QueryKeyValueOptions(label))
        except HTTPException as exception:
            raise CLIError(str(exception))

        if retrieved_kv is None or retrieved_kv.content_type != FeatureFlagConstants.FEATURE_FLAG_CONTENT_TYPE:
            raise CLIError(
                "The feature '{}' you are trying to unlock does not exist.".format(feature))

        confirmation_message = "Are you sure you want to unlock the feature '{}'".format(feature)
        user_confirmation(confirmation_message, yes)

        try:
            updated_key_value = azconfig_client.unlock_keyvalue(
                retrieved_kv, ModifyKeyValueOptions())
            return map_keyvalue_to_featureflag(
                updated_key_value, show_conditions=False)

        except HTTPException as exception:
            if exception.status == StatusCodes.PRECONDITION_FAILED:
                logger.debug(
                    'Retrying unlocking %s times with exception: concurrent setting operations',
                    i + 1)
                time.sleep(retry_interval)
            else:
                raise CLIError(str(exception))
        except Exception as exception:
            raise CLIError(str(exception))
    raise CLIError(
        "Failed to unlock the feature '{}' due to a conflicting operation.".format(feature))


def enable_feature(cmd,
                   feature,
                   name=None,
                   label=None,
                   connection_string=None,
                   yes=False):
    key = FeatureFlagConstants.FEATURE_FLAG_PREFIX + feature
    connection_string = resolve_connection_string(cmd, name, connection_string)
    azconfig_client = AzconfigClient(connection_string)

    retry_times = 3
    retry_interval = 1
    for i in range(0, retry_times):
        try:
            query_options = QueryKeyValueOptions(label=label)
            retrieved_kv = azconfig_client.get_keyvalue(key, query_options)

            if retrieved_kv is None or retrieved_kv.content_type != FeatureFlagConstants.FEATURE_FLAG_CONTENT_TYPE:
                raise CLIError(
                    "The feature flag {} does not exist.".format(feature))

            # we make sure that value retrieved is a valid json and only has the fields supported by backend.
            # if it's invalid, we catch appropriate exception that contains
            # detailed message
            feature_flag_value = map_keyvalue_to_featureflagvalue(retrieved_kv)

            feature_flag_value.enabled = True
            confirmation_message = "Are you sure you want to enable this feature '{}'?".format(
                feature)
            user_confirmation(confirmation_message, yes)

            updated_key_value = __update_existing_key_value(azconfig_client=azconfig_client,
                                                            retrieved_kv=retrieved_kv,
                                                            updated_value=json.dumps(feature_flag_value,
                                                                                     default=lambda o: o.__dict__,
                                                                                     ensure_ascii=False))

            return map_keyvalue_to_featureflag(
                keyvalue=updated_key_value, show_conditions=False)

        except HTTPException as exception:
            if exception.status == StatusCodes.PRECONDITION_FAILED:
                logger.debug(
                    'Retrying enabling %s times with exception: concurrent setting operations',
                    i + 1)
                time.sleep(retry_interval)
            else:
                raise CLIError(str(exception))

        except Exception as exception:
            raise CLIError(str(exception))
    raise CLIError(
        "Failed to enable the feature flag '{}' due to a conflicting operation.".format(feature))


def disable_feature(cmd,
                    feature,
                    name=None,
                    label=None,
                    connection_string=None,
                    yes=False):
    key = FeatureFlagConstants.FEATURE_FLAG_PREFIX + feature
    connection_string = resolve_connection_string(cmd, name, connection_string)
    azconfig_client = AzconfigClient(connection_string)

    retry_times = 3
    retry_interval = 1
    for i in range(0, retry_times):
        try:
            query_options = QueryKeyValueOptions(label=label)
            retrieved_kv = azconfig_client.get_keyvalue(key, query_options)

            if retrieved_kv is None or retrieved_kv.content_type != FeatureFlagConstants.FEATURE_FLAG_CONTENT_TYPE:
                raise CLIError(
                    "The feature flag {} does not exist.".format(feature))

            # we make sure that value retrieved is a valid json and only has the fields supported by backend.
            # if it's invalid, we catch appropriate exception that contains
            # detailed message
            feature_flag_value = map_keyvalue_to_featureflagvalue(retrieved_kv)

            feature_flag_value.enabled = False
            confirmation_message = "Are you sure you want to disable this feature '{}'?".format(
                feature)
            user_confirmation(confirmation_message, yes)

            updated_key_value = __update_existing_key_value(azconfig_client=azconfig_client,
                                                            retrieved_kv=retrieved_kv,
                                                            updated_value=json.dumps(feature_flag_value,
                                                                                     default=lambda o: o.__dict__,
                                                                                     ensure_ascii=False))

            return map_keyvalue_to_featureflag(
                keyvalue=updated_key_value, show_conditions=False)

        except HTTPException as exception:
            if exception.status == StatusCodes.PRECONDITION_FAILED:
                logger.debug(
                    'Retrying disabling %s times with exception: concurrent setting operations',
                    i + 1)
                time.sleep(retry_interval)
            else:
                raise CLIError(str(exception))

        except Exception as exception:
            raise CLIError(str(exception))
    raise CLIError(
        "Failed to disable the feature flag '{}' due to a conflicting operation.".format(feature))


# Feature Flter commands #


def add_filter(cmd,
               feature,
               filter_name,
               name=None,
               label=None,
               filter_parameters=None,
               yes=False,
               index=None,
               connection_string=None):
    key = FeatureFlagConstants.FEATURE_FLAG_PREFIX + feature
    connection_string = resolve_connection_string(cmd, name, connection_string)
    azconfig_client = AzconfigClient(connection_string)

    if index is None:
        index = float("-inf")

    # Construct feature filter to be added
    if filter_parameters is None:
        filter_parameters = {}
    new_filter = FeatureFilter(filter_name, filter_parameters)

    retry_times = 3
    retry_interval = 1
    for i in range(0, retry_times):
        try:
            query_options = QueryKeyValueOptions(label=label)
            retrieved_kv = azconfig_client.get_keyvalue(key, query_options)

            if retrieved_kv is None or retrieved_kv.content_type != FeatureFlagConstants.FEATURE_FLAG_CONTENT_TYPE:
                raise CLIError(
                    "The feature flag {} does not exist.".format(feature))

            # we make sure that value retrieved is a valid json and only has the fields supported by backend.
            # if it's invalid, we catch appropriate exception that contains
            # detailed message
            feature_flag_value = map_keyvalue_to_featureflagvalue(retrieved_kv)
            feature_filters = feature_flag_value.conditions['client_filters']

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
                                                                 default=lambda o: o.__dict__,
                                                                 ensure_ascii=False))

            return new_filter

        except HTTPException as exception:
            if exception.status == StatusCodes.PRECONDITION_FAILED:
                logger.debug(
                    'Retrying adding filter %s times with exception: concurrent setting operations',
                    i + 1)
                time.sleep(retry_interval)
            else:
                raise CLIError(str(exception))

        except Exception as exception:
            raise CLIError(str(exception))
    raise CLIError(
        "Failed to add filter for the feature flag '{}' due to a conflicting operation.".format(feature))


def delete_filter(cmd,
                  feature,
                  filter_name=None,
                  name=None,
                  label=None,
                  index=None,
                  yes=False,
                  connection_string=None,
                  all_=False):
    key = FeatureFlagConstants.FEATURE_FLAG_PREFIX + feature
    azconfig_client = AzconfigClient(resolve_connection_string(cmd, name, connection_string))

    if index is None:
        index = float("-inf")

    if all_:
        return __clear_filter(azconfig_client, feature, label, yes)

    if filter_name is None:
        raise CLIError("Cannot delete filters because filter name is missing. To delete all filters, run the command again with --all option.")

    retry_times = 3
    retry_interval = 1
    for i in range(0, retry_times):
        try:
            retrieved_kv = azconfig_client.get_keyvalue(
                key, QueryKeyValueOptions(label=label))

            if retrieved_kv is None or retrieved_kv.content_type != FeatureFlagConstants.FEATURE_FLAG_CONTENT_TYPE:
                raise CLIError(
                    "The feature flag {} does not exist.".format(feature))

            # we make sure that value retrieved is a valid json and only has the fields supported by backend.
            # if it's invalid, we catch appropriate exception that contains
            # detailed message
            feature_flag_value = map_keyvalue_to_featureflagvalue(retrieved_kv)
            feature_filters = feature_flag_value.conditions['client_filters']

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
                                                                 default=lambda o: o.__dict__,
                                                                 ensure_ascii=False))

            return display_filter

        except HTTPException as exception:
            if exception.status == StatusCodes.PRECONDITION_FAILED:
                logger.debug(
                    'Retrying deleting filter %s times with exception: concurrent setting operations',
                    i + 1)
                time.sleep(retry_interval)
            else:
                raise CLIError(str(exception))

        except Exception as exception:
            raise CLIError(str(exception))
    raise CLIError(
        "Failed to delete filter '{}' for the feature flag '{}' due to a conflicting operation.".format(
            filter_name,
            feature))


def show_filter(cmd,
                feature,
                filter_name,
                index=None,
                name=None,
                label=None,
                connection_string=None):
    key = FeatureFlagConstants.FEATURE_FLAG_PREFIX + feature
    connection_string = resolve_connection_string(cmd, name, connection_string)
    azconfig_client = AzconfigClient(connection_string)

    if index is None:
        index = float("-inf")

    try:
        query_options = QueryKeyValueOptions(label=label)
        retrieved_kv = azconfig_client.get_keyvalue(key, query_options)

        if retrieved_kv is None or retrieved_kv.content_type != FeatureFlagConstants.FEATURE_FLAG_CONTENT_TYPE:
            raise CLIError(
                "The feature flag {} does not exist.".format(feature))

        # we make sure that value retrieved is a valid json and only has the fields supported by backend.
        # if it's invalid, we catch appropriate exception that contains
        # detailed message
        feature_flag_value = map_keyvalue_to_featureflagvalue(retrieved_kv)
        feature_filters = feature_flag_value.conditions['client_filters']

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
                feature,
                name=None,
                label=None,
                connection_string=None,
                top=None,
                all_=False):
    key = FeatureFlagConstants.FEATURE_FLAG_PREFIX + feature
    connection_string = resolve_connection_string(cmd, name, connection_string)
    azconfig_client = AzconfigClient(connection_string)

    try:
        query_options = QueryKeyValueOptions(label=label)
        retrieved_kv = azconfig_client.get_keyvalue(key, query_options)

        if retrieved_kv is None or retrieved_kv.content_type != FeatureFlagConstants.FEATURE_FLAG_CONTENT_TYPE:
            raise CLIError(
                "The feature flag {} does not exist.".format(feature))

        # we make sure that value retrieved is a valid json and only has the fields supported by backend.
        # if it's invalid, we catch appropriate exception that contains
        # detailed message
        feature_flag_value = map_keyvalue_to_featureflagvalue(retrieved_kv)
        feature_filters = feature_flag_value.conditions['client_filters']

        if all_:
            top = len(feature_filters)
        elif top is None:
            top = 100

        return feature_filters[:top]

    except Exception as exception:
        raise CLIError(str(exception))


# Helper functions #


def __clear_filter(azconfig_client,
                   feature,
                   label=None,
                   yes=False):
    key = FeatureFlagConstants.FEATURE_FLAG_PREFIX + feature

    retry_times = 3
    retry_interval = 1
    for i in range(0, retry_times):
        try:
            query_options = QueryKeyValueOptions(label=label)
            retrieved_kv = azconfig_client.get_keyvalue(key, query_options)

            if retrieved_kv is None or retrieved_kv.content_type != FeatureFlagConstants.FEATURE_FLAG_CONTENT_TYPE:
                raise CLIError(
                    "The feature flag {} does not exist.".format(feature))

            # we make sure that value retrieved is a valid json and only has the fields supported by backend.
            # if it's invalid, we catch appropriate exception that contains
            # detailed message
            feature_flag_value = map_keyvalue_to_featureflagvalue(retrieved_kv)

            # These fields will never be missing because we validate that
            # in map_keyvalue_to_featureflagvalue
            feature_filters = feature_flag_value.conditions['client_filters']

            # create a deep copy of the filters to display to the user
            # after deletion
            display_filters = []
            if feature_filters:
                confirmation_message = "Are you sure you want to delete all filters for feature '{0}'?\n".format(feature)
                user_confirmation(confirmation_message, yes)

                display_filters = copy.deepcopy(feature_filters)
                # clearing feature_filters list for python 2.7 compatibility
                del feature_filters[:]

                __update_existing_key_value(azconfig_client=azconfig_client,
                                            retrieved_kv=retrieved_kv,
                                            updated_value=json.dumps(feature_flag_value,
                                                                     default=lambda o: o.__dict__,
                                                                     ensure_ascii=False))

            return display_filters

        except HTTPException as exception:
            if exception.status == StatusCodes.PRECONDITION_FAILED:
                logger.debug(
                    'Retrying deleting filters %s times with exception: concurrent setting operations',
                    i + 1)
                time.sleep(retry_interval)
            else:
                raise CLIError(str(exception))

        except Exception as exception:
            raise CLIError(str(exception))
    raise CLIError(
        "Failed to delete filters for the feature flag '{}' due to a conflicting operation.".format(feature))


def __update_existing_key_value(azconfig_client,
                                retrieved_kv,
                                updated_value):
    '''
        To update the value of a pre-existing KeyValue

        Args:
            azconfig_client - AppConfig client making calls to the service
            retrieved_kv - Pre-existing KeyValue object
            updated_value - Value string to be updated

        Return:
            KeyValue object
    '''
    set_kv = KeyValue(key=retrieved_kv.key,
                      value=updated_value,
                      label=retrieved_kv.label,
                      tags=retrieved_kv.tags,
                      content_type=FeatureFlagConstants.FEATURE_FLAG_CONTENT_TYPE)
    set_kv.etag = retrieved_kv.etag
    set_kv.last_modified = retrieved_kv.last_modified

    try:
        return azconfig_client.update_keyvalue(set_kv, ModifyKeyValueOptions())

    except Exception as exception:
        raise CLIError(str(exception))


def __list_all_keyvalues(azconfig_client,
                         feature,
                         label=None):
    '''
        To get all keys by name or pattern

        Args:
            azconfig_client - AppConfig client making calls to the service
            feature - Feature name or pattern
            label - Feature label or pattern

        Return:
            List of KeyValue objects
    '''

    # We dont support listing comma separated keys and ned to fail with appropriate error
    # (?<!\\)    Matches if the preceding character is not a backslash
    # (?:\\\\)*  Matches any number of occurrences of two backslashes
    # ,          Matches a comma
    unescaped_comma_regex = re.compile(r'(?<!\\)(?:\\\\)*,')
    if unescaped_comma_regex.search(feature):
        raise CLIError("Comma separated feature names are not supported. Please provide escaped string if your feature name contains comma. \nSee \"az appconfig feature list -h\" for correct usage.")

    # Filtering keys on these patterns needs to happen on client side after getting all keys that match user specified pattern
    # If user provides *abc or *abc* or * -> get all keys that match this
    # pattern, then filter based on whether they are feature flags or not
    all_keys_pattern = "*"
    if feature.startswith("*") and feature != all_keys_pattern:
        key = feature
    else:
        key = FeatureFlagConstants.FEATURE_FLAG_PREFIX + feature

    # If user has specified fields, we still get all the fields and then
    # filter what we need from the response.
    query_option = QueryKeyValueCollectionOptions(
        key_filter=key,
        label_filter=QueryKeyValueCollectionOptions.empty_label if label is not None and not label else label,
        fields=None)
    try:
        retrieved_kv = azconfig_client.get_keyvalues(query_option)
        if key != feature:
            valid_features = []
            for kv in retrieved_kv:
                if kv.content_type == FeatureFlagConstants.FEATURE_FLAG_CONTENT_TYPE:
                    valid_features.append(kv)
            return valid_features

        return __custom_key_filtering(retrieved_kv=retrieved_kv, user_key_filter=feature)

    except Exception as exception:
        raise CLIError(str(exception))


def __custom_key_filtering(retrieved_kv, user_key_filter):
    '''
        To get all keys after Client side Filtering based on user specified pattern

        Args:
            retrieved_kv - List of KeyValue objects
            user_key_filter - key pattern to be matched

        Return:
            List of KeyValue objects
    '''

    filtered_kv = []
    try:
        user_key_pattern_regex = re.compile(r"." + user_key_filter)
        for kv in retrieved_kv:
            internal_key = kv.key
            internal_content_type = kv.content_type
            # filter only feature flags
            if internal_key.startswith(
                    FeatureFlagConstants.FEATURE_FLAG_PREFIX) and internal_content_type == FeatureFlagConstants.FEATURE_FLAG_CONTENT_TYPE:
                feature_name = internal_key[len(FeatureFlagConstants.FEATURE_FLAG_PREFIX):]
                # search for user pattern in actual feature name
                if user_key_pattern_regex.search(feature_name):
                    filtered_kv.append(kv)
        return filtered_kv

    except re.error as exception:
        error_msg = "Regular expression error in parsing '{0}'. ".format(user_key_filter) +\
            "Please provide escaped string if your feature name contains special characters. \nSee \"az appconfig feature list -h\" for correct usage.\n"
        raise re.error(error_msg + "Error: " + str(exception))

    except AttributeError as exception:
        raise AttributeError(
            "Could not find 'content_type' attribute in the retrieved key-value data.\n" +
            str(exception))

    return filtered_kv
