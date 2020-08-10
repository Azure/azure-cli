# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class NotificationsData(Model):
    """NotificationsData.

    :param data: Notification data needed
    :type data: dict
    :param identities: List of users who should get the notification
    :type identities: dict
    :param type: Type of Mail Notification.Can be Qna , review or CustomerContact
    :type type: object
    """

    _attribute_map = {
        'data': {'key': 'data', 'type': '{object}'},
        'identities': {'key': 'identities', 'type': '{object}'},
        'type': {'key': 'type', 'type': 'object'}
    }

    def __init__(self, data=None, identities=None, type=None):
        super(NotificationsData, self).__init__()
        self.data = data
        self.identities = identities
        self.type = type
