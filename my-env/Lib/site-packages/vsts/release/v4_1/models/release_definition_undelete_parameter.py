# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ReleaseDefinitionUndeleteParameter(Model):
    """ReleaseDefinitionUndeleteParameter.

    :param comment: Gets or sets comment.
    :type comment: str
    """

    _attribute_map = {
        'comment': {'key': 'comment', 'type': 'str'}
    }

    def __init__(self, comment=None):
        super(ReleaseDefinitionUndeleteParameter, self).__init__()
        self.comment = comment
