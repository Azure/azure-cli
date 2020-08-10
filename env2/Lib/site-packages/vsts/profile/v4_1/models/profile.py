# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class Profile(Model):
    """Profile.

    :param application_container:
    :type application_container: :class:`AttributesContainer <profile.v4_1.models.AttributesContainer>`
    :param core_attributes:
    :type core_attributes: dict
    :param core_revision:
    :type core_revision: int
    :param id:
    :type id: str
    :param profile_state:
    :type profile_state: object
    :param revision:
    :type revision: int
    :param time_stamp:
    :type time_stamp: datetime
    """

    _attribute_map = {
        'application_container': {'key': 'applicationContainer', 'type': 'AttributesContainer'},
        'core_attributes': {'key': 'coreAttributes', 'type': '{CoreProfileAttribute}'},
        'core_revision': {'key': 'coreRevision', 'type': 'int'},
        'id': {'key': 'id', 'type': 'str'},
        'profile_state': {'key': 'profileState', 'type': 'object'},
        'revision': {'key': 'revision', 'type': 'int'},
        'time_stamp': {'key': 'timeStamp', 'type': 'iso-8601'}
    }

    def __init__(self, application_container=None, core_attributes=None, core_revision=None, id=None, profile_state=None, revision=None, time_stamp=None):
        super(Profile, self).__init__()
        self.application_container = application_container
        self.core_attributes = core_attributes
        self.core_revision = core_revision
        self.id = id
        self.profile_state = profile_state
        self.revision = revision
        self.time_stamp = time_stamp
