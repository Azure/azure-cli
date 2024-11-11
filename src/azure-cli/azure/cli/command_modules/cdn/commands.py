# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError

from azure.cli.core.commands import CliCommandType

from ._client_factory import (cf_cdn, cf_custom_domain, cf_endpoints)


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
    cd_not_found_msg = _not_found_msg.format('Custom Domain')
    endpoint_not_found_msg = _not_found_msg.format('Endpoint')

    cdn_endpoints_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.cdn.operations#EndpointsOperations.{}',
        client_factory=cf_endpoints,
        exception_handler=_not_found(endpoint_not_found_msg)
    )

    cdn_domain_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.cdn.operations#CustomDomainsOperations.{}',
        client_factory=cf_custom_domain,
        exception_handler=_not_found(cd_not_found_msg)
    )

    with self.command_group('cdn custom-domain', cdn_domain_sdk) as g:
        g.custom_command('enable-https', 'enable_custom_https', client_factory=cf_cdn)
        g.command('disable-https', 'disable_custom_https')

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

    # from .custom.custom_cdn import CDNEnableHttps
    # self.command_table['cdn custom-domain enable-https'] = CDNEnableHttps(loader=self)

    # from .custom.custom_cdn import CDNCustomDomainDelete
    # self.command_table['cdn custom-domain delete'] = CDNCustomDomainDelete(loader=self)

    from azure.cli.command_modules.cdn.aaz.latest.cdn.endpoint import Show
    self.command_table['cdn endpoint rule show'] = Show(loader=self)
    self.command_table['cdn endpoint rule condition show'] = Show(loader=self)
    self.command_table['cdn endpoint rule action show'] = Show(loader=self)

    from .custom.custom_cdn import CDNEndpointCreate
    self.command_table['cdn endpoint create'] = CDNEndpointCreate(loader=self)

    from .custom.custom_cdn import CDNEndpointUpdate
    self.command_table['cdn endpoint update'] = CDNEndpointUpdate(loader=self)

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

    from .custom.custom_cdn import CdnMigrateToAfd
    self.command_table['cdn profile-migration migrate'] = CdnMigrateToAfd(loader=self)

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

    # from .custom.custom_cdn import CDNEndpointRuleConditionAdd
    # self.command_table['cdn endpoint rule condition add'] = CDNEndpointRuleConditionAdd(loader=self)

    # from .custom.custom_cdn import CDNEndpointRuleConditionRemove
    # self.command_table['cdn endpoint rule condition remove'] = CDNEndpointRuleConditionRemove(loader=self)

    # from .custom.custom_cdn import CDNEndpointRuleActionAdd
    # self.command_table['cdn endpoint rule action add'] = CDNEndpointRuleActionAdd(loader=self)

    # from .custom.custom_cdn import CDNEndpointRuleActionRemove
    # self.command_table['cdn endpoint rule action remove'] = CDNEndpointRuleActionRemove(loader=self)

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

    from .custom.custom_afdx import AFDProfileLogScrubbingShow
    self.command_table['afd profile log-scrubbing show'] = AFDProfileLogScrubbingShow(loader=self)

    from .custom.custom_afdx import AFDEndpointCreate
    self.command_table['afd endpoint create'] = AFDEndpointCreate(loader=self)

    from .custom.custom_afdx import AFDEndpointUpdate
    self.command_table['afd endpoint update'] = AFDEndpointUpdate(loader=self)

    from .custom.custom_afdx import AFDOriginCreate
    self.command_table['afd origin create'] = AFDOriginCreate(loader=self)

    from .custom.custom_afdx import AFDOriginUpdate
    self.command_table['afd origin update'] = AFDOriginUpdate(loader=self)

    from .custom.custom_afdx import AFDOriginGroupCreate
    self.command_table['afd origin-group create'] = AFDOriginGroupCreate(loader=self)

    from .custom.custom_afdx import AFDOriginGroupUpdate
    self.command_table['afd origin-group update'] = AFDOriginGroupUpdate(loader=self)

    from .custom.custom_afdx import AFDRouteCreate
    self.command_table['afd route create'] = AFDRouteCreate(loader=self)

    from .custom.custom_afdx import AFDRouteUpdate
    self.command_table['afd route update'] = AFDRouteUpdate(loader=self)

    from .custom.custom_afdx import AFDRuleCreate
    self.command_table['afd rule create'] = AFDRuleCreate(loader=self)

    from .custom.custom_afdx import AFDRuleConditionShow
    self.command_table['afd rule condition list'] = AFDRuleConditionShow(loader=self)

    from .custom.custom_afdx import AFDRuleconditionAdd
    self.command_table['afd rule condition add'] = AFDRuleconditionAdd(loader=self)

    from .custom.custom_afdx import AFDRuleconditionRemove
    self.command_table['afd rule condition remove'] = AFDRuleconditionRemove(loader=self)

    from .custom.custom_afdx import AFDRuleActionShow
    self.command_table['afd rule action list'] = AFDRuleActionShow(loader=self)

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
