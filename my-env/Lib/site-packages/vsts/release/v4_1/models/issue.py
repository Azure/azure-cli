# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class Issue(Model):
    """Issue.

    :param issue_type:
    :type issue_type: str
    :param message:
    :type message: str
    """

    _attribute_map = {
        'issue_type': {'key': 'issueType', 'type': 'str'},
        'message': {'key': 'message', 'type': 'str'}
    }

    def __init__(self, issue_type=None, message=None):
        super(Issue, self).__init__()
        self.issue_type = issue_type
        self.message = message
