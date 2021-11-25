from ._field_type import AAZModelType
from ._base import AAZBaseType
from ._field_type import AAZModelValue


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
                for name, field in base._schema.fields.items():
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
        super(AAZArguments, self).__init__(
            name="",
            schema=self._schema,
            data={}
        )


# class AAZBaseArg:
#     pass
#
#
# class AAZStringArg(AAZBaseArg):
#     pass
#
#
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
