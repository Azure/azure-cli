# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TfvcItemDescriptor(Model):
    """TfvcItemDescriptor.

    :param path:
    :type path: str
    :param recursion_level:
    :type recursion_level: object
    :param version:
    :type version: str
    :param version_option:
    :type version_option: object
    :param version_type:
    :type version_type: object
    """

    _attribute_map = {
        'path': {'key': 'path', 'type': 'str'},
        'recursion_level': {'key': 'recursionLevel', 'type': 'object'},
        'version': {'key': 'version', 'type': 'str'},
        'version_option': {'key': 'versionOption', 'type': 'object'},
        'version_type': {'key': 'versionType', 'type': 'object'}
    }

    def __init__(self, path=None, recursion_level=None, version=None, version_option=None, version_type=None):
        super(TfvcItemDescriptor, self).__init__()
        self.path = path
        self.recursion_level = recursion_level
        self.version = version
        self.version_option = version_option
        self.version_type = version_type
