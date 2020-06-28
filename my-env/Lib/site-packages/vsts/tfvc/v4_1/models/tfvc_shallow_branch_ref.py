# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TfvcShallowBranchRef(Model):
    """TfvcShallowBranchRef.

    :param path: Path for the branch.
    :type path: str
    """

    _attribute_map = {
        'path': {'key': 'path', 'type': 'str'}
    }

    def __init__(self, path=None):
        super(TfvcShallowBranchRef, self).__init__()
        self.path = path
