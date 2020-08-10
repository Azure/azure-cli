# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class WikiPageMoveResponse(Model):
    """WikiPageMoveResponse.

    :param eTag: Contains the list of ETag values from the response header of the page move API call. The first item in the list contains the version of the wiki page subject to page move.
    :type eTag: list of str
    :param page_move: Defines properties for wiki page move.
    :type page_move: :class:`WikiPageMove <wiki.v4_1.models.WikiPageMove>`
    """

    _attribute_map = {
        'eTag': {'key': 'eTag', 'type': '[str]'},
        'page_move': {'key': 'pageMove', 'type': 'WikiPageMove'}
    }

    def __init__(self, eTag=None, page_move=None):
        super(WikiPageMoveResponse, self).__init__()
        self.eTag = eTag
        self.page_move = page_move
