# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long,too-many-lines

from azure.cli.core.util import CLIError
from azure.cli.core.commands import LongRunningOperation
from azure.core.exceptions import HttpResponseError
from azure.cli.command_modules.servicefabric._sf_utils import (
    _get_resource_group_by_name,
    _create_resource_group_name
)
from azure.mgmt.servicefabricmanagedclusters.models import (
    NetworkSecurityRule,
    ManagedCluster,
    Sku,
    ClientCertificate
)

from azure.cli.command_modules.servicefabric._sf_utils import (
    update_in_collection,
    find_in_collection
)

from knack.log import get_logger

from .._client_factory import (resource_client_factory)

logger = get_logger(__name__)


# pylint:disable=too-many-locals
def create_cluster(cmd,
                   client,
                   resource_group_name,
                   cluster_name,
                   admin_password,
                   admin_user_name=None,
                   dns_name=None,
                   location=None,
                   sku=None,
                   client_connection_port=None,
                   gateway_connection_port=None,
                   client_cert_is_admin=None,
                   client_cert_thumbprint=None,
                   client_cert_common_name=None,
                   client_cert_issuer_thumbprint=None,
                   upgrade_mode=None,
                   upgrade_cadence=None,
                   code_version=None,
                   tags=None):
    try:

        rg = _get_resource_group_by_name(cmd.cli_ctx, resource_group_name)
        if rg is None:
            rg = _create_resource_group_name(cmd.cli_ctx, resource_group_name, location)

        #  set defult parameters
        if location is None:
            location = rg.location

        if dns_name is None:
            dns_name = cluster_name

        if admin_user_name is None:
            admin_user_name = 'vmadmin'

        if sku is None:
            sku = 'Basic'
        skuObj = Sku(name=sku)

        if client_connection_port is None:
            client_connection_port = 19000

        if gateway_connection_port is None:
            gateway_connection_port = 19080

        client_certs = None
        if client_cert_thumbprint is not None or client_cert_common_name is not None:
            client_certs = []

        if client_cert_thumbprint is not None:
            client_certs.append(ClientCertificate(is_admin=client_cert_is_admin, thumbprint=client_cert_thumbprint))
        elif client_cert_common_name is not None:
            if client_cert_issuer_thumbprint is not None:
                client_cert_issuer_thumbprint = ','.join(client_cert_issuer_thumbprint)
            client_certs.append(ClientCertificate(is_admin=client_cert_is_admin, common_name=client_cert_common_name, issuer_thumbprint=client_cert_issuer_thumbprint))

        new_cluster = ManagedCluster(location=location,
                                     dns_name=dns_name,
                                     admin_user_name=admin_user_name,
                                     admin_password=admin_password,
                                     sku=skuObj,
                                     client_connection_port=client_connection_port,
                                     http_gateway_connection_port=gateway_connection_port,
                                     clients=client_certs,
                                     cluster_upgrade_mode=upgrade_mode,
                                     cluster_upgrade_cadence=upgrade_cadence,
                                     cluster_code_version=code_version,
                                     tags=tags)

        logger.info("Creating managed cluster '%s'", cluster_name)
        poller = client.managed_clusters.begin_create_or_update(resource_group_name, cluster_name, new_cluster)
        cluster = LongRunningOperation(cmd.cli_ctx)(poller)
        return cluster
    except HttpResponseError as ex:
        logger.error("HttpResponseError: %s", ex)
        raise


def update_cluster(cmd,
                   client,
                   resource_group_name,
                   cluster_name,
                   client_connection_port=None,
                   gateway_connection_port=None,
                   dns_name=None,
                   tags=None):
    try:
        cluster = client.managed_clusters.get(resource_group_name, cluster_name)

        if client_connection_port is not None:
            cluster.client_connection_port = client_connection_port
        if gateway_connection_port is not None:
            cluster.http_gateway_connection_port = gateway_connection_port
        if dns_name is not None:
            cluster.dns_name = dns_name
        if tags is not None:
            cluster.tags = tags

        if not cluster.public_ip_prefix_id:
            cluster.public_ip_prefix_id = None

        if not cluster.public_i_pv6_prefix_id:
            cluster.public_i_pv6_prefix_id = None

        poller = client.managed_clusters.begin_create_or_update(resource_group_name, cluster_name, cluster)
        return LongRunningOperation(cmd.cli_ctx)(poller)
    except HttpResponseError as ex:
        logger.error("HttpResponseError: %s", ex)
        raise


