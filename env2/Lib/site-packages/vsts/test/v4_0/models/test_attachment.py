# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TestAttachment(Model):
    """TestAttachment.

    :param attachment_type:
    :type attachment_type: object
    :param comment:
    :type comment: str
    :param created_date:
    :type created_date: datetime
    :param file_name:
    :type file_name: str
    :param id:
    :type id: int
    :param url:
    :type url: str
    """

    _attribute_map = {
        'attachment_type': {'key': 'attachmentType', 'type': 'object'},
        'comment': {'key': 'comment', 'type': 'str'},
        'created_date': {'key': 'createdDate', 'type': 'iso-8601'},
        'file_name': {'key': 'fileName', 'type': 'str'},
        'id': {'key': 'id', 'type': 'int'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, attachment_type=None, comment=None, created_date=None, file_name=None, id=None, url=None):
        super(TestAttachment, self).__init__()
        self.attachment_type = attachment_type
        self.comment = comment
        self.created_date = created_date
        self.file_name = file_name
        self.id = id
        self.url = url
