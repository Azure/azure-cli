# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TestMessageLogDetails(Model):
    """TestMessageLogDetails.

    :param date_created: Date when the resource is created
    :type date_created: datetime
    :param entry_id: Id of the resource
    :type entry_id: int
    :param message: Message of the resource
    :type message: str
    """

    _attribute_map = {
        'date_created': {'key': 'dateCreated', 'type': 'iso-8601'},
        'entry_id': {'key': 'entryId', 'type': 'int'},
        'message': {'key': 'message', 'type': 'str'}
    }

    def __init__(self, date_created=None, entry_id=None, message=None):
        super(TestMessageLogDetails, self).__init__()
        self.date_created = date_created
        self.entry_id = entry_id
        self.message = message
