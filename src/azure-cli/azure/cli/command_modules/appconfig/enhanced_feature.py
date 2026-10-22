# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

import json

from knack.log import get_logger
from azure.appconfiguration import (FeatureFlag,
                                    FeatureFlagConditions,
                                    FeatureFlagTelemetryConfiguration)
from azure.core import MatchConditions
from azure.core.exceptions import HttpResponseError, ResourceNotFoundError, ResourceModifiedError
from azure.cli.core.util import user_confirmation
import azure.cli.core.azclierror as CLIErrors

from ._constants import FeatureFlagConstants, SearchFilterOptions
from ._utils import get_appconfig_feature_flag_client

logger = get_logger(__name__)

# Enhanced feature flag commands #


def set_feature(cmd,
                feature_name=None,
                name=None,
                label=None,
                description=None,
                requirement_type=None,
                telemetry_enabled=None,
                tags=None,
                flag=None,
                yes=False,
                connection_string=None,
                auth_mode="key",
                endpoint=None):
    feature_flag_client = get_appconfig_feature_flag_client(cmd, name, connection_string, auth_mode, endpoint)

    if flag is not None:
        # --flag mirrors the data-plane /ff schema (also emitted by 'show'), so deserialize it with the SDK.
        flag_to_load = {k: v for k, v in flag.items()
                        if k not in (FeatureFlagConstants.LAST_MODIFIED, "etag")}
        if feature_name is not None:
            flag_to_load[FeatureFlagConstants.NAME] = feature_name
        feature_flag = FeatureFlag.from_dict(flag_to_load)
        if label is not None:
            feature_flag.label = label
        if tags is not None:
            feature_flag.tags = tags
    else:
        try:
            feature_flag = feature_flag_client.get_feature_flag(name=feature_name, label=label)
        except ResourceNotFoundError:
            feature_flag = None
        except HttpResponseError as exception:
            raise CLIErrors.AzureResponseError("Failed to retrieve enhanced feature flag from config store. " + str(exception))

        if feature_flag is None:
            feature_flag = FeatureFlag(name=feature_name, enabled=False, label=label)

        if description is not None:
            feature_flag.description = description

        if requirement_type is not None:
            if feature_flag.conditions is None:
                feature_flag.conditions = FeatureFlagConditions()
            feature_flag.conditions.requirement_type = requirement_type

        if telemetry_enabled is not None:
            if feature_flag.telemetry is None:
                feature_flag.telemetry = FeatureFlagTelemetryConfiguration(enabled=telemetry_enabled)
            else:
                feature_flag.telemetry.enabled = telemetry_enabled

        if tags is not None:
            feature_flag.tags = tags

    entry = json.dumps(_serialize_feature_flag(feature_flag), indent=2, sort_keys=True, ensure_ascii=False, default=str)
    confirmation_message = "Are you sure you want to set the enhanced feature flag: \n" + entry + "\n"
    user_confirmation(confirmation_message, yes)

    try:
        updated_feature_flag = feature_flag_client.set_feature_flag(feature_flag)
    except HttpResponseError as exception:
        raise CLIErrors.AzureResponseError(str(exception))

    return _serialize_feature_flag(updated_feature_flag)


def show_feature(cmd,
                 feature_name,
                 name=None,
                 label=None,
                 fields=None,
                 connection_string=None,
                 auth_mode="key",
                 endpoint=None):
    feature_flag_client = get_appconfig_feature_flag_client(cmd, name, connection_string, auth_mode, endpoint)

    try:
        feature_flag = feature_flag_client.get_feature_flag(name=feature_name, label=label)
    except ResourceNotFoundError:
        feature_flag = None
    except HttpResponseError as exception:
        raise CLIErrors.AzureResponseError(str(exception))

    if feature_flag is None:
        raise CLIErrors.ResourceNotFoundError("Enhanced feature flag '{}' with label '{}' does not exist.".format(feature_name, label))

    return _serialize_feature_flag(feature_flag, fields)


def list_feature(cmd,
                 feature_name=None,
                 name=None,
                 label=None,
                 fields=None,
                 all_=False,
                 top=None,
                 tags=None,
                 connection_string=None,
                 auth_mode="key",
                 endpoint=None):
    feature_flag_client = get_appconfig_feature_flag_client(cmd, name, connection_string, auth_mode, endpoint)

    try:
        feature_flags = feature_flag_client.list_feature_flags(name_filter=feature_name,
                                                               label_filter=label,
                                                               tags_filter=tags)
    except HttpResponseError as exception:
        raise CLIErrors.AzureResponseError("Failed to read enhanced feature flag(s) that match the specified feature and label. " + str(exception))

    result = []
    count = 0
    for feature_flag in feature_flags:
        result.append(_serialize_feature_flag(feature_flag, fields))
        count += 1
        if not all_ and count >= (top if top is not None else 100):
            break

    return result


