# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class FieldsToEvaluate(Model):
    """FieldsToEvaluate.

    :param fields: List of fields to evaluate.
    :type fields: list of str
    :param field_updates: Updated field values to evaluate.
    :type field_updates: dict
    :param field_values: Initial field values.
    :type field_values: dict
    :param rules_from: URL of the work item type for which the rules need to be executed.
    :type rules_from: list of str
    """

    _attribute_map = {
        'fields': {'key': 'fields', 'type': '[str]'},
        'field_updates': {'key': 'fieldUpdates', 'type': '{object}'},
        'field_values': {'key': 'fieldValues', 'type': '{object}'},
        'rules_from': {'key': 'rulesFrom', 'type': '[str]'}
    }

    def __init__(self, fields=None, field_updates=None, field_values=None, rules_from=None):
        super(FieldsToEvaluate, self).__init__()
        self.fields = fields
        self.field_updates = field_updates
        self.field_values = field_values
        self.rules_from = rules_from
