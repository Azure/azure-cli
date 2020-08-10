# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class PublisherEvent(Model):
    """PublisherEvent.

    :param diagnostics: Add key/value pairs which will be stored with a published notification in the SH service DB.  This key/value pairs are for diagnostic purposes only and will have not effect on the delivery of a notificaton.
    :type diagnostics: dict
    :param event: The event being published
    :type event: :class:`Event <service-hooks.v4_1.models.Event>`
    :param other_resource_versions: Gets or sets the array of older supported resource versions.
    :type other_resource_versions: list of :class:`VersionedResource <service-hooks.v4_1.models.VersionedResource>`
    :param publisher_input_filters: Optional publisher-input filters which restricts the set of subscriptions which are triggered by the event
    :type publisher_input_filters: list of :class:`InputFilter <service-hooks.v4_1.models.InputFilter>`
    :param subscription: Gets or sets matchd hooks subscription which caused this event.
    :type subscription: :class:`Subscription <service-hooks.v4_1.models.Subscription>`
    """

    _attribute_map = {
        'diagnostics': {'key': 'diagnostics', 'type': '{str}'},
        'event': {'key': 'event', 'type': 'Event'},
        'other_resource_versions': {'key': 'otherResourceVersions', 'type': '[VersionedResource]'},
        'publisher_input_filters': {'key': 'publisherInputFilters', 'type': '[InputFilter]'},
        'subscription': {'key': 'subscription', 'type': 'Subscription'}
    }

    def __init__(self, diagnostics=None, event=None, other_resource_versions=None, publisher_input_filters=None, subscription=None):
        super(PublisherEvent, self).__init__()
        self.diagnostics = diagnostics
        self.event = event
        self.other_resource_versions = other_resource_versions
        self.publisher_input_filters = publisher_input_filters
        self.subscription = subscription
