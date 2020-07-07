# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class NotificationSubscriberUpdateParameters(Model):
    """NotificationSubscriberUpdateParameters.

    :param delivery_preference: New delivery preference for the subscriber (indicates how the subscriber should be notified).
    :type delivery_preference: object
    :param preferred_email_address: New preferred email address for the subscriber. Specify an empty string to clear the current address.
    :type preferred_email_address: str
    """

    _attribute_map = {
        'delivery_preference': {'key': 'deliveryPreference', 'type': 'object'},
        'preferred_email_address': {'key': 'preferredEmailAddress', 'type': 'str'}
    }

    def __init__(self, delivery_preference=None, preferred_email_address=None):
        super(NotificationSubscriberUpdateParameters, self).__init__()
        self.delivery_preference = delivery_preference
        self.preferred_email_address = preferred_email_address
