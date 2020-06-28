# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .git_version_descriptor import GitVersionDescriptor


class GitBaseVersionDescriptor(GitVersionDescriptor):
    """GitBaseVersionDescriptor.

    :param version: Version string identifier (name of tag/branch, SHA1 of commit)
    :type version: str
    :param version_options: Version options - Specify additional modifiers to version (e.g Previous)
    :type version_options: object
    :param version_type: Version type (branch, tag, or commit). Determines how Id is interpreted
    :type version_type: object
    :param base_version: Version string identifier (name of tag/branch, SHA1 of commit)
    :type base_version: str
    :param base_version_options: Version options - Specify additional modifiers to version (e.g Previous)
    :type base_version_options: object
    :param base_version_type: Version type (branch, tag, or commit). Determines how Id is interpreted
    :type base_version_type: object
    """

    _attribute_map = {
        'version': {'key': 'version', 'type': 'str'},
        'version_options': {'key': 'versionOptions', 'type': 'object'},
        'version_type': {'key': 'versionType', 'type': 'object'},
        'base_version': {'key': 'baseVersion', 'type': 'str'},
        'base_version_options': {'key': 'baseVersionOptions', 'type': 'object'},
        'base_version_type': {'key': 'baseVersionType', 'type': 'object'}
    }

    def __init__(self, version=None, version_options=None, version_type=None, base_version=None, base_version_options=None, base_version_type=None):
        super(GitBaseVersionDescriptor, self).__init__(version=version, version_options=version_options, version_type=version_type)
        self.base_version = base_version
        self.base_version_options = base_version_options
        self.base_version_type = base_version_type
