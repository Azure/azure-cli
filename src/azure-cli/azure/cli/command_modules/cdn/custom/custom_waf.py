# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.mgmt.cdn.models import (SkuName, PolicyMode, PolicyEnabledState, CdnWebApplicationFirewallPolicy,
                                   ManagedRuleSet, ManagedRuleGroupOverride, CustomRule, RateLimitRule)

from azure.mgmt.cdn.operations import EndpointsOperations

from azure.cli.core.util import (sdk_no_wait, find_child_item)
from azure.cli.core.commands import upsert_to_collection

from knack.util import CLIError
from knack.log import get_logger
logger = get_logger(__name__)


def show_endpoint_waf_policy_link(client: EndpointsOperations,
                                  resource_group_name: str,
                                  profile_name: str,
                                  endpoint_name: str):

    link = client.get(resource_group_name, profile_name, endpoint_name).web_application_firewall_policy_link
    if link is not None:
        return link
    raise CLIError(f"endpoint {endpoint_name} does not have a CDN WAF policy link.", endpoint_name)


def set_endpoint_waf_policy_link(client: EndpointsOperations,
                                 resource_group_name: str,
                                 profile_name: str,
                                 endpoint_name: str,
                                 waf_policy_subscription_id: str = "",
                                 waf_policy_resource_group_name: str = "",
                                 waf_policy_name: str = "",
                                 waf_policy_id: str = ""):

    from azure.mgmt.cdn.models import (EndpointPropertiesUpdateParametersWebApplicationFirewallPolicyLink)

    endpoint = client.get(resource_group_name, profile_name, endpoint_name)

    if waf_policy_id == "":
        if waf_policy_subscription_id is None or waf_policy_resource_group_name is None or waf_policy_name is None:
            raise CLIError('Either --waf-policy-id or all of --waf-policy-subscription-id, '
                           '--waf-policy-resource-group-name, and --waf-policy-name must be specified.')
        waf_policy_id = f'/subscriptions/{waf_policy_subscription_id}' \
                        f'/resourceGroups/{waf_policy_resource_group_name}' \
                        f'/providers/Microsoft.Cdn' \
                        f'/CdnWebApplicationFirewallPolicies/{waf_policy_name}'

    endpoint.web_application_firewall_policy_link = \
        EndpointPropertiesUpdateParametersWebApplicationFirewallPolicyLink(id=waf_policy_id)

    result = client.begin_create(resource_group_name, profile_name, endpoint_name, endpoint).result()
    if result.web_application_firewall_policy_link is not None:
        return result.web_application_firewall_policy_link
    return EndpointPropertiesUpdateParametersWebApplicationFirewallPolicyLink(id=None)


def remove_endpoint_waf_policy_link(client: EndpointsOperations,
                                    resource_group_name: str,
                                    profile_name: str,
                                    endpoint_name: str):

    endpoint = client.get(resource_group_name, profile_name, endpoint_name)
    endpoint.web_application_firewall_policy_link = None
    client.begin_create(resource_group_name, profile_name, endpoint_name, endpoint).wait()


def list_waf_managed_rule_set(client):
    return client.list()


def _show_waf_managed_rule_set(client, rule_set_type, rule_set_version):
    rulesets = client.list()
    for r in rulesets:
        if r.rule_set_type == rule_set_type and r.rule_set_version == rule_set_version:
            return r
    raise CLIError("managed rule set type '{}' version '{}' not found".format(rule_set_type, rule_set_version))


def list_waf_managed_rule_groups(client, rule_set_type, rule_set_version):
    return _show_waf_managed_rule_set(client, rule_set_type, rule_set_version).rule_groups


def set_waf_policy(client,
                   resource_group_name, name,
                   sku=SkuName.standard_microsoft.value,
                   disabled=None,
                   mode=PolicyMode.detection.value,
                   redirect_url=None,
                   block_response_body=None,
                   block_response_status_code=None,
                   tags=None):
    from azure.core.exceptions import ResourceNotFoundError
    from azure.mgmt.cdn.models import (PolicySettings, Sku)
    policy = CdnWebApplicationFirewallPolicy(
        tags=tags,
        sku=Sku(name=sku),
        location='Global',
        policy_settings=PolicySettings(
            enabled_state=PolicyEnabledState.disabled.value if disabled else PolicyEnabledState.enabled.value,
            mode=mode,
            default_redirect_url=redirect_url,
            default_custom_block_response_status_code=block_response_status_code,
            default_custom_block_response_body=block_response_body))

    # Copy config set by sub-commands for updating an existing policy.
    try:
        existing = client.get(resource_group_name, name)
        # Update, let's copy over config set by sub-commands
        policy.custom_rules = existing.custom_rules
        policy.rate_limit_rules = existing.rate_limit_rules
        policy.managed_rules = existing.managed_rules
    except ResourceNotFoundError:
        pass
        # 404 error means it's a new policy, nothing to copy.

    return client.begin_create_or_update(resource_group_name, name, policy)


