# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from knack.arguments import CLIArgumentType
from azure.cli.core.profiles import CustomResourceType
from azure.cli.core.decorators import Completer


# action
def action_class(action_cls):
    return action_cls


def action_class_by_factory(factory):
    return factory


# arg_type
def register_arg_type(register_name, overrides=None, **kwargs):  # pylint: disable=unused-argument
    return CLIArgumentType(overrides=overrides, **kwargs)


def arg_type_by_factory(factory):
    return factory


# client_factory
def client_factory_func(func):
    return func


# completer
def completer_func(func):
    return Completer(func)


def completer_by_factory(factory):
    def wrapper(*args, **kwargs):
        func = factory(*args, **kwargs)
        return Completer(func)
    return wrapper


# exception_handler
def exception_handler_func(func):
    return func


# resource_type
def register_custom_resource_type(register_name, import_prefix, client_name):  # pylint: disable=unused-argument
    return CustomResourceType(import_prefix=import_prefix, client_name=client_name)


# transformer
def transformer_func(func):
    return func


# type_converter
def type_converter_func(func):
    return func


def type_converter_by_factory(factory):
    return factory


# validator
def validator_func(func):
    return func


def validator_by_factory(factory):
    return factory
