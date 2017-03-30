# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import os

import azure.cli.core.azlogging as azlogging
from azure.cli.core._environment import get_config_dir

logger = azlogging.get_az_logger(__name__)  # pylint: disable=invalid-name


class Project(object):
    """
    Class that deals with project settings
    """
    settings_file = os.path.join(get_config_dir(), 'projectResource.json')

    def __init__(self):
        if os.path.exists(self.settings_file):
            with open(self.settings_file) as file_object:
                try:
                    self.settings = json.load(file_object)
                except ValueError:
                    pass
        else:
            self.settings = {}
            self._save_changes()

    def _get_property_value(self, property_name):
        """
        Reads the property value from underlying storage
        """
        if property_name in self.settings:
            return self.settings[property_name]
        return None

    def _set_property_value(self, property_name, property_value):
        """
        Sets the property value and saves it to the underlying storage
        """
        self.settings[property_name] = property_value
        self._save_changes()

    def _save_changes(self):
        """
        Saves the changes to the underlying storage
        """
        with open(self.settings_file, 'w+') as file_object:
            file_object.write(json.dumps(self.settings))

    @property
    def resource_group(self):
        """
        Gets the resource group
        """
        return self._get_property_value('resource_group')

    @resource_group.setter
    def resource_group(self, value):
        """
        Sets the resource group
        """
        self._set_property_value('resource_group', value)

    @property
    def cluster_name(self):
        """
        Gets the cluster name
        """
        return self._get_property_value('cluster_name')

    @cluster_name.setter
    def cluster_name(self, value):
        """
        Sets the cluster name
        """
        self._set_property_value('cluster_name', value)

    @property
    def cluster_resource_group(self):
        """
        Gets the cluster resource group name
        """
        return self._get_property_value('cluster_resource_group')

    @cluster_resource_group.setter
    def cluster_resource_group(self, value):
        """
        Sets the cluster resoure group name
        """
        self._set_property_value('cluster_resource_group', value)

    @property
    def client_id(self):
        """
        Gets the service principal client id
        """
        return self._get_property_value('client_id')

    @client_id.setter
    def client_id(self, value):
        """
        Sets the service principal client id
        """
        self._set_property_value('client_id', value)

    @property
    def client_secret(self):
        """
        Gets the service principal secret
        """
        return self._get_property_value('client_secret')

    @client_secret.setter
    def client_secret(self, value):
        """
        Sets the service principal secret
        """
        self._set_property_value('client_secret', value)

    @property
    def admin_username(self):
        """
        Gets the admin username
        """
        return self._get_property_value('admin_username')

    @admin_username.setter
    def admin_username(self, value):
        """
        Sets the admin username
        """
        self._set_property_value('admin_username', value)

    @property
    def container_registry_url(self):
        """
        Gets the container registry URL
        """
        return self._get_property_value('container_registry_url')

    @container_registry_url.setter
    def container_registry_url(self, value):
        """
        Sets the container registry URL
        """
        self._set_property_value('container_registry_url', value)

    @property
    def project_name(self):
        """
        Gets the project name
        """
        return self._get_property_value('project_name')

    @project_name.setter
    def project_name(self, value):
        """
        Sets the project name
        """
        self._set_property_value('project_name', value)

    @property
    def location(self):
        """
        Gets the location
        """
        return self._get_property_value('location')

    @location.setter
    def location(self, value):
        """
        Sets the location
        """
        self._set_property_value('location', value)

    @property
    def jenkins_hostname(self):
        """
        Gets the Jenkins host name
        """
        return self._get_property_value('jenkins_hostname')

    @jenkins_hostname.setter
    def jenkins_hostname(self, value):
        """
        Sets the Jenkins host name
        """
        self._set_property_value('jenkins_hostname', value)

    @property
    def ssh_private_key(self):
        """
        Gets the SSH private key path
        """
        return self._get_property_value('ssh_private_key')

    @ssh_private_key.setter
    def ssh_private_key(self, value):
        """
        Sets the SSH private key path
        """
        self._set_property_value('ssh_private_key', value)

    def set_ci_pipeline_name(self, ci_pipeline_name, git_url, service_folder):
        """
        Sets the CI pipeline name for a git_url
        """
        ci_pipelines = []
        if 'ci_pipelines' in self.settings:
            ci_pipelines = self.settings['ci_pipelines']

        ci_pipelines.append(
            {git_url: {'pipeline': ci_pipeline_name, 'folder': service_folder}})
        self.settings['ci_pipelines'] = ci_pipelines
        self._save_changes()

    def get_ci_pipeline_name(self, git_url, service_folder):
        """
        Gets the name of the CI pipeline for a git_url
        """
        ci_pipelines = self._get_property_value('ci_pipelines')
        for entry in ci_pipelines:
            if git_url in entry:
                if ci_pipelines[git_url]['folder'] == service_folder:
                    return ci_pipelines[git_url]['pipeline']
        return None

    def set_cd_pipeline_name(self, cd_pipeline_name, git_url, service_folder):
        """
        Sets the CD pipeline name for a git_url
        """
        cd_pipelines = []
        if 'cd_pipelines' in self.settings:
            cd_pipelines = self.settings['cd_pipelines']

        cd_pipelines.append(
            {git_url: {'pipeline': cd_pipeline_name, 'folder': service_folder}})
        self.settings['cd_pipelines'] = cd_pipelines
        self._save_changes()

    def get_cd_pipeline_name(self, git_url, service_folder):
        """
        Gets the name of the CD pipeline for a git_url
        """
        cd_pipelines = self._get_property_value('cd_pipelines')
        for entry in cd_pipelines:
            if git_url in entry:
                if cd_pipelines[git_url]['folder'] == service_folder:
                    return cd_pipelines[git_url]['pipeline']
        return None
