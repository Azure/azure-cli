# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class PlanViewData(Model):
    """PlanViewData.

    :param id:
    :type id: str
    :param revision:
    :type revision: int
    """

    _attribute_map = {
        'id': {'key': 'id', 'type': 'str'},
        'revision': {'key': 'revision', 'type': 'int'}
    }

    def __init__(self, id=None, revision=None):
        super(PlanViewData, self).__init__()
        self.id = id
        self.revision = revision
