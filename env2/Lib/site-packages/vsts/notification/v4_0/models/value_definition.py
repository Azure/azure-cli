# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ValueDefinition(Model):
    """ValueDefinition.

    :param data_source: Gets or sets the data source.
    :type data_source: list of :class:`InputValue <notification.v4_0.models.InputValue>`
    :param end_point: Gets or sets the rest end point.
    :type end_point: str
    :param result_template: Gets or sets the result template.
    :type result_template: str
    """

    _attribute_map = {
        'data_source': {'key': 'dataSource', 'type': '[InputValue]'},
        'end_point': {'key': 'endPoint', 'type': 'str'},
        'result_template': {'key': 'resultTemplate', 'type': 'str'}
    }

    def __init__(self, data_source=None, end_point=None, result_template=None):
        super(ValueDefinition, self).__init__()
        self.data_source = data_source
        self.end_point = end_point
        self.result_template = result_template
