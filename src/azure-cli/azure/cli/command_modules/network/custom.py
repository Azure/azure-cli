# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=no-self-use, no-member, too-many-lines, unused-argument
# pylint: disable=protected-access, too-few-public-methods, line-too-long

from collections import Counter, OrderedDict

from knack.log import get_logger
from azure.mgmt.core.tools import parse_resource_id, is_valid_resource_id, resource_id

from azure.cli.core.aaz import AAZClientConfiguration, has_value, register_client, AAZFileArgTextFormat
from azure.cli.core.aaz._client import AAZMgmtClient
from azure.cli.core.commands.client_factory import get_subscription_id, get_mgmt_service_client

from azure.cli.core.util import CLIError, sdk_no_wait
from azure.cli.core.azclierror import UnrecognizedArgumentError, ResourceNotFoundError
from azure.cli.core.profiles import ResourceType

logger = get_logger(__name__)

remove_basic_option_msg = "It's recommended to create with `%s`. " \
                          "Please be aware that Basic option will be removed in the future."

subnet_disable_ple_msg = ("`--disable-private-endpoint-network-policies` will be deprecated in the future, if you wanna"
                          "disable network policy for private endpoint, please use "
                          "`--private-endpoint-network-policies Disabled` instead.")

subnet_disable_pls_msg = ("`--disable-private-link-service-network-policies` will be deprecated in the future, if you "
                          "wanna disable network policy for private link service, please use "
                          "`--private-link-service-network-policies Disabled` instead.")


@register_client("NonRetryableClient")
class AAZNonRetryableClient(AAZMgmtClient):
    @classmethod
    def _build_configuration(cls, ctx, credential, **kwargs):
        from azure.cli.core.auth.util import resource_to_scopes
        from azure.core.pipeline.policies import RetryPolicy

        retry_policy = RetryPolicy(**kwargs)
        retry_policy._retry_on_status_codes.discard(429)
        kwargs["retry_policy"] = retry_policy

        return AAZClientConfiguration(
            credential=credential,
            credential_scopes=resource_to_scopes(ctx.cli_ctx.cloud.endpoints.active_directory_resource_id),
            **kwargs
        )


# region Utility methods
def _log_pprint_template(template):
    import json
    logger.info('==== BEGIN TEMPLATE ====')
    logger.info(json.dumps(template, indent=2))
    logger.info('==== END TEMPLATE ====')


def _get_default_name(balancer, property_name, option_name):
    return _get_default_value(balancer, property_name, option_name, True)


def _get_default_id(balancer, property_name, option_name):
    return _get_default_value(balancer, property_name, option_name, False)


def _get_default_value(balancer, property_name, option_name, return_name):
    values = [x.id for x in getattr(balancer, property_name)]
    if len(values) > 1:
        raise CLIError("Multiple possible values found for '{0}': {1}\nSpecify '{0}' "
                       "explicitly.".format(option_name, ', '.join(values)))
    if not values:
        raise CLIError("No existing values found for '{0}'. Create one first and try "
                       "again.".format(option_name))
    return values[0].rsplit('/', 1)[1] if return_name else values[0]

# endregion


# region ApplicationGateways
# pylint: disable=too-many-locals
# pylint: disable=too-many-statements
def _is_v2_sku(sku):
    return 'v2' in sku


def _add_aux_subscription(aux_subscriptions, added_resource_id):
    if added_resource_id and is_valid_resource_id(added_resource_id):
        res_parts = parse_resource_id(added_resource_id)
        aux_sub = res_parts['subscription']
        if aux_sub and aux_sub not in aux_subscriptions:
            aux_subscriptions.append(aux_sub)


def create_application_gateway(cmd, application_gateway_name, resource_group_name, location=None,
                               tags=None, no_wait=False, capacity=2,
                               cert_data=None, cert_password=None, key_vault_secret_id=None,
                               frontend_port=None, http_settings_cookie_based_affinity='disabled',
                               http_settings_port=80, http_settings_protocol='Http',
                               routing_rule_type='Basic', servers=None,
                               sku=None, priority=None, private_ip_address=None, public_ip_address=None,
                               public_ip_address_allocation=None,
                               subnet='default', subnet_address_prefix='10.0.0.0/24',
                               virtual_network_name=None, vnet_address_prefix='10.0.0.0/16',
                               public_ip_address_type=None, subnet_type=None, validate=False,
                               connection_draining_timeout=0, enable_http2=None, min_capacity=None, zones=None,
                               custom_error_pages=None, firewall_policy=None, max_capacity=None,
                               user_assigned_identity=None, enable_fips=None,
                               enable_private_link=False,
                               private_link_ip_address=None,
                               private_link_subnet='PrivateLinkDefaultSubnet',
                               private_link_subnet_prefix='10.0.1.0/24',
                               private_link_primary=None,
                               trusted_client_cert=None,
                               ssl_profile=None,
                               ssl_profile_id=None,
                               ssl_cert_name=None):
    from azure.cli.core.util import random_string
    from azure.cli.core.commands.arm import ArmTemplateBuilder
    from azure.cli.command_modules.network._template_builder import (
        build_application_gateway_resource, build_public_ip_resource, build_vnet_resource)

    DeploymentProperties = cmd.get_models('DeploymentProperties', resource_type=ResourceType.MGMT_RESOURCE_RESOURCES)

    tags = tags or {}
    sku_tier = sku.split('_', 1)[0] if not _is_v2_sku(sku) else sku
    http_listener_protocol = 'https' if (cert_data or key_vault_secret_id) else 'http'
    private_ip_allocation = 'Static' if private_ip_address else 'Dynamic'
    virtual_network_name = virtual_network_name or '{}Vnet'.format(application_gateway_name)

    # Build up the ARM template
    master_template = ArmTemplateBuilder()
    ag_dependencies = []

    public_ip_id = public_ip_address if is_valid_resource_id(public_ip_address) else None
    subnet_id = subnet if is_valid_resource_id(subnet) else None

    network_id_template = resource_id(
        subscription=get_subscription_id(cmd.cli_ctx), resource_group=resource_group_name,
        namespace='Microsoft.Network')

    if subnet_type == 'new':
        ag_dependencies.append('Microsoft.Network/virtualNetworks/{}'.format(virtual_network_name))
        vnet = build_vnet_resource(
            cmd, virtual_network_name, location, tags, vnet_address_prefix, subnet,
            subnet_address_prefix,
            enable_private_link=enable_private_link,
            private_link_subnet=private_link_subnet,
            private_link_subnet_prefix=private_link_subnet_prefix)
        master_template.add_resource(vnet)
        subnet_id = '{}/virtualNetworks/{}/subnets/{}'.format(network_id_template,
                                                              virtual_network_name, subnet)

    if public_ip_address_type == 'new':
        ag_dependencies.append('Microsoft.Network/publicIpAddresses/{}'.format(public_ip_address))
        public_ip_sku = None
        if _is_v2_sku(sku):
            public_ip_sku = 'Standard'
            public_ip_address_allocation = 'Static'
        master_template.add_resource(build_public_ip_resource(cmd, public_ip_address, location,
                                                              tags,
                                                              public_ip_address_allocation,
                                                              None, public_ip_sku, None))
        public_ip_id = '{}/publicIPAddresses/{}'.format(network_id_template,
                                                        public_ip_address)

    private_link_subnet_id = None
    private_link_name = 'PrivateLinkDefaultConfiguration'
    private_link_ip_allocation_method = 'Dynamic'
    if enable_private_link:
        private_link_subnet_id = '{}/virtualNetworks/{}/subnets/{}'.format(network_id_template,
                                                                           virtual_network_name,
                                                                           private_link_subnet)
        private_link_ip_allocation_method = 'Static' if private_link_ip_address else 'Dynamic'

    app_gateway_resource = build_application_gateway_resource(
        cmd, application_gateway_name, location, tags, sku, sku_tier, capacity, servers, frontend_port,
        private_ip_address, private_ip_allocation, priority, cert_data, cert_password, key_vault_secret_id,
        http_settings_cookie_based_affinity, http_settings_protocol, http_settings_port,
        http_listener_protocol, routing_rule_type, public_ip_id, subnet_id,
        connection_draining_timeout, enable_http2, min_capacity, zones, custom_error_pages,
        firewall_policy, max_capacity, user_assigned_identity, enable_fips,
        enable_private_link, private_link_name,
        private_link_ip_address, private_link_ip_allocation_method, private_link_primary,
        private_link_subnet_id, trusted_client_cert, ssl_profile, ssl_profile_id, ssl_cert_name)

    app_gateway_resource['dependsOn'] = ag_dependencies
    master_template.add_variable(
        'appGwID',
        "[resourceId('Microsoft.Network/applicationGateways', '{}')]".format(
            application_gateway_name))
    master_template.add_resource(app_gateway_resource)
    master_template.add_output('applicationGateway', application_gateway_name, output_type='object')
    if cert_password:
        master_template.add_secure_parameter('certPassword', cert_password)

    template = master_template.build()
    parameters = master_template.build_parameters()

    # deploy ARM template
    deployment_name = 'ag_deploy_' + random_string(32)
    client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES).deployments
    properties = DeploymentProperties(template=template, parameters=parameters, mode='incremental')
    Deployment = cmd.get_models('Deployment', resource_type=ResourceType.MGMT_RESOURCE_RESOURCES)
    deployment = Deployment(properties=properties)

    if validate:
        _log_pprint_template(template)
        if cmd.supported_api_version(min_api='2019-10-01', resource_type=ResourceType.MGMT_RESOURCE_RESOURCES):
            from azure.cli.core.commands import LongRunningOperation
            validation_poller = client.begin_validate(resource_group_name, deployment_name, deployment)
            return LongRunningOperation(cmd.cli_ctx)(validation_poller)

        return client.validate(resource_group_name, deployment_name, deployment)

    return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name, deployment_name, deployment)


def remove_ag_identity(cmd, resource_group_name, application_gateway_name, no_wait=False):
    from .aaz.latest.network.application_gateway._update import Update as _ApplicationGatewayUpdate

    class IdentityRemove(_ApplicationGatewayUpdate):
        def pre_operations(self):
            args = self.ctx.args
            args.no_wait = no_wait

        def pre_instance_update(self, instance):
            instance.identity = None

    return IdentityRemove(cli_ctx=cmd.cli_ctx)(command_args={
        "name": application_gateway_name,
        "resource_group": resource_group_name
    })


# region application-gateway trusted-client-certificates


def show_ag_backend_health(cmd, resource_group_name, application_gateway_name, expand=None,
                           protocol=None, host=None, path=None, timeout=None, host_name_from_http_settings=None,
                           match_body=None, match_status_codes=None, address_pool=None, http_settings=None):
    from azure.cli.core.commands import LongRunningOperation
    on_demand_arguments = {protocol, host, path, timeout, host_name_from_http_settings, match_body, match_status_codes,
                           address_pool, http_settings}
    if on_demand_arguments.difference({None}):
        if address_pool is not None and not is_valid_resource_id(address_pool):
            address_pool = resource_id(
                subscription=get_subscription_id(cmd.cli_ctx),
                resource_group=resource_group_name,
                namespace="Microsoft.Network",
                type="applicationGateways",
                name=application_gateway_name,
                child_type_1="backendAddressPools",
                child_name_1=address_pool
            )
        if http_settings is not None and not is_valid_resource_id(http_settings):
            http_settings = resource_id(
                subscription=get_subscription_id(cmd.cli_ctx),
                resource_group=resource_group_name,
                namespace="Microsoft.Network",
                type="applicationGateways",
                name=application_gateway_name,
                child_type_1="backendHttpSettingsCollection",
                child_name_1=http_settings
            )

        from .aaz.latest.network.application_gateway._health_on_demand import HealthOnDemand
        return LongRunningOperation(cmd.cli_ctx)(
            HealthOnDemand(cli_ctx=cmd.cli_ctx)(command_args={
                "name": application_gateway_name,
                "resource_group": resource_group_name,
                "expand": expand,
                "protocol": protocol,
                "host": host,
                "path": path,
                "timeout": timeout,
                "host_name_from_http_settings": host_name_from_http_settings,
                "match_body": match_body,
                "match_status_codes": match_status_codes,
                "backend_address_pool": {"id": address_pool},
                "backend_http_settings": {"id": http_settings}
            })
        )

    from .aaz.latest.network.application_gateway._health import Health
    return LongRunningOperation(cmd.cli_ctx)(
        Health(cli_ctx=cmd.cli_ctx)(command_args={
            "name": application_gateway_name,
            "resource_group": resource_group_name,
            "expand": expand
        })
    )
# endregion


# region application-gateway ssl-profile


# endregion


def set_ag_waf_config(cmd, resource_group_name, application_gateway_name, enabled,
                      firewall_mode=None, rule_set_type="OWASP", rule_set_version=None,
                      disabled_rule_groups=None, disabled_rules=None, no_wait=False,
                      request_body_check=None, max_request_body_size=None, file_upload_limit=None, exclusions=None):
    waf_config = {
        "enabled": enabled == "true",
        "firewall_mode": firewall_mode,
        "rule_set_type": rule_set_type,
        "rule_set_version": rule_set_version
    }

    from .aaz.latest.network.application_gateway._update import Update as _ApplicationGatewayUpdate

    class WAFConfigSet(_ApplicationGatewayUpdate):
        def pre_operations(self):
            args = self.ctx.args
            args.no_wait = no_wait

        def pre_instance_update(self, instance):
            def _flatten(collection, expand_property_fn):
                for each in collection:
                    yield from expand_property_fn(each)

            if disabled_rule_groups or disabled_rules:
                disabled_groups = []
                # disabled groups can be added directly
                for group in disabled_rule_groups or []:
                    disabled_groups.append({"rule_group_name": group})
                # for disabled rules, we have to look up the IDs
                if disabled_rules:
                    rule_sets = list_ag_waf_rule_sets(cmd, _type=rule_set_type, version=rule_set_version, group='*')
                    for group in _flatten(rule_sets, lambda r: r["ruleGroups"]):
                        disabled_group = {
                            "rule_group_name": group["ruleGroupName"],
                            "rules": []
                        }
                        for rule in group["rules"]:
                            if str(rule["ruleId"]) in disabled_rules:
                                disabled_group["rules"].append(rule["ruleId"])
                        if disabled_group["rules"]:
                            disabled_groups.append(disabled_group)
                waf_config["disabled_rule_groups"] = disabled_groups
            waf_config["request_body_check"] = request_body_check
            waf_config["max_request_body_size_in_kb"] = max_request_body_size
            waf_config["file_upload_limit_in_mb"] = file_upload_limit
            waf_config["exclusions"] = exclusions

            instance.properties.web_application_firewall_configuration = waf_config

    return WAFConfigSet(cli_ctx=cmd.cli_ctx)(command_args={
        "name": application_gateway_name,
        "resource_group": resource_group_name
    })


