# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ServiceDefinition(Model):
    """ServiceDefinition.

    :param description:
    :type description: str
    :param display_name:
    :type display_name: str
    :param identifier:
    :type identifier: str
    :param inherit_level:
    :type inherit_level: object
    :param location_mappings:
    :type location_mappings: list of :class:`LocationMapping <locations.v4_1.models.LocationMapping>`
    :param max_version: Maximum api version that this resource supports (current server version for this resource). Copied from <c>ApiResourceLocation</c>.
    :type max_version: str
    :param min_version: Minimum api version that this resource supports. Copied from <c>ApiResourceLocation</c>.
    :type min_version: str
    :param parent_identifier:
    :type parent_identifier: str
    :param parent_service_type:
    :type parent_service_type: str
    :param properties:
    :type properties: :class:`object <locations.v4_1.models.object>`
    :param relative_path:
    :type relative_path: str
    :param relative_to_setting:
    :type relative_to_setting: object
    :param released_version: The latest version of this resource location that is in "Release" (non-preview) mode. Copied from <c>ApiResourceLocation</c>.
    :type released_version: str
    :param resource_version: The current resource version supported by this resource location. Copied from <c>ApiResourceLocation</c>.
    :type resource_version: int
    :param service_owner: The service which owns this definition e.g. TFS, ELS, etc.
    :type service_owner: str
    :param service_type:
    :type service_type: str
    :param status:
    :type status: object
    :param tool_id:
    :type tool_id: str
    """

    _attribute_map = {
        'description': {'key': 'description', 'type': 'str'},
        'display_name': {'key': 'displayName', 'type': 'str'},
        'identifier': {'key': 'identifier', 'type': 'str'},
        'inherit_level': {'key': 'inheritLevel', 'type': 'object'},
        'location_mappings': {'key': 'locationMappings', 'type': '[LocationMapping]'},
        'max_version': {'key': 'maxVersion', 'type': 'str'},
        'min_version': {'key': 'minVersion', 'type': 'str'},
        'parent_identifier': {'key': 'parentIdentifier', 'type': 'str'},
        'parent_service_type': {'key': 'parentServiceType', 'type': 'str'},
        'properties': {'key': 'properties', 'type': 'object'},
        'relative_path': {'key': 'relativePath', 'type': 'str'},
        'relative_to_setting': {'key': 'relativeToSetting', 'type': 'object'},
        'released_version': {'key': 'releasedVersion', 'type': 'str'},
        'resource_version': {'key': 'resourceVersion', 'type': 'int'},
        'service_owner': {'key': 'serviceOwner', 'type': 'str'},
        'service_type': {'key': 'serviceType', 'type': 'str'},
        'status': {'key': 'status', 'type': 'object'},
        'tool_id': {'key': 'toolId', 'type': 'str'}
    }

    def __init__(self, description=None, display_name=None, identifier=None, inherit_level=None, location_mappings=None, max_version=None, min_version=None, parent_identifier=None, parent_service_type=None, properties=None, relative_path=None, relative_to_setting=None, released_version=None, resource_version=None, service_owner=None, service_type=None, status=None, tool_id=None):
        super(ServiceDefinition, self).__init__()
        self.description = description
        self.display_name = display_name
        self.identifier = identifier
        self.inherit_level = inherit_level
        self.location_mappings = location_mappings
        self.max_version = max_version
        self.min_version = min_version
        self.parent_identifier = parent_identifier
        self.parent_service_type = parent_service_type
        self.properties = properties
        self.relative_path = relative_path
        self.relative_to_setting = relative_to_setting
        self.released_version = released_version
        self.resource_version = resource_version
        self.service_owner = service_owner
        self.service_type = service_type
        self.status = status
        self.tool_id = tool_id
