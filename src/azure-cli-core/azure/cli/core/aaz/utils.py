# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ._arg import AAZListArg, AAZDictArg, has_value
from ._base import AAZBaseValue

def transform_aaz_list_args(target, source, element_transformer=None):
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
        return

    if source == None:
        target._data = target_schema.process_data(None)
        return

    for idx, element in enumerate(source):
        if not has_value(element):
            continue
        if element == None:
            target[idx] = None
        elif element_transformer:
            target[idx] = element_transformer(element)
        else:
            target[idx] = element

def transform_aaz_dict_args(target, source, element_transformer=None):
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
        return

    if source == None:
        target._data = target_schema.process_data(None)
        return

    for key, element in source.items():
        if not has_value(element):
            continue
        if element == None:
            target[key] = None
        elif element_transformer:
            target[key] = element_transformer(element)
        else:
            target[key] = element