def show_ag_waf_config(cmd, resource_group_name, application_gateway_name):
    from .aaz.latest.network.application_gateway._show import Show
    return Show(cli_ctx=cmd.cli_ctx)(command_args={
        "name": application_gateway_name,
        "resource_group": resource_group_name
    })["webApplicationFirewallConfiguration"]


def list_ag_waf_rule_sets(cmd, _type=None, version=None, group=None):
    from .aaz.latest.network.application_gateway.waf_config._list_rule_sets import ListRuleSets
    rule_sets = ListRuleSets(cli_ctx=cmd.cli_ctx)(command_args={})["value"]

    filtered_sets = []
    # filter by rule set name or version
    for rule_set in rule_sets:
        if _type and _type.lower() != rule_set["ruleSetType"].lower():
            continue
        if version and version.lower() != rule_set["ruleSetVersion"].lower():
            continue

        filtered_groups = []
        for rule_group in rule_set["ruleGroups"]:
            if not group:
                rule_group["rules"] = None
                filtered_groups.append(rule_group)
                continue

            if group.lower() == rule_group["ruleGroupName"].lower() or group == "*":
                filtered_groups.append(rule_group)
        if filtered_groups:
            rule_set["ruleGroups"] = filtered_groups
            filtered_sets.append(rule_set)
    return filtered_sets
# endregion


# region ApplicationGatewayWAFPolicy
# endregion


# region ApplicationGatewayWAFPolicyRules PolicySettings
def list_waf_policy_setting(cmd, resource_group_name, policy_name):
    from .aaz.latest.network.application_gateway.waf_policy._show import Show
    return Show(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "name": policy_name}
    )["policySettings"]
# endregion


# region ApplicationGatewayWAFPolicyRuleMatchConditions


# endregion


# region ApplicationGatewayWAFPolicy ManagedRule ManagedRuleSet
def add_waf_managed_rule_set(cmd, resource_group_name, policy_name,
                             rule_set_type, rule_set_version, rule_group_name=None, rules=None):
    """
    Add managed rule set to the WAF policy managed rules.
    Visit: https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/application-gateway-crs-rulegroups-rules
    """
    if rules is None:
        managed_rule_overrides = []
    else:
        managed_rule_overrides = rules

    if rule_set_type.lower() == "microsoft_httpddosruleset":
        for r in managed_rule_overrides:
            if not r.get('sensitivity', None):
                r['sensitivity'] = 'Medium'

    rule_group_override = None
    if rule_group_name is not None:
        rule_group_override = {
            "rule_group_name": rule_group_name,
            "rules": managed_rule_overrides
        }

    if rule_group_override is None:
        rule_group_overrides = []
    else:
        rule_group_overrides = [rule_group_override]

    new_managed_rule_set = {
        "rule_set_type": rule_set_type,
        "rule_set_version": rule_set_version,
        "rule_group_overrides": rule_group_overrides
    }

    from .aaz.latest.network.application_gateway.waf_policy._update import Update

    class WAFManagedRuleSetAdd(Update):
        def pre_instance_update(self, instance):
            for rule_set in instance.properties.managed_rules.managed_rule_sets:
                if rule_set.rule_set_type == rule_set_type and rule_set.rule_set_version == rule_set_version:
                    for rule_override in rule_set.rule_group_overrides:
                        if rule_override.rule_group_name == rule_group_name:
                            # add one rule
                            rule_override.rules.extend(managed_rule_overrides)
                            break
                    else:
                        # add one rule group
                        if rule_group_override is not None:
                            rule_set.rule_group_overrides.append(rule_group_override)
                    break
            else:
                # add new rule set
                instance.properties.managed_rules.managed_rule_sets.append(new_managed_rule_set)

    return WAFManagedRuleSetAdd(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "name": policy_name
    })


def update_waf_managed_rule_set(cmd, resource_group_name, policy_name,
                                rule_set_type, rule_set_version, rule_group_name=None, rules=None):
    """
    Update (Override) existing rule set of a WAF policy managed rules.
    """
    managed_rule_overrides = rules if rules else None

    rule_group_override = {
        "rule_group_name": rule_group_name,
        "rules": managed_rule_overrides
    } if managed_rule_overrides else None

    if rule_group_override is None:
        rule_group_overrides = []
    else:
        rule_group_overrides = [rule_group_override]

    new_managed_rule_set = {
        "rule_set_type": rule_set_type,
        "rule_set_version": rule_set_version,
        "rule_group_overrides": rule_group_overrides
    }

    from .aaz.latest.network.application_gateway.waf_policy._update import Update

    class WAFManagedRuleSetUpdate(Update):
        def pre_instance_update(self, instance):
            updated_rule_set = None
            for rule_set in instance.properties.managed_rules.managed_rule_sets:
                if rule_set.rule_set_type == rule_set_type and rule_set.rule_set_version != rule_set_version:
                    updated_rule_set = rule_set
                    break

                if rule_set.rule_set_type == rule_set_type and rule_set.rule_set_version == rule_set_version:
                    if rule_group_name is None:
                        updated_rule_set = rule_set
                        break

                    rg = next((g for g in rule_set.rule_group_overrides if g.rule_group_name == rule_group_name), None)
                    if rg:
                        rg.rules = managed_rule_overrides
                    else:
                        rule_set.rule_group_overrides.append(rule_group_override)

            if updated_rule_set:
                new_managed_rule_sets = []
                for rule_set in instance.properties.managed_rules.managed_rule_sets:
                    if rule_set == updated_rule_set:
                        continue

                    new_managed_rule_sets.append(rule_set)
                new_managed_rule_sets.append(new_managed_rule_set)

                instance.properties.managed_rules.managed_rule_sets = new_managed_rule_sets

    return WAFManagedRuleSetUpdate(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "name": policy_name
    })


def remove_waf_managed_rule_set(cmd, resource_group_name, policy_name,
                                rule_set_type, rule_set_version, rule_group_name=None):
    """
    Remove a managed rule set by rule set group name if rule_group_name is specified. Otherwise, remove all rule set.
    """
    from .aaz.latest.network.application_gateway.waf_policy._update import Update

    class WAFManagedRuleSetRemove(Update):
        def pre_instance_update(self, instance):
            delete_rule_set = None
            for rule_set in instance.properties.managed_rules.managed_rule_sets:
                if rule_set.rule_set_type == rule_set_type or rule_set.rule_set_version == rule_set_version:
                    if rule_group_name is None:
                        delete_rule_set = rule_set
                        break
                    # remove one rule from rule group
                    is_removed = False
                    new_rule_group_overrides = []
                    for rg in rule_set.rule_group_overrides:
                        if rg.rule_group_name == rule_group_name and not is_removed:
                            is_removed = True
                            continue

                        new_rule_group_overrides.append(rg)
                    if not is_removed:
                        err_msg = f"Rule set group [{rule_group_name}] is not found."
                        raise ResourceNotFoundError(err_msg)

                    rule_set.rule_group_overrides = new_rule_group_overrides

            if delete_rule_set:
                new_managed_rule_sets = []
                for rule_set in instance.properties.managed_rules.managed_rule_sets:
                    if rule_set == delete_rule_set:
                        continue

                    new_managed_rule_sets.append(rule_set)
                instance.properties.managed_rules.managed_rule_sets = new_managed_rule_sets

    return WAFManagedRuleSetRemove(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "name": policy_name
    })


def list_waf_managed_rules(cmd, resource_group_name, policy_name):
    from .aaz.latest.network.application_gateway.waf_policy._show import Show
    return Show(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "name": policy_name
    })["managedRules"]
# endregion


# region ApplicationGatewayWAFPolicy ManagedRule Exception
def remove_waf_managed_rule_exception(cmd, resource_group_name, policy_name):
    from .aaz.latest.network.application_gateway.waf_policy._update import Update

    class WAFExceptionRemove(Update):
        def pre_instance_update(self, instance):
            instance.properties.managed_rules.exceptions = []

    return WAFExceptionRemove(cli_ctx=cmd.cli_ctx)(command_args={
        "name": policy_name,
        "resource_group": resource_group_name,
    })
# endregion


# region ApplicationGatewayWAFPolicy ManagedRule OwaspCrsExclusionEntry
# pylint: disable=too-many-nested-blocks
def remove_waf_managed_rule_exclusion(cmd, resource_group_name, policy_name):
    from .aaz.latest.network.application_gateway.waf_policy._update import Update

    class WAFExclusionRemove(Update):
        def pre_instance_update(self, instance):
            instance.properties.managed_rules.exclusions = []

    return WAFExclusionRemove(cli_ctx=cmd.cli_ctx)(command_args={
        "name": policy_name,
        "resource_group": resource_group_name,
    })


def add_waf_exclusion_rule_set(cmd, resource_group_name, policy_name,
                               rule_set_type, rule_set_version, match_variable, selector_match_operator, selector,
                               rule_group_name=None, rule_ids=None):
    # build current rules from ids
    if rule_ids is None:
        rules = []
    else:
        rules = [{"rule_id": rule_id} for rule_id in rule_ids]
    # build current rule group from rules
    curr_rule_group = None
    if rule_group_name is not None:
        curr_rule_group = {
            "rule_group_name": rule_group_name,
            "rules": rules,
        }
    # build current rule set from rule group
    if curr_rule_group is None:
        rule_groups = []
    else:
        rule_groups = [curr_rule_group]
    curr_rule_set = {
        "rule_set_type": rule_set_type,
        "rule_set_version": rule_set_version,
        "rule_groups": rule_groups,
    }

    from .aaz.latest.network.application_gateway.waf_policy._update import Update

    class WAFExclusionRuleSetAdd(Update):
        def pre_instance_update(self, instance):
            def _has_exclusion():
                for e in instance.properties.managed_rules.exclusions:
                    if (e.match_variable, e.selector_match_operator, e.selector) == (match_variable, selector_match_operator, selector):
                        return True

                return False

            if not _has_exclusion():
                exclusion = {
                    "match_variable": match_variable,
                    "selector_match_operator": selector_match_operator,
                    "selector": selector,
                    "exclusion_managed_rule_sets": [curr_rule_set],
                }
                instance.properties.managed_rules.exclusions.append(exclusion)
            else:
                for exclusion in instance.properties.managed_rules.exclusions:
                    if (exclusion.match_variable, exclusion.selector_match_operator, exclusion.selector) == (match_variable, selector_match_operator, selector):
                        for rule_set in exclusion.exclusion_managed_rule_sets:
                            if rule_set.rule_set_type == rule_set_type and rule_set.rule_set_version == rule_set_version:
                                for rule_group in rule_set.rule_groups:
                                    # add rules when rule group exists
                                    if rule_group.rule_group_name == rule_group_name:
                                        rule_group.rules.extend(rules)
                                        break
                                else:
                                    # add a new rule group
                                    if curr_rule_group is not None:
                                        rule_set.rule_groups.append(curr_rule_group)
                                break
                        else:
                            # add a new rule set
                            exclusion.exclusion_managed_rule_sets.append(curr_rule_set)

    return WAFExclusionRuleSetAdd(cli_ctx=cmd.cli_ctx)(command_args={
        "name": policy_name,
        "resource_group": resource_group_name,
    })


def remove_waf_exclusion_rule_set(cmd, resource_group_name, policy_name,
                                  rule_set_type, rule_set_version, match_variable, selector_match_operator, selector,
                                  rule_group_name=None):
    from .aaz.latest.network.application_gateway.waf_policy._update import Update

    class WAFExclusionRuleSetRemove(Update):
        def pre_instance_update(self, instance):
            remove_rule_set, remove_exclusion = None, None
            for exclusion in instance.properties.managed_rules.exclusions:
                if (exclusion.match_variable, exclusion.selector_match_operator, exclusion.selector) == (match_variable, selector_match_operator, selector):
                    for rule_set in exclusion.exclusion_managed_rule_sets:
                        if rule_set.rule_set_type == rule_set_type or rule_set.rule_set_version == rule_set_version:
                            if rule_group_name is None:
                                remove_rule_set = rule_set
                                break
                        # remove one rule from rule group
                        is_removed = False
                        new_rule_groups = []
                        for rg in rule_set.rule_groups:
                            if rg.rule_group_name == rule_group_name and not is_removed:
                                is_removed = True
                                continue

                            new_rule_groups.append(rg)
                        if not is_removed:
                            err_msg = f"Rule set group [{rule_group_name}] is not found."
                            raise ResourceNotFoundError(err_msg)

                        rule_set.rule_groups = new_rule_groups

                        if not rule_set.rule_groups:
                            new_rule_sets = []
                            for rs in exclusion.exclusion_managed_rule_sets:
                                if rs == rule_set:
                                    continue

                                new_rule_sets.append(rs)
                            exclusion.exclusion_managed_rule_sets = new_rule_sets
                            if not exclusion.exclusion_managed_rule_sets:
                                remove_exclusion = exclusion

                    if remove_rule_set:
                        new_rule_sets = []
                        for rs in exclusion.exclusion_managed_rule_sets:
                            if rs == remove_rule_set:
                                continue

                            new_rule_sets.append(rs)
                        exclusion.exclusion_managed_rule_sets = new_rule_sets
                        if not exclusion.exclusion_managed_rule_sets:
                            remove_exclusion = exclusion

            if remove_exclusion:
                new_exclusions = []
                for exclusion in instance.properties.managed_rules.exclusions:
                    if exclusion == remove_exclusion:
                        continue

                    new_exclusions.append(exclusion)
                instance.properties.managed_rules.exclusions = new_exclusions

    return WAFExclusionRuleSetRemove(cli_ctx=cmd.cli_ctx)(command_args={
        "name": policy_name,
        "resource_group": resource_group_name,
    })
# endregion


