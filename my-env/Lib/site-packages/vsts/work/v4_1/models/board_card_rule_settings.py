# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class BoardCardRuleSettings(Model):
    """BoardCardRuleSettings.

    :param _links:
    :type _links: :class:`ReferenceLinks <work.v4_1.models.ReferenceLinks>`
    :param rules:
    :type rules: dict
    :param url:
    :type url: str
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'rules': {'key': 'rules', 'type': '{[Rule]}'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, _links=None, rules=None, url=None):
        super(BoardCardRuleSettings, self).__init__()
        self._links = _links
        self.rules = rules
        self.url = url
