# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import argparse
import platform

from azure.cli.core.commands import \
    (CliArgumentType, register_cli_argument)
from azure.cli.core.commands.validators import validate_tag, validate_tags
from azure.cli.core.util import CLIError
from azure.cli.core.commands.validators import generate_deployment_name
from azure.cli.core.profiles import get_sdk, ResourceType, supported_api_version
import azure.cli.core.azlogging as azlogging

logger = azlogging.get_az_logger(__name__)


def get_subscription_locations():
    from azure.cli.core.commands.client_factory import get_subscription_service_client
    subscription_client, subscription_id = get_subscription_service_client()
    return list(subscription_client.subscriptions.list_locations(subscription_id))


def get_location_completion_list(prefix, **kwargs):  # pylint: disable=unused-argument
    result = get_subscription_locations()
    return [l.name for l in result]


def file_type(path):
    import os
    return os.path.expanduser(path)


def location_name_type(name):
    if ' ' in name:
        # if display name is provided, attempt to convert to short form name
        name = next((l.name for l in get_subscription_locations()
                     if l.display_name.lower() == name.lower()), name)
    return name


def get_one_of_subscription_locations():
    result = get_subscription_locations()
    if result:
        return next((r.name for r in result if r.name.lower() == 'westus'), result[0].name)
    else:
        raise CLIError('Current subscription does not have valid location list')


def get_resource_groups():
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    rcf = get_mgmt_service_client(ResourceType.MGMT_RESOURCE_RESOURCES)
    return list(rcf.resource_groups.list())


def get_resource_group_completion_list(prefix, **kwargs):  # pylint: disable=unused-argument
    result = get_resource_groups()
    return [l.name for l in result]


def get_resources_in_resource_group(resource_group_name, resource_type=None):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    rcf = get_mgmt_service_client(ResourceType.MGMT_RESOURCE_RESOURCES)
    filter_str = "resourceType eq '{}'".format(resource_type) if resource_type else None
    if supported_api_version(ResourceType.MGMT_RESOURCE_RESOURCES, max_api='2016-09-01'):
        return list(rcf.resource_groups.list_resources(resource_group_name, filter=filter_str))
    return list(rcf.resources.list_by_resource_group(resource_group_name, filter=filter_str))


def get_resources_in_subscription(resource_type=None):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    rcf = get_mgmt_service_client(ResourceType.MGMT_RESOURCE_RESOURCES)
    filter_str = "resourceType eq '{}'".format(resource_type) if resource_type else None
    return list(rcf.resources.list(filter=filter_str))


def get_resource_name_completion_list(resource_type=None):
    def completer(prefix, action, parsed_args, **kwargs):  # pylint: disable=unused-argument
        if getattr(parsed_args, 'resource_group_name', None):
            rg = parsed_args.resource_group_name
            return [r.name for r in get_resources_in_resource_group(rg, resource_type=resource_type)]
        return [r.name for r in get_resources_in_subscription(resource_type=resource_type)]
    return completer


def get_generic_completion_list(generic_list):
    def completer(prefix, action, parsed_args, **kwargs):  # pylint: disable=unused-argument
        return generic_list
    return completer


class CaseInsensitiveList(list):  # pylint: disable=too-few-public-methods

    def __contains__(self, other):
        return next((True for x in self if other.lower() == x.lower()), False)


def model_choice_list(resource_type, model_name):
    model = get_sdk(resource_type, model_name, mod='models')
    return enum_choice_list(model) if model else {}


def enum_choice_list(data):
    """ Creates the argparse choices and type kwargs for a supplied enum type or list of strings. """
    # transform enum types, otherwise assume list of string choices
    if not data:
        return {}
    try:
        choices = [x.value for x in data]
    except AttributeError:
        choices = data

    def _type(value):
        return next((x for x in choices if x.lower() == value.lower()), value) if value else value
    params = {
        'choices': CaseInsensitiveList(choices),
        'type': _type
    }
    return params


def enum_default(resource_type, enum_name, enum_val_name):
    mod = get_sdk(resource_type, enum_name, mod='models')
    try:
        return getattr(mod, enum_val_name).value
    except AttributeError:
        logger.debug('Skipping param default %s.%s for %s.', enum_name, enum_val_name, resource_type)
        return None


def three_state_flag(positive_label='true', negative_label='false', invert=False):
    """ Creates a flag-like argument that can also accept positive/negative values. This allows
    consistency between create commands that typically use flags and update commands that require
    positive/negative values without introducing breaking changes. Flag-like behavior always
    implies the affirmative unless invert=True then invert the logic.
    - positive_label: label for the positive value (ex: 'enabled')
    - negative_label: label for the negative value (ex: 'disabled')
    - invert: invert the boolean logic for the flag
    """
    choices = [positive_label, negative_label]

    # pylint: disable=too-few-public-methods
    class ThreeStateAction(argparse.Action):

        def __call__(self, parser, namespace, values, option_string=None):
            if invert:
                if values:
                    values = positive_label if values.lower() == negative_label else negative_label
                else:
                    values = values or negative_label
            else:
                values = values or positive_label
            setattr(namespace, self.dest, values.lower() == positive_label)

    params = {
        'choices': CaseInsensitiveList(choices),
        'nargs': '?',
        'action': ThreeStateAction
    }
    return params


class IgnoreAction(argparse.Action):  # pylint: disable=too-few-public-methods

    def __call__(self, parser, namespace, values, option_string=None):
        raise argparse.ArgumentError(None, 'unrecognized argument: {} {}'.format(
            option_string, values or ''))


# GLOBAL ARGUMENT DEFINITIONS

ignore_type = CliArgumentType(
    help=argparse.SUPPRESS,
    nargs='?',
    action=IgnoreAction,
    required=False)

resource_group_name_type = CliArgumentType(
    options_list=('--resource-group', '-g'),
    completer=get_resource_group_completion_list,
    id_part='resource_group',
    help="Name of resource group. You can configure the default group using `az configure --defaults group=<name>`",
    configured_default='group')

name_type = CliArgumentType(options_list=('--name', '-n'), help='the primary resource name')

location_type = CliArgumentType(
    options_list=('--location', '-l'),
    completer=get_location_completion_list,
    type=location_name_type,
    help="Location. You can configure the default location using `az configure --defaults location=<location>`",
    metavar='LOCATION',
    configured_default='location')

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

no_wait_type = CliArgumentType(
    options_list=('--no-wait', ),
    help='do not wait for the long running operation to finish',
    action='store_true'
)

register_cli_argument('', 'resource_group_name', resource_group_name_type)
register_cli_argument('', 'location', location_type)
register_cli_argument('', 'deployment_name', deployment_name_type)
