# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from collections.abc import Iterable


def multi_transformers(*transformers):
    def _multi_transformers(output):
        for t in transformers:
            output = t(output)
        return output
    return _multi_transformers


def filter_out_managed_resources(output):
    return [_ for _ in output if not getattr(_, 'managed')] if output else output


def _extract_subresource_name_from_single_output(output, id_parameter):
    if not getattr(output, id_parameter):
        resource_name = None
    else:
        items = getattr(output, id_parameter).split('/')
        resource_name = items[4] if len(items) > 4 else None

    setattr(output, 'name', resource_name)
    return output


def extract_subresource_name(id_parameter='id'):
    def _extract_subresource_name(output):
        if isinstance(output, Iterable):
            return [_extract_subresource_name_from_single_output(item, id_parameter) for item in output]
        return _extract_subresource_name_from_single_output(output, id_parameter)
    return _extract_subresource_name
