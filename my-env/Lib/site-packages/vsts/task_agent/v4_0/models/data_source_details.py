# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class DataSourceDetails(Model):
    """DataSourceDetails.

    :param data_source_name:
    :type data_source_name: str
    :param data_source_url:
    :type data_source_url: str
    :param parameters:
    :type parameters: dict
    :param resource_url:
    :type resource_url: str
    :param result_selector:
    :type result_selector: str
    """

    _attribute_map = {
        'data_source_name': {'key': 'dataSourceName', 'type': 'str'},
        'data_source_url': {'key': 'dataSourceUrl', 'type': 'str'},
        'parameters': {'key': 'parameters', 'type': '{str}'},
        'resource_url': {'key': 'resourceUrl', 'type': 'str'},
        'result_selector': {'key': 'resultSelector', 'type': 'str'}
    }

    def __init__(self, data_source_name=None, data_source_url=None, parameters=None, resource_url=None, result_selector=None):
        super(DataSourceDetails, self).__init__()
        self.data_source_name = data_source_name
        self.data_source_url = data_source_url
        self.parameters = parameters
        self.resource_url = resource_url
        self.result_selector = result_selector
