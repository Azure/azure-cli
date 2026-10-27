# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.util import todict


def transform_network_rule_json_output(result):
    # 'result' is a plain dict produced by azure.cli.core.util.todict (which, unlike
    # knack.util.todict, understands the typespec-generated SDK models). Rename the
    # service endpoint flag to the historical CLI casing and drop the msrest-era
    # 'additionalProperties' artifact if present.
    result['ignoreMissingVnetServiceEndpoint'] = result.pop('ignoreMissingVNetServiceEndpoint', None)
    result.pop('additionalProperties', None)
    return result


def transform_network_rule_list_output(result):
    return [transform_network_rule_json_output(item) for item in todict(result)]


def transform_db_account_json_output(result):
    # Only convert to a dict when there are virtual network rules to rewrite. Assigning
    # plain dicts back onto the model would be coerced back into VirtualNetworkRule
    # instances (dropping the renamed key), so we convert the whole account to a dict
    # up front and rewrite the rules there.
    if hasattr(result, 'virtual_network_rules') and result.virtual_network_rules:
        result = todict(result)
        result['virtualNetworkRules'] = [
            transform_network_rule_json_output(rule)
            for rule in result.get('virtualNetworkRules') or []
        ]
    return result


def transform_db_account_list_output(result):
    new_result = []
    for item in result:
        new_result.append(transform_db_account_json_output(item))
    return new_result
