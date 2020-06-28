# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ExtensionAssignmentDetails(Model):
    """ExtensionAssignmentDetails.

    :param assignment_status:
    :type assignment_status: object
    :param source_collection_name:
    :type source_collection_name: str
    """

    _attribute_map = {
        'assignment_status': {'key': 'assignmentStatus', 'type': 'object'},
        'source_collection_name': {'key': 'sourceCollectionName', 'type': 'str'}
    }

    def __init__(self, assignment_status=None, source_collection_name=None):
        super(ExtensionAssignmentDetails, self).__init__()
        self.assignment_status = assignment_status
        self.source_collection_name = source_collection_name
