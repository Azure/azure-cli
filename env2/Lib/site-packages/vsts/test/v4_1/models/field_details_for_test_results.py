# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class FieldDetailsForTestResults(Model):
    """FieldDetailsForTestResults.

    :param field_name: Group by field name
    :type field_name: str
    :param groups_for_field: Group by field values
    :type groups_for_field: list of object
    """

    _attribute_map = {
        'field_name': {'key': 'fieldName', 'type': 'str'},
        'groups_for_field': {'key': 'groupsForField', 'type': '[object]'}
    }

    def __init__(self, field_name=None, groups_for_field=None):
        super(FieldDetailsForTestResults, self).__init__()
        self.field_name = field_name
        self.groups_for_field = groups_for_field
