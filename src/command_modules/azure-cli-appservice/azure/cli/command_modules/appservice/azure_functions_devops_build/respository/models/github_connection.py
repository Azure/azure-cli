# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GithubConnection(Model):
    _attribute_map = {
        'errorMessage': {'key': 'errorMessage', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'},
    }

    def __init__(self, errorMessage=None, url=None):  # pylint: disable=super-init-not-called
        self.errorMessage = errorMessage
        self.url = url
