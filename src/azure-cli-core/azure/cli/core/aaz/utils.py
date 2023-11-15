# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=protected-access

from ._arg import AAZListArg, AAZDictArg
from ._base import has_value
from ._field_value import AAZList, AAZDict
from ._base import AAZBaseValue


def assign_aaz_list_arg(target: AAZList, source: AAZList, element_transformer=None):
    """ an convenience function to transform from a source AAZListArg to a target AAZListArg
    Example:

    args.target = assign_aaz_list_arg(args.target, args.source, lambda idx, e: {'idx': idx, "prop": e})
    """
    assert isinstance(target, AAZBaseValue)
    assert isinstance(source, AAZBaseValue)

    target_schema = target._schema
    source_schema = source._schema
    assert isinstance(target_schema, AAZListArg)
    assert isinstance(source_schema, AAZListArg)

    assert target_schema._nullable == source_schema._nullable, "Inconsist nullable property between target and " \
                                                               "source args"
    assert target_schema.Element._nullable == source_schema.Element._nullable, "Inconsist nullable property between " \
                                                                               "target element and source arg element"

    if not has_value(source):
        return target

    if source == None:  # noqa: E711, pylint: disable=singleton-comparison
        return None

    if not source._is_patch:
        # return the whole array
        data = []
        for idx, element in enumerate(source):
            if not has_value(element):
                continue
            if element == None:  # noqa: E711, pylint: disable=singleton-comparison
                data.append(None)
            elif element_transformer:
                data.append(element_transformer(idx, element))
            else:
                data.append(element)
        return data

    # assign by patch way
    for idx, element in enumerate(source):
        if not has_value(element):
            continue
        if element == None:  # noqa: E711, pylint: disable=singleton-comparison
            target[idx] = None
        elif element_transformer:
            target[idx] = element_transformer(idx, element)
        else:
            target[idx] = element

    return target


def assign_aaz_dict_arg(target: AAZDict, source: AAZDict, element_transformer=None):
    """ an convenience function to transform from a source AAZDictArg to a target AAZDictArg
    Example:

    args.target = assign_aaz_dict_arg(args.target, args.source, lambda key, e: {'name': key, "prop": e})
    """

    assert isinstance(target, AAZBaseValue)
    assert isinstance(source, AAZBaseValue)

    target_schema = target._schema
    source_schema = source._schema
    assert isinstance(target_schema, AAZDictArg)
    assert isinstance(source_schema, AAZDictArg)

    assert target_schema._nullable == source_schema._nullable, "Inconsist nullable property between target and " \
                                                               "source args"
    assert target_schema.Element._nullable == source_schema.Element._nullable, "Inconsist nullable property between " \
                                                                               "target element and source arg element"

    if not has_value(source):
        return target

    if source == None:  # noqa: E711, pylint: disable=singleton-comparison
        return None

    if not source._is_patch:
        # return the whole array
        data = {}
        for key, element in source.items():
            if not has_value(element):
                continue
            if element == None:  # noqa: E711, pylint: disable=singleton-comparison
                data[key] = None
            elif element_transformer:
                data[key] = element_transformer(key, element)
            else:
                data[key] = element
        return data

    # assign by patch way
    for key, element in source.items():
        if not has_value(element):
            continue
        if element == None:  # noqa: E711, pylint: disable=singleton-comparison
            target[key] = None
        elif element_transformer:
            target[key] = element_transformer(key, element)
        else:
            target[key] = element

    return target


def get_aaz_profile_module_name(profile_name):
    profile_module_name = profile_name.lower().replace('-', '_')
    if profile_module_name != "latest":
        # the rest profiles for azure-stack use start with digit number, it's not a valid python package name.
        profile_module_name = "profile_" + profile_module_name
    return profile_module_name
