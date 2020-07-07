# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class SubscriptionQuery(Model):
    """SubscriptionQuery.

    :param conditions: One or more conditions to query on. If more than 2 conditions are specified, the combined results of each condition is returned (i.e. conditions are logically OR'ed).
    :type conditions: list of :class:`SubscriptionQueryCondition <notification.v4_0.models.SubscriptionQueryCondition>`
    :param query_flags: Flags the refine the types of subscriptions that will be returned from the query.
    :type query_flags: object
    """

    _attribute_map = {
        'conditions': {'key': 'conditions', 'type': '[SubscriptionQueryCondition]'},
        'query_flags': {'key': 'queryFlags', 'type': 'object'}
    }

    def __init__(self, conditions=None, query_flags=None):
        super(SubscriptionQuery, self).__init__()
        self.conditions = conditions
        self.query_flags = query_flags
