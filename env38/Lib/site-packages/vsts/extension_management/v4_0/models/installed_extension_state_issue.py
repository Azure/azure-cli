# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class InstalledExtensionStateIssue(Model):
    """InstalledExtensionStateIssue.

    :param message: The error message
    :type message: str
    :param source: Source of the installation issue, for example  "Demands"
    :type source: str
    :param type: Installation issue type (Warning, Error)
    :type type: object
    """

    _attribute_map = {
        'message': {'key': 'message', 'type': 'str'},
        'source': {'key': 'source', 'type': 'str'},
        'type': {'key': 'type', 'type': 'object'}
    }

    def __init__(self, message=None, source=None, type=None):
        super(InstalledExtensionStateIssue, self).__init__()
        self.message = message
        self.source = source
        self.type = type