# region DdosProtectionPlans
def create_ddos_plan(cmd, resource_group_name, ddos_plan_name, location=None, tags=None, vnets=None):
    from azure.cli.core.commands import LongRunningOperation
    from azure.cli.command_modules.network.aaz.latest.network.ddos_protection._create import Create
    from azure.cli.command_modules.network.operations.latest.network.vnet._update import VNetUpdate
    Create_Ddos_Protection = Create(cli_ctx=cmd.cli_ctx)
    args = {
        "name": ddos_plan_name,
        "resource_group": resource_group_name,
    }
    if location:
        args['location'] = location
    if tags:
        args['tags'] = tags
    if not vnets:
        # if no VNETs can do a simple PUT
        return Create_Ddos_Protection(args)

    # if VNETs specified, have to create the protection plan and then add the VNETs
    plan_id = LongRunningOperation(cmd.cli_ctx)(Create_Ddos_Protection(args))['id']

    logger.info('Attempting to attach VNets to newly created DDoS protection plan.')
    for vnet_subresource in vnets:
        id_parts = parse_resource_id(vnet_subresource.id)
        poller = VNetUpdate(cli_ctx=cmd.cli_ctx)(command_args={
            'name': id_parts['name'],
            'resource_group': id_parts['resource_group'],
            'ddos_protection_plan': plan_id
        })
        LongRunningOperation(cmd.cli_ctx)(poller)

    show_args = {
        "name": ddos_plan_name,
        "resource_group": resource_group_name,
    }
    from azure.cli.command_modules.network.aaz.latest.network.ddos_protection._show import Show
    Show_Ddos_Protection = Show(cli_ctx=cmd.cli_ctx)
    return Show_Ddos_Protection(show_args)


def update_ddos_plan(cmd, resource_group_name, ddos_plan_name, tags=None, vnets=None):
    from azure.cli.command_modules.network.aaz.latest.network.ddos_protection._update import Update
    Update_Ddos_Protection = Update(cli_ctx=cmd.cli_ctx)
    args = {
        "name": ddos_plan_name,
        "resource_group": resource_group_name,
    }
    if tags is not None:
        args['tags'] = tags
    if vnets is not None:
        from azure.cli.command_modules.network.aaz.latest.network.ddos_protection._show import Show
        from azure.cli.command_modules.network.operations.latest.network.vnet._update import VNetUpdate
        show_args = {
            "name": ddos_plan_name,
            "resource_group": resource_group_name,
        }
        Show_Ddos_Protection = Show(cli_ctx=cmd.cli_ctx)
        show_args = Show_Ddos_Protection(show_args)
        logger.info('Attempting to update the VNets attached to the DDoS protection plan.')
        vnet_ids = set()
        if len(vnets) == 1 and not vnets[0]:
            pass
        else:
            vnet_ids = {x.id for x in vnets}
        if 'virtualNetworks' in show_args:
            existing_vnet_ids = {x['id'] for x in show_args['virtualNetworks']}
        else:
            existing_vnet_ids = set()
        from azure.cli.core.commands import LongRunningOperation
        for vnet_id in vnet_ids.difference(existing_vnet_ids):
            logger.info("Adding VNet '%s' to plan.", vnet_id)
            id_parts = parse_resource_id(vnet_id)
            poller = VNetUpdate(cli_ctx=cmd.cli_ctx)(command_args={
                'name': id_parts['name'],
                'resource_group': id_parts['resource_group'],
                'ddos_protection_plan': show_args['id']
            })
            LongRunningOperation(cmd.cli_ctx)(poller)
        for vnet_id in existing_vnet_ids.difference(vnet_ids):
            logger.info("Removing VNet '%s' from plan.", vnet_id)
            id_parts = parse_resource_id(vnet_id)
            poller = VNetUpdate(cli_ctx=cmd.cli_ctx)(command_args={
                'name': id_parts['name'],
                'resource_group': id_parts['resource_group'],
                'ddos_protection_plan': None
            })
            LongRunningOperation(cmd.cli_ctx)(poller)
    return Update_Ddos_Protection(args)
# endregion


# region DNS Commands
# add delegation name server record for the created child zone in it's parent zone.
def _to_snake(s):
    import re
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', s)

    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def _convert_to_snake_case(element):
    if isinstance(element, dict):
        ret = {}
        for k, v in element.items():
            ret[_to_snake(k)] = _convert_to_snake_case(v)

        return ret

    if isinstance(element, list):
        return [_convert_to_snake_case(i) for i in element]

    return element


def add_dns_delegation(cmd, child_zone, parent_zone, child_rg, child_zone_name):
    """
     :param child_zone: the zone object corresponding to the child that is created.
     :param parent_zone: the parent zone name / FQDN of the parent zone.
                         if parent zone name is mentioned, assume current subscription and resource group.
     :param child_rg: resource group of the child zone
     :param child_zone_name: name of the child zone
    """
    import sys
    from azure.core.exceptions import HttpResponseError
    parent_rg = child_rg
    parent_subscription_id = None
    parent_zone_name = parent_zone

    if is_valid_resource_id(parent_zone):
        id_parts = parse_resource_id(parent_zone)
        parent_rg = id_parts['resource_group']
        parent_subscription_id = id_parts['subscription']
        parent_zone_name = id_parts['name']

    if all([parent_zone_name, parent_rg, child_zone_name, child_zone]) and child_zone_name.endswith(parent_zone_name):
        record_set_name = child_zone_name.replace('.' + parent_zone_name, '')
        try:
            for dname in child_zone["nameServers"]:
                add_dns_ns_record(cmd, parent_rg, parent_zone_name, record_set_name, dname, parent_subscription_id)
            print('Delegation added successfully in \'{}\'\n'.format(parent_zone_name), file=sys.stderr)
        except HttpResponseError as ex:
            logger.error(ex)
            print('Could not add delegation in \'{}\'\n'.format(parent_zone_name), file=sys.stderr)


def create_dns_zone(cmd, resource_group_name, zone_name, parent_zone_name=None, tags=None, if_none_match=False):
    from .aaz.latest.network.dns.zone._create import Create as _DNSZoneCreate

    created_zone = _DNSZoneCreate(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "zone_name": zone_name,
        "if_none_match": '*' if if_none_match else None,
        "location": 'global',
        "tags": tags
    })

    if parent_zone_name is not None:
        logger.info('Attempting to add delegation in the parent zone')
        add_dns_delegation(cmd, created_zone, parent_zone_name, resource_group_name, zone_name)
    return created_zone


def show_dns_soa_record_set(cmd, resource_group_name, zone_name, record_type):
    from .operations.latest.network.dns.record_set.soa._show import RecordSetSOAShow as DNSRecordSetSOAShow

    return DNSRecordSetSOAShow(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "zone_name": zone_name
    })


def update_dns_soa_record(cmd, resource_group_name, zone_name, host=None, email=None,
                          serial_number=None, refresh_time=None, retry_time=None, expire_time=None,
                          minimum_ttl=3600, if_none_match=None):
    record_set_name = '@'
    record_type = 'soa'

    from .operations.latest.network.dns.record_set.soa._show import RecordSetSOAShow as DNSRecordSetSOAShow

    record_set = DNSRecordSetSOAShow(cli_ctx=cmd.cli_ctx)(command_args={
        "zone_name": zone_name,
        "resource_group": resource_group_name
    })

    record_camal = record_set["SOARecord"]
    record = {}
    record["host"] = host or record_camal.get("host", None)
    record["email"] = email or record_camal.get("email", None)
    record["serial_number"] = serial_number or record_camal.get("serialNumber", None)
    record["refresh_time"] = refresh_time or record_camal.get("refreshTime", None)
    record["retry_time"] = retry_time or record_camal.get("retryTime", None)
    record["expire_time"] = expire_time or record_camal.get("expireTime", None)
    record["minimum_ttl"] = minimum_ttl or record_camal.get("minimumTTL", None)

    return _add_save_record(cmd, record, record_type, record_set_name, resource_group_name, zone_name,
                            is_list=False, if_none_match=if_none_match)


def _type_to_property_name(key):
    type_dict = {
        # `record_type`: (`snake_case`, `camel_case`)
        'a': ('a_records', "ARecords"),
        'aaaa': ('aaaa_records', "AAAARecords"),
        'caa': ('caa_records', "caaRecords"),
        'cname': ('cname_record', "CNAMERecord"),
        'ds': ('ds_records', "DSRecords"),
        'mx': ('mx_records', "MXRecords"),
        'naptr': ('naptr_records', "NAPTRRecords"),
        'ns': ('ns_records', "NSRecords"),
        'ptr': ('ptr_records', "PTRRecords"),
        'soa': ('soa_record', "SOARecord"),
        'spf': ('txt_records', "TXTRecords"),
        'srv': ('srv_records', "SRVRecords"),
        'tlsa': ('tlsa_records', "TLSARecords"),
        'txt': ('txt_records', "TXTRecords"),
        'alias': ('target_resource', "targetResource"),
    }
    return type_dict[key.lower()]


def export_zone(cmd, resource_group_name, zone_name, file_name=None):  # pylint: disable=too-many-branches
    from time import localtime, strftime
    from azure.cli.command_modules.network.zone_file.make_zone_file import make_zone_file
    from .aaz.latest.network.dns.record_set._list import List as _DNSRecordSetListByZone

    record_sets = _DNSRecordSetListByZone(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "zone_name": zone_name
    })

    zone_obj = OrderedDict({
        '$origin': zone_name.rstrip('.') + '.',
        'resource-group': resource_group_name,
        'zone-name': zone_name.rstrip('.'),
        'datetime': strftime('%a, %d %b %Y %X %z', localtime())
    })

    for record_set in record_sets:
        record_set = _convert_to_snake_case(record_set)
        record_type = record_set["type"].rsplit('/', 1)[1].lower()
        record_set_name = record_set["name"]
        record_data = record_set.get(_type_to_property_name(record_type)[0])

        if not record_data:
            record_data = []
        if not isinstance(record_data, list):
            record_data = [record_data]

        if record_set_name not in zone_obj:
            zone_obj[record_set_name] = OrderedDict()

        for record in record_data:
            record_obj = {'ttl': record_set["ttl"]}

            if record_type not in zone_obj[record_set_name]:
                zone_obj[record_set_name][record_type] = []
            if record_type == 'aaaa':
                record_obj.update({'ip': record["ipv6_address"]})
            elif record_type == 'a':
                record_obj.update({'ip': record["ipv4_address"]})
            elif record_type == 'caa':
                record_obj.update({'val': record["value"], 'tag': record["tag"], 'flags': record["flags"]})
            elif record_type == 'cname':
                record_obj.update({'alias': record["cname"].rstrip('.') + '.'})
            elif record_type == 'ds':
                record_obj.update({'key_tag': record["key_tag"], 'algorithm': record["algorithm"], 'digest_type': record["digest"]["algorithm_type"], 'digest': record["digest"]["value"]})
            elif record_type == 'mx':
                record_obj.update({'preference': record["preference"], 'host': record["exchange"].rstrip('.') + '.'})
            elif record_type == 'naptr':
                regexp_value = record["regexp"] if record["regexp"] != "" else "EMPTY"
                record_obj.update({'order': record["order"], 'preference': record["preference"], 'flags': record["flags"], 'services': record["services"], 'regexp': regexp_value, 'replacement': record["replacement"].rstrip('.') + '.'})
            elif record_type == 'ns':
                record_obj.update({'host': record["nsdname"].rstrip('.') + '.'})
            elif record_type == 'ptr':
                record_obj.update({'host': record["ptrdname"].rstrip('.') + '.'})
            elif record_type == 'soa':
                record_obj.update({
                    'mname': record["host"].rstrip('.') + '.',
                    'rname': record["email"].rstrip('.') + '.',
                    'serial': int(record["serial_number"]),
                    'refresh': record["refresh_time"],
                    'retry': record["retry_time"],
                    'expire': record["expire_time"],
                    'minimum': record["minimum_ttl"]
                })
                zone_obj['$ttl'] = record["minimum_ttl"]
            elif record_type == 'srv':
                record_obj.update({'priority': record["priority"], 'weight': record["weight"],
                                   'port': record["port"], 'target': record["target"].rstrip('.') + '.'})
            elif record_type == 'tlsa':
                record_obj.update({'usage': record["usage"], 'selector': record["selector"], 'matching_type': record["matching_type"], 'certificate': record["cert_association_data"]})
            elif record_type == 'txt':
                record_obj.update({'txt': ''.join(record["value"])})
            zone_obj[record_set_name][record_type].append(record_obj)

        if len(record_data) == 0:
            record_obj = {'ttl': record_set["ttl"]}

            if record_type not in zone_obj[record_set_name]:
                zone_obj[record_set_name][record_type] = []
            # Checking for alias record
            if (record_type == 'a' or record_type == 'aaaa' or record_type == 'cname') and record_set["target_resource"].get("id", ""):
                target_resource_id = record_set["target_resource"]["id"]
                record_obj.update({'target-resource-id': record_type.upper() + " " + target_resource_id})
                record_type = 'alias'
                if record_type not in zone_obj[record_set_name]:
                    zone_obj[record_set_name][record_type] = []
            elif record_type == 'aaaa' or record_type == 'a':
                record_obj.update({'ip': ''})
            elif record_type == 'cname':
                record_obj.update({'alias': ''})
            zone_obj[record_set_name][record_type].append(record_obj)
    zone_file_content = make_zone_file(zone_obj)
    print(zone_file_content)
    if file_name:
        try:
            with open(file_name, 'w') as f:
                f.write(zone_file_content)
        except OSError:
            raise CLIError('Unable to export to file: {}'.format(file_name))


# pylint: disable=too-many-return-statements, inconsistent-return-statements, too-many-branches
def _build_record(cmd, data):
    record_type = data['delim'].lower()
    try:
        if record_type == 'aaaa':
            return {"ipv6_address": data["ip"]}
        if record_type == 'a':
            return {"ipv4_address": data["ip"]}
        if record_type == 'caa':
            return {"value": data["val"], "flags": int(data["flags"]), "tag": data["tag"]}
        if record_type == 'cname':
            return {"cname": data["alias"]}
        if record_type == 'ds':
            return {"key_tag": int(data["key_tag"]), "algorithm": int(data["algorithm"]),
                    "digest": {"algorithm_type": int(data["digest_type"]), "value": data["digest"]}}
        if record_type == 'mx':
            return {"preference": int(data["preference"]), "exchange": data["host"]}
        if record_type == 'naptr':
            return {"order": int(data["order"]), "preference": int(data["preference"]), "flags": data["flags"],
                    "services": data["services"], "regexp": data["regexp"], "replacement": data["replacement"]}
        if record_type == 'ns':
            return {"nsdname": data["host"]}
        if record_type == 'ptr':
            return {"ptrdname": data["host"]}
        if record_type == 'soa':
            return {"host": data["host"], "email": data["email"], "serial_number": int(data["serial"]),
                    "refresh_time": data["refresh"], "retry_time": data["retry"], "expire_time": data["expire"],
                    "minimum_ttl": data["minimum"]}
        if record_type == 'srv':
            return {"priority": int(data["priority"]), "weight": int(data["weight"]), "port": int(data["port"]),
                    "target": data["target"]}
        if record_type == 'tlsa':
            return {"usage": int(data["usage"]), "selector": int(data["selector"]),
                    "matching_type": int(data["matching_type"]), "cert_association_data": data["certificate"]}
        if record_type in ['txt', 'spf']:
            text_data = data['txt']
            return {"value": text_data} if isinstance(text_data, list) else {"value": [text_data]}
        if record_type == 'alias':
            return {"id": data["resourceId"]}
    except KeyError as ke:
        raise CLIError("The {} record '{}' is missing a property.  {}"
                       .format(record_type, data['name'], ke))


