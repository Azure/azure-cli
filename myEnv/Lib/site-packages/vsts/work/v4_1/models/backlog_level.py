# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class BacklogLevel(Model):
    """BacklogLevel.

    :param category_reference_name: Reference name of the corresponding WIT category
    :type category_reference_name: str
    :param plural_name: Plural name for the backlog level
    :type plural_name: str
    :param work_item_states: Collection of work item states that are included in the plan. The server will filter to only these work item types.
    :type work_item_states: list of str
    :param work_item_types: Collection of valid workitem type names for the given backlog level
    :type work_item_types: list of str
    """

    _attribute_map = {
        'category_reference_name': {'key': 'categoryReferenceName', 'type': 'str'},
        'plural_name': {'key': 'pluralName', 'type': 'str'},
        'work_item_states': {'key': 'workItemStates', 'type': '[str]'},
        'work_item_types': {'key': 'workItemTypes', 'type': '[str]'}
    }

    def __init__(self, category_reference_name=None, plural_name=None, work_item_states=None, work_item_types=None):
        super(BacklogLevel, self).__init__()
        self.category_reference_name = category_reference_name
        self.plural_name = plural_name
        self.work_item_states = work_item_states
        self.work_item_types = work_item_types
