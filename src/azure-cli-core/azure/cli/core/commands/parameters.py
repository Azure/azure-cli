# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import argparse
import platform

from knack.arguments import (
    CLIArgumentType, CaseInsensitiveList, ignore_type, ArgumentsContext)
from knack.log import get_logger
from knack.util import CLIError

from azure.cli.core import EXCLUDED_PARAMS
from azure.cli.core.commands.constants import CLI_PARAM_KWARGS, CLI_POSITIONAL_PARAM_KWARGS
from azure.cli.core.commands.validators import validate_tag, validate_tags, generate_deployment_name
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


# pylint: disable=redefined-builtin
def get_datetime_type(help=None, date=True, time=True, timezone=True):

    help_string = help + ' ' or ''
    accepted_formats = []
    if date:
        accepted_formats.append('date (yyyy-mm-dd)')
    if time:
        accepted_formats.append('time (hh:mm:ss.xxxxx)')
    if timezone:
        accepted_formats.append('timezone (+/-hh:mm)')
    help_string = help_string + 'Format: ' + ', '.join(accepted_formats)

    # pylint: disable=too-few-public-methods
    class DatetimeAction(argparse.Action):

        def __call__(self, parser, namespace, values, option_string=None):
            """ Parse a date value and return the ISO8601 string. """
            import dateutil.parser

            value_string = ' '.join(values)
            dt_val = None
            try:
                # attempt to parse ISO 8601
                dt_val = dateutil.parser.parse(value_string)
            except ValueError:
                pass

            # TODO: custom parsing attempts here

            if not dt_val:
                raise CLIError("Unable to parse: '{}'. Expected format: {}".format(value_string, help_string))

            # Issue warning if any supplied data will be ignored
            if not date and any([dt_val.day, dt_val.month, dt_val.year]):
                logger.warning('Date info will be ignored in %s.', value_string)

            if not time and any([dt_val.hour, dt_val.minute, dt_val.second, dt_val.microsecond]):
                logger.warning('Time info will be ignored in %s.', value_string)

            if not timezone and dt_val.tzinfo:
                logger.warning('Timezone info will be ignored in %s.', value_string)

            iso_string = dt_val.isoformat()
            setattr(namespace, self.dest, iso_string)

    return CLIArgumentType(action=DatetimeAction, nargs='+', help=help_string)


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
            raise CLIError("Command authoring exception: unrecognized default '{}' from choices '{}'"
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
    help="space-separated tags in 'key[=value]' format. {}".format(quote_text),
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
    help='Space-separated list of availability zones into which to provision the resource.',
    choices=['1', '2', '3']
)

zone_type = CLIArgumentType(
    options_list=['--zone', '-z'],
    help='Availability zone into which to provision the resource.',
    choices=['1', '2', '3'],
    nargs=1
)


def patch_arg_make_required(argument):
    argument.settings['required'] = True


def patch_arg_make_optional(argument):
    argument.settings['required'] = False


def patch_arg_update_description(description):
    def _patch_action(argument):
        argument.settings['help'] = description

    return _patch_action