# pylint: disable=too-many-statements
def import_zone(cmd, resource_group_name, zone_name, file_name):
    from azure.cli.core.util import read_file_content
    from azure.core.exceptions import HttpResponseError
    import sys
    logger.warning("In the future, zone name will be case insensitive.")

    from azure.cli.core.azclierror import FileOperationError, UnclassifiedUserFault
    try:
        file_text = read_file_content(file_name)
    except FileNotFoundError:
        raise FileOperationError("No such file: " + str(file_name))
    except IsADirectoryError:
        raise FileOperationError("Is a directory: " + str(file_name))
    except PermissionError:
        raise FileOperationError("Permission denied: " + str(file_name))
    except OSError as e:
        raise UnclassifiedUserFault(e)

    from azure.cli.command_modules.network.zone_file.parse_zone_file import parse_zone_file
    from .operations.latest.network.dns.record_set.soa._show import RecordSetSOAShow as DNSRecordSetSOAShow

    zone_obj = parse_zone_file(file_text, zone_name)

    origin = zone_name
    record_sets = {}
    for record_set_name in zone_obj:
        for record_set_type in zone_obj[record_set_name]:
            record_set_obj = zone_obj[record_set_name][record_set_type]
            if record_set_type == 'soa':
                origin = record_set_name.rstrip('.')

            if not isinstance(record_set_obj, list):
                record_set_obj = [record_set_obj]

            for entry in record_set_obj:

                record_set_ttl = entry['ttl']
                record_set_key = '{}{}'.format(record_set_name.lower(), record_set_type)
                alias_record_type = entry.get("aliasDelim", None)

                if alias_record_type:
                    alias_record_type = alias_record_type.lower()
                    record_set_key = '{}{}'.format(record_set_name.lower(), alias_record_type)

                record = _build_record(cmd, entry)

                if not record:
                    logger.warning('Cannot import %s. RecordType is not found. Skipping...', entry['delim'].lower())
                    continue

                record_set = record_sets.get(record_set_key, None)

                if not record_set:

                    # Workaround for issue #2824
                    relative_record_set_name = record_set_name.rstrip('.')
                    if not relative_record_set_name.endswith(origin):
                        logger.warning(
                            'Cannot import %s. Only records relative to origin may be '
                            'imported at this time. Skipping...', relative_record_set_name)
                        continue

                    record_set = {"ttl": record_set_ttl}
                    record_sets[record_set_key] = record_set

                _add_record(record_set, record, record_set_type,
                            is_list=record_set_type.lower() not in ['soa', 'cname', 'alias'])

    total_records = 0
    for key, rs in record_sets.items():
        rs_name, rs_type = key.lower().rsplit('.', 1)
        rs_name = rs_name[:-(len(origin) + 1)] if rs_name != origin else '@'
        try:
            records_temp = rs[_type_to_property_name(rs_type)[0]]
            record_count = len(records_temp) if isinstance(records_temp, list) else 1
        except (TypeError, KeyError):
            # There is some bug with `alias records` being mapped from `AZURE ALIAS A` to `ARecords`,
            # but `rs` does not contain `a_records`.  We could fix it, but this is just logging, so
            # lets not fail the whole import and hope someone refactors this method
            record_count = 1
        total_records += record_count
    cum_records = 0

    print('== BEGINNING ZONE IMPORT: {} ==\n'.format(zone_name), file=sys.stderr)

    from .aaz.latest.network.dns.zone._create import Create as _DNSZoneCreate

    _DNSZoneCreate(cli_ctx=cmd.cli_ctx)(command_args={
        'resource_group': resource_group_name,
        'zone_name': zone_name,
        'location': 'global'
    })

    for key, rs in record_sets.items():
        rs_name, rs_type = key.lower().rsplit('.', 1)
        rs_name = '@' if rs_name == origin else rs_name

        if rs_name.endswith(origin):
            rs_name = rs_name[:-(len(origin) + 1)]

        try:
            records_temp = rs[_type_to_property_name(rs_type)[0]]
            record_count = len(records_temp) if isinstance(records_temp, list) else 1
        except (TypeError, KeyError):
            record_count = 1

        if rs_name == '@' and rs_type == 'soa':
            root_soa = DNSRecordSetSOAShow(cli_ctx=cmd.cli_ctx)(command_args={
                'resource_group': resource_group_name,
                'zone_name': zone_name,
            })
            rs["soa_record"]["host"] = root_soa["SOARecord"]["host"]
            rs_name = '@'
        elif rs_name == '@' and rs_type == 'ns':
            _DNSRecordSetNSShow = _record_show_func('ns')
            root_ns = _DNSRecordSetNSShow(cli_ctx=cmd.cli_ctx)(command_args={
                'resource_group': resource_group_name,
                'zone_name': zone_name,
                'name': '@'
            })
            root_ns["ttl"] = rs["ttl"]
            rs = _convert_to_snake_case(root_ns)
        try:
            rs["target_resource"] = rs.get("target_resource").get("id") if rs.get("target_resource") else None
            rs["traffic_management_profile"] = rs.get("traffic_management_profile").get("id") if rs.get("traffic_management_profile") else None
            if rs_type == 'soa':
                # SOA records don't have a separate create command; use the base aaz create directly
                from .aaz.latest.network.dns.record_set._create import Create as _RecordSetCreateBase
                _RecordSetCreateBase(cli_ctx=cmd.cli_ctx)(command_args={
                    'resource_group': resource_group_name,
                    'zone_name': zone_name,
                    'name': rs_name,
                    'record_type': 'SOA',
                    **rs
                })
            else:
                _record_create = _record_create_func(rs_type)
                _record_create(cli_ctx=cmd.cli_ctx)(command_args={
                    'resource_group': resource_group_name,
                    'zone_name': zone_name,
                    'name': rs_name,
                    'record_type': rs_type.upper(),
                    **rs
                })

            cum_records += record_count
            print("({}/{}) Imported {} records of type '{}' and name '{}'"
                  .format(cum_records, total_records, record_count, rs_type, rs_name), file=sys.stderr)
        except HttpResponseError as ex:
            logger.error(ex)
    print("\n== {}/{} RECORDS IMPORTED SUCCESSFULLY: '{}' =="
          .format(cum_records, total_records, zone_name), file=sys.stderr)


def add_dns_aaaa_record(cmd, resource_group_name, zone_name, record_set_name, ipv6_address,
                        ttl=3600, if_none_match=None):
    record = {"ipv6_address": ipv6_address}
    record_type = 'aaaa'
    return _add_save_record(cmd, record, record_type, record_set_name, resource_group_name, zone_name,
                            ttl=ttl, if_none_match=if_none_match)


def add_dns_a_record(cmd, resource_group_name, zone_name, record_set_name, ipv4_address,
                     ttl=3600, if_none_match=None):
    record = {"ipv4_address": ipv4_address}
    record_type = 'a'
    return _add_save_record(cmd, record, record_type, record_set_name, resource_group_name, zone_name, 'arecords',
                            ttl=ttl, if_none_match=if_none_match)


def add_dns_caa_record(cmd, resource_group_name, zone_name, record_set_name, value, flags, tag,
                       ttl=3600, if_none_match=None):
    record = {"flags": flags, "tag": tag, "value": value}
    record_type = 'caa'
    return _add_save_record(cmd, record, record_type, record_set_name, resource_group_name, zone_name,
                            ttl=ttl, if_none_match=if_none_match)


def add_dns_cname_record(cmd, resource_group_name, zone_name, record_set_name, cname, ttl=3600, if_none_match=None):
    record = {"cname": cname}
    record_type = 'cname'
    return _add_save_record(cmd, record, record_type, record_set_name, resource_group_name, zone_name,
                            is_list=False, ttl=ttl, if_none_match=if_none_match)


def add_dns_ds_record(cmd, resource_group_name, zone_name, record_set_name, key_tag, algorithm, digest_type, digest,
                      ttl=3600, if_none_match=None):
    record = {"algorithm": algorithm, "key_tag": key_tag, "digest": {"algorithm_type": digest_type, "value": digest}}
    record_type = 'ds'
    return _add_save_record(cmd, record, record_type, record_set_name, resource_group_name, zone_name,
                            ttl=ttl, if_none_match=if_none_match)


def add_dns_mx_record(cmd, resource_group_name, zone_name, record_set_name, preference, exchange,
                      ttl=3600, if_none_match=None):
    record = {"preference": int(preference), "exchange": exchange}
    record_type = 'mx'
    return _add_save_record(cmd, record, record_type, record_set_name, resource_group_name, zone_name,
                            ttl=ttl, if_none_match=if_none_match)


def add_dns_naptr_record(cmd, resource_group_name, zone_name, record_set_name, order, preference, flags, services, regexp, replacement,
                         ttl=3600, if_none_match=None):
    record = {"flags": flags, "order": order, "preference": preference, "regexp": regexp, "replacement": replacement, "services": services}
    record_type = 'naptr'
    return _add_save_record(cmd, record, record_type, record_set_name, resource_group_name, zone_name,
                            ttl=ttl, if_none_match=if_none_match)


def add_dns_ns_record(cmd, resource_group_name, zone_name, record_set_name, dname,
                      subscription_id=None, ttl=3600, if_none_match=None):
    record = {"nsdname": dname}
    record_type = 'ns'
    return _add_save_record(cmd, record, record_type, record_set_name, resource_group_name, zone_name,
                            subscription_id=subscription_id, ttl=ttl, if_none_match=if_none_match)


def add_dns_ptr_record(cmd, resource_group_name, zone_name, record_set_name, dname, ttl=3600, if_none_match=None):
    record = {"ptrdname": dname}
    record_type = 'ptr'
    return _add_save_record(cmd, record, record_type, record_set_name, resource_group_name, zone_name,
                            ttl=ttl, if_none_match=if_none_match)


def add_dns_srv_record(cmd, resource_group_name, zone_name, record_set_name, priority, weight,
                       port, target, if_none_match=None):
    record = {"priority": priority, "weight": weight, "port": port, "target": target}
    record_type = 'srv'
    return _add_save_record(cmd, record, record_type, record_set_name, resource_group_name, zone_name,
                            if_none_match=if_none_match)


def add_dns_tlsa_record(cmd, resource_group_name, zone_name, record_set_name, certificate_usage, selector, matching_type, certificate_data,
                        ttl=3600, if_none_match=None):
    record = {"cert_association_data": certificate_data, "matching_type": matching_type, "selector": selector, "usage": certificate_usage}
    record_type = 'tlsa'
    return _add_save_record(cmd, record, record_type, record_set_name, resource_group_name, zone_name,
                            ttl=ttl, if_none_match=if_none_match)


def add_dns_txt_record(cmd, resource_group_name, zone_name, record_set_name, value, if_none_match=None):
    record = {"value": value}
    record_type = 'txt'
    long_text = ''.join(x for x in record["value"])
    original_len = len(long_text)
    record["value"] = []
    while len(long_text) > 255:
        record["value"].append(long_text[:255])
        long_text = long_text[255:]
    record["value"].append(long_text)
    final_str = ''.join(record["value"])
    final_len = len(final_str)
    assert original_len == final_len
    return _add_save_record(cmd, record, record_type, record_set_name, resource_group_name, zone_name,
                            if_none_match=if_none_match)


def remove_dns_aaaa_record(cmd, resource_group_name, zone_name, record_set_name, ipv6_address,
                           keep_empty_record_set=False):
    record = {"ipv6_address": ipv6_address}
    record_type = 'aaaa'
    return _remove_record(cmd.cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name,
                          keep_empty_record_set=keep_empty_record_set)


def remove_dns_a_record(cmd, resource_group_name, zone_name, record_set_name, ipv4_address,
                        keep_empty_record_set=False):
    record = {"ipv4_address": ipv4_address}
    record_type = 'a'
    return _remove_record(cmd.cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name,
                          keep_empty_record_set=keep_empty_record_set)


def remove_dns_caa_record(cmd, resource_group_name, zone_name, record_set_name, value,
                          flags, tag, keep_empty_record_set=False):
    record = {"flags": flags, "tag": tag, "value": value}
    record_type = 'caa'
    return _remove_record(cmd.cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name,
                          keep_empty_record_set=keep_empty_record_set)


def remove_dns_cname_record(cmd, resource_group_name, zone_name, record_set_name, cname,
                            keep_empty_record_set=False):
    record = {"cname": cname}
    record_type = 'cname'
    return _remove_record(cmd.cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name,
                          is_list=False, keep_empty_record_set=keep_empty_record_set)


def remove_dns_ds_record(cmd, resource_group_name, zone_name, record_set_name, key_tag, algorithm, digest_type, digest, keep_empty_record_set=False):
    record = {"algorithm": algorithm, "key_tag": key_tag, "digest": {"algorithm_type": digest_type, "value": digest}}
    record_type = 'ds'
    return _remove_record(cmd.cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name,
                          keep_empty_record_set=keep_empty_record_set)


def remove_dns_mx_record(cmd, resource_group_name, zone_name, record_set_name, preference, exchange,
                         keep_empty_record_set=False):
    record = {"preference": int(preference), "exchange": exchange}
    record_type = 'mx'
    return _remove_record(cmd.cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name,
                          keep_empty_record_set=keep_empty_record_set)


def remove_dns_naptr_record(cmd, resource_group_name, zone_name, record_set_name, order, preference, flags, services, regexp, replacement, keep_empty_record_set=False):
    record = {"flags": flags, "order": order, "preference": preference, "regexp": regexp, "replacement": replacement, "services": services}
    record_type = 'naptr'
    return _remove_record(cmd.cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name,
                          keep_empty_record_set=keep_empty_record_set)


def remove_dns_ns_record(cmd, resource_group_name, zone_name, record_set_name, dname,
                         keep_empty_record_set=False):
    record = {"nsdname": dname}
    record_type = 'ns'
    return _remove_record(cmd.cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name,
                          keep_empty_record_set=keep_empty_record_set)


def remove_dns_ptr_record(cmd, resource_group_name, zone_name, record_set_name, dname,
                          keep_empty_record_set=False):
    record = {"ptrdname": dname}
    record_type = 'ptr'
    return _remove_record(cmd.cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name,
                          keep_empty_record_set=keep_empty_record_set)


