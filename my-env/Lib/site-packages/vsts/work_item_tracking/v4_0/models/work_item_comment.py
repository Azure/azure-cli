# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .work_item_tracking_resource import WorkItemTrackingResource


class WorkItemComment(WorkItemTrackingResource):
    """WorkItemComment.

    :param url:
    :type url: str
    :param _links:
    :type _links: :class:`ReferenceLinks <work-item-tracking.v4_0.models.ReferenceLinks>`
    :param revised_by:
    :type revised_by: :class:`IdentityReference <work-item-tracking.v4_0.models.IdentityReference>`
    :param revised_date:
    :type revised_date: datetime
    :param revision:
    :type revision: int
    :param text:
    :type text: str
    """

    _attribute_map = {
        'url': {'key': 'url', 'type': 'str'},
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'revised_by': {'key': 'revisedBy', 'type': 'IdentityReference'},
        'revised_date': {'key': 'revisedDate', 'type': 'iso-8601'},
        'revision': {'key': 'revision', 'type': 'int'},
        'text': {'key': 'text', 'type': 'str'}
    }

    def __init__(self, url=None, _links=None, revised_by=None, revised_date=None, revision=None, text=None):
        super(WorkItemComment, self).__init__(url=url, _links=_links)
        self.revised_by = revised_by
        self.revised_date = revised_date
        self.revision = revision
        self.text = text
