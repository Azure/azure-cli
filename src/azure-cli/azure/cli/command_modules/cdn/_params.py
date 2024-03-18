# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from knack.arguments import CLIArgumentType

from azure.mgmt.cdn.models import (QueryStringCachingBehavior, DeliveryRuleAction,
                                   ForwardingProtocol, DeliveryRuleCondition,
                                   AfdQueryStringCachingBehavior, Transform,
                                   MatchProcessingBehavior)

from azure.cli.core.commands.parameters import get_three_state_flag, get_enum_type


# pylint:disable=too-many-statements
def load_arguments(self, _):
    name_arg_type = CLIArgumentType(options_list=('--name', '-n'), metavar='NAME')
    rule_name_type = CLIArgumentType(options_list=('--rule-name'), metavar='RULE_NAME')
    profile_name_help = 'Name of the CDN profile which is unique within the resource group.'

    # Endpoint #

    with self.argument_context('cdn endpoint rule') as c:
        configure_rule_parameters(c, False)

    # Custom Domain #

    with self.argument_context('cdn custom-domain enable-https') as c:
        c.argument('profile_name', id_part=None, help='Name of the parent profile.')
        c.argument('endpoint_name', help='Name of the parent endpoint.')
        c.argument('custom_domain_name', name_arg_type, help='Resource name of the custom domain.')
        c.argument('min_tls_version',
                   help='The minimum TLS version required for the custom domain.',
                   arg_type=get_enum_type(['none', '1.0', '1.2']))
        c.argument('user_cert_protocol_type',
                   arg_group='Bring Your Own Certificate',
                   help='The protocol type of the certificate.',
                   arg_type=get_enum_type(['sni', 'ip']))
        c.argument('user_cert_subscription_id',
                   arg_group='Bring Your Own Certificate',
                   help='The subscription id of the KeyVault certificate')
        c.argument('user_cert_group_name',
                   arg_group='Bring Your Own Certificate',
                   help='The resource group of the KeyVault certificate')
        c.argument('user_cert_vault_name',
                   arg_group='Bring Your Own Certificate',
                   help='The vault name of the KeyVault certificate')
        c.argument('user_cert_secret_name',
                   arg_group='Bring Your Own Certificate',
                   help='The secret name of the KeyVault certificate')
        c.argument('user_cert_secret_version',
                   arg_group='Bring Your Own Certificate',
                   help='The secret version of the KeyVault certificate, If not specified, the "Latest" version will '
                        'always been used and the deployed certificate will be automatically rotated to the latest '
                        'version when a newer version of the certificate is available.')

    # AFDX
    # AFD Rules #
    with self.argument_context('afd rule') as c:
        c.argument('profile_name', help=profile_name_help, id_part='name')
        c.argument('rule_set_name', id_part='child_name_1', help='Name of the rule set.')
        configure_rule_parameters(c, True)
        c.argument('rule_name', rule_name_type, id_part='child_name_2', help='Name of the rule.')
        c.argument('match_processing_behavior',
                   arg_type=get_enum_type(MatchProcessingBehavior),
                   help='Indicate whether rules engine should continue to run the remaining rules or stop if matched.'
                        ' Defaults to Continue.')

    with self.argument_context('afd rule condition list') as c:
        c.argument('profile_name', id_part=None)
        c.argument('rule_set_name', id_part=None)
        c.argument('rule_name', id_part=None)

    with self.argument_context('afd rule action list') as c:
        c.argument('profile_name', id_part=None)
        c.argument('rule_set_name', id_part=None)
        c.argument('rule_name', id_part=None)


