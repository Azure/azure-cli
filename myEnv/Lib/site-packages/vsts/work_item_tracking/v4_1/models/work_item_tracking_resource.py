# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .work_item_tracking_resource_reference import WorkItemTrackingResourceReference


class WorkItemTrackingResource(WorkItemTrackingResourceReference):
    """WorkItemTrackingResource.

    :param url:
    :type url: str
    :param _links: Link references to related REST resources.
    :type _links: :class:`ReferenceLinks <work-item-tracking.v4_1.models.ReferenceLinks>`
    """

    _attribute_map = {
        'url': {'key': 'url', 'type': 'str'},
        '_links': {'key': '_links', 'type': 'ReferenceLinks'}
    }

    def __init__(self, url=None, _links=None):
        super(WorkItemTrackingResource, self).__init__(url=url)
        self._links = _links
