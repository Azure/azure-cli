# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class CloneOperationInformation(Model):
    """CloneOperationInformation.

    :param clone_statistics:
    :type clone_statistics: :class:`CloneStatistics <test.v4_1.models.CloneStatistics>`
    :param completion_date: If the operation is complete, the DateTime of completion. If operation is not complete, this is DateTime.MaxValue
    :type completion_date: datetime
    :param creation_date: DateTime when the operation was started
    :type creation_date: datetime
    :param destination_object: Shallow reference of the destination
    :type destination_object: :class:`ShallowReference <test.v4_1.models.ShallowReference>`
    :param destination_plan: Shallow reference of the destination
    :type destination_plan: :class:`ShallowReference <test.v4_1.models.ShallowReference>`
    :param destination_project: Shallow reference of the destination
    :type destination_project: :class:`ShallowReference <test.v4_1.models.ShallowReference>`
    :param message: If the operation has Failed, Message contains the reason for failure. Null otherwise.
    :type message: str
    :param op_id: The ID of the operation
    :type op_id: int
    :param result_object_type: The type of the object generated as a result of the Clone operation
    :type result_object_type: object
    :param source_object: Shallow reference of the source
    :type source_object: :class:`ShallowReference <test.v4_1.models.ShallowReference>`
    :param source_plan: Shallow reference of the source
    :type source_plan: :class:`ShallowReference <test.v4_1.models.ShallowReference>`
    :param source_project: Shallow reference of the source
    :type source_project: :class:`ShallowReference <test.v4_1.models.ShallowReference>`
    :param state: Current state of the operation. When State reaches Suceeded or Failed, the operation is complete
    :type state: object
    :param url: Url for geting the clone information
    :type url: str
    """

    _attribute_map = {
        'clone_statistics': {'key': 'cloneStatistics', 'type': 'CloneStatistics'},
        'completion_date': {'key': 'completionDate', 'type': 'iso-8601'},
        'creation_date': {'key': 'creationDate', 'type': 'iso-8601'},
        'destination_object': {'key': 'destinationObject', 'type': 'ShallowReference'},
        'destination_plan': {'key': 'destinationPlan', 'type': 'ShallowReference'},
        'destination_project': {'key': 'destinationProject', 'type': 'ShallowReference'},
        'message': {'key': 'message', 'type': 'str'},
        'op_id': {'key': 'opId', 'type': 'int'},
        'result_object_type': {'key': 'resultObjectType', 'type': 'object'},
        'source_object': {'key': 'sourceObject', 'type': 'ShallowReference'},
        'source_plan': {'key': 'sourcePlan', 'type': 'ShallowReference'},
        'source_project': {'key': 'sourceProject', 'type': 'ShallowReference'},
        'state': {'key': 'state', 'type': 'object'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, clone_statistics=None, completion_date=None, creation_date=None, destination_object=None, destination_plan=None, destination_project=None, message=None, op_id=None, result_object_type=None, source_object=None, source_plan=None, source_project=None, state=None, url=None):
        super(CloneOperationInformation, self).__init__()
        self.clone_statistics = clone_statistics
        self.completion_date = completion_date
        self.creation_date = creation_date
        self.destination_object = destination_object
        self.destination_plan = destination_plan
        self.destination_project = destination_project
        self.message = message
        self.op_id = op_id
        self.result_object_type = result_object_type
        self.source_object = source_object
        self.source_plan = source_plan
        self.source_project = source_project
        self.state = state
        self.url = url
