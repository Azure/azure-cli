# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import abc
import copy

from azure.cli.core import azclierror
from azure.cli.core.commands.arm import add_usage, remove_usage, set_usage
from knack.arguments import CLICommandArgument, CaseInsensitiveList
from knack.preview import PreviewItem
from knack.experimental import ExperimentalItem
from knack.util import status_tag_messages
from knack.log import get_logger

from ._arg_action import AAZSimpleTypeArgAction, AAZObjectArgAction, AAZDictArgAction, \
    AAZListArgAction, AAZGenericUpdateAction, AAZGenericUpdateForceStringAction, AAZAnyTypeArgAction
from ._base import AAZBaseType, AAZUndefined
from ._field_type import AAZObjectType, AAZStrType, AAZIntType, AAZBoolType, AAZFloatType, AAZListType, AAZDictType, \
    AAZSimpleType, AAZFreeFormDictType, AAZAnyType
from ._field_value import AAZObject
from ._arg_fmt import AAZObjectArgFormat, AAZListArgFormat, AAZDictArgFormat, AAZFreeFormDictArgFormat, \
    AAZSubscriptionIdArgFormat, AAZResourceLocationArgFormat, AAZResourceIdArgFormat, AAZUuidFormat, AAZDateFormat, \
    AAZTimeFormat, AAZDateTimeFormat, AAZDurationFormat, AAZFileArgTextFormat, AAZPaginationTokenArgFormat, \
    AAZIntArgFormat
from .exceptions import AAZUnregisteredArg
from ._prompt import AAZPromptInput

# pylint: disable=redefined-builtin, protected-access, too-few-public-methods, too-many-instance-attributes

logger = get_logger(__name__)


class AAZArgumentsSchema(AAZObjectType):
    """ Arguments' schema should be defined as fields of it """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._fmt = AAZObjectArgFormat()

    def __call__(self, data=None):
        return AAZObject(
            schema=self,
            data=self.process_data(data=data)
        )


class AAZArgEnum:
    """Argument enum properties"""

    def __init__(self, items, case_sensitive=False, support_extension=False):
        self._case_sensitive = case_sensitive
        self.support_extension = support_extension
        self.items = items

    def to_choices(self):
        """Generate choices property of CLICommandArgument"""
        choices = list(self.items)
        if not self._case_sensitive:
            choices = CaseInsensitiveList(choices)
        return choices

    def __getitem__(self, data):
        key = data
        if isinstance(self.items, dict):
            # convert data, it can be key, value or key.lower() when not case sensitive
            for k, v in self.items.items():
                if v == data or k == data or not self._case_sensitive and k.lower() == data.lower():
                    key = k
                    break

        if key in self.items:
            if isinstance(self.items, (list, tuple, set)):
                return key
            if isinstance(self.items, dict):
                return self.items[key]
            raise NotImplementedError()
        if self.support_extension:
            # support extension value which is not in choices
            if isinstance(self.items, dict):
                values = list(self.items.values())
            elif isinstance(self.items, (list, tuple, set)):
                values = list(self.items)
            try:
                data_type = type(values[0])
                value = data_type(data)
                logger.warning("Use extended value '%s' outside choices %s.", str(value), self.to_choices())
                return value
            except (ValueError, IndexError):
                pass
        raise azclierror.InvalidArgumentValueError(
            f"unrecognized value '{data}' from choices '{self.to_choices()}' ")


