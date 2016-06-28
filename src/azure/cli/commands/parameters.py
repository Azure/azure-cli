import argparse
import re

# pylint: disable=line-too-long
from azure.cli.commands import CliArgumentType, register_cli_argument
from azure.cli.commands.validators import validate_tag, validate_tags
from azure.cli._util import CLIError
from azure.cli.commands.client_factory import (get_subscription_service_client,
                                               get_mgmt_service_client)
from azure.cli.commands.validators import generate_deployment_name
from azure.mgmt.resource.subscriptions import SubscriptionClient

from azure.mgmt.resource.resources import ResourceManagementClient
from azure.cli.application import APPLICATION

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

resource_group_name_type = CliArgumentType(
    options_list=('--resource-group', '-g'),
    completer=get_resource_group_completion_list,
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
register_cli_argument('', 'deployment_name', deployment_name_type)


def split_id_rg_rn_crn(idval):
    raw_parts = idval.split('/')
    result = []
    try:
        for id_part in (4, 8, 10):
            result.append(raw_parts[id_part])
    except IndexError:
        pass

    return result

def register_id_parameter(command_name, *arguments, **kwargs):

    class SplitAction(argparse.Action): #pylint: disable=too-few-public-methods

        def __call__(self, parser, namespace, values, option_string=None):
            split_func_or_regex = kwargs.get('split_func_or_regex', split_id_rg_rn_crn)
            if callable(split_func_or_regex):
                parts = split_func_or_regex(values)
            else:
                parts = re.match(split_func_or_regex, values)

            if parts and len(parts) >= len(arguments):
                for name, value in zip(arguments, parts):
                    setattr(namespace, name, value)
            else:
                setattr(namespace, arguments[-1], values)

    def command_loaded_handler(command_table):
        command = command_table[command_name]
        required_arguments = []
        optional_arguments = []
        for argument in arguments:
            arg = command.arguments[argument]
            if arg.options.get('required', False):
                required_arguments.append(arg)
            else:
                optional_arguments.append(arg)
            arg.required = False

        last_arg = command.arguments[arguments[-1]]
        command.arguments.pop(arguments[-1])
        arguments_if_not_id_specified = []
        for non_last_arg in arguments[:-1]:
            arg = command.arguments[non_last_arg]
            option_metavar = '{} {}'.format(arg.options_list[0], arg.options.get('metavar', arg.name.upper()))
            if not arg in required_arguments:
                option_metavar = '[{}]'.format(option_metavar)
            arguments_if_not_id_specified.append(option_metavar)
        metavar = '(RESOURCE_ID | {} {})'.format(
            last_arg.options.get('metavar', last_arg.name.upper()),
            ' '.join(arguments_if_not_id_specified))

        def required_values_validator(namespace):
            for arg in required_arguments:
                if getattr(namespace, arg.name, None) is None:
                    raise CLIError('{} is required if {} is not specified'.format(arg.name.upper(), 'RESOURCE_ID'))

        command.add_argument(param_name=argparse.SUPPRESS,
                             metavar=metavar,
                             help='ResourceId or {}'.format(last_arg.options.get('help', last_arg.options.get('metavar', 'Resource Name'))),
                             action=SplitAction,
                             validator=required_values_validator)
        APPLICATION.remove(APPLICATION.COMMAND_TABLE_LOADED, command_loaded_handler)

    APPLICATION.register(APPLICATION.COMMAND_TABLE_LOADED, command_loaded_handler)
    