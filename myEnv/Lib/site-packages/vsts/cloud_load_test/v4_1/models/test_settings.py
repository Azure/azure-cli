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

    :param cleanup_command:
    :type cleanup_command: str
    :param host_process_platform:
    :type host_process_platform: object
    :param setup_command:
    :type setup_command: str
    """

    _attribute_map = {
        'cleanup_command': {'key': 'cleanupCommand', 'type': 'str'},
        'host_process_platform': {'key': 'hostProcessPlatform', 'type': 'object'},
        'setup_command': {'key': 'setupCommand', 'type': 'str'}
    }

    def __init__(self, cleanup_command=None, host_process_platform=None, setup_command=None):
        super(TestSettings, self).__init__()
        self.cleanup_command = cleanup_command
        self.host_process_platform = host_process_platform
        self.setup_command = setup_command
