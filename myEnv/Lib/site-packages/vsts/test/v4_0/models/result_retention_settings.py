# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ResultRetentionSettings(Model):
    """ResultRetentionSettings.

    :param automated_results_retention_duration:
    :type automated_results_retention_duration: int
    :param last_updated_by:
    :type last_updated_by: :class:`IdentityRef <test.v4_0.models.IdentityRef>`
    :param last_updated_date:
    :type last_updated_date: datetime
    :param manual_results_retention_duration:
    :type manual_results_retention_duration: int
    """

    _attribute_map = {
        'automated_results_retention_duration': {'key': 'automatedResultsRetentionDuration', 'type': 'int'},
        'last_updated_by': {'key': 'lastUpdatedBy', 'type': 'IdentityRef'},
        'last_updated_date': {'key': 'lastUpdatedDate', 'type': 'iso-8601'},
        'manual_results_retention_duration': {'key': 'manualResultsRetentionDuration', 'type': 'int'}
    }

    def __init__(self, automated_results_retention_duration=None, last_updated_by=None, last_updated_date=None, manual_results_retention_duration=None):
        super(ResultRetentionSettings, self).__init__()
        self.automated_results_retention_duration = automated_results_retention_duration
        self.last_updated_by = last_updated_by
        self.last_updated_date = last_updated_date
        self.manual_results_retention_duration = manual_results_retention_duration