class AAZBaseArg(AAZBaseType):
    """Base argument"""

    def __init__(self, options=None, required=False, help=None, arg_group=None, is_preview=False, is_experimental=False,
                 id_part=None, default=AAZUndefined, blank=AAZUndefined, nullable=False, fmt=None, registered=True,
                 configured_default=None, completer=None):
        """

        :param options: argument optional names.
        :param required: argument is required or not.
        :param help: help can be either string (for short-summary) or a dict with `name`, `short-summary`,
                    `long-summary` and `populator-commands` properties
        :param arg_group: argument group.
        :param is_preview: is preview.
        :param is_experimental: is experimental.
        :param id_part: whether needs id part support in azure.cli.core
        :param default: when the argument flag is not appeared, the default value will be used.
        :param blank: when the argument flag is used without value data, the blank value will be used.
        :param nullable: argument can accept `None` as value
        :param fmt: argument format
        :param registered: control whether register argument into command display
        :param configured_default: the key to retrieve the default value from cli configuration
        :param completer: tab completion if completion is active
        """
        super().__init__(options=options, nullable=nullable)
        self._help = {}  # the key in self._help can be 'name', 'short-summary', 'long-summary', 'populator-commands'

        if self._options:
            self._help['name'] = ' '.join(self._options)
            if isinstance(help, str):
                self._help['short-summary'] = help
            elif isinstance(help, dict):
                self._help.update(help)

        self._required = required
        self._arg_group = arg_group
        self._is_preview = is_preview
        self._is_experimental = is_experimental
        self._id_part = id_part
        self._default = default
        self._blank = blank
        self._fmt = fmt
        self._registered = registered
        self._configured_default = configured_default
        self._completer = completer

    def to_cmd_arg(self, name, **kwargs):
        """ convert AAZArg to CLICommandArgument """
        if not self._registered:
            # argument will not registered in command display
            raise AAZUnregisteredArg()

        options_list = [*self._options] if self._options else None
        arg = CLICommandArgument(
            dest=name,
            options_list=options_list,
            # if default is not None, arg is not required.
            required=self._required if self._default == AAZUndefined else False,
            help=self._help.get('short-summary', None),
            id_part=self._id_part,
            default=copy.deepcopy(self._default),
        )
        if self._arg_group:
            arg.arg_group = self._arg_group

        if self._blank != AAZUndefined:
            arg.nargs = '?'
            if isinstance(self._blank, AAZPromptInput):
                short_summary = arg.type.settings.get('help', None) or ''
                if short_summary:
                    short_summary += '  '
                short_summary += self._blank.help_message
                arg.help = short_summary

        cli_ctx = kwargs.get('cli_ctx', None)
        if cli_ctx is None:
            # define mock cli_ctx for PreviewItem and ExperimentalItem
            class _CLI_CTX:
                enable_color = False
            cli_ctx = _CLI_CTX

        if options_list is None:
            target = f"--{name.replace('_', '-')}"
        else:
            target = sorted(options_list, key=len)[-1]

        if self._is_preview:
            def _get_preview_arg_message(self):
                subject = "{} '{}'".format(self.object_type.capitalize(), self.target)
                return status_tag_messages['preview'].format(subject)
            arg.preview_info = PreviewItem(
                cli_ctx=cli_ctx,
                target=target,
                object_type="argument",
                message_func=_get_preview_arg_message
            )

        if self._is_experimental:
            def _get_experimental_arg_message(self):
                # "Argument xxx"
                subject = "{} '{}'".format(self.object_type.capitalize(), self.target)
                return status_tag_messages['experimental'].format(subject)

            arg.experimental_info = ExperimentalItem(
                cli_ctx=cli_ctx,
                target=target,
                object_type="argument",
                message_func=_get_experimental_arg_message
            )

        if self._configured_default:
            arg.configured_default = self._configured_default

        if self._completer:
            from azure.cli.core.decorators import Completer
            assert isinstance(self._completer, Completer)
            arg.completer = self._completer

        action = self._build_cmd_action()   # call sub class's implementation to build CLICommandArgument action
        if action:
            arg.action = action

        return arg

    @abc.abstractmethod
    def _build_cmd_action(self):
        """build argparse Action"""
        raise NotImplementedError()

    @property
    def _type_in_help(self):
        """argument type displayed in help"""
        return "Undefined"


class AAZSimpleTypeArg(AAZBaseArg, AAZSimpleType):
    """Argument accept simple value"""

    def __init__(self, enum=None, enum_case_sensitive=False, enum_support_extension=False, **kwargs):
        super().__init__(**kwargs)
        self.enum = AAZArgEnum(
            enum, case_sensitive=enum_case_sensitive, support_extension=enum_support_extension
        ) if enum else None

    def to_cmd_arg(self, name, **kwargs):
        arg = super().to_cmd_arg(name, **kwargs)
        if self.enum:
            choices = self.enum.to_choices()
            if self.enum.support_extension:
                # Display the allowed values in help only without verifying the user input in argparse
                short_summary = arg.type.settings.get('help', None) or ''
                if short_summary:
                    short_summary += '  '
                short_summary += 'Allowed values: {}.'.format(', '.join(sorted([str(x) for x in choices])))
                arg.help = short_summary
            else:
                # this will verify the user input in argparse
                arg.choices = choices   # convert it's enum value into choices in arg
        return arg

    def _build_cmd_action(self):
        class Action(AAZSimpleTypeArgAction):
            _schema = self  # bind action class with current schema

        return Action


class AAZStrArg(AAZSimpleTypeArg, AAZStrType):

    @property
    def _type_in_help(self):
        return "String"


