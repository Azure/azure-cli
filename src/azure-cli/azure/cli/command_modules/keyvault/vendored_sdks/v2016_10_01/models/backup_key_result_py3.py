# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class BackupKeyResult(Model):
    """The backup key result, containing the backup blob.

    Variables are only populated by the server, and will be ignored when
    sending a request.

    :ivar value: The backup blob containing the backed up key.
    :vartype value: bytes
    """

    _validation = {
        'value': {'readonly': True},
    }

    _attribute_map = {
        'value': {'key': 'value', 'type': 'base64'},
    }

    def __init__(self, **kwargs) -> None:
        super(BackupKeyResult, self).__init__(**kwargs)
        self.value = None
