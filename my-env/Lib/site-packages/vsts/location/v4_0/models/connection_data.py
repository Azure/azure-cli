# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ConnectionData(Model):
    """ConnectionData.

    :param authenticated_user: The Id of the authenticated user who made this request. More information about the user can be obtained by passing this Id to the Identity service
    :type authenticated_user: :class:`Identity <locations.v4_0.models.Identity>`
    :param authorized_user: The Id of the authorized user who made this request. More information about the user can be obtained by passing this Id to the Identity service
    :type authorized_user: :class:`Identity <locations.v4_0.models.Identity>`
    :param deployment_id: The id for the server.
    :type deployment_id: str
    :param instance_id: The instance id for this host.
    :type instance_id: str
    :param last_user_access: The last user access for this instance.  Null if not requested specifically.
    :type last_user_access: datetime
    :param location_service_data: Data that the location service holds.
    :type location_service_data: :class:`LocationServiceData <locations.v4_0.models.LocationServiceData>`
    :param web_application_relative_directory: The virtual directory of the host we are talking to.
    :type web_application_relative_directory: str
    """

    _attribute_map = {
        'authenticated_user': {'key': 'authenticatedUser', 'type': 'Identity'},
        'authorized_user': {'key': 'authorizedUser', 'type': 'Identity'},
        'deployment_id': {'key': 'deploymentId', 'type': 'str'},
        'instance_id': {'key': 'instanceId', 'type': 'str'},
        'last_user_access': {'key': 'lastUserAccess', 'type': 'iso-8601'},
        'location_service_data': {'key': 'locationServiceData', 'type': 'LocationServiceData'},
        'web_application_relative_directory': {'key': 'webApplicationRelativeDirectory', 'type': 'str'}
    }

    def __init__(self, authenticated_user=None, authorized_user=None, deployment_id=None, instance_id=None, last_user_access=None, location_service_data=None, web_application_relative_directory=None):
        super(ConnectionData, self).__init__()
        self.authenticated_user = authenticated_user
        self.authorized_user = authorized_user
        self.deployment_id = deployment_id
        self.instance_id = instance_id
        self.last_user_access = last_user_access
        self.location_service_data = location_service_data
        self.web_application_relative_directory = web_application_relative_directory
