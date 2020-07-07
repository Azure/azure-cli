# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class WorkItemDeleteShallowReference(Model):
    """WorkItemDeleteShallowReference.

    :param id: Work item ID.
    :type id: int
    :param url: REST API URL of the resource
    :type url: str
    """

    _attribute_map = {
        'id': {'key': 'id', 'type': 'int'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, id=None, url=None):
        super(WorkItemDeleteShallowReference, self).__init__()
        self.id = id
        self.url = url
