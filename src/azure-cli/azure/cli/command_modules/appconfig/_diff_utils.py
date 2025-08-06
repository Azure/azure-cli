# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, too-few-public-methods

import json
import os

from knack.util import CLIError
from knack.log import get_logger

from ._constants import CompareFields, JsonDiff, AppServiceConstants
from ._featuremodels import (custom_serialize_allocation, custom_serialize_variants, map_keyvalue_to_featureflag, custom_serialize_conditions, custom_serialize_telemetry, is_feature_flag)
from ._utils import is_json_content_type

logger = get_logger(__name__)


# Utility class used in diff-ing key-values to find added, deleted and updated key-values.
class KVComparer:
    def __init__(self, src_kvs, compare_fields, preserve_labels=True, label=None, content_type=None):
        self._compare_fields = compare_fields
        self._src_kvs = src_kvs

        for kv in self._src_kvs:

            if content_type and not is_feature_flag(kv):
                kv.content_type = content_type

            if not preserve_labels:
                kv.label = label

    # Returns a diff in the form {"add": List[KeyValue], "delete": List[KeyValue], "update": List[{"new": KeyValue, "old": KeyValue}]}
    def compare(self, dest_kvs, strict=False, ignore_matching_kvs=True):
        if not strict and not self._src_kvs:
            return {}

        if not dest_kvs:
            return {JsonDiff.ADD: self._src_kvs}

        dest_kv_lookup = self._build_lookup(dest_kvs)

        kv_diff = {}
        kv_diff[JsonDiff.ADD] = []
        kv_diff[JsonDiff.DELETE] = []
        kv_diff[JsonDiff.UPDATE] = []

        for kv in self._src_kvs:
            lookup_key = (kv.key, kv.label or "")
            if not dest_kv_lookup.get(lookup_key, None):
                kv_diff[JsonDiff.ADD].append(kv)

            else:
                if not (ignore_matching_kvs and self._kv_equals(kv, dest_kv_lookup[lookup_key], self._compare_fields)):
                    kv_diff[JsonDiff.UPDATE].append({"new": kv, "old": dest_kv_lookup[lookup_key]})

                del dest_kv_lookup[lookup_key]

        if strict:
            kv_diff[JsonDiff.DELETE].extend(dest_kv_lookup.values())

        return kv_diff

    @staticmethod
    def _build_lookup(kvs):
        if not kvs:
            return {}

        lookup = {}
        for kv in kvs:
            lookup[(kv.key, kv.label or "")] = kv

        return lookup

    @staticmethod
    def _try_parse_json_value(value_string):
        try:
            return json.loads(value_string)

        except json.JSONDecodeError:
            return value_string

    @classmethod
    def _kv_equals(cls, kv1, kv2, compare_fields):
        for field in compare_fields:
            if field == CompareFields.VALUE and is_json_content_type(kv1.content_type):
                if not (kv1.content_type == kv2.content_type and
                        cls._try_parse_json_value(kv1.value) == cls._try_parse_json_value(kv2.value)):
                    return False
            else:
                if getattr(kv1, field, "") != getattr(kv2, field, ""):
                    return False
        return True


def print_preview(diff, level, yes=False, strict=False, title="", indent=None, show_update_diff=True):
    if not yes:
        logger.warning('\n---------------- %s Preview ----------------', title.title())

    if not strict and diff == {}:
        logger.warning('Source is empty. No changes will be made.')
        return False

    if not any(diff.values()):
        logger.warning('Target configuration already contains all configuration settings in source. No changes will be made.')
        return False

    if not yes:
        __print_diff(diff, level=level, indent=indent, show_update_diff=show_update_diff)
    return True


def __print_diff(diff_output, level, indent=None, show_update_diff=True):
    serializer = get_serializer(level)

    for action, changes in diff_output.items():
        if len(changes) > 0:
            if action == JsonDiff.UPDATE:
                logger.warning('\nUpdating:')
                for update in changes:
                    if show_update_diff:
                        logger.warning('- %s', json.dumps(update["old"], default=serializer, indent=indent, ensure_ascii=False))
                        logger.warning('+ %s', json.dumps(update["new"], default=serializer, indent=indent, ensure_ascii=False))

                    else:
                        logger.warning(json.dumps(update["new"], default=serializer, indent=indent, ensure_ascii=False))

            elif action in (JsonDiff.DELETE, JsonDiff.ADD):
                subtitle = 'Deleting' if action == JsonDiff.DELETE else 'Adding'
                logger.warning('\n %s:', subtitle)

                for record in changes:
                    logger.warning(json.dumps(record, default=serializer, indent=indent, ensure_ascii=False))

    logger.warning("")  # printing an empty line for formatting purpose


