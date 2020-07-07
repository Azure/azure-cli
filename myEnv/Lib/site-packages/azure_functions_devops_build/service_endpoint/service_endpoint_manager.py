# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import os
try:
    from subprocess import DEVNULL
except ImportError:
    DEVNULL = open(os.devnull, 'w')
from subprocess import check_output, CalledProcessError
import vsts.service_endpoint.v4_1.models as models
from vsts.exceptions import VstsServiceError
from ..base.base_manager import BaseManager
from ..constants import SERVICE_ENDPOINT_DOMAIN
from ..exceptions import RoleAssignmentException


class ServiceEndpointManager(BaseManager):
    """ Manage DevOps service endpoints within projects

    Attributes:
        See BaseManager
    """

    def __init__(self, organization_name="", project_name="", creds=None):
        """Inits ServiceEndpointManager as per BaseManager"""
        super(ServiceEndpointManager, self).__init__(creds, organization_name=organization_name,
                                                     project_name=project_name)

    # Get the details of a service endpoint
    # If endpoint does not exist, return an empty list
    def get_service_endpoints(self, repository_name):
        service_endpoint_name = self._get_service_endpoint_name(repository_name, "pipeline")
        try:
            result = self._service_endpoint_client.get_service_endpoints_by_names(
                self._project_name,
                [service_endpoint_name]
            )
        except VstsServiceError:
            return []
        return result

    # This function requires user permission of Microsoft.Authorization/roleAssignments/write
    # i.e. only the owner of the subscription can use this function
    def create_service_endpoint(self, repository_name):
        """Create a new service endpoint within a project with an associated service principal"""
        project = self._get_project_by_name(self._project_name)

        command = "az account show --o json"
        token_resp = check_output(command, shell=True).decode()
        account = json.loads(token_resp)

        data = {}
        data["subscriptionId"] = account['id']
        data["subscriptionName"] = account['name']
        data["environment"] = "AzureCloud"
        data["scopeLevel"] = "Subscription"

        # The following command requires Microsoft.Authorization/roleAssignments/write permission
        service_principle_name = self._get_service_endpoint_name(repository_name, "pipeline")

        # A service principal name has to include the http/https to be valid
        command = "az ad sp create-for-rbac --o json --name http://" + service_principle_name
        try:
            token_resp = check_output(command, stderr=DEVNULL, shell=True).decode()
        except CalledProcessError:
            raise RoleAssignmentException(command)

        token_resp_dict = json.loads(token_resp)
        auth = models.endpoint_authorization.EndpointAuthorization(
            parameters={
                "tenantid": token_resp_dict['tenant'],
                "serviceprincipalid": token_resp_dict['appId'],
                "authenticationType": "spnKey",
                "serviceprincipalkey": token_resp_dict['password']
            },
            scheme="ServicePrincipal"
        )

        service_endpoint = models.service_endpoint.ServiceEndpoint(
            administrators_group=None,
            authorization=auth,
            data=data,
            name=token_resp_dict['displayName'],
            type="azurerm"
        )
        return self._service_endpoint_client.create_service_endpoint(service_endpoint, project.id)

    def list_service_endpoints(self):
        """List exisiting service endpoints within a project"""
        project = self._get_project_by_name(self._project_name)
        return self._service_endpoint_client.get_service_endpoints(project.id)

    def _get_service_endpoint_name(self, repository_name, service_name):
        return "{domain}/{org}/{proj}/{repo}/{service}".format(
            domain=SERVICE_ENDPOINT_DOMAIN,
            org=self._organization_name,
            proj=self._project_name,
            repo=repository_name,
            service=service_name
        )
