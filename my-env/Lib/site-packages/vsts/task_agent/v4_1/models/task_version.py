# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TaskVersion(Model):
    """TaskVersion.

    :param is_test:
    :type is_test: bool
    :param major:
    :type major: int
    :param minor:
    :type minor: int
    :param patch:
    :type patch: int
    """

    _attribute_map = {
        'is_test': {'key': 'isTest', 'type': 'bool'},
        'major': {'key': 'major', 'type': 'int'},
        'minor': {'key': 'minor', 'type': 'int'},
        'patch': {'key': 'patch', 'type': 'int'}
    }

    def __init__(self, is_test=None, major=None, minor=None, patch=None):
        super(TaskVersion, self).__init__()
        self.is_test = is_test
        self.major = major
        self.minor = minor
        self.patch = patch
