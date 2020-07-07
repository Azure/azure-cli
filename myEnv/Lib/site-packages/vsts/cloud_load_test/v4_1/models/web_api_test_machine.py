# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class WebApiTestMachine(Model):
    """WebApiTestMachine.

    :param last_heart_beat:
    :type last_heart_beat: datetime
    :param machine_name:
    :type machine_name: str
    :param status:
    :type status: str
    """

    _attribute_map = {
        'last_heart_beat': {'key': 'lastHeartBeat', 'type': 'iso-8601'},
        'machine_name': {'key': 'machineName', 'type': 'str'},
        'status': {'key': 'status', 'type': 'str'}
    }

    def __init__(self, last_heart_beat=None, machine_name=None, status=None):
        super(WebApiTestMachine, self).__init__()
        self.last_heart_beat = last_heart_beat
        self.machine_name = machine_name
        self.status = status
