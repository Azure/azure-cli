from knack.arguments import CLICommandArgument, CaseInsensitiveList
from ._base import AAZBaseType, AAZUndefined
from ._field_type import AAZObjectType, AAZStrType, AAZIntType, AAZBoolType, AAZFloatType, AAZListType, AAZDictType, AAZSimpleType
from ._field_value import AAZObject
from ._arg_action import AAZSimpleTypeArgAction, AAZObjectArgAction, AAZDictArgAction, AAZListArgAction
from azure.cli.core import azclierror


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
            raise azclierror.InvalidArgumentValueError(f"unrecognized value '{data}' from choices '{self.to_choices()}' ")


class AAZBaseArg(AAZBaseType):

    def __init__(self, options=None, required=False, help=None, arg_group=None, is_preview=False, is_experimental=False,
                 id_part=None, default=AAZUndefined, blank=AAZUndefined, nullable=False):
        super(AAZBaseArg, self).__init__(options=options, nullable=nullable)
        self._help = help
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
            help=self._help,
            default=None,
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

    def __init__(self, enum=None, fmt=None, **kwargs):
        super().__init__(**kwargs)
        self.enum = enum
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
        enum = enum or AAZArgEnum({
            'true': True, 't': True, 'yes': True, 'y': True, '1': True,
            "false": False, 'f': False, 'no': False, 'n': False, '0': False,
        })
        super(AAZBoolArg, self).__init__(blank=blank, enum=enum, **kwargs)


class AAZFloatArg(AAZSimpleTypeArg, AAZFloatType):
    pass


#

class AAZObjectArg(AAZBaseArg, AAZObjectType):

    def __init__(self, fmt=None, **kwargs):
        super(AAZObjectArg, self).__init__(**kwargs)
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
        class Action(AAZListArgAction):
            _schema = self
        return Action
