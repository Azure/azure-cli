# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import abc
import time
import json
from knack.log import get_logger
from azure.cli.core.util import send_raw_request

logger = get_logger(__name__)
RETRY_MAX = 20
RETRY_INTERVAL = 10


class PrivateEndpointClient:
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def list_private_link_resource(self, cmd, resource_group_name, name):
        return

    @abc.abstractmethod
    def approve_private_endpoint_connection(self, cmd, resource_group_name, resource_name,
                                            name, approval_description=None):
        return

    @abc.abstractmethod
    def reject_private_endpoint_connection(self, cmd, resource_group_name, resource_name,
                                           name, rejection_description=None):
        return

    @abc.abstractmethod
    def remove_private_endpoint_connection(self, cmd, resource_group_name, resource_name, name):
        return

    @abc.abstractmethod
    def show_private_endpoint_connection(self, cmd, resource_group_name, resource_name, name):
        return


class GeneralPrivateEndpointClient(PrivateEndpointClient):

    def __init__(self, rp, api_version, support_list, resource_get_api_version=None):
        self.rp = rp
        self.api_version = api_version
        self.support_list = support_list
        # same with api_version or using specific api version to get resource
        self.resource_get_api_version = resource_get_api_version or api_version

    def _update_private_endpoint_connection_status(self, cmd, resource_group_name,
                                                   resource_name, private_endpoint_connection_name,
                                                   is_approved=True, description=None):

        private_endpoint_connection = self.show_private_endpoint_connection(cmd,
                                                                            resource_group_name,
                                                                            resource_name,
                                                                            private_endpoint_connection_name)

        new_status = "Approved" if is_approved else "Rejected"
        private_endpoint_connection['properties']['privateLinkServiceConnectionState']['status'] = new_status
        private_endpoint_connection['properties']['privateLinkServiceConnectionState']['description'] = description

        url = _build_connection_url_endpoint(resource_group_name,
                                             self.rp,
                                             resource_name,
                                             private_endpoint_connection_name,
                                             self.api_version)
        r = send_raw_request(cmd.cli_ctx, 'put', url, body=json.dumps(private_endpoint_connection))
        query_counts = RETRY_MAX
        while query_counts:
            time.sleep(RETRY_INTERVAL)
            query_counts -= 1
            private_endpoint_connection = self.show_private_endpoint_connection(cmd,
                                                                                resource_group_name,
                                                                                resource_name,
                                                                                private_endpoint_connection_name)
            if private_endpoint_connection['properties'].get('provisioningState', None) in ["Succeeded", "Ready"]:
                if private_endpoint_connection['properties'].get(
                        'privateLinkServiceConnectionState', {}).get('status', None) in [new_status]:
                    return private_endpoint_connection
        logger.warning("Cannot query the state of private endpoint connection. "
                       "Please use `az network private-endpoint-connection show` command to check the status.")
        return r.json()

    def list_private_link_resource(self, cmd, resource_group_name, name):
        url = _build_link_resource_url_endpoint(resource_group_name, self.rp, name, self.api_version)
        r = send_raw_request(cmd.cli_ctx, 'get', url)
        try:
            return r.json()['value']
        except KeyError:
            pass
        return r.json()

    def approve_private_endpoint_connection(self, cmd, resource_group_name,
                                            resource_name, name, approval_description=None):
        return self._update_private_endpoint_connection_status(cmd=cmd,
                                                               resource_group_name=resource_group_name,
                                                               resource_name=resource_name,
                                                               private_endpoint_connection_name=name,
                                                               is_approved=True,
                                                               description=approval_description)

    def reject_private_endpoint_connection(self, cmd, resource_group_name,
                                           resource_name, name, rejection_description=None):
        return self._update_private_endpoint_connection_status(cmd=cmd,
                                                               resource_group_name=resource_group_name,
                                                               resource_name=resource_name,
                                                               private_endpoint_connection_name=name,
                                                               is_approved=False,
                                                               description=rejection_description)

    def remove_private_endpoint_connection(self, cmd, resource_group_name, resource_name, name):
        url = _build_connection_url_endpoint(resource_group_name, self.rp, resource_name, name, self.api_version)
        r = send_raw_request(cmd.cli_ctx, 'delete', url)
        if r.status_code in [201, 202, 204]:
            logger.warning('Deleting operation is asynchronous. '
                           'Please use `az network private-endpoint-connection show to query the status.')

    def show_private_endpoint_connection(self, cmd, resource_group_name, resource_name, name):
        url = _build_connection_url_endpoint(resource_group_name, self.rp, resource_name, name, self.api_version)
        r = send_raw_request(cmd.cli_ctx, 'get', url)
        return r.json()

    def list_private_endpoint_connection(self, cmd, resource_group_name, resource_name):
        if self.support_list:
            url = _build_connections_url_endpoint(resource_group_name, self.rp, resource_name, self.api_version)
            r = send_raw_request(cmd.cli_ctx, 'get', url)
            try:
                return r.json()['value']
            except KeyError:
                pass
            return r.json()
        url = _build_resource_url_endpoint(resource_group_name, self.rp, resource_name, self.resource_get_api_version)
        r = send_raw_request(cmd.cli_ctx, 'get', url)
        return r.json()['properties']['privateEndpointConnections']


def _build_connection_url_endpoint(resource_group_name, namespace_type, resource_name, name, api_version):
    connection_url_endpoint = "/subscriptions/{{subscriptionId}}/" \
                              "resourceGroups/{resource_group_name}/" \
                              "providers/{namespace_type}/" \
                              "{resource_name}/privateEndpointConnections/" \
                              "{name}?api-version={api_version}".format(resource_group_name=resource_group_name,
                                                                        namespace_type=namespace_type,
                                                                        resource_name=resource_name,
                                                                        name=name,
                                                                        api_version=api_version)
    return connection_url_endpoint


def _build_link_resource_url_endpoint(resource_group_name, namespace_type, resource_name, api_version):
    link_resource_url_endpoint = "/subscriptions/{{subscriptionId}}/" \
                                 "resourceGroups/{resource_group_name}/" \
                                 "providers/{namespace_type}/" \
                                 "{resource_name}/privateLinkResources" \
                                 "?api-version={api_version}".format(resource_group_name=resource_group_name,
                                                                     namespace_type=namespace_type,
                                                                     resource_name=resource_name,
                                                                     api_version=api_version)
    return link_resource_url_endpoint


def _build_connections_url_endpoint(resource_group_name, namespace_type, resource_name, api_version):
    connections_url_endpoint = "/subscriptions/{{subscriptionId}}/" \
                               "resourceGroups/{resource_group_name}/" \
                               "providers/{namespace_type}/" \
                               "{resource_name}/privateEndpointConnections" \
                               "?api-version={api_version}".format(resource_group_name=resource_group_name,
                                                                   namespace_type=namespace_type,
                                                                   resource_name=resource_name,
                                                                   api_version=api_version)
    return connections_url_endpoint


def _build_resource_url_endpoint(resource_group_name, namespace_type, resource_name, api_version):
    resource_url_endpoint = "/subscriptions/{{subscriptionId}}/" \
                            "resourceGroups/{resource_group_name}/" \
                            "providers/{namespace_type}/" \
                            "{resource_name}" \
                            "?api-version={api_version}".format(resource_group_name=resource_group_name,
                                                                namespace_type=namespace_type,
                                                                resource_name=resource_name,
                                                                api_version=api_version)
    return resource_url_endpoint