def add_client_cert(cmd,
                    client,
                    resource_group_name,
                    cluster_name,
                    thumbprint=None,
                    common_name=None,
                    issuer_thumbprint=None,
                    is_admin=False):
    try:
        cluster = client.managed_clusters.get(resource_group_name, cluster_name)

        if cluster.clients is None:
            cluster.clients = []

        if thumbprint is not None:
            cluster.clients.append(ClientCertificate(is_admin=is_admin, thumbprint=thumbprint))
        elif common_name is not None:
            if issuer_thumbprint is not None:
                issuer_thumbprint = ','.join(issuer_thumbprint)
            cluster.clients.append(ClientCertificate(is_admin=is_admin, common_name=common_name, issuer_thumbprint=issuer_thumbprint))
        else:
            raise CLIError("Thumbprint and Common name are empty")

        if not cluster.public_ip_prefix_id:
            cluster.public_ip_prefix_id = None

        if not cluster.public_i_pv6_prefix_id:
            cluster.public_i_pv6_prefix_id = None

        poller = client.managed_clusters.begin_create_or_update(resource_group_name, cluster_name, cluster)
        return LongRunningOperation(cmd.cli_ctx)(poller)
    except HttpResponseError as ex:
        logger.error("HttpResponseError: %s", ex)
        raise


def delete_client_cert(cmd,
                       client,
                       resource_group_name,
                       cluster_name,
                       thumbprint=None,
                       common_name=None):
    try:
        cluster = client.managed_clusters.get(resource_group_name, cluster_name)

        if not cluster.public_ip_prefix_id:
            cluster.public_ip_prefix_id = None

        if not cluster.public_i_pv6_prefix_id:
            cluster.public_i_pv6_prefix_id = None

        if cluster.clients is not None:
            initial_size = len(cluster.clients)
            if thumbprint is not None:
                thumbprint = [x.lower() for x in thumbprint]
                cluster.clients = [cert for cert in cluster.clients if cert.thumbprint.lower() not in thumbprint]
            if common_name is not None:
                common_name = [x.lower() for x in common_name]
                cluster.clients = [cert for cert in cluster.clients if cert.common_name.lower() not in common_name]

            if initial_size > len(cluster.clients):
                poller = client.managed_clusters.begin_create_or_update(resource_group_name, cluster_name, cluster)
                return LongRunningOperation(cmd.cli_ctx)(poller)
        return cluster
    except HttpResponseError as ex:
        logger.error("HttpResponseError: %s", ex)
        raise


def list_clusters(client,
                  resource_group_name=None):
    try:
        if resource_group_name is None:
            logger.info("Getting managed clusters by subscription")
            return client.managed_clusters.list_by_subscription()

        logger.info("Getting managed clusters by resource group '%s'", resource_group_name)
        return client.managed_clusters.list_by_resource_group(resource_group_name)
    except HttpResponseError as ex:
        logger.error("HttpResponseError: %s", ex)
        raise


def _get_resource_group_location(cli_ctx, resource_group_name):
    resource_client = resource_client_factory(cli_ctx).resource_groups
    rg = resource_client.get(resource_group_name)
    return rg.location


def add_network_security_rule(cmd,
                              client,
                              resource_group_name,
                              cluster_name,
                              name=None,
                              access=None,
                              description=None,
                              direction=None,
                              protocol=None,
                              priority=None,
                              source_port_ranges=None,
                              dest_port_ranges=None,
                              source_port_range=None,
                              dest_port_range=None,
                              dest_addr_prefixes=None,
                              source_addr_prefixes=None,
                              dest_addr_prefix=None,
                              source_addr_prefix=None):
    try:
        cluster = client.managed_clusters.get(resource_group_name, cluster_name)

        if cluster.network_security_rules is None:
            cluster.network_security_rules = []

        new_network_securityRule = NetworkSecurityRule(name=name,
                                                       access=access,
                                                       description=description,
                                                       direction=direction,
                                                       protocol='*' if protocol == 'any' else protocol,
                                                       priority=priority,
                                                       source_port_ranges=source_port_ranges,
                                                       destination_port_ranges=dest_port_ranges,
                                                       source_port_range=source_port_range,
                                                       destination_port_range=dest_port_range,
                                                       destination_address_prefixes=dest_addr_prefixes,
                                                       source_address_prefixes=source_addr_prefixes,
                                                       destination_address_prefix=dest_addr_prefix,
                                                       source_address_prefix=source_addr_prefix)

        cluster.network_security_rules.append(new_network_securityRule)

        if not cluster.public_ip_prefix_id:
            cluster.public_ip_prefix_id = None

        if not cluster.public_i_pv6_prefix_id:
            cluster.public_i_pv6_prefix_id = None

        poller = client.managed_clusters.begin_create_or_update(resource_group_name, cluster_name, cluster)
        return LongRunningOperation(cmd.cli_ctx)(poller)
    except HttpResponseError as ex:
        logger.error("HttpResponseError: %s", ex)
        raise


