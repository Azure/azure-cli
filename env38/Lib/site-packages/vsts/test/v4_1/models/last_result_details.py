# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class LastResultDetails(Model):
    """LastResultDetails.

    :param date_completed:
    :type date_completed: datetime
    :param duration:
    :type duration: long
    :param run_by:
    :type run_by: :class:`IdentityRef <test.v4_1.models.IdentityRef>`
    """

    _attribute_map = {
        'date_completed': {'key': 'dateCompleted', 'type': 'iso-8601'},
        'duration': {'key': 'duration', 'type': 'long'},
        'run_by': {'key': 'runBy', 'type': 'IdentityRef'}
    }

    def __init__(self, date_completed=None, duration=None, run_by=None):
        super(LastResultDetails, self).__init__()
        self.date_completed = date_completed
        self.duration = duration
        self.run_by = run_by