def get_serializer(level):
    '''
    Helper method that returns a serializer method called in formatting a string representation of a key-value.
    '''
    source_modes = ("appconfig", "appservice", "file", "aks")
    kvset_modes = ("kvset", "restore")

    if level not in source_modes and level not in kvset_modes:
        raise CLIError("Invalid argument '{}' supplied. level argument should be on of the following: {}".format(level, source_modes + kvset_modes))

    def serialize(obj):

        if isinstance(obj, dict):
            return json.JSONEncoder().default(obj)

        # Feature flag format: {"feature": <feature-name>, "state": <on/off>, "conditions": <conditions-dict>}
        if is_feature_flag(obj):

            # State property doesn't make sense in feature flag version 2 schema beacuse of the added properties - variants, allocation, telemetry
            # The State property only exists in the CLI, we should move to showing enabled property instead as the other clients
            # As we move to showing the enabled property, we will show the state property in the CLI only if compatibility mode is true
            env_compatibility_mode = os.environ.get("AZURE_APPCONFIG_FM_COMPATIBLE", True)
            compatibility_mode = str(env_compatibility_mode).lower() == "true"

            feature = map_keyvalue_to_featureflag(obj, hide_enabled=compatibility_mode)
            # name
            feature_json = {'feature': feature.name}
            # state
            if hasattr(feature, 'state'):
                feature_json['state'] = feature.state
            # enabled
            if hasattr(feature, 'enabled'):
                feature_json['enabled'] = feature.enabled
            # description
            if feature.description is not None:
                feature_json['description'] = feature.description
            # conditions
            if feature.conditions:
                feature_json['conditions'] = custom_serialize_conditions(feature.conditions)
            # allocation
            if feature.allocation:
                feature_json['allocation'] = custom_serialize_allocation(feature.allocation)
            # variants
            if feature.variants:
                feature_json['variants'] = custom_serialize_variants(feature.variants)
            # telemetry
            if feature.telemetry:
                feature_json['telemetry'] = custom_serialize_telemetry(feature.telemetry)

            return feature_json

        res = {'key': obj.key, 'value': obj.value}

        # import/export key, value, content_type and tags (same level as key-value): {"key": <key>, "value": <value>, "AppService:SlotSetting": <true/false>}
        if level == 'appservice':

            if obj.tags:
                slot_setting = obj.tags.get(AppServiceConstants.APPSVC_SLOT_SETTING_KEY, 'false')
                res[AppServiceConstants.APPSVC_SLOT_SETTING_KEY] = slot_setting

        # import/export key, value, content-type, and tags (as a sub group): {"key": <key>, "value": <value>, "label": <label> "content_type": <content_type>, "tags": <tags_dict>}
        elif level == 'appconfig':
            res["label"] = obj.label
            res["content_type"] = obj.content_type
            # tags
            tag_json = {}
            if obj.tags:
                for tag_k, tag_v in obj.tags.items():
                    tag_json[tag_k] = tag_v
            res['tags'] = tag_json

        return res

    def serialize_kvset(kv):
        if level == "kvset":  # File import with kvset profile
            kv_json = {
                'key': kv.key,
                'value': kv.value,
                'label': kv.label,
                'content_type': kv.content_type
            }
        else:  # Restore preview format
            kv_json = {
                'key': kv.key,
                'value': kv.value,
                'label': kv.label,
                'locked': kv.locked,
                'last modified': kv.last_modified,
                'content type': kv.content_type
            }

        # tags
        tag_json = {}
        if kv.tags:
            for tag_k, tag_v in kv.tags.items():
                tag_json[tag_k] = tag_v
        kv_json['tags'] = tag_json

        return kv_json

    return serialize if level in source_modes else serialize_kvset