def update_network_security_rule(cmd,
                                 client,
                                 resource_group_name,
                                 cluster_name,
                                 name,
                                 access=None,
                                 description=None,
                                 direction=None,
                                 protocol=None,
                                 priority=None,
                                 source_port_ranges=None,
                                 dest_port_ranges=None,
                                 dest_addr_prefixes=None,
                                 source_addr_prefixes=None):
    try:
        cluster = client.managed_clusters.get(resource_group_name, cluster_name)

        existing_nsg = find_in_collection(cluster, 'network_security_rules', 'name', name)
        if existing_nsg is None:
            logger.error('NSG %s does not exist.', name)
            return None

        if protocol == 'any':
            protocol_val = '*'
        elif protocol is not None:
            protocol_val = protocol
        else:
            protocol_val = existing_nsg.protocol

        updated_network_securityRule = NetworkSecurityRule(name=name,
                                                           access=access if access is not None else existing_nsg.access,
                                                           description=description if description is not None else existing_nsg.description,
                                                           direction=direction if direction is not None else existing_nsg.direction,
                                                           protocol=protocol_val,
                                                           priority=priority if priority is not None else existing_nsg.priority,
                                                           source_port_ranges=source_port_ranges if source_port_ranges is not None else existing_nsg.source_port_ranges,
                                                           destination_port_ranges=dest_port_ranges if dest_port_ranges is not None else existing_nsg.destination_port_ranges,
                                                           destination_address_prefixes=dest_addr_prefixes if dest_addr_prefixes is not None else existing_nsg.destination_address_prefixes,
                                                           source_address_prefixes=source_addr_prefixes if source_addr_prefixes is not None else existing_nsg.source_address_prefixes)

        if not cluster.public_ip_prefix_id:
            cluster.public_ip_prefix_id = None

        if not cluster.public_i_pv6_prefix_id:
            cluster.public_i_pv6_prefix_id = None

        update_in_collection(cluster, 'network_security_rules', updated_network_securityRule, 'name')

        poller = client.managed_clusters.begin_create_or_update(resource_group_name, cluster_name, cluster)
        return LongRunningOperation(cmd.cli_ctx)(poller)
    except HttpResponseError as ex:
        logger.error("HttpResponseError: %s", ex)
        raise


def get_network_security_rule(client,
                              resource_group_name,
                              cluster_name,
                              name):
    try:
        cluster = client.managed_clusters.get(resource_group_name, cluster_name)
        nsg = find_in_collection(cluster, 'network_security_rules', 'name', name)

        if nsg is None:
            raise 'NSG with name {} not found'.format(name)

        return nsg

    except HttpResponseError as ex:
        logger.error("HttpResponseError: %s", ex)
        raise


def list_network_security_rules(client,
                                resource_group_name,
                                cluster_name):
    try:
        cluster = client.managed_clusters.get(resource_group_name, cluster_name)
        return cluster.network_security_rules

    except HttpResponseError as ex:
        logger.error("HttpResponseError: %s", ex)
        raise


def delete_network_security_rule(cmd,
                                 client,
                                 resource_group_name,
                                 cluster_name,
                                 name):
    try:
        cluster = client.managed_clusters.get(resource_group_name, cluster_name)

        if not cluster.public_ip_prefix_id:
            cluster.public_ip_prefix_id = None

        if not cluster.public_i_pv6_prefix_id:
            cluster.public_i_pv6_prefix_id = None

        if cluster.network_security_rules is not None:
            initial_size = len(cluster.network_security_rules)
            if name is not None:
                cluster.network_security_rules = [nsg for nsg in cluster.network_security_rules if nsg.name != name]

            if initial_size > len(cluster.network_security_rules):
                poller = client.managed_clusters.begin_create_or_update(resource_group_name, cluster_name, cluster)
                return LongRunningOperation(cmd.cli_ctx)(poller)

            raise 'NSG with name {} not found'.format(name)

        return cluster
    except HttpResponseError as ex:
        logger.error("HttpResponseError: %s", ex)
        raise
