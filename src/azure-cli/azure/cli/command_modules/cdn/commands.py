# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError

from azure.cli.core.commands import CliCommandType

from ._client_factory import (cf_cdn, cf_custom_domain, cf_endpoints, cf_profiles, cf_origins, cf_resource_usage,
                              cf_edge_nodes, cf_waf_policy, cf_waf_rule_set, cf_origin_groups, cf_afd_rules)


def _not_found(message):
    def _inner_not_found(ex):
        from azure.core.exceptions import ResourceNotFoundError
        if isinstance(ex, ResourceNotFoundError):
            raise CLIError(message)
        raise ex
    return _inner_not_found


def get_custom_sdk(client_factory, exception_handler):
    return CliCommandType(
        operations_tmpl='azure.cli.command_modules.cdn.custom#custom_afdx.{}',
        client_factory=client_factory,
        exception_handler=exception_handler
    )


_not_found_msg = "{}(s) not found. Please verify the resource(s), group or it's parent resources " \
    "exist."


# pylint: disable=too-many-statements
# pylint: disable=too-many-locals
def load_command_table(self, _):
    profile_not_found_msg = _not_found_msg.format('Profile')
    endpoint_not_found_msg = _not_found_msg.format('Endpoint')
    cd_not_found_msg = _not_found_msg.format('Custom Domain')
    origin_not_found_msg = _not_found_msg.format('Origin')
    origin_group_not_found_msg = _not_found_msg.format('Origin Group')
    waf_policy_not_found_msg = _not_found_msg.format('WAF Policy')
    rule_not_found_msg = _not_found_msg.format('Rule')

    cdn_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.cdn#CdnManagementClient.{}',
        client_factory=cf_cdn
    )

    cdn_endpoints_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.cdn.operations#EndpointsOperations.{}',
        client_factory=cf_endpoints,
        exception_handler=_not_found(endpoint_not_found_msg)
    )

    cdn_profiles_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.cdn.operations#ProfilesOperations.{}',
        client_factory=cf_profiles,
        exception_handler=_not_found(profile_not_found_msg)
    )

    cdn_domain_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.cdn.operations#CustomDomainsOperations.{}',
        client_factory=cf_custom_domain,
        exception_handler=_not_found(cd_not_found_msg)
    )

    cdn_origin_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.cdn.operations#OriginsOperations.{}',
        client_factory=cf_origins,
        exception_handler=_not_found(origin_not_found_msg)
    )

    cdn_origin_group_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.cdn.operations#OriginGroupsOperations.{}',
        client_factory=cf_origin_groups,
        exception_handler=_not_found(origin_group_not_found_msg)
    )

    cdn_edge_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.cdn.operations#EdgeNodesOperations.{}',
        client_factory=cf_edge_nodes
    )

    cdn_usage_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.cdn.operations#ResourceUsageOperations.{}',
        client_factory=cf_resource_usage
    )

    cdn_waf_policy_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.cdn.operations#PoliciesOperations.{}',
        client_factory=cf_waf_policy,
        exception_handler=_not_found(waf_policy_not_found_msg)
    )

    cdn_afd_rule_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.cdn.operations#RulesOperations.{}',
        client_factory=cf_afd_rules,
        exception_handler=_not_found(rule_not_found_msg)
    )

    with self.command_group('cdn', cdn_sdk) as g:
        g.custom_command('name-exists', 'check_name_availability', client_factory=cf_cdn)

    with self.command_group('cdn', cdn_usage_sdk) as g:
        g.command('usage', 'list')

    with self.command_group('cdn endpoint', cdn_endpoints_sdk) as g:
        for name in ['start', 'stop', 'delete']:
            g.command(name, f"begin_{name}", supports_no_wait=True)
        g.show_command('show', 'get')
        g.command('list', 'list_by_profile')
        g.custom_command('load', 'load_endpoint_content', client_factory=cf_cdn, supports_no_wait=True)
        g.custom_command('purge', 'purge_endpoint_content', client_factory=cf_cdn, supports_no_wait=True)
        g.custom_command('validate-custom-domain', 'validate_custom_domain', client_factory=cf_cdn)
        g.custom_command('create', 'create_endpoint', client_factory=cf_cdn,
                         doc_string_source='azure.mgmt.cdn.models#Endpoint',
                         supports_no_wait=True)
        g.generic_update_command('update', setter_name='begin_update', setter_arg_name='endpoint_update_properties',
                                 custom_func_name='update_endpoint',
                                 doc_string_source='azure.mgmt.cdn.models#EndpointUpdateParameters',
                                 supports_no_wait=True)

    with self.command_group('cdn endpoint waf policy', cdn_endpoints_sdk, is_preview=True) as g:
        g.custom_show_command('show', 'show_endpoint_waf_policy_link', client_factory=cf_endpoints)
        g.custom_command('set', 'set_endpoint_waf_policy_link', client_factory=cf_endpoints)
        g.custom_command('remove', 'remove_endpoint_waf_policy_link', client_factory=cf_endpoints, confirmation=True)

    with self.command_group('cdn endpoint rule', cdn_endpoints_sdk, is_preview=True) as g:
        g.show_command('show', 'get')
        g.custom_command('add', 'add_rule', client_factory=cf_cdn,
                         doc_string_source='azure.mgmt.cdn.models#Endpoint')
        g.custom_command('remove', 'remove_rule', client_factory=cf_cdn,
                         doc_string_source='azure.mgmt.cdn.models#Endpoint')

    with self.command_group('cdn endpoint rule condition', cdn_endpoints_sdk, is_preview=True) as g:
        g.show_command('show', 'get')
        g.custom_command('add', 'add_condition', client_factory=cf_cdn,
                         doc_string_source='azure.mgmt.cdn.models#Endpoint')
        g.custom_command('remove', 'remove_condition', client_factory=cf_cdn,
                         doc_string_source='azure.mgmt.cdn.models#Endpoint')

    with self.command_group('cdn endpoint rule action', cdn_endpoints_sdk, is_preview=True) as g:
        g.show_command('show', 'get')
        g.custom_command('add', 'add_action', client_factory=cf_cdn,
                         doc_string_source='azure.mgmt.cdn.models#Endpoint')
        g.custom_command('remove', 'remove_action', client_factory=cf_cdn,
                         doc_string_source='azure.mgmt.cdn.models#Endpoint')

    with self.command_group('cdn profile', cdn_profiles_sdk) as g:
        g.custom_show_command('show', 'get_profile', client_factory=cf_cdn)
        g.command('usage', 'list_resource_usage')
        g.custom_command('delete', 'delete_profile', client_factory=cf_cdn)
        g.custom_command('list', 'list_profiles', client_factory=cf_cdn)
        g.custom_command('create', 'create_profile', client_factory=cf_cdn)
        g.generic_update_command('update', setter_name='begin_update', custom_func_name='update_profile',
                                 setter_arg_name='profile_update_parameters',
                                 doc_string_source='azure.mgmt.cdn.models#ProfileUpdateParameters')

    with self.command_group('cdn custom-domain', cdn_domain_sdk) as g:
        g.show_command('show', 'get')
        g.command('delete', 'begin_delete')
        g.command('list', 'list_by_endpoint')
        g.custom_command('create', 'create_custom_domain', client_factory=cf_cdn)
        g.custom_command('enable-https', 'enable_custom_https', client_factory=cf_cdn)
        g.command('disable-https', 'disable_custom_https')

    with self.command_group('cdn origin', cdn_origin_sdk) as g:
        g.show_command('show', 'get')
        g.command('list', 'list_by_endpoint')
        g.custom_command('create', 'create_origin', client_factory=cf_origins, is_preview=True)
        g.custom_command('update', 'update_origin', client_factory=cf_origins)
        g.command('delete', 'begin_delete', confirmation=True)

    with self.command_group('cdn origin-group', cdn_origin_group_sdk, is_preview=True) as g:
        g.show_command('show', 'get')
        g.command('list', 'list_by_endpoint')
        g.custom_command('create', 'create_origin_group', client_factory=cf_origin_groups)
        g.custom_command('update', 'update_origin_group', client_factory=cf_origin_groups)
        g.command('delete', 'begin_delete', confirmation=True)

    with self.command_group('cdn edge-node', cdn_edge_sdk) as g:
        g.command('list', 'list')

    with self.command_group('cdn waf policy', cdn_waf_policy_sdk, is_preview=True,
                            deprecate_info=self.deprecate(hide=False)) as g:
        g.show_command('show', 'get')
        g.command('list', 'list')
        g.custom_command('set', 'set_waf_policy', client_factory=cf_waf_policy)
        g.command('delete', 'delete', confirmation=True)

    with self.command_group('cdn waf policy managed-rule-set', cdn_waf_policy_sdk, is_preview=True) as g:
        g.custom_command('add', 'add_waf_policy_managed_rule_set', client_factory=cf_waf_policy)
        g.custom_command('remove',
                         'remove_waf_policy_managed_rule_set',
                         client_factory=cf_waf_policy,
                         confirmation=True)
        g.custom_command('list', 'list_waf_policy_managed_rule_sets', client_factory=cf_waf_policy)
        g.custom_show_command('show', 'show_waf_policy_managed_rule_set', client_factory=cf_waf_policy)
        g.custom_command('list-available', 'list_waf_managed_rule_set', client_factory=cf_waf_rule_set)

    with self.command_group('cdn waf policy managed-rule-set rule-group-override',
                            cdn_waf_policy_sdk,
                            is_preview=True) as g:
        g.custom_command('set', 'set_waf_managed_rule_group_override', client_factory=cf_waf_policy)
        g.custom_command('delete',
                         'delete_waf_managed_rule_group_override',
                         client_factory=cf_waf_policy,
                         confirmation=True)
        g.custom_command('list', 'list_waf_policy_managed_rule_group_overrides', client_factory=cf_waf_policy)
        g.custom_show_command('show', 'show_waf_managed_rule_group_override', client_factory=cf_waf_policy)
        g.custom_command('list-available', 'list_waf_managed_rule_groups', client_factory=cf_waf_rule_set)

    with self.command_group('cdn waf policy custom-rule', cdn_waf_policy_sdk, is_preview=True) as g:
        g.custom_command('set', 'set_waf_custom_rule', client_factory=cf_waf_policy)
        g.custom_command('delete', 'delete_waf_custom_rule', client_factory=cf_waf_policy, confirmation=True)
        g.custom_command('list', 'list_waf_custom_rules', client_factory=cf_waf_policy)
        g.custom_show_command('show', 'show_waf_custom_rule', client_factory=cf_waf_policy)

    with self.command_group('cdn waf policy rate-limit-rule', cdn_waf_policy_sdk, is_preview=True) as g:
        g.custom_command('set', 'set_waf_rate_limit_rule', client_factory=cf_waf_policy)
        g.custom_command('delete', 'delete_waf_rate_limit_rule', client_factory=cf_waf_policy, confirmation=True)
        g.custom_command('list', 'list_waf_rate_limit_rules', client_factory=cf_waf_policy)
        g.custom_show_command('show', 'show_waf_rate_limit_rule', client_factory=cf_waf_policy)

    with self.command_group('afd', is_preview=True):
        pass

    with self.command_group('afd rule condition',
                            cdn_afd_rule_sdk,
                            custom_command_type=get_custom_sdk(cf_afd_rules, _not_found(rule_not_found_msg))) as g:
        g.custom_command('add', 'add_afd_rule_condition',
                         doc_string_source='azure.mgmt.cdn.models#Rule')
        g.custom_command('remove', 'remove_afd_rule_condition',
                         doc_string_source='azure.mgmt.cdn.models#Rule')
        g.custom_command('list', 'list_afd_rule_condition')

    with self.command_group('afd rule action',
                            cdn_afd_rule_sdk,
                            custom_command_type=get_custom_sdk(cf_afd_rules, _not_found(rule_not_found_msg))) as g:
        g.custom_command('add', 'add_afd_rule_action',
                         doc_string_source='azure.mgmt.cdn.models#Rule')
        g.custom_command('remove', 'remove_afd_rule_action',
                         doc_string_source='azure.mgmt.cdn.models#Rule')
        g.custom_command('list', 'list_afd_rule_action')

    from .custom.custom_afdx import AFDCustomDomainCreate
    self.command_table['afd custom-domain create'] = AFDCustomDomainCreate(loader=self)

    from .custom.custom_afdx import AFDCustomDomainUpdate
    self.command_table['afd custom-domain update'] = AFDCustomDomainUpdate(loader=self)

    from .custom.custom_afdx import AFDProfileShow
    self.command_table['afd profile show'] = AFDProfileShow(loader=self)

    from .custom.custom_afdx import AFDProfileCreate
    self.command_table['afd profile create'] = AFDProfileCreate(loader=self)

    from .custom.custom_afdx import AFDProfileUpdate
    self.command_table['afd profile update'] = AFDProfileUpdate(loader=self)

    from .custom.custom_afdx import AFDEndpointCreate
    self.command_table['afd endpoint create'] = AFDEndpointCreate(loader=self)

    from .custom.custom_afdx import AFDEndpointUpdate
    self.command_table['afd endpoint update'] = AFDEndpointUpdate(loader=self)

    from .custom.custom_afdx import AFDOriginCreate
    self.command_table['afd origin create'] = AFDOriginCreate(loader=self)

    from .custom.custom_afdx import AFDOriginUpdate
    self.command_table['afd origin update'] = AFDOriginUpdate(loader=self)

    from .custom.custom_afdx import AFDRouteCreate
    self.command_table['afd route create'] = AFDRouteCreate(loader=self)

    from .custom.custom_afdx import AFDRouteUpdate
    self.command_table['afd route update'] = AFDRouteUpdate(loader=self)

    from .custom.custom_afdx import AFDRuleCreate
    self.command_table['afd rule create'] = AFDRuleCreate(loader=self)

    from .custom.custom_afdx import AFDSecretCreate
    self.command_table['afd secret create'] = AFDSecretCreate(loader=self)

    from .custom.custom_afdx import AFDSecretUpdate
    self.command_table['afd secret update'] = AFDSecretUpdate(loader=self)

    from .custom.custom_afdx import AFDSecurityPolicyCreate
    self.command_table['afd security-policy create'] = AFDSecurityPolicyCreate(loader=self)

    from .custom.custom_afdx import AFDSecurityPolicyUpdate
    self.command_table['afd security-policy update'] = AFDSecurityPolicyUpdate(loader=self)
