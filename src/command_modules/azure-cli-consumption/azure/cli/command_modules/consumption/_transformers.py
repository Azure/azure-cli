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
