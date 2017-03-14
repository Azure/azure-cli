# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import os

import azure.cli.core.azlogging as azlogging

logger = azlogging.get_az_logger(__name__)  # pylint: disable=invalid-name


class Project(object):
    """
    Class that deals with project settings
    """

    def __init__(self):
        self.settings_file = os.path.join(
            os.path.expanduser('~'), '.azure', 'projectResource.json')
        if os.path.exists(self.settings_file):
            with open(self.settings_file) as file_object:
                self.settings = json.load(file_object)
        else:
            self.settings = None

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
        # TODO: Actually save/store the values here
        self.settings[property_name] = property_value

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
