# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ExtensionPolicy(Model):
    """ExtensionPolicy.

    :param install: Permissions on 'Install' operation
    :type install: object
    :param request: Permission on 'Request' operation
    :type request: object
    """

    _attribute_map = {
        'install': {'key': 'install', 'type': 'object'},
        'request': {'key': 'request', 'type': 'object'}
    }

    def __init__(self, install=None, request=None):
        super(ExtensionPolicy, self).__init__()
        self.install = install
        self.request = request
