# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from knack.arguments import CLIArgumentType

from azure.mgmt.cdn.models import QueryStringCachingBehavior, SkuName, ActionType

from azure.cli.core.commands.parameters import get_three_state_flag, tags_type, get_enum_type
from azure.cli.core.commands.validators import get_default_location_from_resource_group

from ._validators import (validate_origin, validate_priority)
from ._actions import (OriginType, MatchConditionAction, ManagedRuleOverrideAction)


# pylint:disable=too-many-statements
def load_arguments(self, _):

    name_arg_type = CLIArgumentType(options_list=('--name', '-n'), metavar='NAME')
    endpoint_name_type = CLIArgumentType(options_list=('--endpoint-name'), metavar='ENDPOINT_NAME')
    profile_name_help = 'Name of the CDN profile which is unique within the resource group.'

    with self.argument_context('cdn') as c:
        c.argument('name', name_arg_type, id_part='name')
        c.argument('tags', tags_type)

    # Profile #
    with self.argument_context('cdn profile') as c:
        c.argument('profile_name', name_arg_type, id_part='name', help=profile_name_help)

    with self.argument_context('cdn profile create') as c:
        c.argument('sku', arg_type=get_enum_type([item.value for item in list(SkuName)]))
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('name', name_arg_type, id_part='name', help=profile_name_help)

    # Endpoint #

    with self.argument_context('cdn endpoint') as c:
        c.argument('content_paths', nargs='+')
        c.argument('endpoint_name', name_arg_type, id_part='child_name_1', help='Name of the CDN endpoint.')
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('origins', options_list='--origin', nargs='+', action=OriginType, validator=validate_origin,
                   help='Endpoint origin specified by the following space-delimited 3 '
                        'tuple: `www.example.com http_port https_port`. The HTTP and HTTPs'
                        'ports are optional and will default to 80 and 443 respectively.')
        c.argument('is_http_allowed', arg_type=get_three_state_flag(invert=True), options_list='--no-http',
                   help='Indicates whether HTTP traffic is not allowed on the endpoint. '
                   'Default is to allow HTTP traffic.')
        c.argument('is_https_allowed', arg_type=get_three_state_flag(invert=True), options_list='--no-https',
                   help='Indicates whether HTTPS traffic is not allowed on the endpoint. '
                   'Default is to allow HTTPS traffic.')
        c.argument('is_compression_enabled', arg_type=get_three_state_flag(), options_list='--enable-compression',
                   help='If compression is enabled, content will be served as compressed if '
                        'user requests for a compressed version. Content won\'t be compressed '
                        'on CDN when requested content is smaller than 1 byte or larger than 1 '
                        'MB.')
        c.argument('profile_name', help=profile_name_help, id_part='name')

    with self.argument_context('cdn endpoint update') as c:
        caching_behavior = [item.value for item in list(QueryStringCachingBehavior)]
        c.argument('query_string_caching_behavior', options_list='--query-string-caching',
                   arg_type=get_enum_type(caching_behavior))
        c.argument('content_types_to_compress', nargs='+')

    with self.argument_context('cdn endpoint rule') as c:
        c.argument('rule_name', help='Name of the rule.')
        c.argument('order', help='The order of the rule. The order number must start from 0 and consecutive.\
                    Rule with higher order will be applied later.')
        c.argument('match_variable', arg_group="Match Condition", help='Name of the match condition.')
        c.argument('operator', arg_group="Match Condition", help='Operator of the match condition.')
        c.argument('selector', arg_group="Match Condition", help='Selector of the match condition.')
        c.argument('match_values', arg_group="Match Condition", nargs='+',
                   help='Match values of the match condition (comma separated).')
        c.argument('transform', arg_group="Match Condition", arg_type=get_enum_type(['Lowercase', 'Uppercase']),
                   nargs='+', help='Transform to apply before matching.')
        c.argument('negate_condition', arg_group="Match Condition", arg_type=get_three_state_flag(),
                   help='If true, negates the condition')
        c.argument('action_name', arg_group="Action", help='Name of the action.')
        c.argument('cache_behavior', arg_group="Action",
                   arg_type=get_enum_type(['BypassCache', 'Override', 'SetIfMissing']),
                   help='Caching behavior for the requests.')
        c.argument('cache_duration', arg_group="Action",
                   help='The duration for which the content needs to be cached. \
                   Allowed format is [d.]hh:mm:ss.')
        c.argument('header_action', arg_group="Action",
                   arg_type=get_enum_type(['Append', 'Overwrite', 'Delete']),
                   help='Header action for the requests.')
        c.argument('header_name', arg_group="Action", help='Name of the header to modify.')
        c.argument('header_value', arg_group="Action", help='Value of the header.')
        c.argument('redirect_type', arg_group="Action",
                   arg_type=get_enum_type(['Moved', 'Found', 'TemporaryRedirect', 'PermanentRedirect']),
                   help='The redirect type the rule will use when redirecting traffic.')
        c.argument('redirect_protocol', arg_group="Action",
                   arg_type=get_enum_type(['MatchRequest', 'Http', 'Https']),
                   help='Protocol to use for the redirect.')
        c.argument('custom_hostname', arg_group="Action", help='Host to redirect. \
                   Leave empty to use the incoming host as the destination host.')
        c.argument('custom_path', arg_group="Action",
                   help='The full path to redirect. Path cannot be empty and must start with /. \
                   Leave empty to use the incoming path as destination path.')
        c.argument('custom_querystring', arg_group="Action",
                   help='The set of query strings to be placed in the redirect URL. \
                   leave empty to preserve the incoming query string.')
        c.argument('custom_fragment', arg_group="Action", help='Fragment to add to the redirect URL.')
        c.argument('query_string_behavior', arg_group="Action",
                   arg_type=get_enum_type(['Include', 'IncludeAll', 'Exclude', 'ExcludeAll']),
                   help='Query string behavior for the requests.')
        c.argument('query_parameters', arg_group="Action",
                   help='Query parameters to include or exclude (comma separated).')
        c.argument('source_pattern', arg_group="Action",
                   help='A request URI pattern that identifies the type of requests that may be rewritten.')
        c.argument('destination', help='The destination path to be used in the rewrite.')
        c.argument('preserve_unmatched_path', arg_group="Action",
                   arg_type=get_three_state_flag(),
                   help='If True, the remaining path after the source \
                   pattern will be appended to the new destination path.')
        c.argument('index', type=int, help='The index of the condition/action')

    with self.argument_context('cdn endpoint create') as c:
        c.argument('name', name_arg_type, id_part='name', help='Name of the CDN endpoint.')
    with self.argument_context('cdn endpoint set') as c:
        c.argument('name', name_arg_type, id_part='name', help='Name of the CDN endpoint.')

    with self.argument_context('cdn endpoint list') as c:
        c.argument('profile_name', id_part=None)

    with self.argument_context('cdn endpoint waf') as c:
        c.argument('endpoint_name', endpoint_name_type, help='Name of the CDN endpoint.')

    # Custom Domain #

    with self.argument_context('cdn custom-domain') as c:
        c.argument('custom_domain_name', name_arg_type, id_part=None, help='Name of the custom domain.')

    with self.argument_context('cdn custom-domain create') as c:
        c.argument('location', validator=get_default_location_from_resource_group)

    # Origin #
    with self.argument_context('cdn origin') as c:
        c.argument('origin_name', name_arg_type, id_part='name')

    # WAF #

    with self.argument_context('cdn waf policy set') as c:
        c.argument('disabled', arg_type=get_three_state_flag())
        c.argument('block_response_status_code', type=int)
        c.argument('name', name_arg_type, id_part='name', help='The name of the CDN WAF policy.')
    with self.argument_context('cdn waf policy show') as c:
        c.argument('policy_name', name_arg_type, id_part='name', help='The name of the CDN WAF policy.')
    with self.argument_context('cdn waf policy delete') as c:
        c.argument('policy_name', name_arg_type, id_part='name', help='The name of the CDN WAF policy.')

    with self.argument_context('cdn waf policy managed-rule-set') as c:
        c.argument('policy_name', id_part='name', help='Name of the CDN WAF policy.')
        c.argument('rule_set_type', help='The type of the managed rule set.')
        c.argument('rule_set_version', help='The version of the managed rule set.')
    with self.argument_context('cdn waf policy managed-rule-set list') as c:
        # List commands cannot use --ids flag
        c.argument('policy_name', id_part=None)
    with self.argument_context('cdn waf policy managed-rule-set add') as c:
        c.argument('enabled', arg_type=get_three_state_flag())

    with self.argument_context('cdn waf policy managed-rule-set rule-group-override') as c:
        c.argument('name', name_arg_type, id_part=None, help='The name of the rule group.')
    with self.argument_context('cdn waf policy managed-rule-set rule-group-override list') as c:
        # List commands cannot use --ids flag
        c.argument('policy_name', id_part=None)
    with self.argument_context('cdn waf policy managed-rule-set rule-group-override set') as c:
        c.argument('rule_overrides',
                   options_list=['-r', '--rule-override'],
                   action=ManagedRuleOverrideAction,
                   nargs='+')

    with self.argument_context('cdn waf policy custom-rule') as c:
        c.argument('name', name_arg_type, id_part=None, help='The name of the custom rule.')
        c.argument('policy_name', id_part='name', help='Name of the CDN WAF policy.')
    with self.argument_context('cdn waf policy custom-rule list') as c:
        # List commands cannot use --ids flag
        c.argument('policy_name', id_part=None)
    with self.argument_context('cdn waf policy rate-limit-rule') as c:
        c.argument('name', name_arg_type, id_part=None, help='The name of the rate limit rule.')
        c.argument('policy_name', id_part='name', help='Name of the CDN WAF policy.')
    with self.argument_context('cdn waf policy rate-limit-rule list') as c:
        # List commands cannot use --ids flag
        c.argument('policy_name', id_part=None)

    with self.argument_context('cdn waf policy custom-rule set') as c:
        c.argument('match_conditions', options_list=['-m', '--match-condition'], action=MatchConditionAction, nargs='+')
        c.argument('priority', type=int, validator=validate_priority)
        c.argument('action', arg_type=get_enum_type([item.value for item in list(ActionType)]))

    with self.argument_context('cdn waf policy rate-limit-rule set') as c:
        c.argument('match_conditions', options_list=['-m', '--match-condition'], action=MatchConditionAction, nargs='+')
        c.argument('priority', type=int, validator=validate_priority)
        c.argument('action', arg_type=get_enum_type([item.value for item in list(ActionType)]))
        c.argument('request_threshold', type=int)
        c.argument('duration', type=int)
