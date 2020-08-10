# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ReportingWorkItemLink(Model):
    """ReportingWorkItemLink.

    :param changed_by:
    :type changed_by: :class:`IdentityRef <work-item-tracking.v4_0.models.IdentityRef>`
    :param changed_date:
    :type changed_date: datetime
    :param changed_operation:
    :type changed_operation: object
    :param comment:
    :type comment: str
    :param is_active:
    :type is_active: bool
    :param link_type:
    :type link_type: str
    :param rel:
    :type rel: str
    :param source_id:
    :type source_id: int
    :param target_id:
    :type target_id: int
    """

    _attribute_map = {
        'changed_by': {'key': 'changedBy', 'type': 'IdentityRef'},
        'changed_date': {'key': 'changedDate', 'type': 'iso-8601'},
        'changed_operation': {'key': 'changedOperation', 'type': 'object'},
        'comment': {'key': 'comment', 'type': 'str'},
        'is_active': {'key': 'isActive', 'type': 'bool'},
        'link_type': {'key': 'linkType', 'type': 'str'},
        'rel': {'key': 'rel', 'type': 'str'},
        'source_id': {'key': 'sourceId', 'type': 'int'},
        'target_id': {'key': 'targetId', 'type': 'int'}
    }

    def __init__(self, changed_by=None, changed_date=None, changed_operation=None, comment=None, is_active=None, link_type=None, rel=None, source_id=None, target_id=None):
        super(ReportingWorkItemLink, self).__init__()
        self.changed_by = changed_by
        self.changed_date = changed_date
        self.changed_operation = changed_operation
        self.comment = comment
        self.is_active = is_active
        self.link_type = link_type
        self.rel = rel
        self.source_id = source_id
        self.target_id = target_id
