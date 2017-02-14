# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ._util import get_sql_servers_operation

# Creates a firewall rule with special start/end ip address value
# that represents all azure ips.
def firewall_allow_all_azure_ips(
    client,
    server_name,
    resource_group_name):
    
    # Name of the rule that will be created
    rule_name = 'AllowAllAzureIPs'
    
    # Special start/end IP that represents allowing all azure ips
    azure_ip_addr = '0.0.0.0'
    
    return client.create_or_update_firewall_rule(
        resource_group_name=resource_group_name,
        server_name=server_name,
        firewall_rule_name=rule_name,
        start_ip_address=azure_ip_addr,
        end_ip_address=azure_ip_addr)
