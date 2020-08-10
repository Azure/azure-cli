# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ExpressionFilterModel(Model):
    """ExpressionFilterModel.

    :param clauses: Flat list of clauses in this subscription
    :type clauses: list of :class:`ExpressionFilterClause <notification.v4_1.models.ExpressionFilterClause>`
    :param groups: Grouping of clauses in the subscription
    :type groups: list of :class:`ExpressionFilterGroup <notification.v4_1.models.ExpressionFilterGroup>`
    :param max_group_level: Max depth of the Subscription tree
    :type max_group_level: int
    """

    _attribute_map = {
        'clauses': {'key': 'clauses', 'type': '[ExpressionFilterClause]'},
        'groups': {'key': 'groups', 'type': '[ExpressionFilterGroup]'},
        'max_group_level': {'key': 'maxGroupLevel', 'type': 'int'}
    }

    def __init__(self, clauses=None, groups=None, max_group_level=None):
        super(ExpressionFilterModel, self).__init__()
        self.clauses = clauses
        self.groups = groups
        self.max_group_level = max_group_level
