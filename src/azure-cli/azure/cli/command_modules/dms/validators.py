# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.azclierror import ValidationError


def validate_keys_and_values_match(table_map: dict):
    renamed_tables = {s: t for s, t in table_map.items() if s != t}
    if len(renamed_tables) > 0:
        raise ValidationError(
            "All source and target table names should match. The following mismatches were found: %s"
            % str(renamed_tables))


def throw_if_not_dictionary(obj, property_name):
    if not isinstance(obj, dict):
        raise ValidationError("'%s' should be a dictionary" % property_name)


def throw_if_not_list(obj, property_name):
    if not isinstance(obj, list):
        raise ValidationError("'%s' should be a list" % property_name)
