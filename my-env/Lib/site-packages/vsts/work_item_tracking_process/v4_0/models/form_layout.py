# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class FormLayout(Model):
    """FormLayout.

    :param extensions: Gets and sets extensions list
    :type extensions: list of :class:`Extension <work-item-tracking.v4_0.models.Extension>`
    :param pages: Top level tabs of the layout.
    :type pages: list of :class:`Page <work-item-tracking.v4_0.models.Page>`
    :param system_controls: Headers controls of the layout.
    :type system_controls: list of :class:`Control <work-item-tracking.v4_0.models.Control>`
    """

    _attribute_map = {
        'extensions': {'key': 'extensions', 'type': '[Extension]'},
        'pages': {'key': 'pages', 'type': '[Page]'},
        'system_controls': {'key': 'systemControls', 'type': '[Control]'}
    }

    def __init__(self, extensions=None, pages=None, system_controls=None):
        super(FormLayout, self).__init__()
        self.extensions = extensions
        self.pages = pages
        self.system_controls = system_controls
