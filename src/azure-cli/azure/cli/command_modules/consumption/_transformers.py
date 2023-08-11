# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def reservation_summary_output(result):

    result.reserved_hours = str(result.reserved_hours)
    result.usage_date = result.usage_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    result.used_hours = str(result.used_hours)
    result.max_utilization_percentage = str(result.max_utilization_percentage)
    result.min_utilization_percentage = str(result.min_utilization_percentage)
    result.avg_utilization_percentage = str(result.avg_utilization_percentage)
    return result


def transform_reservation_summary_list_output(result):
    return [reservation_summary_output(item) for item in result]


def pricesheet_show_properties(result):
    result.unit_of_measure = str(result.unit_of_measure)
    result.included_quantity = str(result.included_quantity)
    result.unit_price = str(result.unit_price)
    if result.meter_details:
        result.meter_details.total_included_quantity = str(result.meter_details.total_included_quantity)
        result.meter_details.pretax_standard_rate = str(result.meter_details.pretax_standard_rate)
    return result


def transform_pricesheet_show_output(result):
    result.pricesheets = [pricesheet_show_properties(item) for item in result.pricesheets]
    return result


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
