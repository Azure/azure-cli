# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class MavenPomIssueManagement(Model):
    """MavenPomIssueManagement.

    :param system:
    :type system: str
    :param url:
    :type url: str
    """

    _attribute_map = {
        'system': {'key': 'system', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, system=None, url=None):
        super(MavenPomIssueManagement, self).__init__()
        self.system = system
        self.url = url
