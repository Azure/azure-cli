# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def transform_usage_output(result):
    result.usage_start = result.usage_start.strftime("%Y-%m-%dT%H:%M:%SZ")
    result.usage_end = result.usage_end.strftime("%Y-%m-%dT%H:%M:%SZ")
    result.usage_quantity = str(result.usage_quantity)
    result.billable_quantity = str(result.billable_quantity)
    result.pretax_cost = str(result.pretax_cost)
    if result.meter_details:
        result.meter_details.total_included_quantity = str(result.meter_details.total_included_quantity)
        result.meter_details.pretax_standard_rate = str(result.meter_details.pretax_standard_rate)
    return result


def transform_usage_list_output(result):
    return [transform_usage_output(item) for item in result]


def reservation_summaries_output(result):

    result.reserved_hours = str(result.reserved_hours)
    result.usage_date = result.usage_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    result.used_hours = str(result.used_hours)
    result.max_utilization_percentage = str(result.max_utilization_percentage)
    result.min_utilization_percentage = str(result.min_utilization_percentage)
    result.avg_utilization_percentage = str(result.avg_utilization_percentage)
    return result


def transform_reservation_summaries_list_output(result):
    return [reservation_summaries_output(item) for item in result]


def reservation_details_output(result):

    result.reserved_hours = str(result.reserved_hours)
    result.usage_date = result.usage_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    result.used_hours = str(result.used_hours)
    result.total_reserved_quantity = str(result.total_reserved_quantity)
    return result


def transform_reservation_details_list_output(result):
    return [reservation_details_output(item) for item in result]

def transform_budget_output(result):
    #TODO implement
return result

def transform_marketplace_output(result)
    #TODO implement
return result

def transform_pricesheet_output(result):
    result.billing_period_id = str(result.billing_period_id)
    result.meter_id = str(result.meter_id)
    result.meter_name = str(result.meter_name)
    result.unit_of_measure = str(result.unit_of_measure)
    result.included_quantity = str(result.included_quantity)
    result.part_number = str(result.part_number)
    result.unit_price = str(result.unit_price)
    result.currency_code = str(result.currency_code)

    if result.meter_details:        
        result.meter_details.meter_name = str(result.meter_details.meter_name)
        result.meter_details.meter_category = str(result.meter_details.meter_category)
        result.meter_details.unit = str(result.meter_details.unit)
        result.meter_details.meter_location = str(result.meter_details.meter_location)
        result.meter_details.total_included_quantity = str(result.meter_details.total_included_quantity)
        result.meter_details.pretax_standard_rate = str(result.meter_details.pretax_standard_rate)
    return result
