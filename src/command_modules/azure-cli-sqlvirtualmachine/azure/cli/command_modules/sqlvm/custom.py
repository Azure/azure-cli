# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=C0302
from enum import Enum

from knack.log import get_logger

from azure.cli.core.util import (
    CLIError,
    sdk_no_wait,
)


from ._util import (
    get_sqlvirtualmachine_availability_group_listeners_operations,
    get_sqlvirtualmachine_sql_virtual_machine_groups_operations,
    get_sqlvirtualmachine_sql_virtual_machines_operations
)

from azure.mgmt.sqlvirtualmachine.models import(
    WSFCDomainProfile,
    SqlVirtualMachineGroup
)

def sqlvm_list(
    client,
    resource_group_name=None):
    '''
    Lists sql vms or groups in a resource group or subscription
    '''
    if resource_group_name:
        # List all sql vms or groups in the resource group
        return client.list_by_resource_group(resource_group_name=resource_group_name)

    # List all sql vms or groups in the subscription
    return client.list()


def sqlvm_group_create(client, sql_virtual_machine_group_name, resource_group_name, location, sql_image_offer, sql_image_sku,
                        domain_fqdn, cluster_operator_account, sql_service_account,
                        storage_account_url, storage_account_key, cluster_bootstrap_account=None,
                        file_share_witness_path=None, ou_path=None, tags=None):

    '''
    Creates or Updates a SQL virtual machine group.
    '''
    tags = tags or {}

    # Create the windows server failover cluster domain profile object.
    wsfcDomainProfile = WSFCDomainProfile(domain_fqdn=domain_fqdn,
                                            ou_path=ou_path,
                                            cluster_bootstrap_account=cluster_bootstrap_account,
                                            cluster_operator_account=cluster_operator_account,
                                            sql_service_account=sql_service_account,
                                            file_share_witness_path=file_share_witness_path,
                                            storage_account_url=storage_account_url,
                                            storage_account_primary_key=storage_account_key)

    sqlvmGroupObject= SqlVirtualMachineGroup(sql_image_offer=sql_image_offer,
                                            sql_image_sku=sql_image_sku,
                                            wsfc_domain_profile=wsfcDomainProfile,
                                            location=location,
                                            tags=tags)

    return client.create_or_update(resource_group_name=resource_group_name,
                                    sql_virtual_machine_group_name=sql_virtual_machine_group_name,
                                    parameters=sqlvmGroupObject)


def sqlvm_aglistener_create(client, availability_group_listener_name, sql_virtual_machine_group_name, resource_group_name,
                            availability_group_name, port, ip_address, subnet_resource_id, load_balancer_resource_id, probe_port,
                            sql_virtual_machine_instances, public_ip_address_resource_id=None):
    '''
    Creates or Updates an availability group listener
    '''





