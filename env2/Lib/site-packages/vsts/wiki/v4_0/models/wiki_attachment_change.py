# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .wiki_change import WikiChange


class WikiAttachmentChange(WikiChange):
    """WikiAttachmentChange.

    :param overwrite_content_if_existing: Defines whether the content of an existing attachment is to be overwriten or not. If true, the content of the attachment is overwritten on an existing attachment. If attachment non-existing, new attachment is created. If false, exception is thrown if an attachment with same name exists.
    :type overwrite_content_if_existing: bool
    """

    _attribute_map = {
        'overwrite_content_if_existing': {'key': 'overwriteContentIfExisting', 'type': 'bool'}
    }

    def __init__(self, overwrite_content_if_existing=None):
        super(WikiAttachmentChange, self).__init__()
        self.overwrite_content_if_existing = overwrite_content_if_existing
