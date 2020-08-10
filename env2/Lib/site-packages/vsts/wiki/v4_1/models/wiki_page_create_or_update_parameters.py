# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class WikiPageCreateOrUpdateParameters(Model):
    """WikiPageCreateOrUpdateParameters.

    :param content: Content of the wiki page.
    :type content: str
    """

    _attribute_map = {
        'content': {'key': 'content', 'type': 'str'}
    }

    def __init__(self, content=None):
        super(WikiPageCreateOrUpdateParameters, self).__init__()
        self.content = content
