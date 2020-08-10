# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class SourceToTargetRef(Model):
    """SourceToTargetRef.

    :param source_ref: The source ref to copy. For example, refs/heads/master.
    :type source_ref: str
    :param target_ref: The target ref to update. For example, refs/heads/master
    :type target_ref: str
    """

    _attribute_map = {
        'source_ref': {'key': 'sourceRef', 'type': 'str'},
        'target_ref': {'key': 'targetRef', 'type': 'str'}
    }

    def __init__(self, source_ref=None, target_ref=None):
        super(SourceToTargetRef, self).__init__()
        self.source_ref = source_ref
        self.target_ref = target_ref