def remove_dns_srv_record(cmd, resource_group_name, zone_name, record_set_name, priority, weight,
                          port, target, keep_empty_record_set=False):
    record = {"priority": priority, "weight": weight, "port": port, "target": target}
    record_type = 'srv'
    return _remove_record(cmd.cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name,
                          keep_empty_record_set=keep_empty_record_set)


def remove_dns_tlsa_record(cmd, resource_group_name, zone_name, record_set_name, certificate_usage, selector, matching_type, certificate_data, keep_empty_record_set=False):
    record = {"cert_association_data": certificate_data, "matching_type": matching_type, "selector": selector, "usage": certificate_usage}
    record_type = 'tlsa'
    return _remove_record(cmd.cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name,
                          keep_empty_record_set=keep_empty_record_set)


def remove_dns_txt_record(cmd, resource_group_name, zone_name, record_set_name, value,
                          keep_empty_record_set=False):
    record = {"value": value}
    record_type = 'txt'
    return _remove_record(cmd.cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name,
                          keep_empty_record_set=keep_empty_record_set)


def _check_a_record_exist(record, exist_list):
    for r in exist_list:
        if r["ipv4_address"] == record["ipv4_address"]:
            return True
    return False


def _check_aaaa_record_exist(record, exist_list):
    for r in exist_list:
        if r["ipv6_address"] == record["ipv6_address"]:
            return True
    return False


def _check_caa_record_exist(record, exist_list):
    for r in exist_list:
        if (r["flags"], r["tag"], r["value"]) == (record["flags"], record["tag"], record["value"]):
            return True
    return False


def _check_cname_record_exist(record, exist_list):
    for r in exist_list:
        if r["cname"] == record["cname"]:
            return True
    return False


def _check_ds_record_exist(record, exist_list):
    for r in exist_list:
        if (r["algorithm"], r["key_tag"], r["digest"]["algorithm_type"], r["digest"]["value"]) == (record["algorithm"], record["key_tag"], record["digest"]["algorithm_type"], record["digest"]["value"]):
            return True
    return False


def _check_mx_record_exist(record, exist_list):
    for r in exist_list:
        if (r["preference"], r["exchange"]) == (record["preference"], record["exchange"]):
            return True
    return False


def _check_naptr_record_exist(record, exist_list):
    for r in exist_list:
        if (r["flags"], r["order"], r["preference"], r["regexp"], r["replacement"], r["services"]) == (record["flags"], record["order"], record["preference"], record["regexp"], record["replacement"], record["services"]):
            return True
    return False


def _check_ns_record_exist(record, exist_list):
    for r in exist_list:
        if r["nsdname"] == record["nsdname"]:
            return True
    return False


def _check_ptr_record_exist(record, exist_list):
    for r in exist_list:
        if r["ptrdname"] == record["ptrdname"]:
            return True
    return False


def _check_srv_record_exist(record, exist_list):
    for r in exist_list:
        if (r["priority"], r["weight"], r["port"], r["target"]) == (record["priority"], record["weight"], record["port"], record["target"]):
            return True
    return False


def _check_tlsa_record_exist(record, exist_list):
    for r in exist_list:
        if (r["cert_association_data"], r["matching_type"], r["selector"], r["usage"]) == (record["cert_association_data"], record["matching_type"], record["selector"], record["usage"]):
            return True
    return False


def _check_txt_record_exist(record, exist_list):
    for r in exist_list:
        if r["value"] == record["value"]:
            return True
    return False


def _record_exist_func(record_type):
    return globals()["_check_{}_record_exist".format(record_type)]


def _add_record(record_set, record, record_type, is_list=False):
    record_property, _ = _type_to_property_name(record_type)

    if is_list:
        record_list = record_set.get(record_property, None)
        if record_list is None:
            record_set[record_property] = []
            record_list = []

        _record_exist = _record_exist_func(record_type)
        if not _record_exist(record, record_list):
            record_set[record_property].append(record)
    else:
        record_set[record_property] = record


def _dns_record_set_import(record_type, operation):
    """Dynamically import a DNS record set command class from the operations module."""
    import importlib
    rt = record_type.lower()
    op = operation.lower()
    module_path = f"azure.cli.command_modules.network.operations.latest.network.dns.record_set.{rt}._{op}"
    class_name = f"RecordSet{record_type.upper()}{operation.capitalize()}"
    mod = importlib.import_module(module_path)
    return getattr(mod, class_name)


def _record_show_func(record_type):
    return _dns_record_set_import(record_type, "show")


def _record_create_func(record_type):
    return _dns_record_set_import(record_type, "create")


def _record_delete_func(record_type):
    return _dns_record_set_import(record_type, "delete")


def _record_update_func(record_type):
    return _dns_record_set_import(record_type, "update")


def _add_save_record(cmd, record, record_type, record_set_name, resource_group_name, zone_name,
                     is_list=True, subscription_id=None, ttl=None, if_none_match=None):
    from azure.core.exceptions import HttpResponseError

    record_snake, record_camel = _type_to_property_name(record_type)
    try:
        _record_show = _record_show_func(record_type)
        ret = _record_show(cli_ctx=cmd.cli_ctx)(command_args={
            "name": record_set_name,
            "zone_name": zone_name,
            "subscription": subscription_id,
            "resource_group": resource_group_name
        })
        record_set = {}
        record_set["ttl"] = ret.get("TTL", None)
        record_set[record_snake] = ret.get(record_camel, None)
        record_set = _convert_to_snake_case(record_set)
    except HttpResponseError:
        record_set = {"ttl": 3600}

    if ttl is not None:
        record_set["ttl"] = ttl

    _add_record(record_set, record, record_type, is_list)

    record_set["target_resource"] = record_set.get("target_resource").get("id") if record_set.get("target_resource") else None
    _record_create = _record_create_func(record_type)
    return _record_create(cli_ctx=cmd.cli_ctx)(command_args={
        "name": record_set_name,
        "zone_name": zone_name,
        "subscription": subscription_id,
        "resource_group": resource_group_name,
        "if_none_match": "*" if if_none_match else None,
        **record_set
    })


def _remove_record(cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name,
                   keep_empty_record_set, is_list=True):
    record_snake, record_camel = _type_to_property_name(record_type)

    _record_show = _record_show_func(record_type)
    ret = _record_show(cli_ctx=cli_ctx)(command_args={
        "name": record_set_name,
        "zone_name": zone_name,
        "resource_group": resource_group_name,
        "record_type": record_type
    })
    record_set = {}
    record_set["ttl"] = ret.get("TTL", None)
    record_set[record_snake] = ret.get(record_camel, None)
    record_set = _convert_to_snake_case(record_set)

    logger.debug('Retrieved record: %s', str(record_set))

    if is_list:
        record_list = record_set[record_snake]
        if record_list is not None:
            keep_list = [r for r in record_list if not dict_matches_filter(r, record)]
            if len(keep_list) == len(record_list):
                raise CLIError('Record {} not found.'.format(str(record)))

            record_set[record_snake] = keep_list
    else:
        record_set[record_snake] = None

    if is_list:
        records_remaining = len(record_set[record_snake]) if record_set[record_snake] is not None else 0
    else:
        records_remaining = 1 if record_set[record_snake] is not None else 0

    if not records_remaining and not keep_empty_record_set:
        logger.info('Removing empty %s record set: %s', record_type, record_set_name)

        _record_delete = _record_delete_func(record_type)
        return _record_delete(cli_ctx=cli_ctx)(command_args={
            "name": record_set_name,
            "zone_name": zone_name,
            "resource_group": resource_group_name
        })

    _record_update = _record_update_func(record_type)
    return _record_update(cli_ctx=cli_ctx)(command_args={
        "name": record_set_name,
        "zone_name": zone_name,
        "resource_group": resource_group_name,
        **record_set
    })


def dict_matches_filter(d, filter_dict):
    sentinel = object()
    return all(not filter_dict.get(key, None) or
               str(filter_dict[key]) == str(d.get(key, sentinel)) or
               lists_match(filter_dict[key], d.get(key, []))
               for key in filter_dict)


def lists_match(l1, l2):
    try:
        return Counter(l1) == Counter(l2)  # pylint: disable=too-many-function-args
    except TypeError:
        return False
# endregion


# region ExpressRoutes


def _validate_ipv6_address_prefixes(prefixes):
    from ipaddress import ip_network, IPv6Network
    prefixes = prefixes if isinstance(prefixes, list) else [prefixes]
    version = None
    for prefix in prefixes:
        try:
            network = ip_network(prefix)
            if version is None:
                version = type(network)
            else:
                if not isinstance(network, version):  # pylint: disable=isinstance-second-argument-not-valid-type
                    raise CLIError("usage error: '{}' incompatible mix of IPv4 and IPv6 address prefixes."
                                   .format(prefixes))
        except ValueError:
            raise CLIError("usage error: prefix '{}' is not recognized as an IPv4 or IPv6 address prefix."
                           .format(prefix))
    return version == IPv6Network


# endregion


# region ExpressRoute Connection
# pylint: disable=unused-argument


# pylint: disable=unused-argument
# endregion


# region ExpressRoute ports
def update_express_route_port(cmd, instance, tags=None):
    with cmd.update_context(instance) as c:
        c.set_param('tags', tags, True)
    return instance


def download_generated_loa_as_pdf(cmd,
                                  resource_group_name,
                                  express_route_port_name,
                                  customer_name,
                                  file_path='loa.pdf'):
    import os
    import base64

    dirname, basename = os.path.dirname(file_path), os.path.basename(file_path)

    if basename == '':
        basename = 'loa.pdf'
    elif basename.endswith('.pdf') is False:
        basename = basename + '.pdf'

    file_path = os.path.join(dirname, basename)
    from .aaz.latest.network.express_route.port._generate_loa import GenerateLoa
    response = GenerateLoa(cli_ctx=cmd.cli_ctx)(command_args={'resource_group': resource_group_name,
                                                              'name': express_route_port_name,
                                                              'customer_name': customer_name})

    encoded_content = base64.b64decode(response['encodedContent'])

    from azure.cli.core.azclierror import FileOperationError
    try:
        with open(file_path, 'wb') as f:
            f.write(encoded_content)
    except OSError as ex:
        raise FileOperationError(ex)

    logger.warning("The generated letter of authorization is saved at %s", file_path)


# endregion


# region PrivateEndpoint


# endregion


# region PrivateLinkService


# endregion


# region LoadBalancers
def _get_lb_create_aux_subscriptions(public_ip_address, subnet):
    aux_subscriptions = []
    _add_aux_subscription(aux_subscriptions, public_ip_address)
    _add_aux_subscription(aux_subscriptions, subnet)
    return aux_subscriptions


def create_load_balancer(cmd, load_balancer_name, resource_group_name, location=None, tags=None,
                         backend_pool_name=None, frontend_ip_name='LoadBalancerFrontEnd',
                         private_ip_address=None, public_ip_address=None,
                         public_ip_address_allocation=None,
                         public_ip_dns_name=None, subnet=None, subnet_address_prefix='10.0.0.0/24',
                         virtual_network_name=None, vnet_address_prefix='10.0.0.0/16',
                         public_ip_address_type=None, subnet_type=None, validate=False,
                         no_wait=False, sku=None, frontend_ip_zone=None, public_ip_zone=None,
                         private_ip_address_version=None, edge_zone=None):
    from azure.cli.core.util import random_string
    from azure.cli.core.commands.arm import ArmTemplateBuilder
    from azure.cli.command_modules.network._template_builder import (
        build_load_balancer_resource, build_public_ip_resource, build_vnet_resource)

    DeploymentProperties = cmd.get_models('DeploymentProperties', resource_type=ResourceType.MGMT_RESOURCE_RESOURCES)
    aux_subscriptions = _get_lb_create_aux_subscriptions(public_ip_address, subnet)

    if public_ip_address is None:
        logger.warning(
            "Please note that the default public IP used for creation will be changed from Basic to Standard "
            "in the future."
        )

    if sku.lower() == "basic":
        logger.warning(remove_basic_option_msg, "--sku standard")

    tags = tags or {}
    public_ip_address = public_ip_address or 'PublicIP{}'.format(load_balancer_name)
    backend_pool_name = backend_pool_name or '{}bepool'.format(load_balancer_name)
    if not public_ip_address_allocation:
        public_ip_address_allocation = 'Static' if (sku and sku.lower() == 'standard') else 'Dynamic'

    # Build up the ARM template
    master_template = ArmTemplateBuilder()
    lb_dependencies = []

    public_ip_id = public_ip_address if is_valid_resource_id(public_ip_address) else None
    subnet_id = subnet if is_valid_resource_id(subnet) else None
    private_ip_allocation = 'Static' if private_ip_address else 'Dynamic'

    network_id_template = resource_id(
        subscription=get_subscription_id(cmd.cli_ctx), resource_group=resource_group_name,
        namespace='Microsoft.Network')

    if edge_zone:
        edge_zone_type = 'EdgeZone'
    else:
        edge_zone_type = None

    if subnet_type == 'new':
        lb_dependencies.append('Microsoft.Network/virtualNetworks/{}'.format(virtual_network_name))
        vnet = build_vnet_resource(
            cmd, virtual_network_name, location, tags, vnet_address_prefix, subnet,
            subnet_address_prefix)
        master_template.add_resource(vnet)
        subnet_id = '{}/virtualNetworks/{}/subnets/{}'.format(
            network_id_template, virtual_network_name, subnet)

    if public_ip_address_type == 'new':
        lb_dependencies.append('Microsoft.Network/publicIpAddresses/{}'.format(public_ip_address))
        master_template.add_resource(build_public_ip_resource(cmd, public_ip_address, location,
                                                              tags,
                                                              public_ip_address_allocation,
                                                              public_ip_dns_name,
                                                              sku, public_ip_zone, None, edge_zone, edge_zone_type))
        public_ip_id = '{}/publicIPAddresses/{}'.format(network_id_template,
                                                        public_ip_address)

    load_balancer_resource = build_load_balancer_resource(
        cmd, load_balancer_name, location, tags, backend_pool_name, frontend_ip_name,
        public_ip_id, subnet_id, private_ip_address, private_ip_allocation, sku,
        frontend_ip_zone, private_ip_address_version, None, edge_zone, edge_zone_type)
    load_balancer_resource['dependsOn'] = lb_dependencies
    master_template.add_resource(load_balancer_resource)
    master_template.add_output('loadBalancer', load_balancer_name, output_type='object')

    template = master_template.build()

    # deploy ARM template
    deployment_name = 'lb_deploy_' + random_string(32)
    client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES, aux_subscriptions=aux_subscriptions).deployments
    properties = DeploymentProperties(template=template, parameters={}, mode='incremental')
    Deployment = cmd.get_models('Deployment', resource_type=ResourceType.MGMT_RESOURCE_RESOURCES)
    deployment = Deployment(properties=properties)

    if validate:
        _log_pprint_template(template)
        if cmd.supported_api_version(min_api='2019-10-01', resource_type=ResourceType.MGMT_RESOURCE_RESOURCES):
            from azure.cli.core.commands import LongRunningOperation
            validation_poller = client.begin_validate(resource_group_name, deployment_name, deployment)
            return LongRunningOperation(cmd.cli_ctx)(validation_poller)

        return client.validate(resource_group_name, deployment_name, deployment)

    return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name, deployment_name, deployment)


