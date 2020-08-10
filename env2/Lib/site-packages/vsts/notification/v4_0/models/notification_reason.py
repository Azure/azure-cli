# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class NotificationReason(Model):
    """NotificationReason.

    :param notification_reason_type:
    :type notification_reason_type: object
    :param target_identities:
    :type target_identities: list of :class:`IdentityRef <notification.v4_0.models.IdentityRef>`
    """

    _attribute_map = {
        'notification_reason_type': {'key': 'notificationReasonType', 'type': 'object'},
        'target_identities': {'key': 'targetIdentities', 'type': '[IdentityRef]'}
    }

    def __init__(self, notification_reason_type=None, target_identities=None):
        super(NotificationReason, self).__init__()
        self.notification_reason_type = notification_reason_type
        self.target_identities = target_identities
