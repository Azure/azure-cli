# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import subprocess
import vsts.service_endpoint.v4_1.models as models
from ..base.base_manager import BaseManager


class ServiceEndpointManager(BaseManager):
    """ Manage DevOps service endpoints within projects

    Attributes:
        See BaseManager
    """

    def __init__(self, organization_name="", project_name="", creds=None):
        """Inits ServiceEndpointManager as per BaseManager"""
        super(ServiceEndpointManager, self).__init__(creds, organization_name=organization_name,
                                                     project_name=project_name)

    def create_github_service_endpoint(self, githubname, access_token):
        """ Create a github access token connection """
        project = self._get_project_by_name(self._project_name)

        data = {"AvatarUrl": "https://avatars0.githubusercontent.com/u/20589286?v=4"}

        auth = models.endpoint_authorization.EndpointAuthorization(
            parameters={
                "accessToken": access_token
            },
            scheme="PersonalAccessToken"
        )

        service_endpoint = models.service_endpoint.ServiceEndpoint(
            administrators_group=None,
            authorization=auth,
            data=data,
            name=githubname,
            type="github",
            url="http://github.com"
        )

        return self._service_endpoint_client.create_service_endpoint(service_endpoint, project.id)

    def create_service_endpoint(self, servicePrincipalName):
        """Create a new service endpoint within a project with an associated service principal"""
        project = self._get_project_by_name(self._project_name)

        command = "az account show --o json"
        token_resp = subprocess.check_output(command, shell=True).decode()
        account = json.loads(token_resp)

        data = {}
        data["subscriptionId"] = account['id']
        data["subscriptionName"] = account['name']
        data["environment"] = "AzureCloud"
        data["scopeLevel"] = "Subscription"

        # A service principal name has to include the http to be valid
        servicePrincipalNameHttp = "http://" + servicePrincipalName
        command = "az ad sp create-for-rbac --o json --name " + servicePrincipalNameHttp
        token_resp = subprocess.check_output(command, shell=True).decode()
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
