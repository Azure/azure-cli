# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from collections import OrderedDict

def transform_usage_output(result):
    new_entry = OrderedDict()
    new_entry['id'] = result.id
    new_entry['name'] = result.name
    new_entry['type'] = result.type
    if result.tags:
        new_entry['tags'] = result.tags
    new_entry['usageStart'] = result.usage_start.strftime("%Y-%m-%dT%H:%M:%SZ")
    new_entry['usageEnd'] = result.usage_end.strftime("%Y-%m-%dT%H:%M:%SZ")
    new_entry['billingPeriodId'] = result.billing_period_id
    if result.invoice_id:
        new_entry['invoiceId'] = result.invoice_id
    new_entry['instanceName'] = result.instance_name
    if result.instance_id:
        new_entry['instanceId'] = result.instance_id
    if result.instance_location:
        new_entry['instanceLocation'] = result.instance_location
    new_entry['currency'] = result.currency
    new_entry['usageQuantity'] = str(result.usage_quantity)
    new_entry['billableQuantity'] = str(result.billable_quantity)
    new_entry['pretaxCost'] = str(result.pretax_cost)
    new_entry['isEstimated'] = result.is_estimated
    new_entry['meterId'] = result.meter_id
    if result.meter_details:
        new_entry['meterDetails'] = OrderedDict()
        if result.meter_details.meter_name:
            new_entry['meterDetails']['meterName'] = result.meter_details.meter_name
        if result.meter_details.meter_category:
            new_entry['meterDetails']['meterCategory'] = result.meter_details.meter_category
        if result.meter_details.meter_sub_category:
            new_entry['meterDetails']['meterSubCategory'] = result.meter_details.meter_sub_category
        if result.meter_details.unit:
            new_entry['meterDetails']['unit'] = result.meter_details.unit
        if result.meter_details.meter_location:
            new_entry['meterDetails']['meterLocation'] = result.meter_details.meter_location
        if result.meter_details.total_included_quantity:
           new_entry['meterDetails']['totalIncludedQuantity'] = str(result.meter_details.total_included_quantity)
        if result.meter_details.pretax_standard_rate:
            new_entry['meterDetails']['pretaxStandardRate'] = str(result.meter_details.pretax_standard_rate)
    if result.additional_properties:
        new_entry['additionalProperties'] = result.additional_properties
    return new_entry

def transform_usage_list_output(result):
    new_result = []
    for item in result:
        new_result.append(transform_usage_output(item))
    return new_result
