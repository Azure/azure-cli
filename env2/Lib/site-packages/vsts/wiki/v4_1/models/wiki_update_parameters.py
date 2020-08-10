# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class WikiUpdateParameters(Model):
    """WikiUpdateParameters.

    :param versions: Versions of the wiki.
    :type versions: list of :class:`GitVersionDescriptor <wiki.v4_1.models.GitVersionDescriptor>`
    """

    _attribute_map = {
        'versions': {'key': 'versions', 'type': '[GitVersionDescriptor]'}
    }

    def __init__(self, versions=None):
        super(WikiUpdateParameters, self).__init__()
        self.versions = versions
