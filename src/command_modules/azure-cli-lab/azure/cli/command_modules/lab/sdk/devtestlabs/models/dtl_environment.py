# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# coding: utf-8
# pylint: skip-file
from msrest.serialization import Model


class DtlEnvironment(Model):
    """DtlEnvironment.

    :param deployment_properties: The deployment properties of the
     environment.
    :type deployment_properties: :class:`EnvironmentDeploymentProperties
     <azure.mgmt.devtestlabs.models.EnvironmentDeploymentProperties>`
    :param arm_template_display_name: The display name of the Azure Resource
     Manager template that produced the environment.
    :type arm_template_display_name: str
    :param resource_group_id: The identifier  of the resource group containing
     the environment's resources.
    :type resource_group_id: str
    :param created_by_user: The creator of the environment.
    :type created_by_user: str
    :param provisioning_state: The provisioning status of the resource.
    :type provisioning_state: str
    :param unique_identifier: The unique immutable identifier of a resource
     (Guid).
    :type unique_identifier: str
    :param id: The identifier of the resource.
    :type id: str
    :param name: The name of the resource.
    :type name: str
    :param type: The type of the resource.
    :type type: str
    :param location: The location of the resource.
    :type location: str
    :param tags: The tags of the resource.
    :type tags: dict
    """

    _attribute_map = {
        'deployment_properties': {'key': 'properties.deploymentProperties', 'type': 'EnvironmentDeploymentProperties'},
        'arm_template_display_name': {'key': 'properties.armTemplateDisplayName', 'type': 'str'},
        'resource_group_id': {'key': 'properties.resourceGroupId', 'type': 'str'},
        'created_by_user': {'key': 'properties.createdByUser', 'type': 'str'},
        'provisioning_state': {'key': 'properties.provisioningState', 'type': 'str'},
        'unique_identifier': {'key': 'properties.uniqueIdentifier', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'type': {'key': 'type', 'type': 'str'},
        'location': {'key': 'location', 'type': 'str'},
        'tags': {'key': 'tags', 'type': '{str}'},
    }

    def __init__(self, deployment_properties=None, arm_template_display_name=None, resource_group_id=None, created_by_user=None, provisioning_state=None, unique_identifier=None, id=None, name=None, type=None, location=None, tags=None):
        self.deployment_properties = deployment_properties
        self.arm_template_display_name = arm_template_display_name
        self.resource_group_id = resource_group_id
        self.created_by_user = created_by_user
        self.provisioning_state = provisioning_state
        self.unique_identifier = unique_identifier
        self.id = id
        self.name = name
        self.type = type
        self.location = location
        self.tags = tags
