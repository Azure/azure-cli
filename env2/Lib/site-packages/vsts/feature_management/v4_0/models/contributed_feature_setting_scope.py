# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ContributedFeatureSettingScope(Model):
    """ContributedFeatureSettingScope.

    :param setting_scope: The name of the settings scope to use when reading/writing the setting
    :type setting_scope: str
    :param user_scoped: Whether this is a user-scope or this is a host-wide (all users) setting
    :type user_scoped: bool
    """

    _attribute_map = {
        'setting_scope': {'key': 'settingScope', 'type': 'str'},
        'user_scoped': {'key': 'userScoped', 'type': 'bool'}
    }

    def __init__(self, setting_scope=None, user_scoped=None):
        super(ContributedFeatureSettingScope, self).__init__()
        self.setting_scope = setting_scope
        self.user_scoped = user_scoped
