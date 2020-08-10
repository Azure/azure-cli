# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class Event(Model):
    """Event.

    :param created_date: Gets or sets the UTC-based date and time that this event was created.
    :type created_date: datetime
    :param detailed_message: Gets or sets the detailed message associated with this event.
    :type detailed_message: :class:`FormattedEventMessage <service-hooks.v4_0.models.FormattedEventMessage>`
    :param event_type: Gets or sets the type of this event.
    :type event_type: str
    :param id: Gets or sets the unique identifier of this event.
    :type id: str
    :param message: Gets or sets the (brief) message associated with this event.
    :type message: :class:`FormattedEventMessage <service-hooks.v4_0.models.FormattedEventMessage>`
    :param publisher_id: Gets or sets the identifier of the publisher that raised this event.
    :type publisher_id: str
    :param resource: Gets or sets the data associated with this event.
    :type resource: object
    :param resource_containers: Gets or sets the resource containers.
    :type resource_containers: dict
    :param resource_version: Gets or sets the version of the data associated with this event.
    :type resource_version: str
    :param session_token: Gets or sets the Session Token that can be used in further interactions
    :type session_token: :class:`SessionToken <service-hooks.v4_0.models.SessionToken>`
    """

    _attribute_map = {
        'created_date': {'key': 'createdDate', 'type': 'iso-8601'},
        'detailed_message': {'key': 'detailedMessage', 'type': 'FormattedEventMessage'},
        'event_type': {'key': 'eventType', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'message': {'key': 'message', 'type': 'FormattedEventMessage'},
        'publisher_id': {'key': 'publisherId', 'type': 'str'},
        'resource': {'key': 'resource', 'type': 'object'},
        'resource_containers': {'key': 'resourceContainers', 'type': '{ResourceContainer}'},
        'resource_version': {'key': 'resourceVersion', 'type': 'str'},
        'session_token': {'key': 'sessionToken', 'type': 'SessionToken'}
    }

    def __init__(self, created_date=None, detailed_message=None, event_type=None, id=None, message=None, publisher_id=None, resource=None, resource_containers=None, resource_version=None, session_token=None):
        super(Event, self).__init__()
        self.created_date = created_date
        self.detailed_message = detailed_message
        self.event_type = event_type
        self.id = id
        self.message = message
        self.publisher_id = publisher_id
        self.resource = resource
        self.resource_containers = resource_containers
        self.resource_version = resource_version
        self.session_token = session_token
