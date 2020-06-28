# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ManualInterventionUpdateMetadata(Model):
    """ManualInterventionUpdateMetadata.

    :param comment: Sets the comment for manual intervention update.
    :type comment: str
    :param status: Sets the status of the manual intervention.
    :type status: object
    """

    _attribute_map = {
        'comment': {'key': 'comment', 'type': 'str'},
        'status': {'key': 'status', 'type': 'object'}
    }

    def __init__(self, comment=None, status=None):
        super(ManualInterventionUpdateMetadata, self).__init__()
        self.comment = comment
        self.status = status
