# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class WidgetTypesResponse(Model):
    """WidgetTypesResponse.

    :param _links:
    :type _links: :class:`ReferenceLinks <dashboard.v4_1.models.ReferenceLinks>`
    :param uri:
    :type uri: str
    :param widget_types:
    :type widget_types: list of :class:`WidgetMetadata <dashboard.v4_1.models.WidgetMetadata>`
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'uri': {'key': 'uri', 'type': 'str'},
        'widget_types': {'key': 'widgetTypes', 'type': '[WidgetMetadata]'}
    }

    def __init__(self, _links=None, uri=None, widget_types=None):
        super(WidgetTypesResponse, self).__init__()
        self._links = _links
        self.uri = uri
        self.widget_types = widget_types
