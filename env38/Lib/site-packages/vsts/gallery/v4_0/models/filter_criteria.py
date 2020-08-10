# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class FilterCriteria(Model):
    """FilterCriteria.

    :param filter_type:
    :type filter_type: int
    :param value: The value used in the match based on the filter type.
    :type value: str
    """

    _attribute_map = {
        'filter_type': {'key': 'filterType', 'type': 'int'},
        'value': {'key': 'value', 'type': 'str'}
    }

    def __init__(self, filter_type=None, value=None):
        super(FilterCriteria, self).__init__()
        self.filter_type = filter_type
        self.value = value
