from ._base import AAZBaseType, AAZUndefined
from ._field_type import AAZModelType, AAZStrType, AAZIntType, AAZBoolType
from ._field_value import AAZModelValue


def metaclass(metaclass):
    def make_class(cls):
        attrs = cls.__dict__.copy()
        if attrs.get('__dict__'):
            del attrs['__dict__']
            del attrs['__weakref__']
        return metaclass(cls.__name__, cls.__bases__, attrs)
    return make_class


class _AAZArgumentsMeta(type):
    """
    Metaclass for AAZArguments
    """

    def __new__(mcs, name, bases, attrs):
        schema = AAZModelType()
        for base in reversed(bases):
            if hasattr(base, '_schema'):
                for name, field in base._schema._fields.items():
                    setattr(schema, name, field)
        new_attrs = {}
        for name, field in attrs.items():
            if isinstance(field, AAZBaseType):
                setattr(schema, name, field)
            else:
                new_attrs[name] = field
        klass = type.__new__(mcs, name, bases, new_attrs)
        klass._schema = schema

        return klass


@metaclass(_AAZArgumentsMeta)
class AAZArguments(AAZModelValue):

    def __init__(self):
        super(AAZArguments, self).__init__(schema=self._schema, data={})


class AAZBaseArg:

    def __init__(self, options, help, required=False, arg_group=None, is_preview=False, is_experimental=False,
                 id_part=None, default=AAZUndefined, blank=AAZUndefined):
        self._options = options
        self._help = help
        self._required = required
        self._arg_group = arg_group
        self._is_preview = is_preview
        self._is_experimental = is_experimental
        self._id_part = id_part
        self._default = default
        self._blank = blank


class AAZStringArg(AAZBaseArg, AAZStrType):
    pass


# class AAZIntegerArg(AAZBaseArg):
#     pass
#
#
# class AAZBooleanArg(AAZBaseArg):
#     pass
#
#
# class AAZFloatArg(AAZBaseArg):
#     pass
#
#
# class AAZObjectArg(AAZBaseArg):
#     pass
#
#
# class AAZArrayArg(AAZBaseArg):
#     pass
