# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TestCaseResultAttachmentModel(Model):
    """TestCaseResultAttachmentModel.

    :param id:
    :type id: int
    :param iteration_id:
    :type iteration_id: int
    :param name:
    :type name: str
    :param size:
    :type size: long
    :param url:
    :type url: str
    """

    _attribute_map = {
        'id': {'key': 'id', 'type': 'int'},
        'iteration_id': {'key': 'iterationId', 'type': 'int'},
        'name': {'key': 'name', 'type': 'str'},
        'size': {'key': 'size', 'type': 'long'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, id=None, iteration_id=None, name=None, size=None, url=None):
        super(TestCaseResultAttachmentModel, self).__init__()
        self.id = id
        self.iteration_id = iteration_id
        self.name = name
        self.size = size
        self.url = url
