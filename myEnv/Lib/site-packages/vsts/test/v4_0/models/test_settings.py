# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TestSettings(Model):
    """TestSettings.

    :param area_path: Area path required to create test settings
    :type area_path: str
    :param description: Description of the test settings. Used in create test settings.
    :type description: str
    :param is_public: Indicates if the tests settings is public or private.Used in create test settings.
    :type is_public: bool
    :param machine_roles: Xml string of machine roles. Used in create test settings.
    :type machine_roles: str
    :param test_settings_content: Test settings content.
    :type test_settings_content: str
    :param test_settings_id: Test settings id.
    :type test_settings_id: int
    :param test_settings_name: Test settings name.
    :type test_settings_name: str
    """

    _attribute_map = {
        'area_path': {'key': 'areaPath', 'type': 'str'},
        'description': {'key': 'description', 'type': 'str'},
        'is_public': {'key': 'isPublic', 'type': 'bool'},
        'machine_roles': {'key': 'machineRoles', 'type': 'str'},
        'test_settings_content': {'key': 'testSettingsContent', 'type': 'str'},
        'test_settings_id': {'key': 'testSettingsId', 'type': 'int'},
        'test_settings_name': {'key': 'testSettingsName', 'type': 'str'}
    }

    def __init__(self, area_path=None, description=None, is_public=None, machine_roles=None, test_settings_content=None, test_settings_id=None, test_settings_name=None):
        super(TestSettings, self).__init__()
        self.area_path = area_path
        self.description = description
        self.is_public = is_public
        self.machine_roles = machine_roles
        self.test_settings_content = test_settings_content
        self.test_settings_id = test_settings_id
        self.test_settings_name = test_settings_name
