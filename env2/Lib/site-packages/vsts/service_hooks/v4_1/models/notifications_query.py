# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class NotificationsQuery(Model):
    """NotificationsQuery.

    :param associated_subscriptions: The subscriptions associated with the notifications returned from the query
    :type associated_subscriptions: list of :class:`Subscription <service-hooks.v4_1.models.Subscription>`
    :param include_details: If true, we will return all notification history for the query provided; otherwise, the summary is returned.
    :type include_details: bool
    :param max_created_date: Optional maximum date at which the notification was created
    :type max_created_date: datetime
    :param max_results: Optional maximum number of overall results to include
    :type max_results: int
    :param max_results_per_subscription: Optional maximum number of results for each subscription. Only takes effect when a list of subscription ids is supplied in the query.
    :type max_results_per_subscription: int
    :param min_created_date: Optional minimum date at which the notification was created
    :type min_created_date: datetime
    :param publisher_id: Optional publisher id to restrict the results to
    :type publisher_id: str
    :param results: Results from the query
    :type results: list of :class:`Notification <service-hooks.v4_1.models.Notification>`
    :param result_type: Optional notification result type to filter results to
    :type result_type: object
    :param status: Optional notification status to filter results to
    :type status: object
    :param subscription_ids: Optional list of subscription ids to restrict the results to
    :type subscription_ids: list of str
    :param summary: Summary of notifications - the count of each result type (success, fail, ..).
    :type summary: list of :class:`NotificationSummary <service-hooks.v4_1.models.NotificationSummary>`
    """

    _attribute_map = {
        'associated_subscriptions': {'key': 'associatedSubscriptions', 'type': '[Subscription]'},
        'include_details': {'key': 'includeDetails', 'type': 'bool'},
        'max_created_date': {'key': 'maxCreatedDate', 'type': 'iso-8601'},
        'max_results': {'key': 'maxResults', 'type': 'int'},
        'max_results_per_subscription': {'key': 'maxResultsPerSubscription', 'type': 'int'},
        'min_created_date': {'key': 'minCreatedDate', 'type': 'iso-8601'},
        'publisher_id': {'key': 'publisherId', 'type': 'str'},
        'results': {'key': 'results', 'type': '[Notification]'},
        'result_type': {'key': 'resultType', 'type': 'object'},
        'status': {'key': 'status', 'type': 'object'},
        'subscription_ids': {'key': 'subscriptionIds', 'type': '[str]'},
        'summary': {'key': 'summary', 'type': '[NotificationSummary]'}
    }

    def __init__(self, associated_subscriptions=None, include_details=None, max_created_date=None, max_results=None, max_results_per_subscription=None, min_created_date=None, publisher_id=None, results=None, result_type=None, status=None, subscription_ids=None, summary=None):
        super(NotificationsQuery, self).__init__()
        self.associated_subscriptions = associated_subscriptions
        self.include_details = include_details
        self.max_created_date = max_created_date
        self.max_results = max_results
        self.max_results_per_subscription = max_results_per_subscription
        self.min_created_date = min_created_date
        self.publisher_id = publisher_id
        self.results = results
        self.result_type = result_type
        self.status = status
        self.subscription_ids = subscription_ids
        self.summary = summary
