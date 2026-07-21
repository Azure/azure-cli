# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods


def combine_old_and_new_custom_policy(old_policy, new_policy):
    old_rules = old_policy.get('detection_rules', [])
    new_rules = new_policy.get('detection_rules', [])

    new_rule_name = {rule['name']: rule for rule in new_rules}
    combined_rule = []
    used = []

    for rule in old_rules:
        name = rule.get('name')
        if name in new_rule_name:
            combined_rule.append(new_rule_name[name])
            used.append(name)
            continue

        combined_rule.append(rule)

    for rule in new_rules:
        name = rule.get('name')
        if name not in used:
            combined_rule.append(rule)

    new_policy['detection_rules'] = combined_rule
    return new_policy


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

    return new_policy
