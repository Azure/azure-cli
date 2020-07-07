# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .work_item_tracking_reference import WorkItemTrackingReference


class WorkItemRelationType(WorkItemTrackingReference):
    """WorkItemRelationType.

    :param url:
    :type url: str
    :param _links:
    :type _links: :class:`ReferenceLinks <work-item-tracking.v4_0.models.ReferenceLinks>`
    :param name:
    :type name: str
    :param reference_name:
    :type reference_name: str
    :param attributes:
    :type attributes: dict
    """

    _attribute_map = {
        'url': {'key': 'url', 'type': 'str'},
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'name': {'key': 'name', 'type': 'str'},
        'reference_name': {'key': 'referenceName', 'type': 'str'},
        'attributes': {'key': 'attributes', 'type': '{object}'}
    }

    def __init__(self, url=None, _links=None, name=None, reference_name=None, attributes=None):
        super(WorkItemRelationType, self).__init__(url=url, _links=_links, name=name, reference_name=reference_name)
        self.attributes = attributes
