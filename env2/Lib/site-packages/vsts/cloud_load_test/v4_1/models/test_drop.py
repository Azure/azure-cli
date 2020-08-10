# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TestDrop(Model):
    """TestDrop.

    :param access_data:
    :type access_data: :class:`DropAccessData <microsoft.-visual-studio.-test-service.-web-api-model.v4_1.models.DropAccessData>`
    :param created_date:
    :type created_date: datetime
    :param drop_type:
    :type drop_type: str
    :param id:
    :type id: str
    :param load_test_definition:
    :type load_test_definition: :class:`LoadTestDefinition <microsoft.-visual-studio.-test-service.-web-api-model.v4_1.models.LoadTestDefinition>`
    :param test_run_id:
    :type test_run_id: str
    """

    _attribute_map = {
        'access_data': {'key': 'accessData', 'type': 'DropAccessData'},
        'created_date': {'key': 'createdDate', 'type': 'iso-8601'},
        'drop_type': {'key': 'dropType', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'load_test_definition': {'key': 'loadTestDefinition', 'type': 'LoadTestDefinition'},
        'test_run_id': {'key': 'testRunId', 'type': 'str'}
    }

    def __init__(self, access_data=None, created_date=None, drop_type=None, id=None, load_test_definition=None, test_run_id=None):
        super(TestDrop, self).__init__()
        self.access_data = access_data
        self.created_date = created_date
        self.drop_type = drop_type
        self.id = id
        self.load_test_definition = load_test_definition
        self.test_run_id = test_run_id