def list_load_balancer_mapping(cmd, resource_group_name, load_balancer_name, backend_pool_name, request):
    args = {
        "resource_group": resource_group_name,
        "name": load_balancer_name,
        "backend_pool_name": backend_pool_name
    }
    if 'ip_configuration' in request:
        args["ip_configuration"] = {'id': request['ip_configuration']}
    if 'ip_address' in request:
        args["ip_address"] = request['ip_address']
    from .aaz.latest.network.lb._list_mapping import ListMapping
    return ListMapping(cli_ctx=cmd.cli_ctx)(command_args=args)


# workaround for : https://github.com/Azure/azure-cli/issues/17071
def lb_get(client, resource_group_name, load_balancer_name):
    lb = client.get(resource_group_name, load_balancer_name)
    return lb_get_operation(lb)


# workaround for : https://github.com/Azure/azure-cli/issues/17071
def lb_get_operation(lb):
    for item in lb.frontend_ip_configurations:
        if item.zones is not None and len(item.zones) >= 3 and item.subnet is None:
            item.zones = None

    return lb


def _process_vnet_name_and_id(vnet, cmd, resource_group_name):
    if vnet and not is_valid_resource_id(vnet):
        vnet = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=resource_group_name,
            namespace='Microsoft.Network',
            type='virtualNetworks',
            name=vnet)
    return vnet


def _process_subnet_name_and_id(subnet, vnet, cmd, resource_group_name):
    if subnet and not is_valid_resource_id(subnet):
        vnet = _process_vnet_name_and_id(vnet, cmd, resource_group_name)
        if vnet is None:
            raise UnrecognizedArgumentError('vnet should be provided when input subnet name instead of subnet id')

        subnet = vnet + f'/subnets/{subnet}'
    return subnet
# endregion


# region cross-region lb
def create_cross_region_load_balancer(cmd, load_balancer_name, resource_group_name, location=None, tags=None,
                                      backend_pool_name=None, frontend_ip_name='LoadBalancerFrontEnd',
                                      public_ip_address=None, public_ip_address_allocation=None,
                                      public_ip_dns_name=None, public_ip_address_type=None, validate=False,
                                      no_wait=False, frontend_ip_zone=None, public_ip_zone=None):
    from azure.cli.core.util import random_string
    from azure.cli.core.commands.arm import ArmTemplateBuilder
    from azure.cli.command_modules.network._template_builder import (
        build_load_balancer_resource, build_public_ip_resource)

    DeploymentProperties = cmd.get_models('DeploymentProperties', resource_type=ResourceType.MGMT_RESOURCE_RESOURCES)

    sku = 'standard'
    tier = 'Global'

    tags = tags or {}
    public_ip_address = public_ip_address or 'PublicIP{}'.format(load_balancer_name)
    backend_pool_name = backend_pool_name or '{}bepool'.format(load_balancer_name)
    if not public_ip_address_allocation:
        public_ip_address_allocation = 'Static' if (sku and sku.lower() == 'standard') else 'Dynamic'

    # Build up the ARM template
    master_template = ArmTemplateBuilder()
    lb_dependencies = []

    public_ip_id = public_ip_address if is_valid_resource_id(public_ip_address) else None

    network_id_template = resource_id(
        subscription=get_subscription_id(cmd.cli_ctx), resource_group=resource_group_name,
        namespace='Microsoft.Network')

    if public_ip_address_type == 'new':
        lb_dependencies.append('Microsoft.Network/publicIpAddresses/{}'.format(public_ip_address))
        master_template.add_resource(build_public_ip_resource(cmd, public_ip_address, location,
                                                              tags,
                                                              public_ip_address_allocation,
                                                              public_ip_dns_name,
                                                              sku, public_ip_zone, tier))
        public_ip_id = '{}/publicIPAddresses/{}'.format(network_id_template,
                                                        public_ip_address)

    load_balancer_resource = build_load_balancer_resource(
        cmd, load_balancer_name, location, tags, backend_pool_name, frontend_ip_name,
        public_ip_id, None, None, None, sku, frontend_ip_zone, None, tier)
    load_balancer_resource['dependsOn'] = lb_dependencies
    master_template.add_resource(load_balancer_resource)
    master_template.add_output('loadBalancer', load_balancer_name, output_type='object')

    template = master_template.build()

    # deploy ARM template
    deployment_name = 'lb_deploy_' + random_string(32)
    client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES).deployments
    properties = DeploymentProperties(template=template, parameters={}, mode='incremental')
    Deployment = cmd.get_models('Deployment', resource_type=ResourceType.MGMT_RESOURCE_RESOURCES)
    deployment = Deployment(properties=properties)

    if validate:
        _log_pprint_template(template)
        if cmd.supported_api_version(min_api='2019-10-01', resource_type=ResourceType.MGMT_RESOURCE_RESOURCES):
            from azure.cli.core.commands import LongRunningOperation
            validation_poller = client.begin_validate(resource_group_name, deployment_name, deployment)
            return LongRunningOperation(cmd.cli_ctx)(validation_poller)

        return client.validate(resource_group_name, deployment_name, deployment)

    return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name, deployment_name, deployment)
# endregion


# region NetworkInterfaces (NIC)


def _get_nic_ip_config(nic, name):
    if nic.ip_configurations:
        ip_config = next(
            (x for x in nic.ip_configurations if x.name.lower() == name.lower()), None)
    else:
        ip_config = None
    if not ip_config:
        raise CLIError('IP configuration {} not found.'.format(name))
    return ip_config


def add_nic_ip_config_address_pool(cmd, resource_group_name, network_interface_name, ip_config_name,
                                   backend_address_pool, load_balancer_name=None, application_gateway_name=None):
    from .aaz.latest.network.nic.ip_config.lb_pool._add import Add as _LBPoolAdd
    from .aaz.latest.network.nic.ip_config.ag_pool._add import Add as _AGPoolAdd

    class LBPoolAdd(_LBPoolAdd):
        def _output(self, *args, **kwargs):
            result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
            return result["ipConfigurations"][0]

    class AGPoolAdd(_AGPoolAdd):
        def _output(self, *args, **kwargs):
            result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
            return result["ipConfigurations"][0]

    arguments = {
        "ip_config_name": ip_config_name,
        "nic_name": network_interface_name,
        "resource_group": resource_group_name,
        "pool_id": backend_address_pool
    }
    if load_balancer_name:
        return LBPoolAdd(cli_ctx=cmd.cli_ctx)(command_args=arguments)
    if application_gateway_name:
        return AGPoolAdd(cli_ctx=cmd.cli_ctx)(command_args=arguments)


def remove_nic_ip_config_address_pool(cmd, resource_group_name, network_interface_name, ip_config_name,
                                      backend_address_pool, load_balancer_name=None, application_gateway_name=None):
    from .aaz.latest.network.nic.ip_config.lb_pool._remove import Remove as LBPoolRemove
    from .aaz.latest.network.nic.ip_config.ag_pool._remove import Remove as AGPoolRemove

    arguments = {
        "ip_config_name": ip_config_name,
        "nic_name": network_interface_name,
        "resource_group": resource_group_name,
        "pool_id": backend_address_pool
    }
    if load_balancer_name:
        return LBPoolRemove(cli_ctx=cmd.cli_ctx)(command_args=arguments)
    if application_gateway_name:
        return AGPoolRemove(cli_ctx=cmd.cli_ctx)(command_args=arguments)


# endregion


# region NetworkSecurityGroups
def _handle_plural_or_singular(args, plural_name, singular_name):
    values = getattr(args, plural_name)
    if not has_value(values):
        return

    setattr(args, plural_name, values if len(values) > 1 else None)
    setattr(args, singular_name, values[0] if len(values) == 1 else None)


def list_nsg_rules(cmd, resource_group_name, network_security_group_name, include_default=False):
    from .aaz.latest.network.nsg._show import Show
    nsg = Show(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "name": network_security_group_name
    })

    rules = nsg["securityRules"]
    return rules + nsg["defaultSecurityRules"] if include_default else rules
# endregion


# region NetworkWatchers
def _create_network_watchers(cmd, resource_group_name, locations, tags):
    if resource_group_name is None:
        raise CLIError("usage error: '--resource-group' required when enabling new regions")

    from .aaz.latest.network.watcher._create import Create
    for location in locations:
        Create(cli_ctx=cmd.cli_ctx)(command_args={
            'name': 'NetworkWatcher_{}'.format(location),
            'resource_group': resource_group_name,
            'location': location,
            'tags': tags
        })


def _update_network_watchers(cmd, watchers, tags):
    from .aaz.latest.network.watcher._update import Update
    for watcher in watchers:
        id_parts = parse_resource_id(watcher['id'])
        watcher_rg = id_parts['resource_group']
        watcher_name = id_parts['name']
        watcher_tags = watcher.get('tag', None) if tags is None else tags
        Update(cli_ctx=cmd.cli_ctx)(command_args={
            'name': watcher_name,
            'resource_group': watcher_rg,
            'location': watcher['location'],
            'tags': watcher_tags
        })


def _delete_network_watchers(cmd, watchers):
    from .aaz.latest.network.watcher._delete import Delete
    for watcher in watchers:
        from azure.cli.core.commands import LongRunningOperation
        id_parts = parse_resource_id(watcher['id'])
        watcher_rg = id_parts['resource_group']
        watcher_name = id_parts['name']
        logger.warning(
            "Disabling Network Watcher for region '%s' by deleting resource '%s'",
            watcher['location'], watcher['id'])
        poller = Delete(cli_ctx=cmd.cli_ctx)(command_args={
            'name': watcher_name,
            'resource_group': watcher_rg
        })
        LongRunningOperation(cmd.cli_ctx)(poller)


def configure_network_watcher(cmd, locations, resource_group_name=None, enabled=None, tags=None):
    from .aaz.latest.network.watcher._list import List
    watcher_list = List(cli_ctx=cmd.cli_ctx)(command_args={})
    locations_list = [location.lower() for location in locations]
    existing_watchers = [w for w in watcher_list if w["location"] in locations_list]
    nonenabled_regions = list(set(locations) - set(watcher["location"] for watcher in existing_watchers))

    if enabled is None:
        if resource_group_name is not None:
            logger.warning(
                "Resource group '%s' is only used when enabling new regions and will be ignored.",
                resource_group_name)
        for location in nonenabled_regions:
            logger.warning(
                "Region '%s' is not enabled for Network Watcher and will be ignored.", location)
        _update_network_watchers(cmd, existing_watchers, tags)

    elif enabled:
        _create_network_watchers(cmd, resource_group_name, nonenabled_regions, tags)
        _update_network_watchers(cmd, existing_watchers, tags)

    else:
        if tags is not None:
            raise CLIError("usage error: '--tags' cannot be used when disabling regions")
        _delete_network_watchers(cmd, existing_watchers)

    return List(cli_ctx=cmd.cli_ctx)(command_args={})


def remove_nw_connection_monitor_v2_endpoint(client,
                                             watcher_rg,
                                             watcher_name,
                                             connection_monitor_name,
                                             location,
                                             name,
                                             test_groups=None):
    connection_monitor = client.get(watcher_rg, watcher_name, connection_monitor_name)

    # refresh endpoints
    new_endpoints = [endpoint for endpoint in connection_monitor.endpoints if endpoint.name != name]
    connection_monitor.endpoints = new_endpoints

    # refresh test groups
    if test_groups is not None:
        temp_test_groups = [t for t in connection_monitor.test_groups if t.name in test_groups]
    else:
        temp_test_groups = connection_monitor.test_groups

    for test_group in temp_test_groups:
        if name in test_group.sources:
            test_group.sources.remove(name)
        if name in test_group.destinations:
            test_group.destinations.remove(name)

    return client.begin_create_or_update(watcher_rg, watcher_name, connection_monitor_name, connection_monitor)


def show_nw_connection_monitor_v2_endpoint(client,
                                           watcher_rg,
                                           watcher_name,
                                           connection_monitor_name,
                                           location,
                                           name):
    connection_monitor = client.get(watcher_rg, watcher_name, connection_monitor_name)

    for endpoint in connection_monitor.endpoints:
        if endpoint.name == name:
            return endpoint

    raise CLIError('unknown endpoint: {}'.format(name))


def list_nw_connection_monitor_v2_endpoint(client,
                                           watcher_rg,
                                           watcher_name,
                                           connection_monitor_name,
                                           location):
    connection_monitor = client.get(watcher_rg, watcher_name, connection_monitor_name)
    return connection_monitor.endpoints


def remove_nw_connection_monitor_v2_test_configuration(client,
                                                       watcher_rg,
                                                       watcher_name,
                                                       connection_monitor_name,
                                                       location,
                                                       name,
                                                       test_groups=None):
    connection_monitor = client.get(watcher_rg, watcher_name, connection_monitor_name)

    # refresh test configurations
    new_test_configurations = [t for t in connection_monitor.test_configurations if t.name != name]
    connection_monitor.test_configurations = new_test_configurations

    if test_groups is not None:
        temp_test_groups = [t for t in connection_monitor.test_groups if t.name in test_groups]
    else:
        temp_test_groups = connection_monitor.test_groups

    # refresh test groups
    for test_group in temp_test_groups:
        test_group.test_configurations.remove(name)

    return client.begin_create_or_update(watcher_rg, watcher_name, connection_monitor_name, connection_monitor)


def show_nw_connection_monitor_v2_test_configuration(client,
                                                     watcher_rg,
                                                     watcher_name,
                                                     connection_monitor_name,
                                                     location,
                                                     name):
    connection_monitor = client.get(watcher_rg, watcher_name, connection_monitor_name)

    for test_config in connection_monitor.test_configurations:
        if test_config.name == name:
            return test_config

    raise CLIError('unknown test configuration: {}'.format(name))


