# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from knack.arguments import CLIArgumentType
from azure.cli.core.profiles import CustomResourceType


# action
def cls_action_wrapper(action_cls):
    return action_cls


def cls_action_factory_wrapper(factory):
    return factory


# arg_type
def register_arg_type(register_name, overrides=None, **kwargs):  # pylint: disable=unused-argument
    return CLIArgumentType(overrides=overrides, **kwargs)


def arg_type_factory_wrapper(factory):
    return factory


# client_factory
def func_client_factory_wrapper(func):
    return func


# completer
def func_completer_wrapper(func):
    return func


def completer_factory_wrapper(factory):
    return factory


# exception_handler
def func_exception_handler_wrapper(func):
    return func


# resource_type
def register_custom_resource_type(register_name, import_prefix, client_name):  # pylint: disable=unused-argument
    return CustomResourceType(import_prefix=import_prefix, client_name=client_name)


# transformer
def func_transformer_wrapper(func):
    return func


# type_converter
def func_type_converter_wrapper(func):
    return func


def func_type_converter_factory_wrapper(factory):
    return factory


# validator
def func_validator_wrapper(func):
    return func


def validator_factory_wrapper(factory):
    return factory
