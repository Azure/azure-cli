# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GitItemDescriptor(Model):
    """GitItemDescriptor.

    :param path: Path to item
    :type path: str
    :param recursion_level: Specifies whether to include children (OneLevel), all descendants (Full), or None
    :type recursion_level: object
    :param version: Version string (interpretation based on VersionType defined in subclass
    :type version: str
    :param version_options: Version modifiers (e.g. previous)
    :type version_options: object
    :param version_type: How to interpret version (branch,tag,commit)
    :type version_type: object
    """

    _attribute_map = {
        'path': {'key': 'path', 'type': 'str'},
        'recursion_level': {'key': 'recursionLevel', 'type': 'object'},
        'version': {'key': 'version', 'type': 'str'},
        'version_options': {'key': 'versionOptions', 'type': 'object'},
        'version_type': {'key': 'versionType', 'type': 'object'}
    }

    def __init__(self, path=None, recursion_level=None, version=None, version_options=None, version_type=None):
        super(GitItemDescriptor, self).__init__()
        self.path = path
        self.recursion_level = recursion_level
        self.version = version
        self.version_options = version_options
        self.version_type = version_type
