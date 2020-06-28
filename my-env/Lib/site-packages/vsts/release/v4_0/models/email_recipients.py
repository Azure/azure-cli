# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class EmailRecipients(Model):
    """EmailRecipients.

    :param email_addresses:
    :type email_addresses: list of str
    :param tfs_ids:
    :type tfs_ids: list of str
    """

    _attribute_map = {
        'email_addresses': {'key': 'emailAddresses', 'type': '[str]'},
        'tfs_ids': {'key': 'tfsIds', 'type': '[str]'}
    }

    def __init__(self, email_addresses=None, tfs_ids=None):
        super(EmailRecipients, self).__init__()
        self.email_addresses = email_addresses
        self.tfs_ids = tfs_ids
