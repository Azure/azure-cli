# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import argparse

from knack.arguments import CLIArgumentType

from azure.mgmt.cdn.models import QueryStringCachingBehavior, SkuName

from azure.cli.core.commands.parameters import get_three_state_flag, tags_type, get_enum_type
from azure.cli.core.commands.validators import get_default_location_from_resource_group

from ._validators import validate_origin


# pylint:disable=protected-access
# pylint:disable=too-few-public-methods
class OriginType(argparse._AppendAction):
    def __call__(self, parser, namespace, values, option_string=None):
        deep_created_origin = self.get_origin(values, option_string)
        super(OriginType, self).__call__(parser, namespace, deep_created_origin, option_string)

    def get_origin(self, values, option_string):
        from azure.mgmt.cdn.models import DeepCreatedOrigin

        if not 1 <= len(values) <= 3:
            msg = '%s takes 1, 2 or 3 values, %d given'
            raise argparse.ArgumentError(self, msg % (option_string, len(values)))

        deep_created_origin = DeepCreatedOrigin(name='origin', host_name=values[0], http_port=80, https_port=443)
        if len(values) > 1:
            deep_created_origin.http_port = int(values[1])
        if len(values) > 2:
            deep_created_origin.https_port = int(values[2])
        return deep_created_origin


# pylint:disable=too-many-statements
def load_arguments(self, _):

    name_arg_type = CLIArgumentType(options_list=('--name', '-n'), metavar='NAME')
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

        caching_behavior = [item.value for item in list(QueryStringCachingBehavior)]
        c.argument('query_string_caching_behavior', options_list='--query-string-caching',
                   arg_type=get_enum_type(caching_behavior))
        c.argument('content_types_to_compress', nargs='+')
        c.argument('profile_name', help=profile_name_help, id_part='name')

    with self.argument_context('cdn endpoint rule') as c:
        c.argument('rule_name', help='Name of the rule.')
        c.argument('order', help='The order of the rule. The order number must start from 0 and consecutive.\
                    Rule with higher order will be applied later.')
        c.argument('match_variable', help='Name of the match condition.')
        c.argument('operator', help='Operator of the match condition.')
        c.argument('selector', help='Selector of the match condition.')
        c.argument('match_values', help='Match values of the match condition (comma separated).')
        c.argument('transform', arg_type=get_enum_type(['Lowercase', 'Uppercase']),
                   help='Transform to apply before matching.')
        c.argument('negate_condition', arg_type=get_three_state_flag(), options_list='--negate-condition',
                   help='If true, negates the condition')
        c.argument('action_name', help='Name of the action.')
        c.argument('cache_behavior', arg_type=get_enum_type(['BypassCache', 'Override', 'SetIfMissing']))
        c.argument('cache_duration', help='The duration for which the content needs to be cached. \
                   Allowed format is [d.]hh:mm:ss.')
        c.argument('header_action', arg_type=get_enum_type(['Append', 'Overwrite', 'Delete']))
        c.argument('header_name', help='Name of the header to modify.')
        c.argument('header_value', help='Value of the header.')
        c.argument('redirect_type',
                   arg_type=get_enum_type(['Moved', 'Found', 'TemporaryRedirect', 'PermanentRedirect']))
        c.argument('redirect_protocol', arg_type=get_enum_type(['MatchRequest', 'Http', 'Https']))
        c.argument('custom_hostname', help='Host to redirect. \
                   Leave empty to use the incoming host as the destination host.')
        c.argument('custom_path', help='The full path to redirect. Path cannot be empty and must start with /. \
                   Leave empty to use the incoming path as destination path.')
        c.argument('custom_querystring', help='The set of query strings to be placed in the redirect URL. \
                   leave empty to preserve the incoming query string.')
        c.argument('custom_fragment', help='Fragment to add to the redirect URL.')
        c.argument('query_string_behavior', arg_type=get_enum_type(['Include', 'IncludeAll', 'Exclude', 'ExcludeAll']))
        c.argument('query_parameters', help='Query parameters to include or exclude (comma separated).')
        c.argument('source-pattern', help='A request URI pattern that identifies the type of \
                   requests that may be rewritten.')
        c.argument('destination', help='The destination path to be used in the rewrite.')
        c.argument('preserve_unmatched_path', arg_type=get_three_state_flag(), options_list='--preserve-unmatched-path',
                   help='If True, the remaining path after the source pattern '
                        'will be appended to the new destination path.')

    with self.argument_context('cdn endpoint create') as c:
        c.argument('name', name_arg_type, id_part='name', help='Name of the CDN endpoint.')

    with self.argument_context('cdn endpoint list') as c:
        c.argument('profile_name', id_part=None)

    # Custom Domain #

    with self.argument_context('cdn custom-domain') as c:
        c.argument('custom_domain_name', name_arg_type, id_part=None, help='Name of the custom domain.')

    with self.argument_context('cdn custom-domain create') as c:
        c.argument('location', validator=get_default_location_from_resource_group)

    # Origin #
    with self.argument_context('cdn origin') as c:
        c.argument('origin_name', name_arg_type, id_part='name')
