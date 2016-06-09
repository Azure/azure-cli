import argparse
import time
import random

# pylint: disable=line-too-long
from azure.cli.commands import CliArgumentType, register_cli_argument
from azure.cli.commands.validators import validate_tag, validate_tags
from azure.cli.commands.client_factory import (get_subscription_service_client,
                                               get_mgmt_service_client)
from azure.mgmt.resource.subscriptions import (SubscriptionClient,
                                               SubscriptionClientConfiguration)

from azure.mgmt.resource.resources import (ResourceManagementClient,
                                           ResourceManagementClientConfiguration)

def get_subscription_locations():
    subscription_client, subscription_id = get_subscription_service_client(SubscriptionClient, SubscriptionClientConfiguration)
    return list(subscription_client.subscriptions.list_locations(subscription_id))

def get_location_completion_list(prefix, **kwargs):#pylint: disable=unused-argument
    result = get_subscription_locations()
    return [l.name for l in result]

def get_resource_groups():
    rcf = get_mgmt_service_client(ResourceManagementClient, ResourceManagementClientConfiguration)
    return list(rcf.resource_groups.list())

def get_resource_group_completion_list(prefix, **kwargs):#pylint: disable=unused-argument
    result = get_resource_groups()
    return [l.name for l in result]

resource_group_name_type = CliArgumentType(
    options_list=('--resource-group', '-g'),
    completer=get_resource_group_completion_list,
    help='Name of resource group')

name_type = CliArgumentType(options_list=('--name', '-n'), help='the primary resource name')

location_type = CliArgumentType(
    options_list=('--location', '-l'),
    completer=get_location_completion_list,
    help='Location.', metavar='LOCATION')

tags_type = CliArgumentType(
    type=validate_tags,
    help='multiple semicolon separated tags in \'key[=value]\' format. Omit value to clear tags.',
    nargs='?',
    const=''
)

tag_type = CliArgumentType(
    type=validate_tag,
    help='a single tag in \'key[=value]\' format. Omit value to clear tags.',
    nargs='?',
    const=''
)

register_cli_argument('', 'resource_group_name', resource_group_name_type)
register_cli_argument('', 'location', location_type)
register_cli_argument('', 'deployment_name',
                      CliArgumentType(help=argparse.SUPPRESS, required=False,
                                      default='azurecli' + str(time.time())
                                      + str(random.randint(1, 100000))))
