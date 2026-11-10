# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods
import re


def _merge_rules_by_name(old_rules, new_rules):
    new_by_name = {rule.get('name'): rule for rule in new_rules}
    merged = [new_by_name.pop(rule.get('name'), rule) for rule in old_rules]
    return merged + list(new_by_name.values())


def combine_old_and_new_custom_policy(old_policy, new_policy):
    for key in ('detection_rules', 'mitigation_rules'):
        rules = _merge_rules_by_name(old_policy.get(key, []), new_policy.get(key, []))
        if rules:
            new_policy[key] = rules
    return new_policy


def _camel_to_snake(data):
    if isinstance(data, dict):
        return {re.sub(r'(?<!^)(?=[A-Z])', '_', k).lower(): _camel_to_snake(v) for k, v in data.items()}
    if isinstance(data, list):
        return [_camel_to_snake(v) for v in data]
    return data


def convert_ddos_custom_policy_to_snake_case(policy):
    new_policy = {}

    if 'location' in policy:
        new_policy['location'] = policy['location']

    if 'name' in policy:
        new_policy['name'] = policy['name']

    if 'detectionRules' in policy:
        new_policy['detection_rules'] = []

        for rule in policy['detectionRules']:
            detection_rule = {}
            if 'name' in rule:
                detection_rule['name'] = rule['name']

            if 'detectionMode' in rule:
                detection_rule['detection_mode'] = rule['detectionMode']

            if 'trafficDetectionRule' in rule:
                traffic_detection_rule = rule['trafficDetectionRule']

                if 'packetsPerSecond' in traffic_detection_rule:
                    traffic_detection_rule['packets_per_second'] = traffic_detection_rule['packetsPerSecond']
                    traffic_detection_rule.pop('packetsPerSecond')

                if 'trafficType' in traffic_detection_rule:
                    traffic_detection_rule['traffic_type'] = traffic_detection_rule['trafficType']
                    traffic_detection_rule.pop('trafficType')

                detection_rule['traffic_detection_rule'] = traffic_detection_rule

            new_policy['detection_rules'].append(detection_rule)

    if 'mitigationRules' in policy:
        # The create args flatten each rule's `properties`; drop read-only fields the args don't accept.
        new_policy['mitigation_rules'] = [
            {'name': rule.get('name'),
             **_camel_to_snake({k: v for k, v in rule.get('properties', {}).items() if k != 'provisioningState'})}
            for rule in policy['mitigationRules']
        ]

    return new_policy
