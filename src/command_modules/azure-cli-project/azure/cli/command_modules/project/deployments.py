# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import requests

import azure.cli.command_modules.project.utils as utils
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.mgmt.resource.resources import ResourceManagementClient
from azure.mgmt.resource.resources.models import DeploymentProperties


# pylint: disable=too-few-public-methods
class DeployableResource(object):
    """
    Class represents a resource, that's deployable to Azure
    using ARM
    """
    completed_deployment = None

    def __init__(self, resource_group, deployment_name=None):
        self.resource_group = resource_group
        if not deployment_name:
            self.deployment_name = resource_group + utils.get_random_string()
        else:
            self.deployment_name = deployment_name

    def deploy_template(self, template_url, parameters):
        """
        Deploys an ARM template from the provided_url
        using provided parameters to the resource group
        """
        if not template_url:
            raise ValueError('ARM template URL not provided')

        template_json = DeployableResource._get_template_json(template_url)
        properties = DeploymentProperties(template=template_json, template_link=None,
                                          parameters=parameters, mode='incremental')
        client = DeployableResource._get_resource_mgmt_client()
        deployment = client.deployments.create_or_update(
            self.resource_group, self.deployment_name, properties)
        return deployment

    @staticmethod
    def _get_resource_mgmt_client():
        """
        Gets the resource management client
        """
        return get_mgmt_service_client(ResourceManagementClient)

    @staticmethod
    def _get_template_json(template_url):
        """
        Gets the ARM template JSON from the provided URL
        """
        response = requests.get(template_url)
        response.raise_for_status()
        return response.json()
