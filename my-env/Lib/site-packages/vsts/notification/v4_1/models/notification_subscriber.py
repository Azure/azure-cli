# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class NotificationSubscriber(Model):
    """NotificationSubscriber.

    :param delivery_preference: Indicates how the subscriber should be notified by default.
    :type delivery_preference: object
    :param flags:
    :type flags: object
    :param id: Identifier of the subscriber.
    :type id: str
    :param preferred_email_address: Preferred email address of the subscriber. A null or empty value indicates no preferred email address has been set.
    :type preferred_email_address: str
    """

    _attribute_map = {
        'delivery_preference': {'key': 'deliveryPreference', 'type': 'object'},
        'flags': {'key': 'flags', 'type': 'object'},
        'id': {'key': 'id', 'type': 'str'},
        'preferred_email_address': {'key': 'preferredEmailAddress', 'type': 'str'}
    }

    def __init__(self, delivery_preference=None, flags=None, id=None, preferred_email_address=None):
        super(NotificationSubscriber, self).__init__()
        self.delivery_preference = delivery_preference
        self.flags = flags
        self.id = id
        self.preferred_email_address = preferred_email_address
