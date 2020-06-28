# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class Rule(Model):
    """Rule.

    :param clauses:
    :type clauses: list of :class:`FilterClause <work.v4_0.models.FilterClause>`
    :param filter:
    :type filter: str
    :param is_enabled:
    :type is_enabled: str
    :param name:
    :type name: str
    :param settings:
    :type settings: dict
    """

    _attribute_map = {
        'clauses': {'key': 'clauses', 'type': '[FilterClause]'},
        'filter': {'key': 'filter', 'type': 'str'},
        'is_enabled': {'key': 'isEnabled', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'settings': {'key': 'settings', 'type': '{str}'}
    }

    def __init__(self, clauses=None, filter=None, is_enabled=None, name=None, settings=None):
        super(Rule, self).__init__()
        self.clauses = clauses
        self.filter = filter
        self.is_enabled = is_enabled
        self.name = name
        self.settings = settings
