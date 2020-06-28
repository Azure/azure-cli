# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class FileContainer(Model):
    """FileContainer.

    :param artifact_uri: Uri of the artifact associated with the container.
    :type artifact_uri: str
    :param content_location: Download Url for the content of this item.
    :type content_location: str
    :param created_by: Owner.
    :type created_by: str
    :param date_created: Creation date.
    :type date_created: datetime
    :param description: Description.
    :type description: str
    :param id: Id.
    :type id: long
    :param item_location: Location of the item resource.
    :type item_location: str
    :param locator_path: ItemStore Locator for this container.
    :type locator_path: str
    :param name: Name.
    :type name: str
    :param options: Options the container can have.
    :type options: object
    :param scope_identifier: Project Id.
    :type scope_identifier: str
    :param security_token: Security token of the artifact associated with the container.
    :type security_token: str
    :param signing_key_id: Identifier of the optional encryption key.
    :type signing_key_id: str
    :param size: Total size of the files in bytes.
    :type size: long
    """

    _attribute_map = {
        'artifact_uri': {'key': 'artifactUri', 'type': 'str'},
        'content_location': {'key': 'contentLocation', 'type': 'str'},
        'created_by': {'key': 'createdBy', 'type': 'str'},
        'date_created': {'key': 'dateCreated', 'type': 'iso-8601'},
        'description': {'key': 'description', 'type': 'str'},
        'id': {'key': 'id', 'type': 'long'},
        'item_location': {'key': 'itemLocation', 'type': 'str'},
        'locator_path': {'key': 'locatorPath', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'options': {'key': 'options', 'type': 'object'},
        'scope_identifier': {'key': 'scopeIdentifier', 'type': 'str'},
        'security_token': {'key': 'securityToken', 'type': 'str'},
        'signing_key_id': {'key': 'signingKeyId', 'type': 'str'},
        'size': {'key': 'size', 'type': 'long'}
    }

    def __init__(self, artifact_uri=None, content_location=None, created_by=None, date_created=None, description=None, id=None, item_location=None, locator_path=None, name=None, options=None, scope_identifier=None, security_token=None, signing_key_id=None, size=None):
        super(FileContainer, self).__init__()
        self.artifact_uri = artifact_uri
        self.content_location = content_location
        self.created_by = created_by
        self.date_created = date_created
        self.description = description
        self.id = id
        self.item_location = item_location
        self.locator_path = locator_path
        self.name = name
        self.options = options
        self.scope_identifier = scope_identifier
        self.security_token = security_token
        self.signing_key_id = signing_key_id
        self.size = size
