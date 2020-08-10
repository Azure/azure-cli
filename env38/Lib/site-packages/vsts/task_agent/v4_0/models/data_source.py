# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class DataSource(Model):
    """DataSource.

    :param endpoint_url:
    :type endpoint_url: str
    :param name:
    :type name: str
    :param resource_url:
    :type resource_url: str
    :param result_selector:
    :type result_selector: str
    """

    _attribute_map = {
        'endpoint_url': {'key': 'endpointUrl', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'resource_url': {'key': 'resourceUrl', 'type': 'str'},
        'result_selector': {'key': 'resultSelector', 'type': 'str'}
    }

    def __init__(self, endpoint_url=None, name=None, resource_url=None, result_selector=None):
        super(DataSource, self).__init__()
        self.endpoint_url = endpoint_url
        self.name = name
        self.resource_url = resource_url
        self.result_selector = result_selector
