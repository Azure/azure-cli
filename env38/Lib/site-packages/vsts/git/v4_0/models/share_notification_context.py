# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ShareNotificationContext(Model):
    """ShareNotificationContext.

    :param message: Optional user note or message.
    :type message: str
    :param receivers: Identities of users who will receive a share notification.
    :type receivers: list of :class:`IdentityRef <git.v4_0.models.IdentityRef>`
    """

    _attribute_map = {
        'message': {'key': 'message', 'type': 'str'},
        'receivers': {'key': 'receivers', 'type': '[IdentityRef]'}
    }

    def __init__(self, message=None, receivers=None):
        super(ShareNotificationContext, self).__init__()
        self.message = message
        self.receivers = receivers
