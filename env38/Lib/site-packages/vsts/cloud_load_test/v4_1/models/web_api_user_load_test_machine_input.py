# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .web_api_load_test_machine_input import WebApiLoadTestMachineInput


class WebApiUserLoadTestMachineInput(WebApiLoadTestMachineInput):
    """WebApiUserLoadTestMachineInput.

    :param machine_group_id:
    :type machine_group_id: str
    :param machine_type:
    :type machine_type: object
    :param setup_configuration:
    :type setup_configuration: :class:`WebApiSetupParamaters <microsoft.-visual-studio.-test-service.-web-api-model.v4_1.models.WebApiSetupParamaters>`
    :param supported_run_types:
    :type supported_run_types: list of TestRunType
    :param agent_group_name:
    :type agent_group_name: str
    :param tenant_id:
    :type tenant_id: str
    :param user_load_agent_resources_uri:
    :type user_load_agent_resources_uri: str
    :param vSTSAccount_uri:
    :type vSTSAccount_uri: str
    """

    _attribute_map = {
        'machine_group_id': {'key': 'machineGroupId', 'type': 'str'},
        'machine_type': {'key': 'machineType', 'type': 'object'},
        'setup_configuration': {'key': 'setupConfiguration', 'type': 'WebApiSetupParamaters'},
        'supported_run_types': {'key': 'supportedRunTypes', 'type': '[TestRunType]'},
        'agent_group_name': {'key': 'agentGroupName', 'type': 'str'},
        'tenant_id': {'key': 'tenantId', 'type': 'str'},
        'user_load_agent_resources_uri': {'key': 'userLoadAgentResourcesUri', 'type': 'str'},
        'vSTSAccount_uri': {'key': 'vSTSAccountUri', 'type': 'str'}
    }

    def __init__(self, machine_group_id=None, machine_type=None, setup_configuration=None, supported_run_types=None, agent_group_name=None, tenant_id=None, user_load_agent_resources_uri=None, vSTSAccount_uri=None):
        super(WebApiUserLoadTestMachineInput, self).__init__(machine_group_id=machine_group_id, machine_type=machine_type, setup_configuration=setup_configuration, supported_run_types=supported_run_types)
        self.agent_group_name = agent_group_name
        self.tenant_id = tenant_id
        self.user_load_agent_resources_uri = user_load_agent_resources_uri
        self.vSTSAccount_uri = vSTSAccount_uri
