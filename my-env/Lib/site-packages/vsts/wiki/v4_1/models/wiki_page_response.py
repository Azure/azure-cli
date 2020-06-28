# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class WikiPageResponse(Model):
    """WikiPageResponse.

    :param eTag: Contains the list of ETag values from the response header of the pages API call. The first item in the list contains the version of the wiki page.
    :type eTag: list of str
    :param page: Defines properties for wiki page.
    :type page: :class:`WikiPage <wiki.v4_1.models.WikiPage>`
    """

    _attribute_map = {
        'eTag': {'key': 'eTag', 'type': '[str]'},
        'page': {'key': 'page', 'type': 'WikiPage'}
    }

    def __init__(self, eTag=None, page=None):
        super(WikiPageResponse, self).__init__()
        self.eTag = eTag
        self.page = page
