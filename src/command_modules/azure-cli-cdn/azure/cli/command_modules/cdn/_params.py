# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import argparse

from azure.mgmt.cdn.models import QueryStringCachingBehavior, SkuName

from azure.cli.core.commands.parameters import get_three_state_flag, tags_type, get_enum_type
from azure.cli.core.commands.validators import get_default_location_from_resource_group

from knack.arguments import CLIArgumentType

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

        deep_created_origin = DeepCreatedOrigin('origin', values[0], http_port=80, https_port=443)
        if len(values) > 1:
            deep_created_origin.http_port = int(values[1])
        if len(values) > 2:
            deep_created_origin.https_port = int(values[2])
        return deep_created_origin


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
        c.argument('endpoint_name', name_arg_type, id_part='name', help='Name of the CDN endpoint.')
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('origins', options_list='--origin', nargs='+', action=OriginType, validator=validate_origin,
                   help='Endpoint origin specified by the following space delimited 3 '
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

    with self.argument_context('cdn endpoint create') as c:
        c.argument('name', name_arg_type, id_part='name', help='Name of the CDN endpoint.')

    with self.argument_context('cdn endpoint load') as c:
        c.argument('content_paths', nargs='+')

    with self.argument_context('cdn endpoint purge') as c:
        c.argument('content_paths', nargs='+')

    # Custom Domain #

    with self.argument_context('cdn custom-domain') as c:
        c.argument('custom_domain_name', name_arg_type, id_part=None, help='Name of the custom domain.')

    with self.argument_context('cdn custom-domain create') as c:
        c.argument('location', validator=get_default_location_from_resource_group)

    # Origin #
    with self.argument_context('cdn origin') as c:
        c.argument('origin_name', name_arg_type, id_part='name')
