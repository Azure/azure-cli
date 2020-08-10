# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class VersionControlProjectInfo(Model):
    """VersionControlProjectInfo.

    :param default_source_control_type:
    :type default_source_control_type: object
    :param project:
    :type project: :class:`TeamProjectReference <tfvc.v4_1.models.TeamProjectReference>`
    :param supports_git:
    :type supports_git: bool
    :param supports_tFVC:
    :type supports_tFVC: bool
    """

    _attribute_map = {
        'default_source_control_type': {'key': 'defaultSourceControlType', 'type': 'object'},
        'project': {'key': 'project', 'type': 'TeamProjectReference'},
        'supports_git': {'key': 'supportsGit', 'type': 'bool'},
        'supports_tFVC': {'key': 'supportsTFVC', 'type': 'bool'}
    }

    def __init__(self, default_source_control_type=None, project=None, supports_git=None, supports_tFVC=None):
        super(VersionControlProjectInfo, self).__init__()
        self.default_source_control_type = default_source_control_type
        self.project = project
        self.supports_git = supports_git
        self.supports_tFVC = supports_tFVC
