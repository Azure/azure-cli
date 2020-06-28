# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .git_version_descriptor import GitVersionDescriptor


class GitTargetVersionDescriptor(GitVersionDescriptor):
    """GitTargetVersionDescriptor.

    :param version: Version string identifier (name of tag/branch, SHA1 of commit)
    :type version: str
    :param version_options: Version options - Specify additional modifiers to version (e.g Previous)
    :type version_options: object
    :param version_type: Version type (branch, tag, or commit). Determines how Id is interpreted
    :type version_type: object
    :param target_version: Version string identifier (name of tag/branch, SHA1 of commit)
    :type target_version: str
    :param target_version_options: Version options - Specify additional modifiers to version (e.g Previous)
    :type target_version_options: object
    :param target_version_type: Version type (branch, tag, or commit). Determines how Id is interpreted
    :type target_version_type: object
    """

    _attribute_map = {
        'version': {'key': 'version', 'type': 'str'},
        'version_options': {'key': 'versionOptions', 'type': 'object'},
        'version_type': {'key': 'versionType', 'type': 'object'},
        'target_version': {'key': 'targetVersion', 'type': 'str'},
        'target_version_options': {'key': 'targetVersionOptions', 'type': 'object'},
        'target_version_type': {'key': 'targetVersionType', 'type': 'object'}
    }

    def __init__(self, version=None, version_options=None, version_type=None, target_version=None, target_version_options=None, target_version_type=None):
        super(GitTargetVersionDescriptor, self).__init__(version=version, version_options=version_options, version_type=version_type)
        self.target_version = target_version
        self.target_version_options = target_version_options
        self.target_version_type = target_version_type
