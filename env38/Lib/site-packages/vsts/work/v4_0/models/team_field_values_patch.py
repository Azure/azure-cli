# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TeamFieldValuesPatch(Model):
    """TeamFieldValuesPatch.

    :param default_value:
    :type default_value: str
    :param values:
    :type values: list of :class:`TeamFieldValue <work.v4_0.models.TeamFieldValue>`
    """

    _attribute_map = {
        'default_value': {'key': 'defaultValue', 'type': 'str'},
        'values': {'key': 'values', 'type': '[TeamFieldValue]'}
    }

    def __init__(self, default_value=None, values=None):
        super(TeamFieldValuesPatch, self).__init__()
        self.default_value = default_value
        self.values = values
