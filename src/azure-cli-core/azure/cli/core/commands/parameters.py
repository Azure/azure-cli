#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
import argparse
import platform

from azure.cli.core.commands import CliArgumentType, register_cli_argument
from azure.cli.core.commands.validators import validate_tag, validate_tags
from azure.cli.core._util import CLIError
from azure.cli.core.commands.validators import generate_deployment_name

def get_subscription_locations():
    from azure.cli.core.commands.client_factory import get_subscription_service_client
    from azure.mgmt.resource.subscriptions import SubscriptionClient
    subscription_client, subscription_id = get_subscription_service_client(SubscriptionClient)
    return list(subscription_client.subscriptions.list_locations(subscription_id))

def get_location_completion_list(prefix, **kwargs):#pylint: disable=unused-argument
    result = get_subscription_locations()
    return [l.name for l in result]

def location_name_type(name):
    if ' ' in name:
        # if display name is provided, attempt to convert to short form name
        name = next((l.name for l in get_subscription_locations() if l.display_name.lower() == name.lower()), name)
    return name

def get_one_of_subscription_locations():
    result = get_subscription_locations()
    if result:
        return next((r.name for r in result if r.name.lower() == 'westus'), result[0].name)
    else:
        raise CLIError('Current subscription does not have valid location list')

def get_resource_groups():
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.resource.resources import ResourceManagementClient
    rcf = get_mgmt_service_client(ResourceManagementClient)
    return list(rcf.resource_groups.list())

def get_resource_group_completion_list(prefix, **kwargs):#pylint: disable=unused-argument
    result = get_resource_groups()
    return [l.name for l in result]

def get_resources_in_resource_group(resource_group_name, resource_type=None):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.resource.resources import ResourceManagementClient
    rcf = get_mgmt_service_client(ResourceManagementClient)
    filter_str = "resourceType eq '{}'".format(resource_type) if resource_type else None
    return list(rcf.resource_groups.list_resources(resource_group_name, filter=filter_str))

def get_resources_in_subscription(resource_type=None):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.resource.resources import ResourceManagementClient
    rcf = get_mgmt_service_client(ResourceManagementClient)
    filter_str = "resourceType eq '{}'".format(resource_type) if resource_type else None
    return list(rcf.resources.list(filter=filter_str))

def get_resource_name_completion_list(resource_type=None):
    def completer(prefix, action, parsed_args, **kwargs):#pylint: disable=unused-argument
        if getattr(parsed_args, 'resource_group_name', None):
            rg = parsed_args.resource_group_name
            return [r.name for r in get_resources_in_resource_group(rg, resource_type=resource_type)]
        else:
            return [r.name for r in get_resources_in_subscription(resource_type=resource_type)]
    return completer

def get_generic_completion_list(generic_list):
    def completer(prefix, action, parsed_args, **kwargs): # pylint: disable=unused-argument
        return generic_list
    return completer

class CaseInsenstiveList(list): # pylint: disable=too-few-public-methods
    def __contains__(self, other):
        return next((True for x in self if other.lower() == x.lower()), False)

def enum_choice_list(data):
    """ Creates the argparse choices and type kwargs for a supplied enum type or list of strings. """
    # transform enum types, otherwise assume list of string choices
    try:
        choices = [x.value for x in data]
    except AttributeError:
        choices = data
    def _type(value):
        return next((x for x in choices if x.lower() == value.lower()), value) if value else value
    params = {
        'choices': CaseInsenstiveList(choices),
        'type': _type
    }
    return params

class IgnoreAction(argparse.Action): # pylint: disable=too-few-public-methods
    def __call__(self, parser, namespace, values, option_string=None):
        raise argparse.ArgumentError(None, 'unrecognized argument: {} {}'.format(
            option_string, values or ''))

# GLOBAL ARGUMENT DEFINTIONS

ignore_type = CliArgumentType(
    help=argparse.SUPPRESS,
    nargs='?',
    action=IgnoreAction,
    required=False)

resource_group_name_type = CliArgumentType(
    options_list=('--resource-group', '-g'),
    completer=get_resource_group_completion_list,
    id_part='resource_group',
    help='Name of resource group')

name_type = CliArgumentType(options_list=('--name', '-n'), help='the primary resource name')

location_type = CliArgumentType(
    options_list=('--location', '-l'),
    completer=get_location_completion_list,
    type=location_name_type,
    help='Location.', metavar='LOCATION')

deployment_name_type = CliArgumentType(
    help=argparse.SUPPRESS,
    required=False,
    validator=generate_deployment_name
)

quotes = '""' if platform.system() == 'Windows' else "''"
quote_text = 'Use {} to clear existing tags.'.format(quotes)

tags_type = CliArgumentType(
    validator=validate_tags,
    help="space separated tags in 'key[=value]' format. {}".format(quote_text),
    nargs='*'
)

tag_type = CliArgumentType(
    type=validate_tag,
    help="a single tag in 'key[=value]' format. {}".format(quote_text),
    nargs='?',
    const=''
)

register_cli_argument('', 'resource_group_name', resource_group_name_type)
register_cli_argument('', 'location', location_type)
register_cli_argument('', 'deployment_name', deployment_name_type)


