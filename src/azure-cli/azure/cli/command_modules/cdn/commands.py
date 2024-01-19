# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError

from azure.cli.core.commands import CliCommandType

from ._client_factory import (cf_endpoints, cf_waf_policy, cf_waf_rule_set, cf_afd_rules)


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
    endpoint_not_found_msg = _not_found_msg.format('Endpoint')
    waf_policy_not_found_msg = _not_found_msg.format('WAF Policy')
    rule_not_found_msg = _not_found_msg.format('Rule')

    cdn_endpoints_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.cdn.operations#EndpointsOperations.{}',
        client_factory=cf_endpoints,
        exception_handler=_not_found(endpoint_not_found_msg)
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

    from .custom.custom_cdn import CDNProfileCreate
    self.command_table['cdn profile create'] = CDNProfileCreate(loader=self)

    from .custom.custom_cdn import CDNProfileUpdate
    self.command_table['cdn profile update'] = CDNProfileUpdate(loader=self)

    from .custom.custom_cdn import CDNProfileDelete
    self.command_table['cdn profile delete'] = CDNProfileDelete(loader=self)

    from .custom.custom_cdn import CDNProfileShow
    self.command_table['cdn profile show'] = CDNProfileShow(loader=self)

    from .custom.custom_cdn import CDNProfileList
    self.command_table['cdn profile list'] = CDNProfileList(loader=self)

    from azure.cli.command_modules.cdn.aaz.latest.cdn.endpoint import Show
    self.command_table['cdn endpoint rule show'] = Show(loader=self)
    self.command_table['cdn endpoint rule condition show'] = Show(loader=self)
    self.command_table['cdn endpoint rule action show'] = Show(loader=self)

    from .custom.custom_cdn import CDNEndpointCreate
    self.command_table['cdn endpoint create'] = CDNEndpointCreate(loader=self)

    from .custom.custom_cdn import CDNEndpointUpdate
    self.command_table['cdn endpoint update'] = CDNEndpointUpdate(loader=self)

    from .custom.custom_cdn import CDNEnableCustomHttp
    self.command_table['cdn endpoint enable-custom-http'] = CDNEnableCustomHttp(loader=self)

    from .custom.custom_cdn import NameExistsWithType
    self.command_table['cdn endpoint name-exists'] = NameExistsWithType(loader=self)

    from .custom.custom_cdn import CDNOriginCreate
    self.command_table['cdn origin create'] = CDNOriginCreate(loader=self)

    from .custom.custom_cdn import CDNOriginUpdate
    self.command_table['cdn origin update'] = CDNOriginUpdate(loader=self)

    from .custom.custom_cdn import CDNOriginGroupCreate
    self.command_table['cdn origin-group create'] = CDNOriginGroupCreate(loader=self)

    from .custom.custom_cdn import CDNOriginGroupUpdate
    self.command_table['cdn origin-group update'] = CDNOriginGroupUpdate(loader=self)

    from .custom.custom_cdn import CDNEndpointRuleAdd
    self.command_table['cdn endpoint rule add'] = CDNEndpointRuleAdd(loader=self)

    from .custom.custom_cdn import CDNEndpointRuleRemove
    self.command_table['cdn endpoint rule remove'] = CDNEndpointRuleRemove(loader=self)

    from .custom.custom_cdn import CDNEndpointRuleConditionAdd
    self.command_table['cdn endpoint rule condition add'] = CDNEndpointRuleConditionAdd(loader=self)

    from .custom.custom_cdn import CDNEndpointRuleConditionRemove
    self.command_table['cdn endpoint rule condition remove'] = CDNEndpointRuleConditionRemove(loader=self)

    from .custom.custom_cdn import CDNEndpointRuleActionAdd
    self.command_table['cdn endpoint rule action add'] = CDNEndpointRuleActionAdd(loader=self)

    from .custom.custom_cdn import CDNEndpointRuleActionRemove
    self.command_table['cdn endpoint rule action remove'] = CDNEndpointRuleActionRemove(loader=self)

    with self.command_group('cdn endpoint waf policy', cdn_endpoints_sdk, is_preview=True) as g:
        g.custom_show_command('show', 'show_endpoint_waf_policy_link', client_factory=cf_endpoints)
        g.custom_command('set', 'set_endpoint_waf_policy_link', client_factory=cf_endpoints)
        g.custom_command('remove', 'remove_endpoint_waf_policy_link', client_factory=cf_endpoints, confirmation=True)

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
        g.custom_command('list', 'list_afd_rule_condition')

    with self.command_group('afd rule action',
                            cdn_afd_rule_sdk,
                            custom_command_type=get_custom_sdk(cf_afd_rules, _not_found(rule_not_found_msg))) as g:
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

    from .custom.custom_afdx import AFDRuleconditionAdd
    self.command_table['afd rule condition add'] = AFDRuleconditionAdd(loader=self)

    from .custom.custom_afdx import AFDRuleconditionRemove
    self.command_table['afd rule condition remove'] = AFDRuleconditionRemove(loader=self)

    from .custom.custom_afdx import AFDRuleActionCreate
    self.command_table['afd rule action add'] = AFDRuleActionCreate(loader=self)

    from .custom.custom_afdx import AFDRuleActionRemove
    self.command_table['afd rule action remove'] = AFDRuleActionRemove(loader=self)

    from .custom.custom_afdx import AFDSecretCreate
    self.command_table['afd secret create'] = AFDSecretCreate(loader=self)

    from .custom.custom_afdx import AFDSecretUpdate
    self.command_table['afd secret update'] = AFDSecretUpdate(loader=self)

    from .custom.custom_afdx import AFDSecurityPolicyCreate
    self.command_table['afd security-policy create'] = AFDSecurityPolicyCreate(loader=self)

    from .custom.custom_afdx import AFDSecurityPolicyUpdate
    self.command_table['afd security-policy update'] = AFDSecurityPolicyUpdate(loader=self)