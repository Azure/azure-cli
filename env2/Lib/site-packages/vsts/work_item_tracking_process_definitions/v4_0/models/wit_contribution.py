# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class WitContribution(Model):
    """WitContribution.

    :param contribution_id: The id for the contribution.
    :type contribution_id: str
    :param height: The height for the contribution.
    :type height: int
    :param inputs: A dictionary holding key value pairs for contribution inputs.
    :type inputs: dict
    :param show_on_deleted_work_item: A value indicating if the contribution should be show on deleted workItem.
    :type show_on_deleted_work_item: bool
    """

    _attribute_map = {
        'contribution_id': {'key': 'contributionId', 'type': 'str'},
        'height': {'key': 'height', 'type': 'int'},
        'inputs': {'key': 'inputs', 'type': '{object}'},
        'show_on_deleted_work_item': {'key': 'showOnDeletedWorkItem', 'type': 'bool'}
    }

    def __init__(self, contribution_id=None, height=None, inputs=None, show_on_deleted_work_item=None):
        super(WitContribution, self).__init__()
        self.contribution_id = contribution_id
        self.height = height
        self.inputs = inputs
        self.show_on_deleted_work_item = show_on_deleted_work_item
