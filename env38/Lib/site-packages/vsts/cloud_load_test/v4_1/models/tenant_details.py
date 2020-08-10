# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TenantDetails(Model):
    """TenantDetails.

    :param access_details:
    :type access_details: list of :class:`AgentGroupAccessData <microsoft.-visual-studio.-test-service.-web-api-model.v4_1.models.AgentGroupAccessData>`
    :param id:
    :type id: str
    :param static_machines:
    :type static_machines: list of :class:`WebApiTestMachine <microsoft.-visual-studio.-test-service.-web-api-model.v4_1.models.WebApiTestMachine>`
    :param user_load_agent_input:
    :type user_load_agent_input: :class:`WebApiUserLoadTestMachineInput <microsoft.-visual-studio.-test-service.-web-api-model.v4_1.models.WebApiUserLoadTestMachineInput>`
    :param user_load_agent_resources_uri:
    :type user_load_agent_resources_uri: str
    :param valid_geo_locations:
    :type valid_geo_locations: list of str
    """

    _attribute_map = {
        'access_details': {'key': 'accessDetails', 'type': '[AgentGroupAccessData]'},
        'id': {'key': 'id', 'type': 'str'},
        'static_machines': {'key': 'staticMachines', 'type': '[WebApiTestMachine]'},
        'user_load_agent_input': {'key': 'userLoadAgentInput', 'type': 'WebApiUserLoadTestMachineInput'},
        'user_load_agent_resources_uri': {'key': 'userLoadAgentResourcesUri', 'type': 'str'},
        'valid_geo_locations': {'key': 'validGeoLocations', 'type': '[str]'}
    }

    def __init__(self, access_details=None, id=None, static_machines=None, user_load_agent_input=None, user_load_agent_resources_uri=None, valid_geo_locations=None):
        super(TenantDetails, self).__init__()
        self.access_details = access_details
        self.id = id
        self.static_machines = static_machines
        self.user_load_agent_input = user_load_agent_input
        self.user_load_agent_resources_uri = user_load_agent_resources_uri
        self.valid_geo_locations = valid_geo_locations
