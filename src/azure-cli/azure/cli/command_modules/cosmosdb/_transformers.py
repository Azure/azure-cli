# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import todict


def transform_network_rule_json_output(result):
    result = todict(result)
    result['ignoreMissingVnetServiceEndpoint'] = result.pop('ignoreMissingVNetServiceEndpoint', None)
    del result['additionalProperties']
    return result


def transform_network_rule_list_output(result):
    new_result = []
    for item in result:
        new_result.append(transform_network_rule_json_output(item))
    return new_result


def transform_db_account_json_output(result):
    if hasattr(result, 'virtual_network_rules') and result.virtual_network_rules:
        result.virtual_network_rules = transform_network_rule_list_output(result.virtual_network_rules)
    return result


def transform_db_account_list_output(result):
    new_result = []
    for item in result:
        new_result.append(transform_db_account_json_output(item))
    return new_result
