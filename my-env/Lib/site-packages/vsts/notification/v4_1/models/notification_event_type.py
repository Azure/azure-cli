# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class NotificationEventType(Model):
    """NotificationEventType.

    :param category:
    :type category: :class:`NotificationEventTypeCategory <notification.v4_1.models.NotificationEventTypeCategory>`
    :param color: Gets or sets the color representing this event type. Example: rgb(128,245,211) or #fafafa
    :type color: str
    :param custom_subscriptions_allowed:
    :type custom_subscriptions_allowed: bool
    :param event_publisher:
    :type event_publisher: :class:`NotificationEventPublisher <notification.v4_1.models.NotificationEventPublisher>`
    :param fields:
    :type fields: dict
    :param has_initiator:
    :type has_initiator: bool
    :param icon: Gets or sets the icon representing this event type. Can be a URL or a CSS class. Example: css://some-css-class
    :type icon: str
    :param id: Gets or sets the unique identifier of this event definition.
    :type id: str
    :param name: Gets or sets the name of this event definition.
    :type name: str
    :param roles:
    :type roles: list of :class:`NotificationEventRole <notification.v4_1.models.NotificationEventRole>`
    :param supported_scopes: Gets or sets the scopes that this event type supports
    :type supported_scopes: list of str
    :param url: Gets or sets the rest end point to get this event type details (fields, fields types)
    :type url: str
    """

    _attribute_map = {
        'category': {'key': 'category', 'type': 'NotificationEventTypeCategory'},
        'color': {'key': 'color', 'type': 'str'},
        'custom_subscriptions_allowed': {'key': 'customSubscriptionsAllowed', 'type': 'bool'},
        'event_publisher': {'key': 'eventPublisher', 'type': 'NotificationEventPublisher'},
        'fields': {'key': 'fields', 'type': '{NotificationEventField}'},
        'has_initiator': {'key': 'hasInitiator', 'type': 'bool'},
        'icon': {'key': 'icon', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'roles': {'key': 'roles', 'type': '[NotificationEventRole]'},
        'supported_scopes': {'key': 'supportedScopes', 'type': '[str]'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, category=None, color=None, custom_subscriptions_allowed=None, event_publisher=None, fields=None, has_initiator=None, icon=None, id=None, name=None, roles=None, supported_scopes=None, url=None):
        super(NotificationEventType, self).__init__()
        self.category = category
        self.color = color
        self.custom_subscriptions_allowed = custom_subscriptions_allowed
        self.event_publisher = event_publisher
        self.fields = fields
        self.has_initiator = has_initiator
        self.icon = icon
        self.id = id
        self.name = name
        self.roles = roles
        self.supported_scopes = supported_scopes
        self.url = url