class AzArgumentContext(ArgumentsContext):

    def __init__(self, command_loader, scope, **kwargs):
        from azure.cli.core.commands import _merge_kwargs as merge_kwargs
        super(AzArgumentContext, self).__init__(command_loader, scope)
        self.scope = scope  # this is called "command" in knack, but that is not an accurate name
        self.group_kwargs = merge_kwargs(kwargs, command_loader.module_kwargs, CLI_PARAM_KWARGS)
        self.is_stale = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.is_stale = True

    def _applicable(self):
        if self.command_loader.skip_applicability:
            return True
        command_name = self.command_loader.command_name
        scope = self.scope
        return command_name.startswith(scope)

    def _check_stale(self):
        if self.is_stale:
            message = "command authoring error: argument context '{}' is stale! " \
                      "Check that the subsequent block for has a corresponding `as` statement.".format(self.scope)
            logger.error(message)
            raise CLIError(message)

    def _flatten_kwargs(self, kwargs, arg_type, supported_kwargs=None):
        merged_kwargs = self._merge_kwargs(kwargs, supported_kwargs=supported_kwargs)
        if arg_type:
            arg_type_copy = arg_type.settings.copy()
            arg_type_copy.update(merged_kwargs)
            return arg_type_copy
        return merged_kwargs

    def _merge_kwargs(self, kwargs, base_kwargs=None, supported_kwargs=None):
        from azure.cli.core.commands import _merge_kwargs as merge_kwargs
        base = base_kwargs if base_kwargs is not None else getattr(self, 'group_kwargs')
        return merge_kwargs(kwargs, base, supported_kwargs or CLI_PARAM_KWARGS)

    # pylint: disable=arguments-differ
    def argument(self, dest, arg_type=None, **kwargs):
        self._check_stale()
        if not self._applicable():
            return

        merged_kwargs = self._flatten_kwargs(kwargs, arg_type)
        resource_type = merged_kwargs.get('resource_type', None)
        min_api = merged_kwargs.get('min_api', None)
        max_api = merged_kwargs.get('max_api', None)
        operation_group = merged_kwargs.get('operation_group', None)
        if merged_kwargs.get('options_list') == []:
            del merged_kwargs['options_list']
        if self.command_loader.supported_api_version(resource_type=resource_type,
                                                     min_api=min_api,
                                                     max_api=max_api,
                                                     operation_group=operation_group):
            super(AzArgumentContext, self).argument(dest, **merged_kwargs)
        else:
            super(AzArgumentContext, self).argument(dest, arg_type=ignore_type)

    def positional(self, dest, arg_type=None, **kwargs):
        self._check_stale()
        if not self._applicable():
            return

        if self.scope not in self.command_loader.command_table:
            raise ValueError("command authoring error: positional argument '{}' cannot be registered to a group-level "
                             "scope '{}'. It must be registered to a specific command.".format(dest, self.scope))

        # Before adding the new positional arg, ensure that there are no existing positional arguments
        # registered for this command.
        command_args = self.command_loader.argument_registry.arguments[self.scope]
        positional_args = {k: v for k, v in command_args.items() if v.settings.get('options_list') == []}
        if positional_args and dest not in positional_args:
            raise CLIError("command authoring error: commands may have, at most, one positional argument. '{}' already "
                           "has positional argument: {}.".format(self.scope, ' '.join(positional_args.keys())))

        merged_kwargs = self._flatten_kwargs(kwargs, arg_type, supported_kwargs=CLI_POSITIONAL_PARAM_KWARGS)
        merged_kwargs = {k: v for k, v in merged_kwargs.items() if k in CLI_POSITIONAL_PARAM_KWARGS}
        merged_kwargs['options_list'] = []

        resource_type = merged_kwargs.get('resource_type', None)
        min_api = merged_kwargs.get('min_api', None)
        max_api = merged_kwargs.get('max_api', None)
        operation_group = merged_kwargs.get('operation_group', None)
        if self.command_loader.supported_api_version(resource_type=resource_type,
                                                     min_api=min_api,
                                                     max_api=max_api,
                                                     operation_group=operation_group):
            super(AzArgumentContext, self).argument(dest, **merged_kwargs)
        else:
            super(AzArgumentContext, self).argument(dest, arg_type=ignore_type)

    def expand(self, dest, model_type, group_name=None, patches=None):
        # TODO:
        # two privates symbols are imported here. they should be made public or this utility class
        # should be moved into azure.cli.core
        from knack.introspection import extract_args_from_signature, option_descriptions

        self._check_stale()
        if not self._applicable():
            return

        if not patches:
            patches = dict()

        # fetch the documentation for model parameters first. for models, which are the classes
        # derive from msrest.serialization.Model and used in the SDK API to carry parameters, the
        # document of their properties are attached to the classes instead of constructors.
        parameter_docs = option_descriptions(model_type)

        def get_complex_argument_processor(expanded_arguments, assigned_arg, model_type):
            """
            Return a validator which will aggregate multiple arguments to one complex argument.
            """

            def _expansion_validator_impl(namespace):
                """
                The validator create a argument of a given type from a specific set of arguments from CLI
                command.
                :param namespace: The argparse namespace represents the CLI arguments.
                :return: The argument of specific type.
                """
                ns = vars(namespace)
                kwargs = dict((k, ns[k]) for k in ns if k in set(expanded_arguments))

                setattr(namespace, assigned_arg, model_type(**kwargs))

            return _expansion_validator_impl

        expanded_arguments = []
        for name, arg in extract_args_from_signature(model_type.__init__, excluded_params=EXCLUDED_PARAMS):
            arg = arg.type
            if name in parameter_docs:
                arg.settings['help'] = parameter_docs[name]

            if group_name:
                arg.settings['arg_group'] = group_name

            if name in patches:
                patches[name](arg)

            self.extra(name, arg_type=arg)
            expanded_arguments.append(name)

        dest_option = ['--__{}'.format(dest.upper())]
        self.argument(dest,
                      arg_type=ignore_type,
                      options_list=dest_option,
                      validator=get_complex_argument_processor(expanded_arguments, dest, model_type))

    def ignore(self, *args):
        self._check_stale()
        if not self._applicable():
            return

        for arg in args:
            super(AzArgumentContext, self).ignore(arg)

    def extra(self, dest, arg_type=None, **kwargs):
        self._check_stale()
        if not self._applicable():
            return

        if self.scope not in self.command_loader.command_table:
            raise ValueError("command authoring error: extra argument '{}' cannot be registered to a group-level "
                             "scope '{}'. It must be registered to a specific command.".format(dest, self.scope))

        merged_kwargs = self._flatten_kwargs(kwargs, arg_type)
        resource_type = merged_kwargs.get('resource_type', None)
        min_api = merged_kwargs.get('min_api', None)
        max_api = merged_kwargs.get('max_api', None)
        operation_group = merged_kwargs.get('operation_group', None)
        if self.command_loader.supported_api_version(resource_type=resource_type,
                                                     min_api=min_api,
                                                     max_api=max_api,
                                                     operation_group=operation_group):
            merged_kwargs.pop('dest', None)
            super(AzArgumentContext, self).extra(argument_dest=dest, **merged_kwargs)
