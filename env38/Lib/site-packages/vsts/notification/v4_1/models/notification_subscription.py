# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class NotificationSubscription(Model):
    """NotificationSubscription.

    :param _links: Links to related resources, APIs, and views for the subscription.
    :type _links: :class:`ReferenceLinks <notification.v4_1.models.ReferenceLinks>`
    :param admin_settings: Admin-managed settings for the subscription. Only applies when the subscriber is a group.
    :type admin_settings: :class:`SubscriptionAdminSettings <notification.v4_1.models.SubscriptionAdminSettings>`
    :param channel: Channel for delivering notifications triggered by the subscription.
    :type channel: :class:`ISubscriptionChannel <notification.v4_1.models.ISubscriptionChannel>`
    :param description: Description of the subscription. Typically describes filter criteria which helps identity the subscription.
    :type description: str
    :param diagnostics: Diagnostics for this subscription.
    :type diagnostics: :class:`SubscriptionDiagnostics <notification.v4_1.models.SubscriptionDiagnostics>`
    :param extended_properties: Any extra properties like detailed description for different contexts, user/group contexts
    :type extended_properties: dict
    :param filter: Matching criteria for the subscription. ExpressionFilter
    :type filter: :class:`ISubscriptionFilter <notification.v4_1.models.ISubscriptionFilter>`
    :param flags: Read-only indicators that further describe the subscription.
    :type flags: object
    :param id: Subscription identifier.
    :type id: str
    :param last_modified_by: User that last modified (or created) the subscription.
    :type last_modified_by: :class:`IdentityRef <notification.v4_1.models.IdentityRef>`
    :param modified_date: Date when the subscription was last modified. If the subscription has not been updated since it was created, this value will indicate when the subscription was created.
    :type modified_date: datetime
    :param permissions: The permissions the user have for this subscriptions.
    :type permissions: object
    :param scope: The container in which events must be published from in order to be matched by the subscription. If empty, the scope is the current host (typically an account or project collection). For example, a subscription scoped to project A will not produce notifications for events published from project B.
    :type scope: :class:`SubscriptionScope <notification.v4_1.models.SubscriptionScope>`
    :param status: Status of the subscription. Typically indicates whether the subscription is enabled or not.
    :type status: object
    :param status_message: Message that provides more details about the status of the subscription.
    :type status_message: str
    :param subscriber: User or group that will receive notifications for events matching the subscription's filter criteria.
    :type subscriber: :class:`IdentityRef <notification.v4_1.models.IdentityRef>`
    :param url: REST API URL of the subscriotion.
    :type url: str
    :param user_settings: User-managed settings for the subscription. Only applies when the subscriber is a group. Typically used to indicate whether the calling user is opted in or out of a group subscription.
    :type user_settings: :class:`SubscriptionUserSettings <notification.v4_1.models.SubscriptionUserSettings>`
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'admin_settings': {'key': 'adminSettings', 'type': 'SubscriptionAdminSettings'},
        'channel': {'key': 'channel', 'type': 'ISubscriptionChannel'},
        'description': {'key': 'description', 'type': 'str'},
        'diagnostics': {'key': 'diagnostics', 'type': 'SubscriptionDiagnostics'},
        'extended_properties': {'key': 'extendedProperties', 'type': '{str}'},
        'filter': {'key': 'filter', 'type': 'ISubscriptionFilter'},
        'flags': {'key': 'flags', 'type': 'object'},
        'id': {'key': 'id', 'type': 'str'},
        'last_modified_by': {'key': 'lastModifiedBy', 'type': 'IdentityRef'},
        'modified_date': {'key': 'modifiedDate', 'type': 'iso-8601'},
        'permissions': {'key': 'permissions', 'type': 'object'},
        'scope': {'key': 'scope', 'type': 'SubscriptionScope'},
        'status': {'key': 'status', 'type': 'object'},
        'status_message': {'key': 'statusMessage', 'type': 'str'},
        'subscriber': {'key': 'subscriber', 'type': 'IdentityRef'},
        'url': {'key': 'url', 'type': 'str'},
        'user_settings': {'key': 'userSettings', 'type': 'SubscriptionUserSettings'}
    }

    def __init__(self, _links=None, admin_settings=None, channel=None, description=None, diagnostics=None, extended_properties=None, filter=None, flags=None, id=None, last_modified_by=None, modified_date=None, permissions=None, scope=None, status=None, status_message=None, subscriber=None, url=None, user_settings=None):
        super(NotificationSubscription, self).__init__()
        self._links = _links
        self.admin_settings = admin_settings
        self.channel = channel
        self.description = description
        self.diagnostics = diagnostics
        self.extended_properties = extended_properties
        self.filter = filter
        self.flags = flags
        self.id = id
        self.last_modified_by = last_modified_by
        self.modified_date = modified_date
        self.permissions = permissions
        self.scope = scope
        self.status = status
        self.status_message = status_message
        self.subscriber = subscriber
        self.url = url
        self.user_settings = user_settings
