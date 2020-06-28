# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class WikiAttachmentResponse(Model):
    """WikiAttachmentResponse.

    :param attachment: Defines properties for wiki attachment file.
    :type attachment: :class:`WikiAttachment <wiki.v4_1.models.WikiAttachment>`
    :param eTag: Contains the list of ETag values from the response header of the attachments API call. The first item in the list contains the version of the wiki attachment.
    :type eTag: list of str
    """

    _attribute_map = {
        'attachment': {'key': 'attachment', 'type': 'WikiAttachment'},
        'eTag': {'key': 'eTag', 'type': '[str]'}
    }

    def __init__(self, attachment=None, eTag=None):
        super(WikiAttachmentResponse, self).__init__()
        self.attachment = attachment
        self.eTag = eTag
