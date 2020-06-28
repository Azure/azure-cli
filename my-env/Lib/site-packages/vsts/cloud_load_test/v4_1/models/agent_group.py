# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class AgentGroup(Model):
    """AgentGroup.

    :param created_by:
    :type created_by: IdentityRef
    :param creation_time:
    :type creation_time: datetime
    :param group_id:
    :type group_id: str
    :param group_name:
    :type group_name: str
    :param machine_access_data:
    :type machine_access_data: list of :class:`AgentGroupAccessData <microsoft.-visual-studio.-test-service.-web-api-model.v4_1.models.AgentGroupAccessData>`
    :param machine_configuration:
    :type machine_configuration: :class:`WebApiUserLoadTestMachineInput <microsoft.-visual-studio.-test-service.-web-api-model.v4_1.models.WebApiUserLoadTestMachineInput>`
    :param tenant_id:
    :type tenant_id: str
    """

    _attribute_map = {
        'created_by': {'key': 'createdBy', 'type': 'IdentityRef'},
        'creation_time': {'key': 'creationTime', 'type': 'iso-8601'},
        'group_id': {'key': 'groupId', 'type': 'str'},
        'group_name': {'key': 'groupName', 'type': 'str'},
        'machine_access_data': {'key': 'machineAccessData', 'type': '[AgentGroupAccessData]'},
        'machine_configuration': {'key': 'machineConfiguration', 'type': 'WebApiUserLoadTestMachineInput'},
        'tenant_id': {'key': 'tenantId', 'type': 'str'}
    }

    def __init__(self, created_by=None, creation_time=None, group_id=None, group_name=None, machine_access_data=None, machine_configuration=None, tenant_id=None):
        super(AgentGroup, self).__init__()
        self.created_by = created_by
        self.creation_time = creation_time
        self.group_id = group_id
        self.group_name = group_name
        self.machine_access_data = machine_access_data
        self.machine_configuration = machine_configuration
        self.tenant_id = tenant_id
