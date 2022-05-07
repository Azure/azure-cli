from azure.cli.core import azclierror
from knack.arguments import CLICommandArgument, CaseInsensitiveList

from ._arg_action import AAZSimpleTypeArgAction, AAZObjectArgAction, AAZDictArgAction, AAZListArgAction
from ._base import AAZBaseType, AAZUndefined
from ._field_type import AAZObjectType, AAZStrType, AAZIntType, AAZBoolType, AAZFloatType, AAZListType, AAZDictType, \
    AAZSimpleType
from ._field_value import AAZObject


class AAZArgumentsSchema(AAZObjectType):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __call__(self, data=None):
        if data is None:
            data = {}
        return AAZObject(
            schema=self,
            data=self.process_data(data=data)
        )


class AAZArgEnum:

    def __init__(self, items, case_sensitive=False):
        self._case_sensitive = case_sensitive
        self.items = items

    def to_choices(self):
        choices = [key for key in self.items]
        if not self._case_sensitive:
            choices = CaseInsensitiveList(choices)
        return choices

    def __getitem__(self, data):
        key = data
        # if not self._case_sensitive:
        if isinstance(self.items, dict):
            for k, v in self.items.items():
                if v == data:
                    key = k
                    break
                elif k == data or not self._case_sensitive and k.lower() == data.lower():
                    key = k
                    break

        if key in self.items:
            if isinstance(self.items, (list, tuple, set)):
                return key
            elif isinstance(self.items, dict):
                return self.items[key]
            else:
                raise NotImplementedError()
        else:
            raise azclierror.InvalidArgumentValueError(
                f"unrecognized value '{data}' from choices '{self.to_choices()}' ")


class AAZBaseArg(AAZBaseType):

    def __init__(self, options=None, required=False, help=None, arg_group=None, is_preview=False, is_experimental=False,
                 id_part=None, default=AAZUndefined, blank=AAZUndefined, nullable=False):
        super().__init__(options=options, nullable=nullable)
        self._help = {}  # the key of self._help is 'name', 'short-summary', 'long-summery', 'populator-commands'

        if self._options:
            self._help['name'] = ' '.join(self._options)
            if isinstance(help, str):
                self._help['short-summery'] = help
            elif isinstance(help, dict):
                self._help.update(help)
        # TODO: add arguments help into command's AZ_HELP

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
            help=self._help.get('short-summery', None),
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

    def _build_cmd_action(self):
        return None


class AAZSimpleTypeArg(AAZBaseArg, AAZSimpleType):

    def __init__(self, enum=None, enum_case_sensitive=False, fmt=None, **kwargs):
        super().__init__(**kwargs)
        self.enum = AAZArgEnum(enum, case_sensitive=enum_case_sensitive) if enum else None
        self._fmt = fmt

    def to_cmd_arg(self, name):
        arg = super().to_cmd_arg(name=name)
        if self.enum:
            arg.choices = self.enum.to_choices()
        return arg

    def _build_cmd_action(self):
        class Action(AAZSimpleTypeArgAction):
            _schema = self

        return Action


class AAZStrArg(AAZSimpleTypeArg, AAZStrType):
    pass


class AAZIntArg(AAZSimpleTypeArg, AAZIntType):
    pass


class AAZBoolArg(AAZSimpleTypeArg, AAZBoolType):

    def __init__(self, blank=True, enum=None, **kwargs):
        enum = enum or {
            'true': True, 't': True, 'yes': True, 'y': True, '1': True,
            "false": False, 'f': False, 'no': False, 'n': False, '0': False,
        }
        super().__init__(blank=blank, enum=enum, **kwargs)


class AAZFloatArg(AAZSimpleTypeArg, AAZFloatType):
    pass


#
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


class AAZResourceGroupNameArg(AAZStrArg):

    def __init__(
            self, options=('--resource-group', '-g'), id_part='resource_group',
            help="Name of resource group. You can configure the default group using `az configure --defaults group=<name>`",
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


class AAZResourceIdArg(AAZStrArg):
    # TODO: Resource Id arg can support both name and id. And can construct id from name by ResourceId Format
    pass


def has_value(arg_value):
    return arg_value != AAZUndefined
