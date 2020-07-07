# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ProfileAttributeBase(Model):
    """ProfileAttributeBase.

    :param descriptor:
    :type descriptor: :class:`AttributeDescriptor <profile.v4_1.models.AttributeDescriptor>`
    :param revision:
    :type revision: int
    :param time_stamp:
    :type time_stamp: datetime
    :param value:
    :type value: object
    """

    _attribute_map = {
        'descriptor': {'key': 'descriptor', 'type': 'AttributeDescriptor'},
        'revision': {'key': 'revision', 'type': 'int'},
        'time_stamp': {'key': 'timeStamp', 'type': 'iso-8601'},
        'value': {'key': 'value', 'type': 'object'}
    }

    def __init__(self, descriptor=None, revision=None, time_stamp=None, value=None):
        super(ProfileAttributeBase, self).__init__()
        self.descriptor = descriptor
        self.revision = revision
        self.time_stamp = time_stamp
        self.value = value
