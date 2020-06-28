# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ExtensionDataCollection(Model):
    """ExtensionDataCollection.

    :param collection_name: The name of the collection
    :type collection_name: str
    :param documents: A list of documents belonging to the collection
    :type documents: list of :class:`object <extension-management.v4_0.models.object>`
    :param scope_type: The type of the collection's scope, such as Default or User
    :type scope_type: str
    :param scope_value: The value of the collection's scope, such as Current or Me
    :type scope_value: str
    """

    _attribute_map = {
        'collection_name': {'key': 'collectionName', 'type': 'str'},
        'documents': {'key': 'documents', 'type': '[object]'},
        'scope_type': {'key': 'scopeType', 'type': 'str'},
        'scope_value': {'key': 'scopeValue', 'type': 'str'}
    }

    def __init__(self, collection_name=None, documents=None, scope_type=None, scope_value=None):
        super(ExtensionDataCollection, self).__init__()
        self.collection_name = collection_name
        self.documents = documents
        self.scope_type = scope_type
        self.scope_value = scope_value
