# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class BoardCardSettings(Model):
    """BoardCardSettings.

    :param cards:
    :type cards: dict
    """

    _attribute_map = {
        'cards': {'key': 'cards', 'type': '{[FieldSetting]}'}
    }

    def __init__(self, cards=None):
        super(BoardCardSettings, self).__init__()
        self.cards = cards
