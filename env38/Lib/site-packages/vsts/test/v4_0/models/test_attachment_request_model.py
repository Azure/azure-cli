# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TestAttachmentRequestModel(Model):
    """TestAttachmentRequestModel.

    :param attachment_type:
    :type attachment_type: str
    :param comment:
    :type comment: str
    :param file_name:
    :type file_name: str
    :param stream:
    :type stream: str
    """

    _attribute_map = {
        'attachment_type': {'key': 'attachmentType', 'type': 'str'},
        'comment': {'key': 'comment', 'type': 'str'},
        'file_name': {'key': 'fileName', 'type': 'str'},
        'stream': {'key': 'stream', 'type': 'str'}
    }

    def __init__(self, attachment_type=None, comment=None, file_name=None, stream=None):
        super(TestAttachmentRequestModel, self).__init__()
        self.attachment_type = attachment_type
        self.comment = comment
        self.file_name = file_name
        self.stream = stream
