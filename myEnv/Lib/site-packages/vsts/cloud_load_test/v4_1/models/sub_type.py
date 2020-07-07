# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class SubType(Model):
    """SubType.

    :param count:
    :type count: int
    :param error_detail_list:
    :type error_detail_list: list of :class:`ErrorDetails <microsoft.-visual-studio.-test-service.-web-api-model.v4_1.models.ErrorDetails>`
    :param occurrences:
    :type occurrences: int
    :param sub_type_name:
    :type sub_type_name: str
    :param url:
    :type url: str
    """

    _attribute_map = {
        'count': {'key': 'count', 'type': 'int'},
        'error_detail_list': {'key': 'errorDetailList', 'type': '[ErrorDetails]'},
        'occurrences': {'key': 'occurrences', 'type': 'int'},
        'sub_type_name': {'key': 'subTypeName', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, count=None, error_detail_list=None, occurrences=None, sub_type_name=None, url=None):
        super(SubType, self).__init__()
        self.count = count
        self.error_detail_list = error_detail_list
        self.occurrences = occurrences
        self.sub_type_name = sub_type_name
        self.url = url
