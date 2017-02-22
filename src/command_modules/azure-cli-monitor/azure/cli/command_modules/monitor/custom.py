# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def list_metric_definitions(client, resource_uri, metric_names=None):
    '''Commands to manage metric definitions.
    :param str resource_uri: The identifier of the resource
    :param str metric_names: The list of metric names
    '''
    odata_filter = _list_metric_definitions_filter_builder(metric_names)
    metric_definitions = client.list(resource_uri, filter=odata_filter)
    return list(metric_definitions)


def _list_metric_definitions_filter_builder(metric_names=None):
    '''Build up OData filter string from metric_names
    '''
    filters = []
    if metric_names:
        if "," in metric_names:
            names = metric_names.split(",")
            for metric_name in names:
                filters.append("name.value eq '{}'".format(metric_name))
        else:
            filters.append("name.value eq '{}'".format(metric_names))
    return ' or '.join(filters)
