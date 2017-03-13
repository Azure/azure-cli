
from azure.mgmt.resource.resources.models import DeploymentProperties
from azure.mgmt.resource.resources import ResourceManagementClient
from azure.cli.core.commands.client_factory import get_mgmt_service_client

import requests
import random
import string
import utils


class DeployableResource(object):
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

        template_json = self._get_template_json(template_url)
        properties = DeploymentProperties(template=template_json, template_link=None,
                                          parameters=parameters, mode='incremental')
        client = self._get_resource_mgmt_client()
        deployment = client.deployments.create_or_update(
            self.resource_group, self.deployment_name, properties)
        deployment.add_done_callback(self._deployment_completed)
        return deployment

    def _deployment_completed(self, completed_deployment):
        """
        Called when deployment is completed
        """
        self.completed_deployment = completed_deployment
        print 'Deployment "{}" to resource group "{}" completed.'.format(
            self.deployment_name, self.resource_group)

    def _get_resource_mgmt_client(self):
        """
        Gets the resource management client
        """
        return get_mgmt_service_client(ResourceManagementClient)

    def _get_template_json(self, template_url):
        """
        Gets the ARM template JSON from the provided URL
        """
        response = requests.get(template_url)
        response.raise_for_status()
        return response.json()
