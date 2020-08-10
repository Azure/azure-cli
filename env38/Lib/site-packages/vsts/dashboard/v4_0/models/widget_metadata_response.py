# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class WidgetMetadataResponse(Model):
    """WidgetMetadataResponse.

    :param uri:
    :type uri: str
    :param widget_metadata:
    :type widget_metadata: :class:`WidgetMetadata <dashboard.v4_0.models.WidgetMetadata>`
    """

    _attribute_map = {
        'uri': {'key': 'uri', 'type': 'str'},
        'widget_metadata': {'key': 'widgetMetadata', 'type': 'WidgetMetadata'}
    }

    def __init__(self, uri=None, widget_metadata=None):
        super(WidgetMetadataResponse, self).__init__()
        self.uri = uri
        self.widget_metadata = widget_metadata
