# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# coding: utf-8
# pylint: skip-file
from msrest.serialization import Model


class VirtualNetwork(Model):
    """A virtual network.

    :param allowed_subnets: The allowed subnets of the virtual network.
    :type allowed_subnets: list of :class:`Subnet
     <azure.mgmt.devtestlabs.models.Subnet>`
    :param description: The description of the virtual network.
    :type description: str
    :param external_provider_resource_id: The Microsoft.Network resource
     identifier of the virtual network.
    :type external_provider_resource_id: str
    :param external_subnets: The external subnet properties.
    :type external_subnets: list of :class:`ExternalSubnet
     <azure.mgmt.devtestlabs.models.ExternalSubnet>`
    :param subnet_overrides: The subnet overrides of the virtual network.
    :type subnet_overrides: list of :class:`SubnetOverride
     <azure.mgmt.devtestlabs.models.SubnetOverride>`
    :param created_date: The creation date of the virtual network.
    :type created_date: datetime
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
        'allowed_subnets': {'key': 'properties.allowedSubnets', 'type': '[Subnet]'},
        'description': {'key': 'properties.description', 'type': 'str'},
        'external_provider_resource_id': {'key': 'properties.externalProviderResourceId', 'type': 'str'},
        'external_subnets': {'key': 'properties.externalSubnets', 'type': '[ExternalSubnet]'},
        'subnet_overrides': {'key': 'properties.subnetOverrides', 'type': '[SubnetOverride]'},
        'created_date': {'key': 'properties.createdDate', 'type': 'iso-8601'},
        'provisioning_state': {'key': 'properties.provisioningState', 'type': 'str'},
        'unique_identifier': {'key': 'properties.uniqueIdentifier', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'type': {'key': 'type', 'type': 'str'},
        'location': {'key': 'location', 'type': 'str'},
        'tags': {'key': 'tags', 'type': '{str}'},
    }

    def __init__(self, allowed_subnets=None, description=None, external_provider_resource_id=None, external_subnets=None, subnet_overrides=None, created_date=None, provisioning_state=None, unique_identifier=None, id=None, name=None, type=None, location=None, tags=None):
        self.allowed_subnets = allowed_subnets
        self.description = description
        self.external_provider_resource_id = external_provider_resource_id
        self.external_subnets = external_subnets
        self.subnet_overrides = subnet_overrides
        self.created_date = created_date
        self.provisioning_state = provisioning_state
        self.unique_identifier = unique_identifier
        self.id = id
        self.name = name
        self.type = type
        self.location = location
        self.tags = tags
