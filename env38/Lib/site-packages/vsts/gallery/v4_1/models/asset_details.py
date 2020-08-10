# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class AssetDetails(Model):
    """AssetDetails.

    :param answers: Gets or sets the Answers, which contains vs marketplace extension name and publisher name
    :type answers: :class:`Answers <gallery.v4_1.models.Answers>`
    :param publisher_natural_identifier: Gets or sets the VS publisher Id
    :type publisher_natural_identifier: str
    """

    _attribute_map = {
        'answers': {'key': 'answers', 'type': 'Answers'},
        'publisher_natural_identifier': {'key': 'publisherNaturalIdentifier', 'type': 'str'}
    }

    def __init__(self, answers=None, publisher_natural_identifier=None):
        super(AssetDetails, self).__init__()
        self.answers = answers
        self.publisher_natural_identifier = publisher_natural_identifier
