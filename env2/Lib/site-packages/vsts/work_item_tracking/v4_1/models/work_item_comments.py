# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .work_item_tracking_resource import WorkItemTrackingResource


class WorkItemComments(WorkItemTrackingResource):
    """WorkItemComments.

    :param url:
    :type url: str
    :param _links: Link references to related REST resources.
    :type _links: :class:`ReferenceLinks <work-item-tracking.v4_1.models.ReferenceLinks>`
    :param comments: Comments collection.
    :type comments: list of :class:`WorkItemComment <work-item-tracking.v4_1.models.WorkItemComment>`
    :param count: The count of comments.
    :type count: int
    :param from_revision_count: Count of comments from the revision.
    :type from_revision_count: int
    :param total_count: Total count of comments.
    :type total_count: int
    """

    _attribute_map = {
        'url': {'key': 'url', 'type': 'str'},
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'comments': {'key': 'comments', 'type': '[WorkItemComment]'},
        'count': {'key': 'count', 'type': 'int'},
        'from_revision_count': {'key': 'fromRevisionCount', 'type': 'int'},
        'total_count': {'key': 'totalCount', 'type': 'int'}
    }

    def __init__(self, url=None, _links=None, comments=None, count=None, from_revision_count=None, total_count=None):
        super(WorkItemComments, self).__init__(url=url, _links=_links)
        self.comments = comments
        self.count = count
        self.from_revision_count = from_revision_count
        self.total_count = total_count
