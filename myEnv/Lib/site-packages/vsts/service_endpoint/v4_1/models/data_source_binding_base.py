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

    :param data_source_name: Gets or sets the name of the data source.
    :type data_source_name: str
    :param endpoint_id: Gets or sets the endpoint Id.
    :type endpoint_id: str
    :param endpoint_url: Gets or sets the url of the service endpoint.
    :type endpoint_url: str
    :param headers: Gets or sets the authorization headers.
    :type headers: list of :class:`AuthorizationHeader <microsoft.-team-foundation.-distributed-task.-common.-contracts.v4_1.models.AuthorizationHeader>`
    :param parameters: Gets or sets the parameters for the data source.
    :type parameters: dict
    :param result_selector: Gets or sets the result selector.
    :type result_selector: str
    :param result_template: Gets or sets the result template.
    :type result_template: str
    :param target: Gets or sets the target of the data source.
    :type target: str
    """

    _attribute_map = {
        'data_source_name': {'key': 'dataSourceName', 'type': 'str'},
        'endpoint_id': {'key': 'endpointId', 'type': 'str'},
        'endpoint_url': {'key': 'endpointUrl', 'type': 'str'},
        'headers': {'key': 'headers', 'type': '[AuthorizationHeader]'},
        'parameters': {'key': 'parameters', 'type': '{str}'},
        'result_selector': {'key': 'resultSelector', 'type': 'str'},
        'result_template': {'key': 'resultTemplate', 'type': 'str'},
        'target': {'key': 'target', 'type': 'str'}
    }

    def __init__(self, data_source_name=None, endpoint_id=None, endpoint_url=None, headers=None, parameters=None, result_selector=None, result_template=None, target=None):
        super(DataSourceBindingBase, self).__init__()
        self.data_source_name = data_source_name
        self.endpoint_id = endpoint_id
        self.endpoint_url = endpoint_url
        self.headers = headers
        self.parameters = parameters
        self.result_selector = result_selector
        self.result_template = result_template
        self.target = target