def list_nw_connection_monitor_v2_test_configuration(client,
                                                     watcher_rg,
                                                     watcher_name,
                                                     connection_monitor_name,
                                                     location):
    connection_monitor = client.get(watcher_rg, watcher_name, connection_monitor_name)
    return connection_monitor.test_configurations


def remove_nw_connection_monitor_v2_test_group(client,
                                               watcher_rg,
                                               watcher_name,
                                               connection_monitor_name,
                                               location,
                                               name):
    connection_monitor = client.get(watcher_rg, watcher_name, connection_monitor_name)

    new_test_groups, removed_test_group = [], None
    for t in connection_monitor.test_groups:
        if t.name == name:
            removed_test_group = t
        else:
            new_test_groups.append(t)

    if removed_test_group is None:
        raise CLIError('test group: "{}" not exist'.format(name))
    connection_monitor.test_groups = new_test_groups

    # deal with endpoints which are only referenced by this removed test group
    removed_endpoints = []
    for e in removed_test_group.sources + removed_test_group.destinations:
        tmp = [t for t in connection_monitor.test_groups if (e in t.sources or e in t.destinations)]
        if not tmp:
            removed_endpoints.append(e)
    connection_monitor.endpoints = [e for e in connection_monitor.endpoints if e.name not in removed_endpoints]

    # deal with test configurations which are only referenced by this remove test group
    removed_test_configurations = []
    for c in removed_test_group.test_configurations:
        tmp = [t for t in connection_monitor.test_groups if c in t.test_configurations]
        if not tmp:
            removed_test_configurations.append(c)
    connection_monitor.test_configurations = [c for c in connection_monitor.test_configurations
                                              if c.name not in removed_test_configurations]

    return client.begin_create_or_update(watcher_rg, watcher_name, connection_monitor_name, connection_monitor)


def show_nw_connection_monitor_v2_test_group(client,
                                             watcher_rg,
                                             watcher_name,
                                             connection_monitor_name,
                                             location,
                                             name):
    connection_monitor = client.get(watcher_rg, watcher_name, connection_monitor_name)

    for t in connection_monitor.test_groups:
        if t.name == name:
            return t

    raise CLIError('unknown test group: {}'.format(name))


def list_nw_connection_monitor_v2_test_group(client,
                                             watcher_rg,
                                             watcher_name,
                                             connection_monitor_name,
                                             location):
    connection_monitor = client.get(watcher_rg, watcher_name, connection_monitor_name)
    return connection_monitor.test_groups


# combination of resource_group_name and nsg is for old output
# combination of location and flow_log_name is for new output
def show_nw_flow_logging(cmd, watcher_rg, watcher_name, location=None, resource_group_name=None, nsg=None,
                         flow_log_name=None):
    # deprecated approach to show flow log
    if nsg is not None:
        from .aaz.latest.network.watcher.flow_log._configure_flow_log import ConfigureFlowLog
        return ConfigureFlowLog(cli_ctx=cmd.cli_ctx)(command_args={"network_watcher_name": watcher_name,
                                                                   "resource_group": watcher_rg,
                                                                   "target_resource_id": nsg})

    # new approach to show flow log
    from .aaz.latest.network.watcher.flow_log._show import Show
    return Show(cli_ctx=cmd.cli_ctx)(command_args={"network_watcher_name": watcher_name,
                                                   "resource_group": watcher_rg,
                                                   "name": flow_log_name})


def update_nw_flow_log_getter(client, watcher_rg, watcher_name, flow_log_name):
    return client.get(watcher_rg, watcher_name, flow_log_name)


def update_nw_flow_log_setter(client, watcher_rg, watcher_name, flow_log_name, parameters):
    return client.begin_create_or_update(watcher_rg, watcher_name, flow_log_name, parameters)
# endregion


# region PublicIPAddresses
def create_public_ip(cmd, resource_group_name, public_ip_address_name, location=None, tags=None,
                     allocation_method=None, dns_name=None, dns_name_scope=None,
                     idle_timeout=4, reverse_fqdn=None, version=None, sku=None, tier=None, zone=None, ip_tags=None,
                     public_ip_prefix=None, edge_zone=None, ip_address=None,
                     protection_mode=None, ddos_protection_plan=None):
    public_ip_args = {
        'name': public_ip_address_name,
        "resource_group": resource_group_name,
        'location': location,
        'tags': tags,
        'allocation_method': allocation_method,
        'idle_timeout': idle_timeout,
        'ip_address': ip_address,
        'ip_tags': ip_tags
    }

    if public_ip_prefix:
        metadata = parse_resource_id(public_ip_prefix)
        resource_group_name = metadata["resource_group"]
        public_ip_prefix_name = metadata["resource_name"]
        public_ip_args["public_ip_prefix"] = public_ip_prefix

        # reuse prefix information
        from .aaz.latest.network.public_ip.prefix._show import Show
        pip_obj = Show(cli_ctx=cmd.cli_ctx)(command_args={'resource_group': resource_group_name, 'name': public_ip_prefix_name})
        version = pip_obj['publicIPAddressVersion']
        sku = pip_obj['sku']['name']
        tier = pip_obj['sku']['tier']
        zone = pip_obj['zones'] if 'zones' in pip_obj else None

    if sku.lower() == "basic":
        logger.warning(remove_basic_option_msg, "--sku standard")

    if not allocation_method:
        if sku and sku.lower() == 'standard':
            public_ip_args['allocation_method'] = 'Static'
        else:
            public_ip_args['allocation_method'] = 'Dynamic'

    public_ip_args['version'] = version
    public_ip_args['zone'] = zone

    if sku:
        public_ip_args['sku'] = sku
    if tier:
        if not sku:
            public_ip_args['sku'] = 'Basic'
        public_ip_args['tier'] = tier

    if dns_name or dns_name_scope or reverse_fqdn:
        public_ip_args['dns_name'] = dns_name
        public_ip_args['dns_name_scope'] = dns_name_scope
        public_ip_args['reverse_fqdn'] = reverse_fqdn

    if edge_zone:
        public_ip_args['edge_zone'] = edge_zone
        public_ip_args['type'] = 'EdgeZone'
    if protection_mode:
        public_ip_args['ddos_protection_mode'] = protection_mode
    if ddos_protection_plan:
        public_ip_args['ddos_protection_plan'] = ddos_protection_plan

    from .operations.latest.network.public_ip._create import PublicIPCreate

    return PublicIPCreate(cli_ctx=cmd.cli_ctx)(command_args=public_ip_args)


# endregion


# region TrafficManagers
def create_traffic_manager_profile(cmd, traffic_manager_profile_name, resource_group_name,
                                   routing_method, unique_dns_name, monitor_path=None,
                                   monitor_port=80, monitor_protocol="HTTP",
                                   profile_status="Enabled",
                                   ttl=30, tags=None, interval=None, timeout=None, max_failures=None,
                                   monitor_custom_headers=None, status_code_ranges=None, max_return=None):
    from .aaz.latest.network.traffic_manager.profile._create import Create
    if monitor_path is None and monitor_protocol == 'HTTP':
        monitor_path = '/'
    args = {
        "name": traffic_manager_profile_name,
        "location": "global",
        "resource_group": resource_group_name,
        "unique_dns_name": unique_dns_name,
        "ttl": ttl,
        "max_return": max_return,
        "status": profile_status,
        "routing_method": routing_method,
        "tags": tags,
        "custom_headers": monitor_custom_headers,
        "status_code_ranges": status_code_ranges,
        "interval": interval,
        "path": monitor_path,
        "port": monitor_port,
        "protocol": monitor_protocol,
        "timeout": timeout,
        "max_failures": max_failures
    }

    return Create(cli_ctx=cmd.cli_ctx)(command_args=args)


def update_traffic_manager_profile(cmd, traffic_manager_profile_name, resource_group_name,
                                   profile_status=None, routing_method=None, tags=None,
                                   monitor_protocol=None, monitor_port=None, monitor_path=None,
                                   ttl=None, timeout=None, interval=None, max_failures=None,
                                   monitor_custom_headers=None, status_code_ranges=None, max_return=None):
    from .aaz.latest.network.traffic_manager.profile._update import Update
    args = {
        "name": traffic_manager_profile_name,
        "resource_group": resource_group_name
    }
    if ttl is not None:
        args["ttl"] = ttl
    if max_return is not None:
        args["max_return"] = max_return
    if profile_status is not None:
        args["status"] = profile_status
    if routing_method is not None:
        args["routing_method"] = routing_method
    if tags is not None:
        args["tags"] = tags
    if monitor_custom_headers is not None:
        args["custom_headers"] = monitor_custom_headers
    if status_code_ranges is not None:
        args["status_code_ranges"] = status_code_ranges
    if interval is not None:
        args["interval"] = interval
    if monitor_path is not None:
        args["path"] = monitor_path
    if monitor_port is not None:
        args["port"] = monitor_port
    if monitor_protocol is not None:
        args["protocol"] = monitor_protocol
    if timeout is not None:
        args["timeout"] = timeout
    if max_failures is not None:
        args["max_failures"] = max_failures

    return Update(cli_ctx=cmd.cli_ctx)(command_args=args)


def create_traffic_manager_endpoint(cmd, resource_group_name, profile_name, endpoint_type, endpoint_name,
                                    target_resource_id=None, target=None,
                                    endpoint_status=None, weight=None, priority=None,
                                    endpoint_location=None, endpoint_monitor_status=None,
                                    min_child_endpoints=None, min_child_ipv4=None, min_child_ipv6=None,
                                    geo_mapping=None, monitor_custom_headers=None, subnets=None, always_serve=None):
    from .aaz.latest.network.traffic_manager.endpoint._create import Create
    args = {
        "name": endpoint_name,
        "type": endpoint_type,
        "profile_name": profile_name,
        "resource_group": resource_group_name,
        "custom_headers": monitor_custom_headers,
        "endpoint_location": endpoint_location,
        "endpoint_monitor_status": endpoint_monitor_status,
        "endpoint_status": endpoint_status,
        "geo_mapping": geo_mapping,
        "min_child_endpoints": min_child_endpoints,
        "min_child_ipv4": min_child_ipv4,
        "min_child_ipv6": min_child_ipv6,
        "priority": priority,
        "subnets": subnets,
        "target": target,
        "target_resource_id": target_resource_id,
        "weight": weight,
        "always_serve": always_serve,
    }

    return Create(cli_ctx=cmd.cli_ctx)(command_args=args)


def update_traffic_manager_endpoint(cmd, resource_group_name, profile_name, endpoint_name,
                                    endpoint_type, endpoint_location=None,
                                    endpoint_status=None, endpoint_monitor_status=None,
                                    priority=None, target=None, target_resource_id=None,
                                    weight=None, min_child_endpoints=None, min_child_ipv4=None,
                                    min_child_ipv6=None, geo_mapping=None,
                                    subnets=None, monitor_custom_headers=None, always_serve=None):
    from .aaz.latest.network.traffic_manager.endpoint._update import Update
    args = {
        "name": endpoint_name,
        "type": endpoint_type,
        "profile_name": profile_name,
        "resource_group": resource_group_name
    }
    if monitor_custom_headers is not None:
        args["custom_headers"] = monitor_custom_headers
    if endpoint_location is not None:
        args["endpoint_location"] = endpoint_location
    if endpoint_monitor_status is not None:
        args["endpoint_monitor_status"] = endpoint_monitor_status
    if endpoint_status is not None:
        args["endpoint_status"] = endpoint_status
    if geo_mapping is not None:
        args["geo_mapping"] = geo_mapping
    if min_child_endpoints is not None:
        args["min_child_endpoints"] = min_child_endpoints
    if min_child_ipv4 is not None:
        args["min_child_ipv4"] = min_child_ipv4
    if min_child_ipv6 is not None:
        args["min_child_ipv6"] = min_child_ipv6
    if priority is not None:
        args["priority"] = priority
    if subnets is not None:
        args["subnets"] = subnets
    if target is not None:
        args["target"] = target
    if target_resource_id is not None:
        args["target_resource_id"] = target_resource_id
    if weight is not None:
        args["weight"] = weight
    if always_serve is not None:
        args["always_serve"] = always_serve

    return Update(cli_ctx=cmd.cli_ctx)(command_args=args)


def list_traffic_manager_endpoints(cmd, resource_group_name, profile_name, endpoint_type=None):
    from .aaz.latest.network.traffic_manager.profile._show import Show
    profile = Show(cli_ctx=cmd.cli_ctx)(command_args={
        "profile_name": profile_name,
        "resource_group": resource_group_name,
    })

    return [endpoint for endpoint in profile["endpoints"] if not endpoint_type or endpoint["type"].endswith(endpoint_type)]
# endregion


# region VirtualNetworks
def list_available_ips(cmd, resource_group_name, virtual_network_name):
    from .aaz.latest.network.vnet._show import Show
    vnet = Show(cli_ctx=cmd.cli_ctx)(command_args={
        "name": virtual_network_name,
        "resource_group": resource_group_name,
    })

    start_ip = vnet["addressSpace"]["addressPrefixes"][0].split("/")[0]

    from .aaz.latest.network.vnet._check_ip_address import CheckIpAddress
    return CheckIpAddress(cli_ctx=cmd.cli_ctx)(command_args={
        "name": virtual_network_name,
        "resource_group": resource_group_name,
        "ip_address": start_ip,
    }).get("availableIPAddresses", [])


def subnet_list_available_ips(cmd, resource_group_name, virtual_network_name, subnet_name):
    from .aaz.latest.network.vnet.subnet._show import Show
    subnet = Show(cli_ctx=cmd.cli_ctx)(command_args={
        "name": subnet_name,
        "resource_group": resource_group_name,
        "vnet_name": virtual_network_name,
    })

    try:
        address_prefix = subnet["addressPrefixes"][0]
    except KeyError:
        address_prefix = subnet["addressPrefix"]
    start_ip = address_prefix.split("/")[0]

    from .aaz.latest.network.vnet._check_ip_address import CheckIpAddress
    return CheckIpAddress(cli_ctx=cmd.cli_ctx)(command_args={
        "name": virtual_network_name,
        "resource_group": resource_group_name,
        "ip_address": start_ip,
    }).get("availableIPAddresses", [])


