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


def _generic_table_convert(source, row_convert_fn):
    if not isinstance(source, list):
        source = [source]

    return [row_convert_fn(each) for each in source]


def action_group_list_table(results):
    if not isinstance(results, list):
        results = [results]

    output_results = []
    for result in results:
        data = _item_to_ordered_dict(result, 'name', 'resourceGroup', 'groupShortName', 'enabled', 'location',
                                     ('emailReceivers', 'email'), ('smsReceivers', 'sms'),
                                     ('webhookReceivers', 'webhook'), ('armRoleReceivers', 'armrole'),
                                     ('azureAppPushReceivers', 'azureapppush'), ('itsmReceivers', 'itsm'),
                                     ('automationRunbookReceivers', 'automationrunbook'), ('voiceReceivers', 'voice'),
                                     ('logicAppReceivers', 'logicapp'), ('azureFunctionReceivers', 'azurefunction'))

        output_results.append(data)

    return output_results


def metrics_definitions_table(results):
    def row_convert(item):
        from collections import OrderedDict
        result = OrderedDict()
        result['Display Name'] = item['name']['localizedValue']
        result['Metric Name'] = item['name']['value']
        result['Unit'] = item['unit']
        result['Type'] = item['primaryAggregationType']
        result['Dimension Required'] = 'True' if item['isDimensionRequired'] else 'False'
        result['Dimensions'] = ', '.join(d['value'] for d in item.get('dimensions', []) or [])

        return result

    return _generic_table_convert(results, row_convert)


def metrics_namespaces_table(results):
    def row_convert(item):
        from collections import OrderedDict
        result = OrderedDict()
        result['Classification'] = item['classification']
        result['Metric Namespace Name'] = item['properties']['metricNamespaceName']
        return result
    return _generic_table_convert(results, row_convert)


def metrics_table(results):
    from collections import OrderedDict

    def from_time(time_string):
        from datetime import datetime
        try:
            return datetime.strptime(time_string, '%Y-%m-%dT%H:%M:%S+00:00').strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            return time_string

    retval = []
    for value_group in results['value']:
        name = value_group['name']['localizedValue']
        for series in value_group['timeseries']:
            metadata = dict((m['name']['localizedValue'], m['value']) for m in series['metadatavalues'])

            for data in series['data']:
                row = OrderedDict()
                row['Timestamp'] = from_time(data['timeStamp'])
                row['Name'] = name
                for metadata_name, metadata_value in metadata.items():
                    row[metadata_name] = metadata_value

                for field in data:
                    if field == 'timeStamp':
                        continue
                    row[field] = data[field]
                retval.append(row)
    return retval
