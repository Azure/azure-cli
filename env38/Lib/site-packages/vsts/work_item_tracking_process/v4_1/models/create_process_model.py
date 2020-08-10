# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class CreateProcessModel(Model):
    """CreateProcessModel.

    :param description: Description of the process
    :type description: str
    :param name: Name of the process
    :type name: str
    :param parent_process_type_id: The ID of the parent process
    :type parent_process_type_id: str
    :param reference_name: Reference name of the process
    :type reference_name: str
    """

    _attribute_map = {
        'description': {'key': 'description', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'parent_process_type_id': {'key': 'parentProcessTypeId', 'type': 'str'},
        'reference_name': {'key': 'referenceName', 'type': 'str'}
    }

    def __init__(self, description=None, name=None, parent_process_type_id=None, reference_name=None):
        super(CreateProcessModel, self).__init__()
        self.description = description
        self.name = name
        self.parent_process_type_id = parent_process_type_id
        self.reference_name = reference_name
