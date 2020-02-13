# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import abc

class PrivateEndpointClient(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def list_private_link_resource(self, cmd, resource_group_name, name):
        return

    @abc.abstractmethod
    def approve_private_endpoint_connection(self, cmd, resource_group_name, service_name,
                                            name, approval_description=None):
        return

    @abc.abstractmethod
    def reject_private_endpoint_connection(self, cmd, resource_group_name, service_name,
                                           name, rejection_description=None):
        return

    @abc.abstractmethod
    def remove_private_endpoint_connection(self, cmd, resource_group_name, service_name, name):
        return

    @abc.abstractmethod
    def show_private_endpoint_connection(self, cmd, resource_group_name, service_name, name):
        return