class AAZDurationArg(AAZStrArg):

    def __init__(self, fmt=None, **kwargs):
        fmt = fmt or AAZDurationFormat()
        super().__init__(fmt=fmt, **kwargs)

    @property
    def _type_in_help(self):
        return "Duration"


class AAZDateArg(AAZStrArg):

    def __init__(self, fmt=None, **kwargs):
        fmt = fmt or AAZDateFormat()
        super().__init__(fmt=fmt, **kwargs)

    @property
    def _type_in_help(self):
        return "Date"


class AAZTimeArg(AAZStrArg):

    def __init__(self, fmt=None, **kwargs):
        fmt = fmt or AAZTimeFormat()
        super().__init__(fmt=fmt, **kwargs)

    @property
    def _type_in_help(self):
        return "Time"


class AAZDateTimeArg(AAZStrArg):

    def __init__(self, fmt=None, **kwargs):
        fmt = fmt or AAZDateTimeFormat()
        super().__init__(fmt=fmt, **kwargs)

    @property
    def _type_in_help(self):
        return "DateTime"


class AAZUuidArg(AAZStrArg):

    def __init__(self, fmt=None, **kwargs):
        fmt = fmt or AAZUuidFormat()
        super().__init__(fmt=fmt, **kwargs)

    @property
    def _type_in_help(self):
        return "GUID/UUID"


class AAZPasswordArg(AAZStrArg):

    @property
    def _type_in_help(self):
        return "Password"


class AAZIntArg(AAZSimpleTypeArg, AAZIntType):

    @property
    def _type_in_help(self):
        return "Int"


class AAZBoolArg(AAZSimpleTypeArg, AAZBoolType):

    def __init__(self, blank=True, enum=None, **kwargs):
        enum = enum or {
            'true': True, 't': True, 'yes': True, 'y': True, '1': True,
            "false": False, 'f': False, 'no': False, 'n': False, '0': False,
        }
        super().__init__(blank=blank, enum=enum, **kwargs)

    @property
    def _type_in_help(self):
        return "Boolean"


class AAZFloatArg(AAZSimpleTypeArg, AAZFloatType):

    @property
    def _type_in_help(self):
        return "Float"


class AAZAnyTypeArg(AAZBaseArg, AAZAnyType):

    def _build_cmd_action(self):
        class Action(AAZAnyTypeArgAction):
            _schema = self  # bind action class with current schema
        return Action

    def to_cmd_arg(self, name, **kwargs):
        from ._help import shorthand_help_messages
        arg = super().to_cmd_arg(name, **kwargs)
        short_summary = arg.type.settings.get('help', None) or ''
        if short_summary:
            short_summary += '  '
        short_summary += shorthand_help_messages['short-summary-anytype']
        arg.help = short_summary
        return arg

    @property
    def _type_in_help(self):
        return "Any"


class AAZCompoundTypeArg(AAZBaseArg):

    @abc.abstractmethod
    def _build_cmd_action(self):
        raise NotImplementedError()

    def to_cmd_arg(self, name, **kwargs):
        from ._help import shorthand_help_messages
        arg = super().to_cmd_arg(name, **kwargs)
        short_summary = arg.type.settings.get('help', None) or ''
        if short_summary:
            short_summary += '  '
        short_summary += shorthand_help_messages['short-summary'] + ' ' + shorthand_help_messages['show-help']
        if isinstance(self, AAZListArg) and self.singular_options:
            singular_options = '  Singular flags: ' + ' '.join(
                [f'`{opt}`' for opt in self.singular_options])
            short_summary += singular_options + '.'
        arg.help = short_summary
        return arg


class AAZObjectArg(AAZCompoundTypeArg, AAZObjectType):

    def __init__(self, fmt=None, **kwargs):
        fmt = fmt or AAZObjectArgFormat()
        super().__init__(fmt=fmt, **kwargs)

    def to_cmd_arg(self, name, **kwargs):
        arg = super().to_cmd_arg(name, **kwargs)
        if self._blank != AAZUndefined:
            arg.nargs = '*'
        else:
            arg.nargs = '+'
        return arg

    def _build_cmd_action(self):
        class Action(AAZObjectArgAction):
            _schema = self  # bind action class with current schema

        return Action

    @property
    def _type_in_help(self):
        return "Object"


class AAZDictArg(AAZCompoundTypeArg, AAZDictType):

    def __init__(self, fmt=None, **kwargs):
        fmt = fmt or AAZDictArgFormat()
        super().__init__(fmt=fmt, **kwargs)

    def to_cmd_arg(self, name, **kwargs):
        arg = super().to_cmd_arg(name, **kwargs)
        if self._blank != AAZUndefined:
            arg.nargs = '*'
        else:
            arg.nargs = '+'
        return arg

    def _build_cmd_action(self):
        class Action(AAZDictArgAction):
            _schema = self  # bind action class with current schema

        return Action

    @property
    def _type_in_help(self):
        return f"Dict<String,{self.Element._type_in_help}>"


