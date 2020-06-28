# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TfvcVersionDescriptor(Model):
    """TfvcVersionDescriptor.

    :param version:
    :type version: str
    :param version_option:
    :type version_option: object
    :param version_type:
    :type version_type: object
    """

    _attribute_map = {
        'version': {'key': 'version', 'type': 'str'},
        'version_option': {'key': 'versionOption', 'type': 'object'},
        'version_type': {'key': 'versionType', 'type': 'object'}
    }

    def __init__(self, version=None, version_option=None, version_type=None):
        super(TfvcVersionDescriptor, self).__init__()
        self.version = version
        self.version_option = version_option
        self.version_type = version_type
