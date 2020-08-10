# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class DataSourceBindingBase(Model):
    """DataSourceBindingBase.

    :param data_source_name:
    :type data_source_name: str
    :param endpoint_id:
    :type endpoint_id: str
    :param endpoint_url:
    :type endpoint_url: str
    :param parameters:
    :type parameters: dict
    :param result_selector:
    :type result_selector: str
    :param result_template:
    :type result_template: str
    :param target:
    :type target: str
    """

    _attribute_map = {
        'data_source_name': {'key': 'dataSourceName', 'type': 'str'},
        'endpoint_id': {'key': 'endpointId', 'type': 'str'},
        'endpoint_url': {'key': 'endpointUrl', 'type': 'str'},
        'parameters': {'key': 'parameters', 'type': '{str}'},
        'result_selector': {'key': 'resultSelector', 'type': 'str'},
        'result_template': {'key': 'resultTemplate', 'type': 'str'},
        'target': {'key': 'target', 'type': 'str'}
    }

    def __init__(self, data_source_name=None, endpoint_id=None, endpoint_url=None, parameters=None, result_selector=None, result_template=None, target=None):
        super(DataSourceBindingBase, self).__init__()
        self.data_source_name = data_source_name
        self.endpoint_id = endpoint_id
        self.endpoint_url = endpoint_url
        self.parameters = parameters
        self.result_selector = result_selector
        self.result_template = result_template
        self.target = target
