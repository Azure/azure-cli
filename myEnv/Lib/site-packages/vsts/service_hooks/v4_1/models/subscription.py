# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class Subscription(Model):
    """Subscription.

    :param _links: Reference Links
    :type _links: :class:`ReferenceLinks <service-hooks.v4_1.models.ReferenceLinks>`
    :param action_description:
    :type action_description: str
    :param consumer_action_id:
    :type consumer_action_id: str
    :param consumer_id:
    :type consumer_id: str
    :param consumer_inputs: Consumer input values
    :type consumer_inputs: dict
    :param created_by:
    :type created_by: :class:`IdentityRef <service-hooks.v4_1.models.IdentityRef>`
    :param created_date:
    :type created_date: datetime
    :param event_description:
    :type event_description: str
    :param event_type:
    :type event_type: str
    :param id:
    :type id: str
    :param modified_by:
    :type modified_by: :class:`IdentityRef <service-hooks.v4_1.models.IdentityRef>`
    :param modified_date:
    :type modified_date: datetime
    :param probation_retries:
    :type probation_retries: str
    :param publisher_id:
    :type publisher_id: str
    :param publisher_inputs: Publisher input values
    :type publisher_inputs: dict
    :param resource_version:
    :type resource_version: str
    :param status:
    :type status: object
    :param subscriber:
    :type subscriber: :class:`IdentityRef <service-hooks.v4_1.models.IdentityRef>`
    :param url:
    :type url: str
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'action_description': {'key': 'actionDescription', 'type': 'str'},
        'consumer_action_id': {'key': 'consumerActionId', 'type': 'str'},
        'consumer_id': {'key': 'consumerId', 'type': 'str'},
        'consumer_inputs': {'key': 'consumerInputs', 'type': '{str}'},
        'created_by': {'key': 'createdBy', 'type': 'IdentityRef'},
        'created_date': {'key': 'createdDate', 'type': 'iso-8601'},
        'event_description': {'key': 'eventDescription', 'type': 'str'},
        'event_type': {'key': 'eventType', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'modified_by': {'key': 'modifiedBy', 'type': 'IdentityRef'},
        'modified_date': {'key': 'modifiedDate', 'type': 'iso-8601'},
        'probation_retries': {'key': 'probationRetries', 'type': 'str'},
        'publisher_id': {'key': 'publisherId', 'type': 'str'},
        'publisher_inputs': {'key': 'publisherInputs', 'type': '{str}'},
        'resource_version': {'key': 'resourceVersion', 'type': 'str'},
        'status': {'key': 'status', 'type': 'object'},
        'subscriber': {'key': 'subscriber', 'type': 'IdentityRef'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, _links=None, action_description=None, consumer_action_id=None, consumer_id=None, consumer_inputs=None, created_by=None, created_date=None, event_description=None, event_type=None, id=None, modified_by=None, modified_date=None, probation_retries=None, publisher_id=None, publisher_inputs=None, resource_version=None, status=None, subscriber=None, url=None):
        super(Subscription, self).__init__()
        self._links = _links
        self.action_description = action_description
        self.consumer_action_id = consumer_action_id
        self.consumer_id = consumer_id
        self.consumer_inputs = consumer_inputs
        self.created_by = created_by
        self.created_date = created_date
        self.event_description = event_description
        self.event_type = event_type
        self.id = id
        self.modified_by = modified_by
        self.modified_date = modified_date
        self.probation_retries = probation_retries
        self.publisher_id = publisher_id
        self.publisher_inputs = publisher_inputs
        self.resource_version = resource_version
        self.status = status
        self.subscriber = subscriber
        self.url = url
