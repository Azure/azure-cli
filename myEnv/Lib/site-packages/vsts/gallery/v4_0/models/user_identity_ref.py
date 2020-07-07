# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class UserIdentityRef(Model):
    """UserIdentityRef.

    :param display_name: User display name
    :type display_name: str
    :param id: User VSID
    :type id: str
    """

    _attribute_map = {
        'display_name': {'key': 'displayName', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'}
    }

    def __init__(self, display_name=None, id=None):
        super(UserIdentityRef, self).__init__()
        self.display_name = display_name
        self.id = id
