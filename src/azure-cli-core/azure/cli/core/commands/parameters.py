# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import argparse
import platform

from knack.arguments import CLIArgumentType, CaseInsensitiveList
from knack.log import get_logger
from knack.util import CLIError

from azure.cli.core.commands.validators import validate_tag, validate_tags
from azure.cli.core.commands.validators import generate_deployment_name
from azure.cli.core.decorators import Completer
from azure.cli.core.profiles import ResourceType

logger = get_logger(__name__)


def get_subscription_locations(cli_ctx):
    from azure.cli.core.commands.client_factory import get_subscription_service_client
    subscription_client, subscription_id = get_subscription_service_client(cli_ctx)
    return list(subscription_client.subscriptions.list_locations(subscription_id))


@Completer
def get_location_completion_list(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
    result = get_subscription_locations(cmd.cli_ctx)
    return [l.name for l in result]


def file_type(path):
    import os
    return os.path.expanduser(path)


def get_location_name_type(cli_ctx):
    def location_name_type(name):
        if ' ' in name:
            # if display name is provided, attempt to convert to short form name
            name = next((l.name for l in get_subscription_locations(cli_ctx)
                         if l.display_name.lower() == name.lower()), name)
        return name
    return location_name_type


def get_one_of_subscription_locations(cli_ctx):
    result = get_subscription_locations(cli_ctx)
    if result:
        return next((r.name for r in result if r.name.lower() == 'westus'), result[0].name)
    else:
        raise CLIError('Current subscription does not have valid location list')


def get_resource_groups(cli_ctx):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    rcf = get_mgmt_service_client(cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES)
    return list(rcf.resource_groups.list())


@Completer
def get_resource_group_completion_list(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
    result = get_resource_groups(cmd.cli_ctx)
    return [l.name for l in result]


def get_resources_in_resource_group(cli_ctx, resource_group_name, resource_type=None):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.cli.core.profiles import supported_api_version

    rcf = get_mgmt_service_client(cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES)
    filter_str = "resourceType eq '{}'".format(resource_type) if resource_type else None
    if supported_api_version(cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES, max_api='2016-09-01'):
        return list(rcf.resource_groups.list_resources(resource_group_name, filter=filter_str))
    return list(rcf.resources.list_by_resource_group(resource_group_name, filter=filter_str))


def get_resources_in_subscription(cli_ctx, resource_type=None):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    rcf = get_mgmt_service_client(cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES)
    filter_str = "resourceType eq '{}'".format(resource_type) if resource_type else None
    return list(rcf.resources.list(filter=filter_str))


def get_resource_name_completion_list(resource_type=None):

    @Completer
    def completer(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
        rg = getattr(namespace, 'resource_group_name', None)
        if rg:
            return [r.name for r in get_resources_in_resource_group(cmd.cli_ctx, rg, resource_type=resource_type)]
        return [r.name for r in get_resources_in_subscription(cmd.cli_ctx, resource_type)]

    return completer


def get_generic_completion_list(generic_list):

    @Completer
    def completer(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
        return generic_list
    return completer


def get_three_state_flag(positive_label='true', negative_label='false', invert=False, return_label=False):
    """ Creates a flag-like argument that can also accept positive/negative values. This allows
    consistency between create commands that typically use flags and update commands that require
    positive/negative values without introducing breaking changes. Flag-like behavior always
    implies the affirmative unless invert=True then invert the logic.
    - positive_label: label for the positive value (ex: 'enabled')
    - negative_label: label for the negative value (ex: 'disabled')
    - invert: invert the boolean logic for the flag
    - return_label: if true, return the corresponding label. Otherwise, return a boolean value
    """
    choices = [positive_label, negative_label]

    # pylint: disable=too-few-public-methods
    class ThreeStateAction(argparse.Action):

        def __call__(self, parser, namespace, values, option_string=None):
            values = values or positive_label
            is_positive = values.lower() == positive_label.lower()
            is_positive = not is_positive if invert else is_positive
            set_val = None
            if return_label:
                set_val = positive_label if is_positive else negative_label
            else:
                set_val = is_positive
            setattr(namespace, self.dest, set_val)

    params = {
        'choices': CaseInsensitiveList(choices),
        'nargs': '?',
        'action': ThreeStateAction
    }
    return CLIArgumentType(**params)


def get_enum_type(data, default=None):
    """ Creates the argparse choices and type kwargs for a supplied enum type or list of strings. """
    if not data:
        return None

    # transform enum types, otherwise assume list of string choices
    try:
        choices = [x.value for x in data]
    except AttributeError:
        choices = data

    # pylint: disable=too-few-public-methods
    class DefaultAction(argparse.Action):

        def __call__(self, parser, args, values, option_string=None):

            def _get_value(val):
                return next((x for x in self.choices if x.lower() == val.lower()), val)

            if isinstance(values, list):
                values = [_get_value(v) for v in values]
            else:
                values = _get_value(values)
            setattr(args, self.dest, values)

    def _type(value):
        return next((x for x in choices if x.lower() == value.lower()), value) if value else value

    default_value = None
    if default:
        default_value = next((x for x in choices if x.lower() == default.lower()), None)
        if not default_value:
            raise CLIError("Command authoring exception: urecognized default '{}' from choices '{}'"
                           .format(default, choices))
        arg_type = CLIArgumentType(choices=CaseInsensitiveList(choices), action=DefaultAction, default=default_value)
    else:
        arg_type = CLIArgumentType(choices=CaseInsensitiveList(choices), action=DefaultAction)
    return arg_type


# GLOBAL ARGUMENT DEFINITIONS

resource_group_name_type = CLIArgumentType(
    options_list=('--resource-group', '-g'),
    completer=get_resource_group_completion_list,
    id_part='resource_group',
    help="Name of resource group. You can configure the default group using `az configure --defaults group=<name>`",
    configured_default='group')

name_type = CLIArgumentType(options_list=('--name', '-n'), help='the primary resource name')


def get_location_type(cli_ctx):
    location_type = CLIArgumentType(
        options_list=('--location', '-l'),
        completer=get_location_completion_list,
        type=get_location_name_type(cli_ctx),
        help="Location. You can configure the default location using `az configure --defaults location=<location>`",
        metavar='LOCATION',
        configured_default='location')
    return location_type


deployment_name_type = CLIArgumentType(
    help=argparse.SUPPRESS,
    required=False,
    validator=generate_deployment_name
)

quotes = '""' if platform.system() == 'Windows' else "''"
quote_text = 'Use {} to clear existing tags.'.format(quotes)

tags_type = CLIArgumentType(
    validator=validate_tags,
    help="space separated tags in 'key[=value]' format. {}".format(quote_text),
    nargs='*'
)

tag_type = CLIArgumentType(
    type=validate_tag,
    help="a single tag in 'key[=value]' format. {}".format(quote_text),
    nargs='?',
    const=''
)

no_wait_type = CLIArgumentType(
    options_list=('--no-wait', ),
    help='do not wait for the long-running operation to finish',
    action='store_true'
)

zones_type = CLIArgumentType(
    options_list=['--zones', '-z'],
    nargs='+',
    help='Space separated list of availability zones into which to provision the resource.',
    choices=['1', '2', '3']
)

zone_type = CLIArgumentType(
    options_list=['--zone', '-z'],
    help='Availability zone into which to provision the resource.',
    choices=['1', '2', '3'],
    nargs=1
)
