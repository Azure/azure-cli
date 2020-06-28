# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class BacklogFields(Model):
    """BacklogFields.

    :param type_fields: Field Type (e.g. Order, Activity) to Field Reference Name map
    :type type_fields: dict
    """

    _attribute_map = {
        'type_fields': {'key': 'typeFields', 'type': '{str}'}
    }

    def __init__(self, type_fields=None):
        super(BacklogFields, self).__init__()
        self.type_fields = type_fields
