# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ValidationIssue(Model):
    """ValidationIssue.

    :param description:
    :type description: str
    :param file:
    :type file: str
    :param help_link:
    :type help_link: str
    :param issue_type:
    :type issue_type: object
    :param line:
    :type line: int
    """

    _attribute_map = {
        'description': {'key': 'description', 'type': 'str'},
        'file': {'key': 'file', 'type': 'str'},
        'help_link': {'key': 'helpLink', 'type': 'str'},
        'issue_type': {'key': 'issueType', 'type': 'object'},
        'line': {'key': 'line', 'type': 'int'}
    }

    def __init__(self, description=None, file=None, help_link=None, issue_type=None, line=None):
        super(ValidationIssue, self).__init__()
        self.description = description
        self.file = file
        self.help_link = help_link
        self.issue_type = issue_type
        self.line = line
