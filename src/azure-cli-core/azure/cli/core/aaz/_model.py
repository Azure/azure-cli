from .exceptions import AAZUnknownFieldError, AAZUndefinedValueError
from copy import deepcopy
from ._base import AAZBaseType


# class AAZFieldDescriptor:
#     """
#     serve as field accessors
#     """
#
#     def __init__(self, name):
#         self.name = name
#
#     def __get__(self, instance, cls):
#         if instance is None:
#             return cls._schema.fields[self.name]
#         else:
#             if self.name not in instance._data:
#                 raise AAZUndefinedValueError(cls, self.name)
#             return instance._data[self.name]
#
#     def __set__(self, instance, value):
#         # field = instance._fields[self.name]
#         instance._data[self.name] = value
#
#     def __delete__(self, instance):
#         del instance._data[self.name]
#
#
# class _AAZModelMeta(type):
#     """
#     Metaclass for AAZArguments
#     """
#
#     def __new__(mcs, name, bases, attrs):
#         fields = {}
#         for base in reversed(bases):
#             if hasattr(base, '_schema'):
#                 fields.update(deepcopy(base._schema.fields))
#
#         for key, value in attrs.items():
#             if isinstance(value, AAZBaseType):
#                 fields[key] = value
#
#         for key, field in fields.items():
#             if isinstance(field, AAZBaseType):
#                 attrs[key] = AAZFieldDescriptor(key)
#
#         klass = type.__new__(mcs, name, bases, attrs)
#
#         klass._schema = AAZSchema(*(AAZField(k, f) for k, f in fields.items()))
#
#         return klass
#
#

#
#
# @metaclass(_AAZModelMeta)
# class AAZModel(object):
#
#     def __init__(self):
#         self._data = {}
#
#     def __getitem__(self, name):
#         if name in self._schema.fields:
#             return getattr(self, name)
#         else:
#             raise AAZUnknownFieldError(self, name)
#
#     def __setitem__(self, name, value):
#         if name in self._schema.fields:
#             return setattr(self, name, value)
#         else:
#             raise AAZUnknownFieldError(self, name)
#
#     def __delitem__(self, name):
#         if name in self._schema.fields:
#             return delattr(self, name)
#         else:
#             raise AAZUnknownFieldError(self, name)
