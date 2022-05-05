# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import abc

from azure.cli.core import azclierror
from knack.arguments import CLICommandArgument, CaseInsensitiveList

from ._arg_action import AAZSimpleTypeArgAction, AAZObjectArgAction, AAZDictArgAction, AAZListArgAction, \
    AAZGenericUpdateAction
from ._base import AAZBaseType, AAZUndefined
from ._field_type import AAZObjectType, AAZStrType, AAZIntType, AAZBoolType, AAZFloatType, AAZListType, AAZDictType, \
    AAZSimpleType
from ._field_value import AAZObject

# pylint: disable=redefined-builtin, protected-access


class AAZArgumentsSchema(AAZObjectType):

    def __call__(self, data=None):
        return AAZObject(
            schema=self,
            data=self.process_data(data=data)
        )


class AAZArgEnum:

    def __init__(self, items, case_sensitive=False):
        self._case_sensitive = case_sensitive
        self.items = items

    def to_choices(self):
        choices = list(self.items)
        if not self._case_sensitive:
            choices = CaseInsensitiveList(choices)
        return choices

    def __getitem__(self, data):
        key = data
        if isinstance(self.items, dict):
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
        else:
            raise azclierror.InvalidArgumentValueError(
                f"unrecognized value '{data}' from choices '{self.to_choices()}' ")


class AAZBaseArg(AAZBaseType):  # pylint: disable=too-many-instance-attributes

    def __init__(self, options=None, required=False, help=None, arg_group=None, is_preview=False, is_experimental=False,
                 id_part=None, default=AAZUndefined, blank=AAZUndefined, nullable=False):
        super().__init__(options=options, nullable=nullable)
        self._help = {}  # the key of self._help is 'name', 'short-summary', 'long-summary', 'populator-commands'

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

    def to_cmd_arg(self, name):
        arg = CLICommandArgument(
            dest=name,
            options_list=[*self._options] if self._options else None,
            required=self._required,
            help=self._help.get('short-summary', None),
            default=self._default,
        )
        if self._arg_group:
            arg.arg_group = self._arg_group

        if self._blank != AAZUndefined:
            arg.nargs = '?'

        action = self._build_cmd_action()
        if action:
            arg.action = action

        return arg

    @abc.abstractmethod
    def _build_cmd_action(self):
        raise NotImplementedError()

    @property
    def _type_in_help(self):
        return "Undefined"


class AAZSimpleTypeArg(AAZBaseArg, AAZSimpleType):

    def __init__(self, enum=None, enum_case_sensitive=False, fmt=None, **kwargs):
        super().__init__(**kwargs)
        self.enum = AAZArgEnum(enum, case_sensitive=enum_case_sensitive) if enum else None
        self._fmt = fmt

    def to_cmd_arg(self, name):
        arg = super().to_cmd_arg(name)
        if self.enum:
            arg.choices = self.enum.to_choices()
        return arg

    def _build_cmd_action(self):
        class Action(AAZSimpleTypeArgAction):
            _schema = self

        return Action


class AAZStrArg(AAZSimpleTypeArg, AAZStrType):

    @property
    def _type_in_help(self):
        return "String"


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


class AAZObjectArg(AAZBaseArg, AAZObjectType):

    def __init__(self, fmt=None, **kwargs):
        super().__init__(**kwargs)
        self._fmt = fmt

    def to_cmd_arg(self, name):
        arg = super().to_cmd_arg(name)
        if self._blank != AAZUndefined:
            arg.nargs = '*'
        else:
            arg.nargs = '+'
        return arg

    def _build_cmd_action(self):
        class Action(AAZObjectArgAction):
            _schema = self

        return Action

    @property
    def _type_in_help(self):
        return "Object"


class AAZDictArg(AAZBaseArg, AAZDictType):

    def __init__(self, fmt=None, **kwargs):
        super().__init__(**kwargs)
        self._fmt = fmt

    def to_cmd_arg(self, name):
        arg = super().to_cmd_arg(name)
        if self._blank != AAZUndefined:
            arg.nargs = '*'
        else:
            arg.nargs = '+'
        return arg

    def _build_cmd_action(self):
        class Action(AAZDictArgAction):
            _schema = self

        return Action

    @property
    def _type_in_help(self):
        return f"Dict<String,{self.Element._type_in_help}>"


class AAZListArg(AAZBaseArg, AAZListType):

    def __init__(self, fmt=None, singular_options=None, **kwargs):
        super().__init__(**kwargs)
        self._fmt = fmt
        self.singular_options = singular_options

    def to_cmd_arg(self, name):
        arg = super().to_cmd_arg(name)
        if self.singular_options:
            assert arg.options_list
            arg.options_list.extend(self.singular_options)

        if self._blank != AAZUndefined:
            arg.nargs = '*'
        else:
            arg.nargs = '+'
        return arg

    def _build_cmd_action(self):
        class Action(AAZListArgAction):
            _schema = self

        return Action

    @property
    def _type_in_help(self):
        return f"List<{self.Element._type_in_help}>"


