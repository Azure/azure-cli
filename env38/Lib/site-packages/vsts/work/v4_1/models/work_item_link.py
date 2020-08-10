# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class WorkItemLink(Model):
    """WorkItemLink.

    :param rel: The type of link.
    :type rel: str
    :param source: The source work item.
    :type source: :class:`WorkItemReference <microsoft.-team-foundation.-work-item-tracking.-web-api.v4_1.models.WorkItemReference>`
    :param target: The target work item.
    :type target: :class:`WorkItemReference <microsoft.-team-foundation.-work-item-tracking.-web-api.v4_1.models.WorkItemReference>`
    """

    _attribute_map = {
        'rel': {'key': 'rel', 'type': 'str'},
        'source': {'key': 'source', 'type': 'WorkItemReference'},
        'target': {'key': 'target', 'type': 'WorkItemReference'}
    }

    def __init__(self, rel=None, source=None, target=None):
        super(WorkItemLink, self).__init__()
        self.rel = rel
        self.source = source
        self.target = target
