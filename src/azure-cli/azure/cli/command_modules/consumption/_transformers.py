# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def budget_output(result):
    result['amount'] = str(result['amount'])
    if 'currentSpend' in result:
        result['currentSpend']['amount'] = str(result['currentSpend'].get('amount', None))
    if 'notifications' in result:
        for key in result['notifications']:
            value = result['notifications'][key]
            value['threshold'] = str(value.get('threshold', None))
    return result


def transform_budget_show_output(result):
    return budget_output(result)


def transform_budget_create_update_output(result):
    return budget_output(result)
