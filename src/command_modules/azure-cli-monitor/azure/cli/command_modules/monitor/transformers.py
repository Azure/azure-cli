# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""The output transformers for monitor commands. The global import should be limited to improve performance."""


def _item_to_ordered_dict(item, *properties):
    from collections import OrderedDict
    result = OrderedDict()

    for p in properties:
        if isinstance(p, tuple):
            property_name, display_name = p
        else:
            property_name = display_name = str(p)

        value = item.get(property_name)

        if isinstance(value, str):
            result[display_name] = value
        elif isinstance(value, list):
            result[display_name] = str(len(value))
        elif value is not None:
            result[display_name] = str(value)

    return result


def action_group_list_table(results):
    if not isinstance(results, list):
        results = [results]

    output_results = []
    for result in results:
        data = _item_to_ordered_dict(result, 'name', 'resourceGroup', 'groupShortName', 'enabled', 'location',
                                     ('emailReceivers', 'email'),
                                     ('smsReceivers', 'sms'),
                                     ('webhookReceivers', 'webhook'))

        output_results.append(data)

    return output_results