# Warning: This type should not be used any more, the new aaz-dev-tools only use AAZDictType with AAZAnyType
class AAZFreeFormDictArg(AAZDictArg, AAZFreeFormDictType):

    def __init__(self, fmt=None, **kwargs):
        fmt = fmt or AAZFreeFormDictArgFormat()
        super().__init__(fmt=fmt, **kwargs)
        # for backward compatible, support nullable value here for AAZFreeFormDictArg,
        # from the new code gen tools, it will avoid using AAZFreeFormDictArg
        self._element = AAZAnyTypeArg(nullable=True)


class AAZListArg(AAZCompoundTypeArg, AAZListType):

    def __init__(self, fmt=None, singular_options=None, **kwargs):
        fmt = fmt or AAZListArgFormat()
        super().__init__(fmt=fmt, **kwargs)
        self.singular_options = singular_options

    def to_cmd_arg(self, name, **kwargs):
        arg = super().to_cmd_arg(name, **kwargs)
        if self.singular_options:
            assert arg.options_list
            arg.options_list.extend(self.singular_options)  # support to parse singular options

        if self._blank != AAZUndefined:
            arg.nargs = '*'
        else:
            arg.nargs = '+'
        return arg

    def _build_cmd_action(self):
        class Action(AAZListArgAction):
            _schema = self  # bind action class with current schema

        return Action

    @property
    def _type_in_help(self):
        return f"List<{self.Element._type_in_help}>"


class AAZResourceGroupNameArg(AAZStrArg):

    def __init__(
            self, options=('--resource-group', '-g'), id_part='resource_group',
            help="Name of resource group. "
                 "You can configure the default group using `az configure --defaults group=<name>`",
            configured_default='group',
            completer=None,
            **kwargs):
        from azure.cli.core.commands.parameters import get_resource_group_completion_list
        completer = completer or get_resource_group_completion_list
        super().__init__(
            options=options,
            id_part=id_part,
            help=help,
            configured_default=configured_default,
            completer=completer,
            **kwargs
        )

    def to_cmd_arg(self, name, **kwargs):
        from azure.cli.core.local_context import LocalContextAttribute, LocalContextAction, ALL
        arg = super().to_cmd_arg(name, **kwargs)
        arg.local_context_attribute = LocalContextAttribute(
            name='resource_group_name',
            actions=[LocalContextAction.SET, LocalContextAction.GET],
            scopes=[ALL]
        )
        return arg


class AAZResourceLocationArg(AAZStrArg):

    def __init__(
            self, options=('--location', '-l'),
            help="Location. Values from: `az account list-locations`. "
                 "You can configure the default location using `az configure --defaults location=<location>`.",
            fmt=None,
            configured_default='location',
            completer=None,
            **kwargs):
        from azure.cli.core.commands.parameters import get_location_completion_list

        fmt = fmt or AAZResourceLocationArgFormat()
        completer = completer or get_location_completion_list
        super().__init__(
            options=options,
            help=help,
            fmt=fmt,
            configured_default=configured_default,
            completer=completer,
            **kwargs
        )

    def to_cmd_arg(self, name, **kwargs):
        from azure.cli.core.local_context import LocalContextAttribute, LocalContextAction, ALL
        arg = super().to_cmd_arg(name, **kwargs)
        if self._required and \
                isinstance(self._fmt, AAZResourceLocationArgFormat) and self._fmt._resource_group_arg is not None:
            # when location is required and it will be retrived from resource group by default, arg is not required.
            arg.required = False
            short_summary = arg.type.settings.get('help', None) or ''
            if short_summary:
                short_summary += '  '
            short_summary += "When not specified, the location of the resource group will be used."
            arg.help = short_summary

        arg.local_context_attribute = LocalContextAttribute(
            name='location',
            actions=[LocalContextAction.SET, LocalContextAction.GET],
            scopes=[ALL]
        )
        return arg


class AAZResourceIdArg(AAZStrArg):
    """ResourceId Argument"""

    def __init__(self, fmt=None, **kwargs):
        fmt = fmt or AAZResourceIdArgFormat()
        super().__init__(fmt=fmt, **kwargs)


