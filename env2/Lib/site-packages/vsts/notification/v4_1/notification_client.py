# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest import Serializer, Deserializer
from ...vss_client import VssClient
from . import models


class NotificationClient(VssClient):
    """Notification
    :param str base_url: Service URL
    :param Authentication creds: Authenticated credentials.
    """

    def __init__(self, base_url=None, creds=None):
        super(NotificationClient, self).__init__(base_url, creds)
        client_models = {k: v for k, v in models.__dict__.items() if isinstance(v, type)}
        self._serialize = Serializer(client_models)
        self._deserialize = Deserializer(client_models)

    resource_area_identifier = None

    def list_logs(self, source, entry_id=None, start_time=None, end_time=None):
        """ListLogs.
        [Preview API] List diagnostic logs this service.
        :param str source:
        :param str entry_id:
        :param datetime start_time:
        :param datetime end_time:
        :rtype: [INotificationDiagnosticLog]
        """
        route_values = {}
        if source is not None:
            route_values['source'] = self._serialize.url('source', source, 'str')
        if entry_id is not None:
            route_values['entryId'] = self._serialize.url('entry_id', entry_id, 'str')
        query_parameters = {}
        if start_time is not None:
            query_parameters['startTime'] = self._serialize.query('start_time', start_time, 'iso-8601')
        if end_time is not None:
            query_parameters['endTime'] = self._serialize.query('end_time', end_time, 'iso-8601')
        response = self._send(http_method='GET',
                              location_id='991842f3-eb16-4aea-ac81-81353ef2b75c',
                              version='4.1-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[INotificationDiagnosticLog]', self._unwrap_collection(response))

    def get_subscription_diagnostics(self, subscription_id):
        """GetSubscriptionDiagnostics.
        [Preview API]
        :param str subscription_id:
        :rtype: :class:`<SubscriptionDiagnostics> <notification.v4_1.models.SubscriptionDiagnostics>`
        """
        route_values = {}
        if subscription_id is not None:
            route_values['subscriptionId'] = self._serialize.url('subscription_id', subscription_id, 'str')
        response = self._send(http_method='GET',
                              location_id='20f1929d-4be7-4c2e-a74e-d47640ff3418',
                              version='4.1-preview.1',
                              route_values=route_values)
        return self._deserialize('SubscriptionDiagnostics', response)

    def update_subscription_diagnostics(self, update_parameters, subscription_id):
        """UpdateSubscriptionDiagnostics.
        [Preview API]
        :param :class:`<UpdateSubscripitonDiagnosticsParameters> <notification.v4_1.models.UpdateSubscripitonDiagnosticsParameters>` update_parameters:
        :param str subscription_id:
        :rtype: :class:`<SubscriptionDiagnostics> <notification.v4_1.models.SubscriptionDiagnostics>`
        """
        route_values = {}
        if subscription_id is not None:
            route_values['subscriptionId'] = self._serialize.url('subscription_id', subscription_id, 'str')
        content = self._serialize.body(update_parameters, 'UpdateSubscripitonDiagnosticsParameters')
        response = self._send(http_method='PUT',
                              location_id='20f1929d-4be7-4c2e-a74e-d47640ff3418',
                              version='4.1-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('SubscriptionDiagnostics', response)

    def publish_event(self, notification_event):
        """PublishEvent.
        [Preview API] Publish an event.
        :param :class:`<VssNotificationEvent> <notification.v4_1.models.VssNotificationEvent>` notification_event:
        :rtype: :class:`<VssNotificationEvent> <notification.v4_1.models.VssNotificationEvent>`
        """
        content = self._serialize.body(notification_event, 'VssNotificationEvent')
        response = self._send(http_method='POST',
                              location_id='14c57b7a-c0e6-4555-9f51-e067188fdd8e',
                              version='4.1-preview.1',
                              content=content)
        return self._deserialize('VssNotificationEvent', response)

    def get_event_type(self, event_type):
        """GetEventType.
        [Preview API] Get a specific event type.
        :param str event_type:
        :rtype: :class:`<NotificationEventType> <notification.v4_1.models.NotificationEventType>`
        """
        route_values = {}
        if event_type is not None:
            route_values['eventType'] = self._serialize.url('event_type', event_type, 'str')
        response = self._send(http_method='GET',
                              location_id='cc84fb5f-6247-4c7a-aeae-e5a3c3fddb21',
                              version='4.1-preview.1',
                              route_values=route_values)
        return self._deserialize('NotificationEventType', response)

    def list_event_types(self, publisher_id=None):
        """ListEventTypes.
        [Preview API] List available event types for this service. Optionally filter by only event types for the specified publisher.
        :param str publisher_id: Limit to event types for this publisher
        :rtype: [NotificationEventType]
        """
        query_parameters = {}
        if publisher_id is not None:
            query_parameters['publisherId'] = self._serialize.query('publisher_id', publisher_id, 'str')
        response = self._send(http_method='GET',
                              location_id='cc84fb5f-6247-4c7a-aeae-e5a3c3fddb21',
                              version='4.1-preview.1',
                              query_parameters=query_parameters)
        return self._deserialize('[NotificationEventType]', self._unwrap_collection(response))

    def get_subscriber(self, subscriber_id):
        """GetSubscriber.
        [Preview API]
        :param str subscriber_id:
        :rtype: :class:`<NotificationSubscriber> <notification.v4_1.models.NotificationSubscriber>`
        """
        route_values = {}
        if subscriber_id is not None:
            route_values['subscriberId'] = self._serialize.url('subscriber_id', subscriber_id, 'str')
        response = self._send(http_method='GET',
                              location_id='4d5caff1-25ba-430b-b808-7a1f352cc197',
                              version='4.1-preview.1',
                              route_values=route_values)
        return self._deserialize('NotificationSubscriber', response)

    def update_subscriber(self, update_parameters, subscriber_id):
        """UpdateSubscriber.
        [Preview API]
        :param :class:`<NotificationSubscriberUpdateParameters> <notification.v4_1.models.NotificationSubscriberUpdateParameters>` update_parameters:
        :param str subscriber_id:
        :rtype: :class:`<NotificationSubscriber> <notification.v4_1.models.NotificationSubscriber>`
        """
        route_values = {}
        if subscriber_id is not None:
            route_values['subscriberId'] = self._serialize.url('subscriber_id', subscriber_id, 'str')
        content = self._serialize.body(update_parameters, 'NotificationSubscriberUpdateParameters')
        response = self._send(http_method='PATCH',
                              location_id='4d5caff1-25ba-430b-b808-7a1f352cc197',
                              version='4.1-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('NotificationSubscriber', response)

    def query_subscriptions(self, subscription_query):
        """QuerySubscriptions.
        [Preview API] Query for subscriptions. A subscription is returned if it matches one or more of the specified conditions.
        :param :class:`<SubscriptionQuery> <notification.v4_1.models.SubscriptionQuery>` subscription_query:
        :rtype: [NotificationSubscription]
        """
        content = self._serialize.body(subscription_query, 'SubscriptionQuery')
        response = self._send(http_method='POST',
                              location_id='6864db85-08c0-4006-8e8e-cc1bebe31675',
                              version='4.1-preview.1',
                              content=content)
        return self._deserialize('[NotificationSubscription]', self._unwrap_collection(response))

    def create_subscription(self, create_parameters):
        """CreateSubscription.
        [Preview API] Create a new subscription.
        :param :class:`<NotificationSubscriptionCreateParameters> <notification.v4_1.models.NotificationSubscriptionCreateParameters>` create_parameters:
        :rtype: :class:`<NotificationSubscription> <notification.v4_1.models.NotificationSubscription>`
        """
        content = self._serialize.body(create_parameters, 'NotificationSubscriptionCreateParameters')
        response = self._send(http_method='POST',
                              location_id='70f911d6-abac-488c-85b3-a206bf57e165',
                              version='4.1-preview.1',
                              content=content)
        return self._deserialize('NotificationSubscription', response)

    def delete_subscription(self, subscription_id):
        """DeleteSubscription.
        [Preview API] Delete a subscription.
        :param str subscription_id:
        """
        route_values = {}
        if subscription_id is not None:
            route_values['subscriptionId'] = self._serialize.url('subscription_id', subscription_id, 'str')
        self._send(http_method='DELETE',
                   location_id='70f911d6-abac-488c-85b3-a206bf57e165',
                   version='4.1-preview.1',
                   route_values=route_values)

    def get_subscription(self, subscription_id, query_flags=None):
        """GetSubscription.
        [Preview API] Get a notification subscription by its ID.
        :param str subscription_id:
        :param str query_flags:
        :rtype: :class:`<NotificationSubscription> <notification.v4_1.models.NotificationSubscription>`
        """
        route_values = {}
        if subscription_id is not None:
            route_values['subscriptionId'] = self._serialize.url('subscription_id', subscription_id, 'str')
        query_parameters = {}
        if query_flags is not None:
            query_parameters['queryFlags'] = self._serialize.query('query_flags', query_flags, 'str')
        response = self._send(http_method='GET',
                              location_id='70f911d6-abac-488c-85b3-a206bf57e165',
                              version='4.1-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('NotificationSubscription', response)

    def list_subscriptions(self, target_id=None, ids=None, query_flags=None):
        """ListSubscriptions.
        [Preview API]
        :param str target_id:
        :param [str] ids:
        :param str query_flags:
        :rtype: [NotificationSubscription]
        """
        query_parameters = {}
        if target_id is not None:
            query_parameters['targetId'] = self._serialize.query('target_id', target_id, 'str')
        if ids is not None:
            ids = ",".join(ids)
            query_parameters['ids'] = self._serialize.query('ids', ids, 'str')
        if query_flags is not None:
            query_parameters['queryFlags'] = self._serialize.query('query_flags', query_flags, 'str')
        response = self._send(http_method='GET',
                              location_id='70f911d6-abac-488c-85b3-a206bf57e165',
                              version='4.1-preview.1',
                              query_parameters=query_parameters)
        return self._deserialize('[NotificationSubscription]', self._unwrap_collection(response))

    def update_subscription(self, update_parameters, subscription_id):
        """UpdateSubscription.
        [Preview API] Update an existing subscription. Depending on the type of subscription and permissions, the caller can update the description, filter settings, channel (delivery) settings and more.
        :param :class:`<NotificationSubscriptionUpdateParameters> <notification.v4_1.models.NotificationSubscriptionUpdateParameters>` update_parameters:
        :param str subscription_id:
        :rtype: :class:`<NotificationSubscription> <notification.v4_1.models.NotificationSubscription>`
        """
        route_values = {}
        if subscription_id is not None:
            route_values['subscriptionId'] = self._serialize.url('subscription_id', subscription_id, 'str')
        content = self._serialize.body(update_parameters, 'NotificationSubscriptionUpdateParameters')
        response = self._send(http_method='PATCH',
                              location_id='70f911d6-abac-488c-85b3-a206bf57e165',
                              version='4.1-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('NotificationSubscription', response)

    def get_subscription_templates(self):
        """GetSubscriptionTemplates.
        [Preview API] Get available subscription templates.
        :rtype: [NotificationSubscriptionTemplate]
        """
        response = self._send(http_method='GET',
                              location_id='fa5d24ba-7484-4f3d-888d-4ec6b1974082',
                              version='4.1-preview.1')
        return self._deserialize('[NotificationSubscriptionTemplate]', self._unwrap_collection(response))

    def update_subscription_user_settings(self, user_settings, subscription_id, user_id):
        """UpdateSubscriptionUserSettings.
        [Preview API] Update the specified user's settings for the specified subscription. This API is typically used to opt in or out of a shared subscription. User settings can only be applied to shared subscriptions, like team subscriptions or default subscriptions.
        :param :class:`<SubscriptionUserSettings> <notification.v4_1.models.SubscriptionUserSettings>` user_settings:
        :param str subscription_id:
        :param str user_id: ID of the user
        :rtype: :class:`<SubscriptionUserSettings> <notification.v4_1.models.SubscriptionUserSettings>`
        """
        route_values = {}
        if subscription_id is not None:
            route_values['subscriptionId'] = self._serialize.url('subscription_id', subscription_id, 'str')
        if user_id is not None:
            route_values['userId'] = self._serialize.url('user_id', user_id, 'str')
        content = self._serialize.body(user_settings, 'SubscriptionUserSettings')
        response = self._send(http_method='PUT',
                              location_id='ed5a3dff-aeb5-41b1-b4f7-89e66e58b62e',
                              version='4.1-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('SubscriptionUserSettings', response)