def _find_policy_managed_rule_set(policy, rule_set_type, rule_set_version):
    for r in policy.managed_rules.managed_rule_sets:
        if r.rule_set_type == rule_set_type and r.rule_set_version == rule_set_version:
            return r
    return None


def add_waf_policy_managed_rule_set(client,
                                    resource_group_name,
                                    policy_name,
                                    rule_set_type,
                                    rule_set_version):

    # Get the existing WAF policy.
    policy = client.get(resource_group_name, policy_name)

    # Verify the managed rule set is not already added to the policy.
    existing = _find_policy_managed_rule_set(policy, rule_set_type, rule_set_version)
    if existing is not None:
        raise CLIError("managed rule set type '{}' version '{}' is already added to WAF policy '{}'"
                       .format(rule_set_type, rule_set_version, policy_name))

    # Add the managed rule set to the policy.
    policy.managed_rules.managed_rule_sets.append(ManagedRuleSet(rule_set_type=rule_set_type,
                                                                 rule_set_version=rule_set_version))
    result = client.begin_create_or_update(resource_group_name, policy_name, policy).result()

    # Return the new managed rule set from the updated policy.
    updated = _find_policy_managed_rule_set(result, rule_set_type, rule_set_version)
    if updated is None:
        raise CLIError("failed to get added managed rule set in WAF policy '{}'".format(policy_name))

    return updated


def remove_waf_policy_managed_rule_set(client,
                                       resource_group_name,
                                       policy_name,
                                       rule_set_type,
                                       rule_set_version):
    # Get the existing WAF policy.
    policy = client.get(resource_group_name, policy_name)

    # Verify the managed rule set is added to the policy.
    existing = _find_policy_managed_rule_set(policy, rule_set_type, rule_set_version)
    if existing is None:
        raise CLIError("managed rule set type '{}' version '{}' is not added to WAF policy '{}'"
                       .format(rule_set_type, rule_set_version, policy_name))

    # Remove the managed rule set from the policy.
    policy.managed_rules.managed_rule_sets.remove(existing)
    client.begin_create_or_update(resource_group_name, policy_name, policy).wait()


def list_waf_policy_managed_rule_sets(client,
                                      resource_group_name,
                                      policy_name):
    policy = client.get(resource_group_name, policy_name)
    return policy.managed_rules.managed_rule_sets


def show_waf_policy_managed_rule_set(client,
                                     resource_group_name,
                                     policy_name,
                                     rule_set_type,
                                     rule_set_version):
    policy = client.get(resource_group_name, policy_name)
    existing = _find_policy_managed_rule_set(policy, rule_set_type, rule_set_version)
    if existing is None:
        raise CLIError("managed rule set type '{}' version '{}' is not added to WAF policy '{}'"
                       .format(rule_set_type, rule_set_version, policy_name))
    return existing


def set_waf_managed_rule_group_override(client,
                                        resource_group_name,
                                        policy_name,
                                        rule_set_type,
                                        rule_set_version,
                                        name,
                                        rule_overrides):
    policy = client.get(resource_group_name, policy_name)
    ruleset = _find_policy_managed_rule_set(policy, rule_set_type, rule_set_version)
    if ruleset is None:
        raise CLIError("managed rule set type '{}' version '{}' is not added to WAF policy '{}'"
                       .format(rule_set_type, rule_set_version, policy_name))

    rulegroup = ManagedRuleGroupOverride(rule_group_name=name, rules=rule_overrides)
    upsert_to_collection(ruleset, 'rule_group_overrides', rulegroup, 'rule_group_name')
    policy = client.begin_create_or_update(resource_group_name, policy_name, policy).result()
    ruleset = _find_policy_managed_rule_set(policy, rule_set_type, rule_set_version)
    return find_child_item(ruleset, name, path='rule_group_overrides', key_path='rule_group_name')


