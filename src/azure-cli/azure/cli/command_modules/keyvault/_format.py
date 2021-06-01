# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
"""Table transformer for keyvault commands"""


def build_table_output(result, projection):

    if not isinstance(result, list):
        result = [result]

    final_list = []

    from collections import OrderedDict
    for item in result:
        def _value_from_path(each_item, path):
            obj = each_item
            try:
                for part in path.split('.'):
                    obj = obj.get(part, None)
            except AttributeError:
                obj = None
            return obj or ' '

        item_dict = OrderedDict()
        for element in projection:
            item_dict[element[0]] = _value_from_path(item, element[1])
        final_list.append(item_dict)

    return final_list


def transform_secret_list(result):
    return build_table_output(result, [
        ('Name', 'name'),
        ('Id', 'id'),
        ('ContentType', 'contentType'),
        ('Enabled', 'attributes.enabled'),
        ('Expires', 'attributes.expires')
    ])
