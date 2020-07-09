# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from msrest.paging import Paged


class SasDefinitionItemPaged(Paged):
    """
    A paging container for iterating over a list of :class:`SasDefinitionItem <azure.keyvault.v2016_10_01.models.SasDefinitionItem>` object
    """

    _attribute_map = {
        'next_link': {'key': 'nextLink', 'type': 'str'},
        'current_page': {'key': 'value', 'type': '[SasDefinitionItem]'}
    }

    def __init__(self, *args, **kwargs):

        super(SasDefinitionItemPaged, self).__init__(*args, **kwargs)
