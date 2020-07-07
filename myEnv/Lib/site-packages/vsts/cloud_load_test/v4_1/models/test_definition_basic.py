# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TestDefinitionBasic(Model):
    """TestDefinitionBasic.

    :param access_data:
    :type access_data: :class:`DropAccessData <microsoft.-visual-studio.-test-service.-web-api-model.v4_1.models.DropAccessData>`
    :param created_by:
    :type created_by: IdentityRef
    :param created_date:
    :type created_date: datetime
    :param id:
    :type id: str
    :param last_modified_by:
    :type last_modified_by: IdentityRef
    :param last_modified_date:
    :type last_modified_date: datetime
    :param load_test_type:
    :type load_test_type: object
    :param name:
    :type name: str
    """

    _attribute_map = {
        'access_data': {'key': 'accessData', 'type': 'DropAccessData'},
        'created_by': {'key': 'createdBy', 'type': 'IdentityRef'},
        'created_date': {'key': 'createdDate', 'type': 'iso-8601'},
        'id': {'key': 'id', 'type': 'str'},
        'last_modified_by': {'key': 'lastModifiedBy', 'type': 'IdentityRef'},
        'last_modified_date': {'key': 'lastModifiedDate', 'type': 'iso-8601'},
        'load_test_type': {'key': 'loadTestType', 'type': 'object'},
        'name': {'key': 'name', 'type': 'str'}
    }

    def __init__(self, access_data=None, created_by=None, created_date=None, id=None, last_modified_by=None, last_modified_date=None, load_test_type=None, name=None):
        super(TestDefinitionBasic, self).__init__()
        self.access_data = access_data
        self.created_by = created_by
        self.created_date = created_date
        self.id = id
        self.last_modified_by = last_modified_by
        self.last_modified_date = last_modified_date
        self.load_test_type = load_test_type
        self.name = name
