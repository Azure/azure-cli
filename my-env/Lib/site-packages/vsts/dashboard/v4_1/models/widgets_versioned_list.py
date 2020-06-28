# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class WidgetsVersionedList(Model):
    """WidgetsVersionedList.

    :param eTag:
    :type eTag: list of str
    :param widgets:
    :type widgets: list of :class:`Widget <dashboard.v4_1.models.Widget>`
    """

    _attribute_map = {
        'eTag': {'key': 'eTag', 'type': '[str]'},
        'widgets': {'key': 'widgets', 'type': '[Widget]'}
    }

    def __init__(self, eTag=None, widgets=None):
        super(WidgetsVersionedList, self).__init__()
        self.eTag = eTag
        self.widgets = widgets
