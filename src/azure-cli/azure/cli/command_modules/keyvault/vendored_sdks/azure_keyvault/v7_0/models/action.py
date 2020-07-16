# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class Action(Model):
    """The action that will be executed.

    :param action_type: The type of the action. Possible values include:
     'EmailContacts', 'AutoRenew'
    :type action_type: str or ~azure.keyvault.v7_0.models.ActionType
    """

    _attribute_map = {
        'action_type': {'key': 'action_type', 'type': 'ActionType'},
    }

    def __init__(self, **kwargs):
        super(Action, self).__init__(**kwargs)
        self.action_type = kwargs.get('action_type', None)
