# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .data_source_binding_base import DataSourceBindingBase


class DataSourceBinding(DataSourceBindingBase):
    """DataSourceBinding.

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
        'target': {'key': 'target', 'type': 'str'},
    }

    def __init__(self, data_source_name=None, endpoint_id=None, endpoint_url=None, parameters=None, result_selector=None, result_template=None, target=None):
        super(DataSourceBinding, self).__init__(data_source_name=data_source_name, endpoint_id=endpoint_id, endpoint_url=endpoint_url, parameters=parameters, result_selector=result_selector, result_template=result_template, target=target)
