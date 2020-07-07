# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class EnvironmentRetentionPolicy(Model):
    """EnvironmentRetentionPolicy.

    :param days_to_keep:
    :type days_to_keep: int
    :param releases_to_keep:
    :type releases_to_keep: int
    :param retain_build:
    :type retain_build: bool
    """

    _attribute_map = {
        'days_to_keep': {'key': 'daysToKeep', 'type': 'int'},
        'releases_to_keep': {'key': 'releasesToKeep', 'type': 'int'},
        'retain_build': {'key': 'retainBuild', 'type': 'bool'}
    }

    def __init__(self, days_to_keep=None, releases_to_keep=None, retain_build=None):
        super(EnvironmentRetentionPolicy, self).__init__()
        self.days_to_keep = days_to_keep
        self.releases_to_keep = releases_to_keep
        self.retain_build = retain_build