class AAZSubscriptionIdArg(AAZStrArg):

    def __init__(
            self, help="Name or ID of subscription. You can configure the default subscription "
                       "using `az account set -s NAME_OR_ID`",
            fmt=None,
            completer=None,
            **kwargs):
        from azure.cli.core._completers import get_subscription_id_list
        fmt = fmt or AAZSubscriptionIdArgFormat()
        completer = completer or get_subscription_id_list
        super().__init__(
            help=help,
            fmt=fmt,
            completer=completer,
            **kwargs
        )


class AAZFileArg(AAZStrArg):

    def __init__(self, fmt=None, **kwargs):
        fmt = fmt or AAZFileArgTextFormat()
        super().__init__(fmt=fmt, **kwargs)


# Generic Update arguments
class AAZGenericUpdateForceStringArg(AAZBoolArg):

    def __init__(
            self, options=('--force-string',), arg_group='Generic Update',
            help="When using 'set' or 'add', preserve string literals instead of attempting to convert to JSON.",
            **kwargs):
        super().__init__(
            options=options,
            help=help,
            arg_group=arg_group,
            **kwargs,
        )

    def _build_cmd_action(self):
        class Action(AAZGenericUpdateForceStringAction):
            _schema = self  # bind action class with current schema
        return Action


class AAZGenericUpdateArg(AAZBaseArg, AAZListType):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.Element = AAZStrType()

    @abc.abstractmethod
    def _build_cmd_action(self):
        raise NotImplementedError()


class AAZGenericUpdateSetArg(AAZGenericUpdateArg):

    def __init__(
            self, options=('--set',), arg_group='Generic Update',
            help='Update an object by specifying a property path and value to set.'
                 '  Example: {}'.format(set_usage),
            **kwargs):
        super().__init__(
            options=options,
            help=help,
            arg_group=arg_group,
            **kwargs,
        )

    def to_cmd_arg(self, name, **kwargs):
        arg = super().to_cmd_arg(name, **kwargs)
        arg.nargs = '+'
        arg.metavar = 'KEY=VALUE'
        return arg

    def _build_cmd_action(self):
        class Action(AAZGenericUpdateAction):
            ACTION_NAME = "set"
        return Action


class AAZGenericUpdateAddArg(AAZGenericUpdateArg):

    def __init__(
            self, options=('--add',), arg_group='Generic Update',
            help='Add an object to a list of objects by specifying a path and key value pairs.'
                 '  Example: {}'.format(add_usage),
            **kwargs):
        super().__init__(
            options=options,
            help=help,
            arg_group=arg_group,
            **kwargs,
        )

    def to_cmd_arg(self, name, **kwargs):
        arg = super().to_cmd_arg(name, **kwargs)
        arg.nargs = '+'
        arg.metavar = 'LIST KEY=VALUE'
        return arg

    def _build_cmd_action(self):
        class Action(AAZGenericUpdateAction):
            ACTION_NAME = "add"
        return Action


class AAZGenericUpdateRemoveArg(AAZGenericUpdateArg):

    def __init__(
            self, options=('--remove', ), arg_group='Generic Update',
            help='Remove a property or an element from a list.'
                 '  Example: {}'.format(remove_usage),
            **kwargs):
        super().__init__(
            options=options,
            help=help,
            arg_group=arg_group,
            **kwargs,
        )

    def to_cmd_arg(self, name, **kwargs):
        arg = super().to_cmd_arg(name, **kwargs)
        arg.nargs = '+'
        arg.metavar = 'LIST INDEX'
        return arg

    def _build_cmd_action(self):
        class Action(AAZGenericUpdateAction):
            ACTION_NAME = "remove"
        return Action


class AAZPaginationTokenArg(AAZStrArg):
    def __init__(
            self, options=("--next-token",), arg_group="Pagination",
            help="Token to specify where to start paginating. This is the token value from a previously truncated "
                 "response.",
            fmt=None,
            **kwargs
    ):
        fmt = fmt or AAZPaginationTokenArgFormat()

        super().__init__(
            options=options,
            arg_group=arg_group,
            help=help,
            fmt=fmt,
            **kwargs,
        )


class AAZPaginationLimitArg(AAZIntArg):
    def __init__(
            self, options=("--max-items",), arg_group="Pagination",
            help="Total number of items to return in the command's output. If the total number of items available is "
                 "more than the value specified, a token is provided in the command's output. To resume pagination, "
                 "provide the token value in `--next-token` argument of a subsequent command.",
            fmt=None,
            **kwargs
    ):
        fmt = fmt or AAZIntArgFormat(minimum=1)

        super().__init__(
            options=options,
            arg_group=arg_group,
            help=help,
            fmt=fmt,
            **kwargs,
        )
