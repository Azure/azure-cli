# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class InstallationTarget(Model):
    """InstallationTarget.

    :param target:
    :type target: str
    :param target_version:
    :type target_version: str
    """

    _attribute_map = {
        'target': {'key': 'target', 'type': 'str'},
        'target_version': {'key': 'targetVersion', 'type': 'str'}
    }

    def __init__(self, target=None, target_version=None):
        super(InstallationTarget, self).__init__()
        self.target = target
        self.target_version = target_version
