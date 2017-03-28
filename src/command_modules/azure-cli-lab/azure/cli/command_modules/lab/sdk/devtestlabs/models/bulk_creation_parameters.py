# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# coding: utf-8
# pylint: skip-file
from msrest.serialization import Model


class BulkCreationParameters(Model):
    """BulkCreationParameters.

    :param instance_count: The number of virtual machine instances to create.
    :type instance_count: int
    """

    _attribute_map = {
        'instance_count': {'key': 'instanceCount', 'type': 'int'},
    }

    def __init__(self, instance_count=None):
        self.instance_count = instance_count
