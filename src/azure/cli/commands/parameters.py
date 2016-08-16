#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

import argparse
import platform

# pylint: disable=line-too-long
from azure.cli.commands import CliArgumentType, register_cli_argument
from azure.cli.commands.validators import validate_tag, validate_tags
from azure.cli._util import CLIError
from azure.cli.commands.client_factory import (get_subscription_service_client,
                                               get_mgmt_service_client)
from azure.cli.commands.validators import generate_deployment_name
from azure.mgmt.resource.subscriptions import SubscriptionClient

from azure.mgmt.resource.resources import ResourceManagementClient

def get_subscription_locations():
    subscription_client, subscription_id = get_subscription_service_client(SubscriptionClient)
    return list(subscription_client.subscriptions.list_locations(subscription_id))

def get_location_completion_list(prefix, **kwargs):#pylint: disable=unused-argument
    result = get_subscription_locations()
    return [l.name for l in result]

def get_one_of_subscription_locations():
    result = get_subscription_locations()
    if result:
        return next((r.name for r in result if r.name.lower() == 'westus'), result[0].name)
    else:
        raise CLIError('Current subscription does not have valid location list')

def get_resource_groups():
    rcf = get_mgmt_service_client(ResourceManagementClient)
    return list(rcf.resource_groups.list())

def get_resource_group_completion_list(prefix, **kwargs):#pylint: disable=unused-argument
    result = get_resource_groups()
    return [l.name for l in result]

def get_resources_in_resource_group(resource_group_name, resource_type=None):
    rcf = get_mgmt_service_client(ResourceManagementClient)
    filter_str = "resourceType eq '{}'".format(resource_type) if resource_type else None
    return list(rcf.resource_groups.list_resources(resource_group_name, filter=filter_str))

def get_resources_in_subscription(resource_type=None):
    rcf = get_mgmt_service_client(ResourceManagementClient)
    filter_str = "resourceType eq '{}'".format(resource_type) if resource_type else None
    return list(rcf.resources.list(filter=filter_str))

def get_resource_name_completion_list(resource_type=None):
    def completer(prefix, action, parsed_args, **kwargs):#pylint: disable=unused-argument
        if parsed_args.resource_group_name:
            rg = parsed_args.resource_group_name
            return [r.name for r in get_resources_in_resource_group(rg, resource_type=resource_type)]
        else:
            return [r.name for r in get_resources_in_subscription(resource_type=resource_type)]
    return completer

def get_enum_type_completion_list(enum_type=None):
    ENUM_MAPPING_KEY = '_value2member_map_'
    def completer(prefix, action, parsed_args, **kwargs): # pylint: disable=unused-argument
        return list(enum_type.__dict__[ENUM_MAPPING_KEY].keys())
    return completer

def get_enum_choices(enum_type):
    return [x.value for x in enum_type]

resource_group_name_type = CliArgumentType(
    options_list=('--resource-group', '-g'),
    completer=get_resource_group_completion_list,
    id_part='resource_group',
    help='Name of resource group')

name_type = CliArgumentType(options_list=('--name', '-n'), help='the primary resource name')

location_type = CliArgumentType(
    options_list=('--location', '-l'),
    completer=get_location_completion_list,
    help='Location.', metavar='LOCATION')

deployment_name_type = CliArgumentType(
    help=argparse.SUPPRESS,
    required=False,
    validator=generate_deployment_name
)

quotes = '""' if platform.system() == 'Windows' else "''"
quote_text = 'Use {} to clear existing tags.'.format(quotes)

tags_type = CliArgumentType(
    type=validate_tags,
    help='multiple semicolon separated tags in \'key[=value]\' format.  {}'.format(quote_text),
    nargs='?',
    const=''
)

tag_type = CliArgumentType(
    type=validate_tag,
    help='a single tag in \'key[=value]\' format.  {}'.format(quote_text),
    nargs='?',
    const=''
)

register_cli_argument('', 'resource_group_name', resource_group_name_type)
register_cli_argument('', 'location', location_type)
register_cli_argument('', 'deployment_name', deployment_name_type)


