# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .team_settings_data_contract_base import TeamSettingsDataContractBase


class TeamFieldValues(TeamSettingsDataContractBase):
    """TeamFieldValues.

    :param _links: Collection of links relevant to resource
    :type _links: :class:`ReferenceLinks <work.v4_1.models.ReferenceLinks>`
    :param url: Full http link to the resource
    :type url: str
    :param default_value: The default team field value
    :type default_value: str
    :param field: Shallow ref to the field being used as a team field
    :type field: :class:`FieldReference <work.v4_1.models.FieldReference>`
    :param values: Collection of all valid team field values
    :type values: list of :class:`TeamFieldValue <work.v4_1.models.TeamFieldValue>`
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'url': {'key': 'url', 'type': 'str'},
        'default_value': {'key': 'defaultValue', 'type': 'str'},
        'field': {'key': 'field', 'type': 'FieldReference'},
        'values': {'key': 'values', 'type': '[TeamFieldValue]'}
    }

    def __init__(self, _links=None, url=None, default_value=None, field=None, values=None):
        super(TeamFieldValues, self).__init__(_links=_links, url=url)
        self.default_value = default_value
        self.field = field
        self.values = values