# pylint: disable=protected-access
def configure_rule_parameters(c, is_afdx):
    c.argument('rule_name', help='Name of the rule.')
    c.argument('order', type=int,
               help='The order in which the rules are applied for the endpoint. Possible values {0,1,2,3,………}. '
               'A rule with a lower order will be applied before one with a higher order. '
               'Rule with order 0 is a special rule. '
               'It does not require any condition and actions listed in it will always be applied.')

    if is_afdx:
        c.argument('match_variable', arg_group="Match Condition",
                   help='Name of the match condition: '
                        'https://docs.microsoft.com/en-us/azure/frontdoor/rules-match-conditions',
                   arg_type=get_enum_type(DeliveryRuleCondition._subtype_map["name"].keys()))
    else:
        c.argument('match_variable', arg_group="Match Condition",
                   help='Name of the match condition: '
                        'https://docs.microsoft.com/en-us/azure/cdn/cdn-standard-rules-engine-match-conditions',
                   arg_type=get_enum_type(DeliveryRuleCondition._subtype_map["name"].keys()))

    c.argument('operator', arg_group="Match Condition", help='Operator of the match condition.')
    c.argument('selector', arg_group="Match Condition", help='Selector of the match condition.')
    c.argument('match_values', arg_group="Match Condition", nargs='+',
               help='Match values of the match condition. e.g, space separated values "GET" "HTTP"')

    if not is_afdx:
        c.argument('transform', arg_group="Match Condition", arg_type=get_enum_type(['Lowercase', 'Uppercase']),
                   nargs='+', help='Transform to apply before matching.')
    else:
        transforms = [item.value for item in list(Transform)]
        c.argument('transforms', arg_group="Match Condition", arg_type=get_enum_type(transforms),
                   nargs='+', help='Transform to apply before matching.')

    c.argument('negate_condition', arg_group="Match Condition", arg_type=get_three_state_flag(),
               help='If true, negates the condition')

    all_actions = list(DeliveryRuleAction._subtype_map["name"].keys())
    if is_afdx:
        excldued_actions = ["UrlSigning", "CacheExpiration", "CacheKeyQueryString", "OriginGroupOverride"]
        c.argument('action_name', arg_group="Action",
                   help='The name of the action for the delivery rule: '
                        'https://docs.microsoft.com/en-us/azure/frontdoor/front-door-rules-engine-actions',
                   arg_type=get_enum_type([action for action in all_actions if action not in excldued_actions]))

        c.argument('cache_behavior', arg_group="Action",
                   arg_type=get_enum_type(['HonorOrigin', 'OverrideAlways', 'OverrideIfOriginMissing']),
                   help='Caching behavior for the requests.')
        c.argument('query_string_caching_behavior',
                   arg_group="Action",
                   arg_type=get_enum_type(AfdQueryStringCachingBehavior),
                   help="Defines how CDN caches requests that include query strings. "
                        "You can ignore any query strings when caching, "
                        "bypass caching to prevent requests that contain query strings from being cached, "
                        "or cache every request with a unique URL.")

        c.argument('query_parameters', arg_group="Action",
                   nargs='*',
                   help="query parameters to include or exclude")
        c.argument('forwarding_protocol', arg_group="Action",
                   arg_type=get_enum_type(ForwardingProtocol),
                   help="Protocol this rule will use when forwarding traffic to backends.")
        c.argument(
            'is_compression_enabled', arg_group="Action",
            arg_type=get_three_state_flag(),
            options_list='--enable-compression',
            help='Indicates whether content compression is enabled on AzureFrontDoor. Default value is false. '
                 'If compression is enabled, content will be served as compressed if user requests for a '
                 "compressed version. Content won't be compressed on AzureFrontDoor when requested content is "
                 'smaller than 1 byte or larger than 1 MB.')
        c.argument('enable_caching', arg_type=get_three_state_flag(invert=False),
                   options_list='--enable-caching',
                   arg_group="Action",
                   help='Indicates whether to enable caching on the route.')
    else:
        excldued_actions = ["RouteConfigurationOverride", "UrlSigning"]
        c.argument('action_name', arg_group="Action",
                   help='The name of the action for the delivery rule: '
                        'https://docs.microsoft.com/en-us/azure/cdn/cdn-standard-rules-engine-actions',
                   arg_type=get_enum_type([action for action in all_actions if action not in excldued_actions]))

        # CacheExpirationAction parameters
        c.argument('cache_behavior', arg_group="Action",
                   arg_type=get_enum_type(['BypassCache', 'Override', 'SetIfMissing']),
                   help='Caching behavior for the requests.')
        c.argument('query_string_caching_behavior',
                   options_list='--query-string-caching',
                   arg_type=get_enum_type(QueryStringCachingBehavior),
                   help="Defines how CDN caches requests that include query strings. "
                        "You can ignore any query strings when caching, "
                        "bypass caching to prevent requests that contain query strings from being cached, "
                        "or cache every request with a unique URL.")

        # CacheKeyQueryStringAction parameters
        c.argument('query_parameters', arg_group="Action",
                   help='Query parameters to include or exclude (comma separated).')
        c.argument('query_string_behavior', arg_group="Action",
                   arg_type=get_enum_type(['Include', 'IncludeAll', 'Exclude', 'ExcludeAll']),
                   help='Query string behavior for the requests.')

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

    c.argument('source_pattern', arg_group="Action",
               help='A request URI pattern that identifies the type of requests that may be rewritten.')
    c.argument('destination', arg_group="Action", help='The destination path to be used in the rewrite.')
    c.argument('preserve_unmatched_path', arg_group="Action",
               arg_type=get_three_state_flag(),
               help='If True, the remaining path after the source \
               pattern will be appended to the new destination path.')
    c.argument('index', type=int, help='The index of the condition/action')
    c.argument('origin_group', arg_group="Action",
               help='Name or ID of the OriginGroup that would override the default OriginGroup')
