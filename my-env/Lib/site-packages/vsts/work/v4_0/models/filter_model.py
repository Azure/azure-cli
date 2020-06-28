# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class FilterModel(Model):
    """FilterModel.

    :param clauses:
    :type clauses: list of :class:`FilterClause <work.v4_0.models.FilterClause>`
    :param groups:
    :type groups: list of :class:`FilterGroup <work.v4_0.models.FilterGroup>`
    :param max_group_level:
    :type max_group_level: int
    """

    _attribute_map = {
        'clauses': {'key': 'clauses', 'type': '[FilterClause]'},
        'groups': {'key': 'groups', 'type': '[FilterGroup]'},
        'max_group_level': {'key': 'maxGroupLevel', 'type': 'int'}
    }

    def __init__(self, clauses=None, groups=None, max_group_level=None):
        super(FilterModel, self).__init__()
        self.clauses = clauses
        self.groups = groups
        self.max_group_level = max_group_level
