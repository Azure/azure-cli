# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import argparse

from azure.mgmt.cdn.models import (QueryStringCachingBehavior, SkuName)

from azure.cli.core.commands import (register_cli_argument, CliArgumentType)
from azure.cli.core.commands.parameters import enum_choice_list
from azure.cli.core.commands.validators import get_default_location_from_resource_group
from ._validators import validate_origin


class OriginType(argparse._AppendAction):
    def __call__(self, parser, namespace, values, option_string=None):
        from azure.mgmt.cdn.models import DeepCreatedOrigin

        if not (1 <= len(values) <= 3):
            msg = '%s takes 1, 2 or 3 values, %d given'
            raise argparse.ArgumentError(self, msg % (option_string, len(values)))

        deep_created_origin = DeepCreatedOrigin('origin', values[0], http_port=80, https_port=443)
        if len(values) > 1:
            deep_created_origin.http_port = int(values[2])
        if len(values) > 2:
            deep_created_origin.https_port = int(values[3])
        super(OriginType, self).__call__(parser, namespace, deep_created_origin, option_string)

name_arg_type = CliArgumentType(options_list=('--name', '-n'), metavar='NAME')

register_cli_argument('cdn', 'name', name_arg_type, id_part='name')

register_cli_argument('cdn profile create',
                      'sku',
                      **enum_choice_list([item.value for item in SkuName.__members__.values()]))
register_cli_argument('cdn profile create', 'location',
                      validator=get_default_location_from_resource_group)
register_cli_argument('cdn profile', 'profile_name', name_arg_type, id_part='name')

register_cli_argument('cdn custom-domain create', 'location',
                      validator=get_default_location_from_resource_group)

register_cli_argument('cdn endpoint', 'endpoint_name', name_arg_type, id_part='name')

endpoint_create = 'cdn endpoint create'
register_cli_argument(endpoint_create, 'location',
                      validator=get_default_location_from_resource_group)
register_cli_argument(endpoint_create,
                      'origins',
                      options_list='--origin',
                      nargs='+',
                      action=OriginType,
                      validator=validate_origin,
                      help='Endpoint origin specified by the following space delimited 3 \
tuple: `www.example.com http_port https_port`. The HTTP and HTTPs ports are \
optional and will default to 80 and 443 respectively.')
register_cli_argument(endpoint_create, 'is_http_allowed',
                      options_list='--no-http',
                      action='store_false',
                      help='Indicates whether HTTP traffic is not allowed on the endpoint. \
Default is to allow HTTP traffic.')
register_cli_argument(endpoint_create, 'is_https_allowed',
                      options_list='--no-https',
                      action='store_false',
                      help='Indicates whether HTTPS traffic is not allowed on the endpoint. \
Default is to allow HTTPS traffic.')
register_cli_argument(endpoint_create, 'is_compression_enabled',
                      options_list='--enable-compression',
                      action='store_true',
                      help='If compression is enabled, content will be served as compressed if \
user requests for a compressed version. Content won\'t be compressed on CDN when requested content \
is smaller than 1 byte or larger than 1 MB.')
caching_behavior = [item.value for item in QueryStringCachingBehavior.__members__.values()]
register_cli_argument(endpoint_create,
                      'query_string_caching_behavior',
                      options_list='--query-string-caching',
                      **enum_choice_list(caching_behavior))
register_cli_argument(endpoint_create, 'content_types_to_compress', nargs='+')