class AAZResourceGroupNameArg(AAZStrArg):

    def __init__(
            self, options=('--resource-group', '-g'), id_part='resource_group',
            help="Name of resource group. "
                 "You can configure the default group using `az configure --defaults group=<name>`",
            **kwargs):
        super().__init__(
            options=options,
            id_part=id_part,
            help=help,
            **kwargs
        )

    def to_cmd_arg(self, name):
        from azure.cli.core.commands.parameters import get_resource_group_completion_list
        from azure.cli.core.local_context import LocalContextAttribute, LocalContextAction, ALL
        arg = super().to_cmd_arg(name)
        arg.completer = get_resource_group_completion_list
        arg.configured_default = 'group'
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
            **kwargs):
        super(AAZResourceLocationArg, self).__init__(
            options=options,
            help=help,
            fmt=None,   # TODO: add ResourceLocation Format, which can transform value with space
            **kwargs
        )

    def to_cmd_arg(self, name):
        from azure.cli.core.commands.parameters import get_location_completion_list
        from azure.cli.core.local_context import LocalContextAttribute, LocalContextAction, ALL
        arg = super().to_cmd_arg(name)
        arg.completer = get_location_completion_list
        arg.configured_default = 'location'
        arg.local_context_attribute = LocalContextAttribute(
            name='location',
            actions=[LocalContextAction.SET, LocalContextAction.GET],
            scopes=[ALL]
        )
        return arg


class AAZSubscriptionIdArg(AAZStrArg):

    def __init__(
            self, help="Name or ID of subscription.",
            **kwargs):
        super().__init__(
            help=help,
            fmt=None,  # TODO: add format, which can transform name to subscription id
            **kwargs
        )

    def to_cmd_arg(self, name):
        from azure.cli.core._completers import get_subscription_id_list
        arg = super().to_cmd_arg(name)
        arg.completer = get_subscription_id_list

        return arg


class AAZGenericUpdateForceString(AAZBoolArg):

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


class AAZGenericUpdateArg(AAZBaseArg, AAZListType):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.Element = AAZStrType()

    @abc.abstractmethod
    def _build_cmd_action(self):
        raise NotImplementedError()


class AAZGenericUpdateSetArg(AAZGenericUpdateArg):
    _example = '--set property1.property2=<value>'

    def __init__(
            self, options=('--set',), arg_group='Generic Update',
            help='Update an object by specifying a property path and value to set.'
                 '  Example: {}'.format(_example),
            **kwargs):
        super().__init__(
            options=options,
            help=help,
            arg_group=arg_group,
            **kwargs,
        )

    def to_cmd_arg(self, name):
        arg = super().to_cmd_arg(name)
        arg.nargs = '+'
        arg.metavar = 'KEY=VALUE'
        return arg

    def _build_cmd_action(self):
        return AAZGenericUpdateAction


class AAZGenericUpdateAddArg(AAZGenericUpdateArg):
    _example = '--add property.listProperty <key=value, string or JSON string>'

    def __init__(
            self, options=('--add',), arg_group='Generic Update',
            help='Add an object to a list of objects by specifying a path and key value pairs.'
                 '  Example: {}'.format(_example),
            **kwargs):
        super().__init__(
            options=options,
            help=help,
            arg_group=arg_group,
            **kwargs,
        )

    def to_cmd_arg(self, name):
        arg = super().to_cmd_arg(name)
        arg.nargs = '+'
        arg.metavar = 'LIST KEY=VALUE'
        return arg

    def _build_cmd_action(self):
        return AAZGenericUpdateAction


class AAZGenericUpdateRemoveArg(AAZGenericUpdateArg):
    _example = '--remove property.list <indexToRemove> OR --remove propertyToRemove'

    def __init__(
            self, options=('--remove', ), arg_group='Generic Update',
            help='Remove a property or an element from a list.'
                 '  Example: {}'.format(_example),
            **kwargs):
        super().__init__(
            options=options,
            help=help,
            arg_group=arg_group,
            **kwargs,
        )

    def to_cmd_arg(self, name):
        arg = super().to_cmd_arg(name)
        arg.nargs = '+'
        arg.metavar = 'LIST INDEX'
        return arg

    def _build_cmd_action(self):
        return AAZGenericUpdateAction


class AAZResourceIdArg(AAZStrArg):
    # TODO: Resource Id arg can support both name and id. And can construct id from name by ResourceId Format
    pass


def has_value(arg_value):
    return arg_value != AAZUndefined
