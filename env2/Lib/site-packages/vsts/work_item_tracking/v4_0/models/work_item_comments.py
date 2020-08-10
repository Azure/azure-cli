# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class WorkItemComments(Model):
    """WorkItemComments.

    :param comments:
    :type comments: list of :class:`WorkItemComment <work-item-tracking.v4_0.models.WorkItemComment>`
    :param count:
    :type count: int
    :param from_revision_count:
    :type from_revision_count: int
    :param total_count:
    :type total_count: int
    """

    _attribute_map = {
        'comments': {'key': 'comments', 'type': '[WorkItemComment]'},
        'count': {'key': 'count', 'type': 'int'},
        'from_revision_count': {'key': 'fromRevisionCount', 'type': 'int'},
        'total_count': {'key': 'totalCount', 'type': 'int'}
    }

    def __init__(self, comments=None, count=None, from_revision_count=None, total_count=None):
        super(WorkItemComments, self).__init__()
        self.comments = comments
        self.count = count
        self.from_revision_count = from_revision_count
        self.total_count = total_count
