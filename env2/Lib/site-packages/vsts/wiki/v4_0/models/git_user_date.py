# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GitUserDate(Model):
    """GitUserDate.

    :param date:
    :type date: datetime
    :param email:
    :type email: str
    :param name:
    :type name: str
    """

    _attribute_map = {
        'date': {'key': 'date', 'type': 'iso-8601'},
        'email': {'key': 'email', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'}
    }

    def __init__(self, date=None, email=None, name=None):
        super(GitUserDate, self).__init__()
        self.date = date
        self.email = email
        self.name = name
