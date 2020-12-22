# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from collections.abc import Iterable
from azure.cli.command_modules.keyvault._validators import KeyEncryptionDataType


def multi_transformers(*transformers):
    def _multi_transformers(output, **command_args):
        for t in transformers:
            output = t(output, **command_args)
        return output
    return _multi_transformers


def keep_max_results(output, **command_args):
    maxresults = command_args.get('maxresults', None)
    if maxresults:
        return [_ for _ in output][:maxresults]
    return output


def filter_out_managed_resources(output, **command_args):  # pylint: disable=unused-argument
    is_kv_transform = command_args.get('kv_transform')
    if is_kv_transform:
        if command_args.get('include_managed'):
            return output
        return [_ for _ in output if not getattr(_, 'managed')] if output else output
    return output


def _extract_subresource_name_from_single_output(output, id_parameter):
    if not getattr(output, id_parameter):
        resource_name = None
    else:
        items = getattr(output, id_parameter).split('/')
        resource_name = items[4] if len(items) > 4 else None

    setattr(output, 'name', resource_name)
    return output


def extract_subresource_name(id_parameter='id'):
    def _extract_subresource_name(output, **command_args):  # pylint: disable=unused-argument
        if isinstance(output, Iterable):
            return [_extract_subresource_name_from_single_output(item, id_parameter) for item in output]
        return _extract_subresource_name_from_single_output(output, id_parameter)
    return _extract_subresource_name


def transform_key_decryption_output(output, **command_args):
    data_type = command_args.get('data_type')
    if data_type == KeyEncryptionDataType.BASE64:
        return output
    raw_result = getattr(output, 'result')
    if not raw_result or not isinstance(raw_result, bytes):
        return output
    setattr(output, 'result', raw_result.decode('utf-8'))
    return output