def delete_feature(cmd,
                   feature_name=None,
                   name=None,
                   label=None,
                   tags=None,
                   yes=False,
                   connection_string=None,
                   auth_mode="key",
                   endpoint=None):
    feature_flag_client = get_appconfig_feature_flag_client(cmd, name, connection_string, auth_mode, endpoint)

    try:
        feature_flags = feature_flag_client.list_feature_flags(
            name_filter=feature_name if feature_name else SearchFilterOptions.ANY_KEY,
            label_filter=SearchFilterOptions.EMPTY_LABEL if label is None else label,
            tags_filter=tags)
        feature_flags = list(feature_flags)
    except HttpResponseError as exception:
        raise CLIErrors.AzureResponseError("Failed to read enhanced feature flag(s) that match the specified feature, label and tags. " + str(exception))

    confirmation_message = "Found '{}' feature flags matching the specified feature, label, and tags. Are you sure you want to delete these feature flags?".format(len(feature_flags))
    user_confirmation(confirmation_message, yes)

    deleted_feature_flags = []
    exception_messages = []
    for feature_flag in feature_flags:
        try:
            deleted_feature_flag = feature_flag_client.delete_feature_flag(name=feature_flag.name,
                                                                           label=feature_flag.label,
                                                                           etag=feature_flag.etag,
                                                                           match_condition=MatchConditions.IfNotModified)
            if deleted_feature_flag is not None:
                deleted_feature_flags.append(_serialize_feature_flag(deleted_feature_flag))
        except ResourceModifiedError:
            exception_messages.append("Failed to delete feature flag '{}' with label '{}' due to a conflicting operation.".format(feature_flag.name, feature_flag.label))
        except HttpResponseError as exception:
            exception_messages.append(str(exception))
            raise CLIErrors.AzureResponseError('Delete operation failed. The following error(s) occurred:\n' + json.dumps(exception_messages, indent=2, ensure_ascii=False))

    # Log errors if partially succeeded
    if exception_messages:
        if deleted_feature_flags:
            logger.error('Delete operation partially failed. The following error(s) occurred:\n%s\n',
                         json.dumps(exception_messages, indent=2, ensure_ascii=False))
        else:
            raise CLIErrors.AzureResponseError('Delete operation failed. \n' + json.dumps(exception_messages, indent=2, ensure_ascii=False))

    return deleted_feature_flags


def enable_feature(cmd,
                   feature_name,
                   name=None,
                   label=None,
                   yes=False,
                   connection_string=None,
                   auth_mode="key",
                   endpoint=None):
    return _set_feature_state(cmd, feature_name, enabled=True, name=name, label=label, yes=yes,
                              connection_string=connection_string, auth_mode=auth_mode, endpoint=endpoint)


def disable_feature(cmd,
                    feature_name,
                    name=None,
                    label=None,
                    yes=False,
                    connection_string=None,
                    auth_mode="key",
                    endpoint=None):
    return _set_feature_state(cmd, feature_name, enabled=False, name=name, label=label, yes=yes,
                              connection_string=connection_string, auth_mode=auth_mode, endpoint=endpoint)


def _set_feature_state(cmd, feature_name, enabled, name, label, yes, connection_string, auth_mode, endpoint):
    feature_flag_client = get_appconfig_feature_flag_client(cmd, name, connection_string, auth_mode, endpoint)

    try:
        feature_flag = feature_flag_client.get_feature_flag(name=feature_name, label=label)
    except ResourceNotFoundError:
        feature_flag = None
    except HttpResponseError as exception:
        raise CLIErrors.AzureResponseError("Failed to retrieve enhanced feature flag from config store. " + str(exception))

    if feature_flag is None:
        raise CLIErrors.ResourceNotFoundError("Enhanced feature flag '{}' with label '{}' not found.".format(feature_name, label))

    feature_flag.enabled = enabled
    action = "enable" if enabled else "disable"
    confirmation_message = "Are you sure you want to {} this enhanced feature flag '{}'?".format(action, feature_name)
    user_confirmation(confirmation_message, yes)

    try:
        updated_feature_flag = feature_flag_client.set_feature_flag(feature_flag)
    except HttpResponseError as exception:
        raise CLIErrors.AzureResponseError(str(exception))

    return _serialize_feature_flag(updated_feature_flag)


def _serialize_feature_flag(feature_flag, fields=None):
    result = {
        FeatureFlagConstants.NAME: feature_flag.name,
        FeatureFlagConstants.ENABLED: feature_flag.enabled,
        FeatureFlagConstants.LABEL: feature_flag.label,
        FeatureFlagConstants.DESCRIPTION: feature_flag.description,
        FeatureFlagConstants.CONDITIONS: feature_flag.conditions.as_dict() if feature_flag.conditions is not None else None,
        FeatureFlagConstants.VARIANTS: [variant.as_dict() for variant in feature_flag.variants] if feature_flag.variants is not None else None,
        FeatureFlagConstants.ALLOCATION: feature_flag.allocation.as_dict() if feature_flag.allocation is not None else None,
        FeatureFlagConstants.TELEMETRY: feature_flag.telemetry.as_dict() if feature_flag.telemetry is not None else None,
        FeatureFlagConstants.TAGS: feature_flag.tags,
        FeatureFlagConstants.LAST_MODIFIED: feature_flag.last_modified,
    }

    if fields:
        return {field: result[field] for field in fields if field in result}

    return result
