# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class FileContainerItem(Model):
    """FileContainerItem.

    :param container_id: Container Id.
    :type container_id: long
    :param content_id:
    :type content_id: str
    :param content_location: Download Url for the content of this item.
    :type content_location: str
    :param created_by: Creator.
    :type created_by: str
    :param date_created: Creation date.
    :type date_created: datetime
    :param date_last_modified: Last modified date.
    :type date_last_modified: datetime
    :param file_encoding: Encoding of the file. Zero if not a file.
    :type file_encoding: int
    :param file_hash: Hash value of the file. Null if not a file.
    :type file_hash: str
    :param file_id: Id of the file content.
    :type file_id: int
    :param file_length: Length of the file. Zero if not of a file.
    :type file_length: long
    :param file_type: Type of the file. Zero if not a file.
    :type file_type: int
    :param item_location: Location of the item resource.
    :type item_location: str
    :param item_type: Type of the item: Folder, File or String.
    :type item_type: object
    :param last_modified_by: Modifier.
    :type last_modified_by: str
    :param path: Unique path that identifies the item.
    :type path: str
    :param scope_identifier: Project Id.
    :type scope_identifier: str
    :param status: Status of the item: Created or Pending Upload.
    :type status: object
    :param ticket:
    :type ticket: str
    """

    _attribute_map = {
        'container_id': {'key': 'containerId', 'type': 'long'},
        'content_id': {'key': 'contentId', 'type': 'str'},
        'content_location': {'key': 'contentLocation', 'type': 'str'},
        'created_by': {'key': 'createdBy', 'type': 'str'},
        'date_created': {'key': 'dateCreated', 'type': 'iso-8601'},
        'date_last_modified': {'key': 'dateLastModified', 'type': 'iso-8601'},
        'file_encoding': {'key': 'fileEncoding', 'type': 'int'},
        'file_hash': {'key': 'fileHash', 'type': 'str'},
        'file_id': {'key': 'fileId', 'type': 'int'},
        'file_length': {'key': 'fileLength', 'type': 'long'},
        'file_type': {'key': 'fileType', 'type': 'int'},
        'item_location': {'key': 'itemLocation', 'type': 'str'},
        'item_type': {'key': 'itemType', 'type': 'object'},
        'last_modified_by': {'key': 'lastModifiedBy', 'type': 'str'},
        'path': {'key': 'path', 'type': 'str'},
        'scope_identifier': {'key': 'scopeIdentifier', 'type': 'str'},
        'status': {'key': 'status', 'type': 'object'},
        'ticket': {'key': 'ticket', 'type': 'str'}
    }

    def __init__(self, container_id=None, content_id=None, content_location=None, created_by=None, date_created=None, date_last_modified=None, file_encoding=None, file_hash=None, file_id=None, file_length=None, file_type=None, item_location=None, item_type=None, last_modified_by=None, path=None, scope_identifier=None, status=None, ticket=None):
        super(FileContainerItem, self).__init__()
        self.container_id = container_id
        self.content_id = content_id
        self.content_location = content_location
        self.created_by = created_by
        self.date_created = date_created
        self.date_last_modified = date_last_modified
        self.file_encoding = file_encoding
        self.file_hash = file_hash
        self.file_id = file_id
        self.file_length = file_length
        self.file_type = file_type
        self.item_location = item_location
        self.item_type = item_type
        self.last_modified_by = last_modified_by
        self.path = path
        self.scope_identifier = scope_identifier
        self.status = status
        self.ticket = ticket
