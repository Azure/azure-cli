# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class CategoryConfiguration(Model):
    """CategoryConfiguration.

    :param name: Name
    :type name: str
    :param reference_name: Category Reference Name
    :type reference_name: str
    :param work_item_types: Work item types for the backlog category
    :type work_item_types: list of :class:`WorkItemTypeReference <work.v4_0.models.WorkItemTypeReference>`
    """

    _attribute_map = {
        'name': {'key': 'name', 'type': 'str'},
        'reference_name': {'key': 'referenceName', 'type': 'str'},
        'work_item_types': {'key': 'workItemTypes', 'type': '[WorkItemTypeReference]'}
    }

    def __init__(self, name=None, reference_name=None, work_item_types=None):
        super(CategoryConfiguration, self).__init__()
        self.name = name
        self.reference_name = reference_name
        self.work_item_types = work_item_types
