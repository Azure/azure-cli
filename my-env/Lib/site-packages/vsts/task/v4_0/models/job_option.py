# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class JobOption(Model):
    """JobOption.

    :param data:
    :type data: dict
    :param id: Gets the id of the option.
    :type id: str
    """

    _attribute_map = {
        'data': {'key': 'data', 'type': '{str}'},
        'id': {'key': 'id', 'type': 'str'}
    }

    def __init__(self, data=None, id=None):
        super(JobOption, self).__init__()
        self.data = data
        self.id = id
