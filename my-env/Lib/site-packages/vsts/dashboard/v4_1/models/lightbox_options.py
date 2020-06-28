# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class LightboxOptions(Model):
    """LightboxOptions.

    :param height: Height of desired lightbox, in pixels
    :type height: int
    :param resizable: True to allow lightbox resizing, false to disallow lightbox resizing, defaults to false.
    :type resizable: bool
    :param width: Width of desired lightbox, in pixels
    :type width: int
    """

    _attribute_map = {
        'height': {'key': 'height', 'type': 'int'},
        'resizable': {'key': 'resizable', 'type': 'bool'},
        'width': {'key': 'width', 'type': 'int'}
    }

    def __init__(self, height=None, resizable=None, width=None):
        super(LightboxOptions, self).__init__()
        self.height = height
        self.resizable = resizable
        self.width = width