def delete_waf_managed_rule_group_override(client,
                                           resource_group_name,
                                           policy_name,
                                           rule_set_type,
                                           rule_set_version,
                                           name):
    policy = client.get(resource_group_name, policy_name)
    ruleset = _find_policy_managed_rule_set(policy, rule_set_type, rule_set_version)
    if ruleset is None:
        raise CLIError("managed rule set type '{}' version '{}' is not added to WAF policy '{}'"
                       .format(rule_set_type, rule_set_version, policy_name))

    override = find_child_item(ruleset, name, path='rule_group_overrides', key_path='rule_group_name')
    ruleset.rule_group_overrides.remove(override)
    client.begin_create_or_update(resource_group_name, policy_name, policy).wait()


def list_waf_policy_managed_rule_group_overrides(client,
                                                 resource_group_name,
                                                 policy_name,
                                                 rule_set_type,
                                                 rule_set_version):
    ruleset = show_waf_policy_managed_rule_set(client,
                                               resource_group_name,
                                               policy_name,
                                               rule_set_type,
                                               rule_set_version)
    return ruleset.rule_group_overrides


def show_waf_managed_rule_group_override(client,
                                         resource_group_name,
                                         policy_name,
                                         rule_set_type,
                                         rule_set_version,
                                         name):
    ruleset = show_waf_policy_managed_rule_set(client,
                                               resource_group_name,
                                               policy_name,
                                               rule_set_type,
                                               rule_set_version)
    return find_child_item(ruleset, name, path='rule_group_overrides', key_path='rule_group_name')


def set_waf_custom_rule(client,
                        resource_group_name,
                        policy_name,
                        name,
                        priority,
                        action,
                        match_conditions,
                        disabled=None):
    from azure.mgmt.cdn.models import (CustomRuleEnabledState)

    rule = CustomRule(name=name,
                      enabled_state=CustomRuleEnabledState.disabled if disabled else CustomRuleEnabledState.enabled,
                      action=action,
                      match_conditions=match_conditions,
                      priority=priority)

    policy = client.get(resource_group_name, policy_name)
    upsert_to_collection(policy.custom_rules, 'rules', rule, 'name')
    policy = client.begin_create_or_update(resource_group_name, policy_name, policy).result()
    return find_child_item(policy.custom_rules, name, path='rules', key_path='name')


def delete_waf_custom_rule(client,
                           resource_group_name,
                           policy_name,
                           name,
                           no_wait=None):
    policy = client.get(resource_group_name, policy_name)
    rule = find_child_item(policy.custom_rules, name, path='rules', key_path='name')
    policy.custom_rules.rules.remove(rule)
    return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name, policy_name, policy)


def show_waf_custom_rule(client, resource_group_name, policy_name, name):
    policy = client.get(resource_group_name, policy_name)
    return find_child_item(policy.custom_rules, name, path='rules', key_path='name')


def list_waf_custom_rules(client,
                          resource_group_name,
                          policy_name):
    return client.get(resource_group_name, policy_name).custom_rules.rules


def set_waf_rate_limit_rule(client,
                            resource_group_name,
                            policy_name,
                            name,
                            priority,
                            action,
                            request_threshold,
                            duration,
                            match_conditions,
                            disabled=None):
    from azure.mgmt.cdn.models import (CustomRuleEnabledState)

    rule = RateLimitRule(name=name,
                         enabled_state=CustomRuleEnabledState.disabled if disabled else CustomRuleEnabledState.enabled,
                         rate_limit_threshold=request_threshold,
                         rate_limit_duration_in_minutes=duration,
                         action=action,
                         match_conditions=match_conditions,
                         priority=priority)

    policy = client.get(resource_group_name, policy_name)
    upsert_to_collection(policy.rate_limit_rules, 'rules', rule, 'name')
    updated = client.begin_create_or_update(resource_group_name, policy_name, policy).result()
    return find_child_item(updated.rate_limit_rules, name, path='rules', key_path='name')


def delete_waf_rate_limit_rule(client,
                               resource_group_name,
                               policy_name,
                               name,
                               no_wait=None):
    policy = client.get(resource_group_name, policy_name)
    rule = find_child_item(policy.rate_limit_rules, name, path='rules', key_path='name')
    policy.rate_limit_rules.rules.remove(rule)
    return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name, policy_name, policy)


def show_waf_rate_limit_rule(client, resource_group_name, policy_name, name):
    policy = client.get(resource_group_name, policy_name)
    return find_child_item(policy.rate_limit_rules, name, path='rules', key_path='name')


def list_waf_rate_limit_rules(client,
                              resource_group_name,
                              policy_name):
    return client.get(resource_group_name, policy_name).rate_limit_rules.rules