def sync_vnet_peering(cmd, resource_group_name, virtual_network_name, virtual_network_peering_name):
    from .aaz.latest.network.vnet.peering._show import Show
    from .operations.latest.network.vnet.peering._create import VNetPeeringCreate
    try:
        peering = Show(cli_ctx=cmd.cli_ctx)(command_args={
            "name": virtual_network_peering_name,
            "resource_group": resource_group_name,
            "vnet_name": virtual_network_name,
        })
    except ResourceNotFoundError:
        err_msg = f"Virtual network peering {virtual_network_name} doesn't exist."
        raise ResourceNotFoundError(err_msg)

    return VNetPeeringCreate(cli_ctx=cmd.cli_ctx)(command_args={
        "name": virtual_network_peering_name,
        "resource_group": resource_group_name,
        "vnet_name": virtual_network_name,
        "remote_vnet": peering["remoteVirtualNetwork"].pop("id", None),
        "allow_vnet_access": peering.pop("allowVirtualNetworkAccess", None),
        "allow_gateway_transit": peering.pop("allowGatewayTransit", None),
        "allow_forwarded_traffic": peering.pop("allowForwardedTraffic", None),
        "use_remote_gateways": peering.pop("useRemoteGateways", None),
        "sync_remote": "true",
    })
# endregion


# region VirtualNetworkGateways
class RootCertFormat(AAZFileArgTextFormat):
    def read_file(self, file_path):
        with open(file_path, 'r', encoding=self._encoding) as cert_file:
            lines = cert_file.readlines()

        cert_data = ''.join(line.strip() for line in lines if not line.startswith('-----'))
        return cert_data


def generate_vpn_client(cmd, resource_group_name, virtual_network_gateway_name, processor_architecture=None,
                        authentication_method=None, radius_server_auth_certificate=None, client_root_certificates=None,
                        use_legacy=False):
    generate_args = {"name": virtual_network_gateway_name,
                     "resource_group": resource_group_name,
                     "processor_architecture": processor_architecture}
    if not use_legacy:
        generate_args['authentication_method'] = authentication_method
        generate_args['radius_server_auth_certificate'] = radius_server_auth_certificate
        generate_args['client_root_certificates'] = client_root_certificates
        from .aaz.latest.network.vnet_gateway.vpn_client._generate_vpn_profile import GenerateVpnProfile as _VpnProfileGenerate

        return _VpnProfileGenerate(cli_ctx=cmd.cli_ctx)(command_args=generate_args)
    # legacy implementation
    from .aaz.latest.network.vnet_gateway.vpn_client._generate import Generate as _VpnClientPackageGenerate

    return _VpnClientPackageGenerate(cli_ctx=cmd.cli_ctx)(command_args=generate_args)
# endregion


# region VirtualNetworkGatewayConnections
# pylint: disable=too-many-locals
def _get_vpn_connection_aux_subscriptions(local_gateway, vnet_gateway):
    aux_subscriptions = []
    _add_aux_subscription(aux_subscriptions, local_gateway)
    _add_aux_subscription(aux_subscriptions, vnet_gateway)

    return aux_subscriptions


def create_vpn_connection(cmd, resource_group_name, connection_name, vnet_gateway1,
                          location=None, tags=None, no_wait=False, validate=False,
                          vnet_gateway2=None, express_route_circuit2=None, local_gateway2=None,
                          authorization_key=None, enable_bgp=False, routing_weight=10,
                          connection_type=None, shared_key=None,
                          use_policy_based_traffic_selectors=False,
                          express_route_gateway_bypass=None, ingress_nat_rule=None, egress_nat_rule=None, auth_type=None, cert_auth=None):
    from azure.cli.core.util import random_string
    from azure.cli.core.commands.arm import ArmTemplateBuilder
    from azure.cli.command_modules.network._template_builder import build_vpn_connection_resource

    DeploymentProperties = cmd.get_models('DeploymentProperties', resource_type=ResourceType.MGMT_RESOURCE_RESOURCES)
    tags = tags or {}

    # Build up the ARM template
    master_template = ArmTemplateBuilder()
    vpn_connection_resource = build_vpn_connection_resource(
        cmd, connection_name, location, tags, vnet_gateway1,
        vnet_gateway2 or local_gateway2 or express_route_circuit2,
        connection_type, authorization_key, enable_bgp, routing_weight, shared_key,
        use_policy_based_traffic_selectors, express_route_gateway_bypass, ingress_nat_rule, egress_nat_rule, auth_type, cert_auth)
    master_template.add_resource(vpn_connection_resource)
    master_template.add_output('resource', connection_name, output_type='object')
    if shared_key:
        master_template.add_secure_parameter('sharedKey', shared_key)
    if authorization_key:
        master_template.add_secure_parameter('authorizationKey', authorization_key)

    template = master_template.build()
    parameters = master_template.build_parameters()

    aux_subscriptions = _get_vpn_connection_aux_subscriptions(local_gateway2, vnet_gateway2)

    # deploy ARM template
    deployment_name = 'vpn_connection_deploy_' + random_string(32)
    client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES, aux_subscriptions=aux_subscriptions).deployments
    properties = DeploymentProperties(template=template, parameters=parameters, mode='incremental')
    Deployment = cmd.get_models('Deployment', resource_type=ResourceType.MGMT_RESOURCE_RESOURCES)
    deployment = Deployment(properties=properties)

    if validate:
        _log_pprint_template(template)
        if cmd.supported_api_version(min_api='2019-10-01', resource_type=ResourceType.MGMT_RESOURCE_RESOURCES):
            from azure.cli.core.commands import LongRunningOperation
            validation_poller = client.begin_validate(resource_group_name, deployment_name, deployment)
            return LongRunningOperation(cmd.cli_ctx)(validation_poller)

        return client.validate(resource_group_name, deployment_name, deployment)

    return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name, deployment_name, deployment)


def list_vpn_connections(cmd, resource_group_name, virtual_network_gateway_name=None):
    from .aaz.latest.network.vpn_connection._list import List
    from .aaz.latest.network.vpn_connection._list_connection import ListConnection
    if virtual_network_gateway_name:
        return ListConnection(cli_ctx=cmd.cli_ctx)(command_args={"resource_group": resource_group_name,
                                                                 "vnet_gateway": virtual_network_gateway_name})
    return List(cli_ctx=cmd.cli_ctx)(command_args={"resource_group": resource_group_name})
# endregion


# region IPSec Policy Commands
def clear_vnet_gateway_ipsec_policies(cmd, resource_group_name, gateway_name, no_wait=False):
    from .aaz.latest.network.vnet_gateway._update import Update as _VnetGatewayUpdate

    class VnetGatewayIpsecPoliciesClear(_VnetGatewayUpdate):

        def _output(self, *args, **kwargs):
            result = self.deserialize_output(
                self.ctx.vars.instance.properties.vpn_client_configuration.vpn_client_ipsec_policies,
                client_flatten=True
            )
            return result

        def pre_instance_update(self, instance):
            instance.properties.vpn_client_configuration.vpn_client_ipsec_policies = None

    ipsec_policies_args = {
        "resource_group": resource_group_name,
        "name": gateway_name,
        "no_wait": no_wait
    }

    return VnetGatewayIpsecPoliciesClear(cli_ctx=cmd.cli_ctx)(command_args=ipsec_policies_args)


def clear_vpn_conn_ipsec_policies(cmd, resource_group_name, connection_name, no_wait=False):
    from .aaz.latest.network.vpn_connection._update import Update as _VpnConnectionUpdate

    class VpnConnIpsecPoliciesClear(_VpnConnectionUpdate):

        def _output(self, *args, **kwargs):
            result = self.deserialize_output(self.ctx.vars.instance.properties.ipsec_policies, client_flatten=True)
            return result

        def pre_operations(self):
            args = self.ctx.args
            args.ipsec_policies = None
            args.use_policy_based_traffic_selectors = False

    ipsec_policies_args = {
        "resource_group": resource_group_name,
        "name": connection_name,
        "no_wait": no_wait,
    }
    return VpnConnIpsecPoliciesClear(cli_ctx=cmd.cli_ctx)(command_args=ipsec_policies_args)


def remove_vnet_gateway_aad(cmd, resource_group_name, gateway_name, no_wait=False):
    from .aaz.latest.network.vnet_gateway._update import Update as _VnetGatewayUpdate

    class VnetGatewayAadRemove(_VnetGatewayUpdate):
        def pre_operations(self):
            args = self.ctx.args
            args.no_wait = no_wait

    aad_args = {"resource_group": resource_group_name,
                "name": gateway_name,
                "aad_audience": None,
                "aad_issuer": None,
                "aad_tenant": None,
                "vpn_auth_type": None}
    from azure.cli.core.commands import LongRunningOperation
    poller = VnetGatewayAadRemove(cli_ctx=cmd.cli_ctx)(command_args=aad_args)
    return LongRunningOperation(cmd.cli_ctx)(poller)['vpnClientConfiguration']


# endregion


# region VirtualHub
def create_virtual_hub(cmd,
                       resource_group_name,
                       virtual_hub_name,
                       hosted_subnet,
                       public_ip_address,
                       hub_routing_preference=None,
                       auto_scale_config=None,
                       location=None,
                       tags=None):
    from azure.core.exceptions import HttpResponseError
    from azure.cli.core.commands import LongRunningOperation
    from .aaz.latest.network.routeserver._show import Show
    from .aaz.latest.network.routeserver._list import List

    list_result = List(cli_ctx=cmd.cli_ctx)(command_args={'resource_group': resource_group_name})
    for x in list_result:
        if x['name'] == virtual_hub_name:
            raise CLIError('The VirtualHub "{}" under resource group "{}" exists'.format(
                virtual_hub_name, resource_group_name))

    args = {
        'resource_group': resource_group_name,
        'name': virtual_hub_name,
        'location': location,
        'tags': tags,
        'sku': 'Standard',
        "hub_routing_preference": hub_routing_preference,
        "auto_scale_config": auto_scale_config
    }
    from .aaz.latest.network.routeserver._create import Create
    vhub_poller = Create(cli_ctx=cmd.cli_ctx)(command_args=args)
    LongRunningOperation(cmd.cli_ctx)(vhub_poller)

    from .aaz.latest.network.routeserver.ip_config._create import Create as IPConfigCreate
    from .aaz.latest.network.routeserver.ip_config._delete import Delete as IPConfigDelete
    try:
        create_poller = IPConfigCreate(cli_ctx=cmd.cli_ctx)(command_args={
            'name': 'Default',
            'vhub_name': virtual_hub_name,
            'resource_group': resource_group_name,
            'subnet': hosted_subnet,
            'public_ip_address': public_ip_address
        })
        LongRunningOperation(cmd.cli_ctx)(create_poller)
    except Exception as ex:
        logger.error(ex)
        try:
            delete_poller = IPConfigDelete(cli_ctx=cmd.cli_ctx)(command_args={
                'name': 'Default',
                'vhub_name': virtual_hub_name,
                'resource_group': resource_group_name
            })
            LongRunningOperation(cmd.cli_ctx)(delete_poller)
        except HttpResponseError:
            pass
        from .aaz.latest.network.routeserver._delete import Delete
        Delete(cli_ctx=cmd.cli_ctx)(command_args={'resource_group': resource_group_name, 'name': virtual_hub_name})
        raise ex

    return Show(cli_ctx=cmd.cli_ctx)(command_args={'resource_group': resource_group_name, 'name': virtual_hub_name})


def delete_virtual_hub(cmd, resource_group_name, virtual_hub_name):
    from azure.cli.core.commands import LongRunningOperation
    from .aaz.latest.network.routeserver.ip_config._list import List as IPConfigList
    from .aaz.latest.network.routeserver.ip_config._delete import Delete as IPConfigDelete
    ip_configs = IPConfigList(cli_ctx=cmd.cli_ctx)(command_args={
        'vhub_name': virtual_hub_name,
        'resource_group': resource_group_name
    })
    try:
        ip_config = next(ip_configs)  # there will always be only 1
        poller = IPConfigDelete(cli_ctx=cmd.cli_ctx)(command_args={
            'name': ip_config['name'],
            'vhub_name': virtual_hub_name,
            'resource_group': resource_group_name
        })
        LongRunningOperation(cmd.cli_ctx)(poller)
    except StopIteration:
        pass
    from .aaz.latest.network.routeserver._delete import Delete
    return Delete(cli_ctx=cmd.cli_ctx)(command_args={'resource_group': resource_group_name, 'name': virtual_hub_name})
# endregion


def remove_nw_connection_monitor_output(cmd, connection_monitor_name, location):

    update_args = {
        'connection_monitor_name': connection_monitor_name,
        'location': location
    }
    from .operations.latest.network.watcher._helpers import WatcherConnectionMonitorOutputRemove
    return WatcherConnectionMonitorOutputRemove(cli_ctx=cmd.cli_ctx)(command_args=update_args)


def remove_nw_connection_monitor_test_group(cmd, connection_monitor_name, location, name):
    update_args = {
        'connection_monitor_name': connection_monitor_name,
        'location': location,
        'test_group_name': name
    }
    from .operations.latest.network.watcher._helpers import WatcherConnectionMonitorTestGroupRemove
    return WatcherConnectionMonitorTestGroupRemove(cli_ctx=cmd.cli_ctx)(command_args=update_args)


def create_ddos_custom_policy(cmd, ddos_custom_policy_name, resource_group_name, location=None, tags=None,
                              detection_rule_name=None, detection_mode=None, traffic_type=None,
                              packets_per_second=None, no_wait=None):
    from .aaz.latest.network.ddos_custom_policy._create import Create as DdosCustomPolicyCreate
    from .aaz.latest.network.ddos_custom_policy._show import Show as DdosCustomPolicyShow
    from .operations.ddos_custom_policy import convert_ddos_custom_policy_to_snake_case, combine_old_and_new_custom_policy
    from ._template_builder import build_ddos_custom_policy

    existing_policy = None

    try:
        existing_policy = DdosCustomPolicyShow(cli_ctx=cmd.cli_ctx)(command_args={
            'ddos_custom_policy_name': ddos_custom_policy_name,
            'resource_group': resource_group_name
        })

        existing_policy = convert_ddos_custom_policy_to_snake_case(existing_policy)
    except ResourceNotFoundError:
        # No existing DDoS custom policy; proceed with creation.
        logger.debug("DDoS custom policy '%s' not found in resource group '%s'.",
                     ddos_custom_policy_name, resource_group_name)
    except Exception as err:  # pylint: disable=broad-except
        # Log unexpected errors while preserving previous behavior of not failing the command.
        logger.warning("Failed to retrieve existing DDoS custom policy '%s' in resource group '%s': %s",
                       ddos_custom_policy_name, resource_group_name, err)

    policy = build_ddos_custom_policy(cmd, ddos_custom_policy_name, location, tags, detection_rule_name, detection_mode,
                                      packets_per_second, traffic_type)

    if existing_policy:
        policy = combine_old_and_new_custom_policy(existing_policy, policy)

    policy['resource_group'] = resource_group_name
    policy['no_wait'] = no_wait

    return DdosCustomPolicyCreate(cli_ctx=cmd.cli_ctx)(command_args=policy)
