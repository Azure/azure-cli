# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class RetentionSettings(Model):
    """RetentionSettings.

    :param days_to_keep_deleted_releases:
    :type days_to_keep_deleted_releases: int
    :param default_environment_retention_policy:
    :type default_environment_retention_policy: :class:`EnvironmentRetentionPolicy <release.v4_1.models.EnvironmentRetentionPolicy>`
    :param maximum_environment_retention_policy:
    :type maximum_environment_retention_policy: :class:`EnvironmentRetentionPolicy <release.v4_1.models.EnvironmentRetentionPolicy>`
    """

    _attribute_map = {
        'days_to_keep_deleted_releases': {'key': 'daysToKeepDeletedReleases', 'type': 'int'},
        'default_environment_retention_policy': {'key': 'defaultEnvironmentRetentionPolicy', 'type': 'EnvironmentRetentionPolicy'},
        'maximum_environment_retention_policy': {'key': 'maximumEnvironmentRetentionPolicy', 'type': 'EnvironmentRetentionPolicy'}
    }

    def __init__(self, days_to_keep_deleted_releases=None, default_environment_retention_policy=None, maximum_environment_retention_policy=None):
        super(RetentionSettings, self).__init__()
        self.days_to_keep_deleted_releases = days_to_keep_deleted_releases
        self.default_environment_retention_policy = default_environment_retention_policy
        self.maximum_environment_retention_policy = maximum_environment_retention_policy
