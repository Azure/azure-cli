# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ResolvedDataProvider(Model):
    """ResolvedDataProvider.

    :param duration: The total time the data provider took to resolve its data (in milliseconds)
    :type duration: int
    :param error:
    :type error: str
    :param id:
    :type id: str
    """

    _attribute_map = {
        'duration': {'key': 'duration', 'type': 'int'},
        'error': {'key': 'error', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'}
    }

    def __init__(self, duration=None, error=None, id=None):
        super(ResolvedDataProvider, self).__init__()
        self.duration = duration
        self.error = error
        self.id = id
