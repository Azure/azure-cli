# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class WebApiLoadTestMachineInput(Model):
    """WebApiLoadTestMachineInput.

    :param machine_group_id:
    :type machine_group_id: str
    :param machine_type:
    :type machine_type: object
    :param setup_configuration:
    :type setup_configuration: :class:`WebApiSetupParamaters <microsoft.-visual-studio.-test-service.-web-api-model.v4_1.models.WebApiSetupParamaters>`
    :param supported_run_types:
    :type supported_run_types: list of TestRunType
    """

    _attribute_map = {
        'machine_group_id': {'key': 'machineGroupId', 'type': 'str'},
        'machine_type': {'key': 'machineType', 'type': 'object'},
        'setup_configuration': {'key': 'setupConfiguration', 'type': 'WebApiSetupParamaters'},
        'supported_run_types': {'key': 'supportedRunTypes', 'type': '[object]'}
    }

    def __init__(self, machine_group_id=None, machine_type=None, setup_configuration=None, supported_run_types=None):
        super(WebApiLoadTestMachineInput, self).__init__()
        self.machine_group_id = machine_group_id
        self.machine_type = machine_type
        self.setup_configuration = setup_configuration
        self.supported_run_types = supported_run_types
