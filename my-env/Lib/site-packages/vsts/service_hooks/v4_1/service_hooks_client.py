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


class ServiceHooksClient(VssClient):
    """ServiceHooks
    :param str base_url: Service URL
    :param Authentication creds: Authenticated credentials.
    """

    def __init__(self, base_url=None, creds=None):
        super(ServiceHooksClient, self).__init__(base_url, creds)
        client_models = {k: v for k, v in models.__dict__.items() if isinstance(v, type)}
        self._serialize = Serializer(client_models)
        self._deserialize = Deserializer(client_models)

    resource_area_identifier = None

    def get_consumer_action(self, consumer_id, consumer_action_id, publisher_id=None):
        """GetConsumerAction.
        Get details about a specific consumer action.
        :param str consumer_id: ID for a consumer.
        :param str consumer_action_id: ID for a consumerActionId.
        :param str publisher_id:
        :rtype: :class:`<ConsumerAction> <service-hooks.v4_1.models.ConsumerAction>`
        """
        route_values = {}
        if consumer_id is not None:
            route_values['consumerId'] = self._serialize.url('consumer_id', consumer_id, 'str')
        if consumer_action_id is not None:
            route_values['consumerActionId'] = self._serialize.url('consumer_action_id', consumer_action_id, 'str')
        query_parameters = {}
        if publisher_id is not None:
            query_parameters['publisherId'] = self._serialize.query('publisher_id', publisher_id, 'str')
        response = self._send(http_method='GET',
                              location_id='c3428e90-7a69-4194-8ed8-0f153185ee0d',
                              version='4.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('ConsumerAction', response)

    def list_consumer_actions(self, consumer_id, publisher_id=None):
        """ListConsumerActions.
        Get a list of consumer actions for a specific consumer.
        :param str consumer_id: ID for a consumer.
        :param str publisher_id:
        :rtype: [ConsumerAction]
        """
        route_values = {}
        if consumer_id is not None:
            route_values['consumerId'] = self._serialize.url('consumer_id', consumer_id, 'str')
        query_parameters = {}
        if publisher_id is not None:
            query_parameters['publisherId'] = self._serialize.query('publisher_id', publisher_id, 'str')
        response = self._send(http_method='GET',
                              location_id='c3428e90-7a69-4194-8ed8-0f153185ee0d',
                              version='4.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[ConsumerAction]', self._unwrap_collection(response))

    def get_consumer(self, consumer_id, publisher_id=None):
        """GetConsumer.
        Get a specific consumer service. Optionally filter out consumer actions that do not support any event types for the specified publisher.
        :param str consumer_id: ID for a consumer.
        :param str publisher_id:
        :rtype: :class:`<Consumer> <service-hooks.v4_1.models.Consumer>`
        """
        route_values = {}
        if consumer_id is not None:
            route_values['consumerId'] = self._serialize.url('consumer_id', consumer_id, 'str')
        query_parameters = {}
        if publisher_id is not None:
            query_parameters['publisherId'] = self._serialize.query('publisher_id', publisher_id, 'str')
        response = self._send(http_method='GET',
                              location_id='4301c514-5f34-4f5d-a145-f0ea7b5b7d19',
                              version='4.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('Consumer', response)

    def list_consumers(self, publisher_id=None):
        """ListConsumers.
        Get a list of available service hook consumer services. Optionally filter by consumers that support at least one event type from the specific publisher.
        :param str publisher_id:
        :rtype: [Consumer]
        """
        query_parameters = {}
        if publisher_id is not None:
            query_parameters['publisherId'] = self._serialize.query('publisher_id', publisher_id, 'str')
        response = self._send(http_method='GET',
                              location_id='4301c514-5f34-4f5d-a145-f0ea7b5b7d19',
                              version='4.1',
                              query_parameters=query_parameters)
        return self._deserialize('[Consumer]', self._unwrap_collection(response))

    def get_subscription_diagnostics(self, subscription_id):
        """GetSubscriptionDiagnostics.
        [Preview API]
        :param str subscription_id:
        :rtype: :class:`<SubscriptionDiagnostics> <service-hooks.v4_1.models.SubscriptionDiagnostics>`
        """
        route_values = {}
        if subscription_id is not None:
            route_values['subscriptionId'] = self._serialize.url('subscription_id', subscription_id, 'str')
        response = self._send(http_method='GET',
                              location_id='3b36bcb5-02ad-43c6-bbfa-6dfc6f8e9d68',
                              version='4.1-preview.1',
                              route_values=route_values)
        return self._deserialize('SubscriptionDiagnostics', response)

    def update_subscription_diagnostics(self, update_parameters, subscription_id):
        """UpdateSubscriptionDiagnostics.
        [Preview API]
        :param :class:`<UpdateSubscripitonDiagnosticsParameters> <service-hooks.v4_1.models.UpdateSubscripitonDiagnosticsParameters>` update_parameters:
        :param str subscription_id:
        :rtype: :class:`<SubscriptionDiagnostics> <service-hooks.v4_1.models.SubscriptionDiagnostics>`
        """
        route_values = {}
        if subscription_id is not None:
            route_values['subscriptionId'] = self._serialize.url('subscription_id', subscription_id, 'str')
        content = self._serialize.body(update_parameters, 'UpdateSubscripitonDiagnosticsParameters')
        response = self._send(http_method='PUT',
                              location_id='3b36bcb5-02ad-43c6-bbfa-6dfc6f8e9d68',
                              version='4.1-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('SubscriptionDiagnostics', response)

    def get_event_type(self, publisher_id, event_type_id):
        """GetEventType.
        Get a specific event type.
        :param str publisher_id: ID for a publisher.
        :param str event_type_id:
        :rtype: :class:`<EventTypeDescriptor> <service-hooks.v4_1.models.EventTypeDescriptor>`
        """
        route_values = {}
        if publisher_id is not None:
            route_values['publisherId'] = self._serialize.url('publisher_id', publisher_id, 'str')
        if event_type_id is not None:
            route_values['eventTypeId'] = self._serialize.url('event_type_id', event_type_id, 'str')
        response = self._send(http_method='GET',
                              location_id='db4777cd-8e08-4a84-8ba3-c974ea033718',
                              version='4.1',
                              route_values=route_values)
        return self._deserialize('EventTypeDescriptor', response)

    def list_event_types(self, publisher_id):
        """ListEventTypes.
        Get the event types for a specific publisher.
        :param str publisher_id: ID for a publisher.
        :rtype: [EventTypeDescriptor]
        """
        route_values = {}
        if publisher_id is not None:
            route_values['publisherId'] = self._serialize.url('publisher_id', publisher_id, 'str')
        response = self._send(http_method='GET',
                              location_id='db4777cd-8e08-4a84-8ba3-c974ea033718',
                              version='4.1',
                              route_values=route_values)
        return self._deserialize('[EventTypeDescriptor]', self._unwrap_collection(response))

    def get_notification(self, subscription_id, notification_id):
        """GetNotification.
        Get a specific notification for a subscription.
        :param str subscription_id: ID for a subscription.
        :param int notification_id:
        :rtype: :class:`<Notification> <service-hooks.v4_1.models.Notification>`
        """
        route_values = {}
        if subscription_id is not None:
            route_values['subscriptionId'] = self._serialize.url('subscription_id', subscription_id, 'str')
        if notification_id is not None:
            route_values['notificationId'] = self._serialize.url('notification_id', notification_id, 'int')
        response = self._send(http_method='GET',
                              location_id='0c62d343-21b0-4732-997b-017fde84dc28',
                              version='4.1',
                              route_values=route_values)
        return self._deserialize('Notification', response)

    def get_notifications(self, subscription_id, max_results=None, status=None, result=None):
        """GetNotifications.
        Get a list of notifications for a specific subscription. A notification includes details about the event, the request to and the response from the consumer service.
        :param str subscription_id: ID for a subscription.
        :param int max_results: Maximum number of notifications to return. Default is **100**.
        :param str status: Get only notifications with this status.
        :param str result: Get only notifications with this result type.
        :rtype: [Notification]
        """
        route_values = {}
        if subscription_id is not None:
            route_values['subscriptionId'] = self._serialize.url('subscription_id', subscription_id, 'str')
        query_parameters = {}
        if max_results is not None:
            query_parameters['maxResults'] = self._serialize.query('max_results', max_results, 'int')
        if status is not None:
            query_parameters['status'] = self._serialize.query('status', status, 'str')
        if result is not None:
            query_parameters['result'] = self._serialize.query('result', result, 'str')
        response = self._send(http_method='GET',
                              location_id='0c62d343-21b0-4732-997b-017fde84dc28',
                              version='4.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[Notification]', self._unwrap_collection(response))

    def query_notifications(self, query):
        """QueryNotifications.
        Query for notifications. A notification includes details about the event, the request to and the response from the consumer service.
        :param :class:`<NotificationsQuery> <service-hooks.v4_1.models.NotificationsQuery>` query:
        :rtype: :class:`<NotificationsQuery> <service-hooks.v4_1.models.NotificationsQuery>`
        """
        content = self._serialize.body(query, 'NotificationsQuery')
        response = self._send(http_method='POST',
                              location_id='1a57562f-160a-4b5c-9185-905e95b39d36',
                              version='4.1',
                              content=content)
        return self._deserialize('NotificationsQuery', response)

    def query_input_values(self, input_values_query, publisher_id):
        """QueryInputValues.
        :param :class:`<InputValuesQuery> <service-hooks.v4_1.models.InputValuesQuery>` input_values_query:
        :param str publisher_id:
        :rtype: :class:`<InputValuesQuery> <service-hooks.v4_1.models.InputValuesQuery>`
        """
        route_values = {}
        if publisher_id is not None:
            route_values['publisherId'] = self._serialize.url('publisher_id', publisher_id, 'str')
        content = self._serialize.body(input_values_query, 'InputValuesQuery')
        response = self._send(http_method='POST',
                              location_id='d815d352-a566-4dc1-a3e3-fd245acf688c',
                              version='4.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('InputValuesQuery', response)

    def get_publisher(self, publisher_id):
        """GetPublisher.
        Get a specific service hooks publisher.
        :param str publisher_id: ID for a publisher.
        :rtype: :class:`<Publisher> <service-hooks.v4_1.models.Publisher>`
        """
        route_values = {}
        if publisher_id is not None:
            route_values['publisherId'] = self._serialize.url('publisher_id', publisher_id, 'str')
        response = self._send(http_method='GET',
                              location_id='1e83a210-5b53-43bc-90f0-d476a4e5d731',
                              version='4.1',
                              route_values=route_values)
        return self._deserialize('Publisher', response)

    def list_publishers(self):
        """ListPublishers.
        Get a list of publishers.
        :rtype: [Publisher]
        """
        response = self._send(http_method='GET',
                              location_id='1e83a210-5b53-43bc-90f0-d476a4e5d731',
                              version='4.1')
        return self._deserialize('[Publisher]', self._unwrap_collection(response))

    def query_publishers(self, query):
        """QueryPublishers.
        Query for service hook publishers.
        :param :class:`<PublishersQuery> <service-hooks.v4_1.models.PublishersQuery>` query:
        :rtype: :class:`<PublishersQuery> <service-hooks.v4_1.models.PublishersQuery>`
        """
        content = self._serialize.body(query, 'PublishersQuery')
        response = self._send(http_method='POST',
                              location_id='99b44a8a-65a8-4670-8f3e-e7f7842cce64',
                              version='4.1',
                              content=content)
        return self._deserialize('PublishersQuery', response)

    def create_subscription(self, subscription):
        """CreateSubscription.
        Create a subscription.
        :param :class:`<Subscription> <service-hooks.v4_1.models.Subscription>` subscription: Subscription to be created.
        :rtype: :class:`<Subscription> <service-hooks.v4_1.models.Subscription>`
        """
        content = self._serialize.body(subscription, 'Subscription')
        response = self._send(http_method='POST',
                              location_id='fc50d02a-849f-41fb-8af1-0a5216103269',
                              version='4.1',
                              content=content)
        return self._deserialize('Subscription', response)

    def delete_subscription(self, subscription_id):
        """DeleteSubscription.
        Delete a specific service hooks subscription.
        :param str subscription_id: ID for a subscription.
        """
        route_values = {}
        if subscription_id is not None:
            route_values['subscriptionId'] = self._serialize.url('subscription_id', subscription_id, 'str')
        self._send(http_method='DELETE',
                   location_id='fc50d02a-849f-41fb-8af1-0a5216103269',
                   version='4.1',
                   route_values=route_values)

    def get_subscription(self, subscription_id):
        """GetSubscription.
        Get a specific service hooks subscription.
        :param str subscription_id: ID for a subscription.
        :rtype: :class:`<Subscription> <service-hooks.v4_1.models.Subscription>`
        """
        route_values = {}
        if subscription_id is not None:
            route_values['subscriptionId'] = self._serialize.url('subscription_id', subscription_id, 'str')
        response = self._send(http_method='GET',
                              location_id='fc50d02a-849f-41fb-8af1-0a5216103269',
                              version='4.1',
                              route_values=route_values)
        return self._deserialize('Subscription', response)

    def list_subscriptions(self, publisher_id=None, event_type=None, consumer_id=None, consumer_action_id=None):
        """ListSubscriptions.
        Get a list of subscriptions.
        :param str publisher_id: ID for a subscription.
        :param str event_type: Maximum number of notifications to return. Default is 100.
        :param str consumer_id: ID for a consumer.
        :param str consumer_action_id: ID for a consumerActionId.
        :rtype: [Subscription]
        """
        query_parameters = {}
        if publisher_id is not None:
            query_parameters['publisherId'] = self._serialize.query('publisher_id', publisher_id, 'str')
        if event_type is not None:
            query_parameters['eventType'] = self._serialize.query('event_type', event_type, 'str')
        if consumer_id is not None:
            query_parameters['consumerId'] = self._serialize.query('consumer_id', consumer_id, 'str')
        if consumer_action_id is not None:
            query_parameters['consumerActionId'] = self._serialize.query('consumer_action_id', consumer_action_id, 'str')
        response = self._send(http_method='GET',
                              location_id='fc50d02a-849f-41fb-8af1-0a5216103269',
                              version='4.1',
                              query_parameters=query_parameters)
        return self._deserialize('[Subscription]', self._unwrap_collection(response))

    def replace_subscription(self, subscription, subscription_id=None):
        """ReplaceSubscription.
        Update a subscription. <param name="subscriptionId">ID for a subscription that you wish to update.</param>
        :param :class:`<Subscription> <service-hooks.v4_1.models.Subscription>` subscription:
        :param str subscription_id:
        :rtype: :class:`<Subscription> <service-hooks.v4_1.models.Subscription>`
        """
        route_values = {}
        if subscription_id is not None:
            route_values['subscriptionId'] = self._serialize.url('subscription_id', subscription_id, 'str')
        content = self._serialize.body(subscription, 'Subscription')
        response = self._send(http_method='PUT',
                              location_id='fc50d02a-849f-41fb-8af1-0a5216103269',
                              version='4.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('Subscription', response)

    def create_subscriptions_query(self, query):
        """CreateSubscriptionsQuery.
        Query for service hook subscriptions.
        :param :class:`<SubscriptionsQuery> <service-hooks.v4_1.models.SubscriptionsQuery>` query:
        :rtype: :class:`<SubscriptionsQuery> <service-hooks.v4_1.models.SubscriptionsQuery>`
        """
        content = self._serialize.body(query, 'SubscriptionsQuery')
        response = self._send(http_method='POST',
                              location_id='c7c3c1cf-9e05-4c0d-a425-a0f922c2c6ed',
                              version='4.1',
                              content=content)
        return self._deserialize('SubscriptionsQuery', response)

    def create_test_notification(self, test_notification, use_real_data=None):
        """CreateTestNotification.
        Sends a test notification. This is useful for verifying the configuration of an updated or new service hooks subscription.
        :param :class:`<Notification> <service-hooks.v4_1.models.Notification>` test_notification:
        :param bool use_real_data: Only allow testing with real data in existing subscriptions.
        :rtype: :class:`<Notification> <service-hooks.v4_1.models.Notification>`
        """
        query_parameters = {}
        if use_real_data is not None:
            query_parameters['useRealData'] = self._serialize.query('use_real_data', use_real_data, 'bool')
        content = self._serialize.body(test_notification, 'Notification')
        response = self._send(http_method='POST',
                              location_id='1139462c-7e27-4524-a997-31b9b73551fe',
                              version='4.1',
                              query_parameters=query_parameters,
                              content=content)
        return self._deserialize('Notification', response)

