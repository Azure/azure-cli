# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class WorkItemStateTransition(Model):
    """WorkItemStateTransition.

    :param actions:
    :type actions: list of str
    :param to:
    :type to: str
    """

    _attribute_map = {
        'actions': {'key': 'actions', 'type': '[str]'},
        'to': {'key': 'to', 'type': 'str'}
    }

    def __init__(self, actions=None, to=None):
        super(WorkItemStateTransition, self).__init__()
        self.actions = actions
        self.to = to
