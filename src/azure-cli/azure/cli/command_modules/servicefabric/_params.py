# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
import argparse

from azure.cli.command_modules.servicefabric._validators import (
    validate_create_application, validate_create_managed_application,
    validate_create_managed_cluster, validate_create_managed_service,
    validate_create_service, validate_update_application,
    validate_update_managed_application, validate_update_managed_service,
    validate_create_managed_service_correlation, validate_create_managed_service_load_metric,
    validate_update_managed_service_load_metric, validate_update_managed_service_correlation,
    validate_network_security_rule)
from azure.cli.core.commands.parameters import (get_enum_type,
                                                get_three_state_flag,
                                                resource_group_name_type,
                                                tags_type)
from azure.cli.core.commands.validators import get_default_location_from_resource_group
from azure.cli.core.util import CLIError, get_json_object
from azure.mgmt.servicefabricmanagedclusters.models import (FailureAction,
                                                            MoveCost,
                                                            PartitionScheme,
                                                            RollingUpgradeMode,
                                                            ServiceKind,
                                                            DiskType,
                                                            ClusterUpgradeMode,
                                                            ClusterUpgradeCadence)
from knack.arguments import CLIArgumentType


def load_arguments(self, _):  # pylint: disable=too-many-statements
    # PARAMETER REGISTRATION
    application_parameters = CLIArgumentType(
        options_list=['--parameters', '--application-parameters'],
        action=AddAppParamsAction,
        nargs='+',
        help='Specify the application parameters as key/value pairs. These parameters must exist in the application manifest. '
        'for example: --application-parameters param1=value1 param2=value2')

    minimum_nodes = CLIArgumentType(
        options_list=['--min-nodes', '--minimum-nodes'],
        help='Specify the minimum number of nodes where Service Fabric will reserve capacity for this application, '
        'this does not mean that the application is guaranteed to have replicas on all those nodes. The value of this parameter must be a non-negative integer. '
        'Default value for this is zero, which means no capacity is reserved for the application.')

    maximum_nodes = CLIArgumentType(
        options_list=['--max-nodes', '--maximum-nodes'],
        help='Specify the maximum number of nodes on which to place an application. '
        'The value of this parameter must be a non-negative integer. The default value is 0, which indicates the application can be placed on any number of nodes in the cluster.')

    application_type_version = CLIArgumentType(
        options_list=['--version', '--application-type-version'],
        help='Specify the application type version.')

    package_url = CLIArgumentType(
        help='Specify the url of the application package sfpkg file.')

    with self.argument_context('sf') as c:
        c.argument('resource_group_name', arg_type=resource_group_name_type, id_part=None, help='Specify the resource group name. You can configure the default group using `az configure --defaults group=<name>`')
        c.argument('cluster_name', options_list=['--cluster-name', '-c'], help='Specify the name of the cluster, if not given it will be same as resource group name')
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('secret_identifier', help='The existing Azure key vault secret URL')
        c.argument('certificate_file', help='The existing certificate file path for the primary cluster certificate.')
        c.argument('parameter_file', help='The path to the template parameter file.')
        c.argument('template_file', help='The path to the template file.')
        c.argument('vm_password', help='The password of the Vm')
        c.argument('certificate_output_folder', options_list=['--certificate-output-folder', '--cert-out-folder'], help='The folder of the new certificate file to be created.')
        c.argument('certificate_password', help='The password of the certificate file.')
        c.argument('certificate_subject_name', options_list=['--certificate-subject-name', '--cert-subject-name'], help='The subject name of the certificate to be created.')
        c.argument('vault_resource_group_name', options_list=['--vault-rg', c.deprecate(target='--vault-resource-group', redirect='--vault-rg', hide=True)],
                   help='Key vault resource group name, if not given it will be cluster resource group name')
        c.argument('vault_name', help='Azure key vault name, if not given it will be the cluster resource group name')
        c.argument('cluster_size', options_list=['--cluster-size', '-s'], help='The number of nodes in the cluster. Default are 5 nodes')
        c.argument('vm_sku', help='VM Sku')
        c.argument('vm_user_name', help='The user name for logging to Vm. Default will be adminuser')
        c.argument('vm_os', arg_type=get_enum_type(['WindowsServer2012R2Datacenter',
                                                    'WindowsServer2016Datacenter',
                                                    'WindowsServer2016DatacenterwithContainers',
                                                    'UbuntuServer1604',
                                                    'WindowsServer1709',
                                                    'WindowsServer1709withContainers',
                                                    'WindowsServer1803withContainers',
                                                    'WindowsServer1809withContainers',
                                                    'WindowsServer2019Datacenter',
                                                    'WindowsServer2019DatacenterwithContainers']),
                   default='WindowsServer2016Datacenter', options_list=['--vm-os', '--os'],
                   help='The Operating System of the VMs that make up the cluster.')
        c.argument('node_type', help='the Node type name.')

    # cluster
    with self.argument_context('sf cluster list') as c:
        c.argument('resource_group_name', arg_type=resource_group_name_type, id_part=None, help='The resource group name')

    with self.argument_context('sf client certificate') as c:
        c.argument('certificate_common_name', help='client certificate common name.')
        c.argument('admin_client_thumbprints', options_list=['--admin-client-thumbprints', '--admin-client-tps'], nargs='+', help='Space-separated list of client certificate thumbprint that only has admin permission, ')
        c.argument('certificate_issuer_thumbprint', options_list=['--certificate-issuer-thumbprint', '--cert-issuer-tp'], help='client certificate issuer thumbprint.')

    with self.argument_context('sf cluster client-certificate') as c:
        c.argument('is_admin', help='Client authentication type.')
        c.argument('certificate_issuer_thumbprint', options_list=['--certificate-issuer-thumbprint', '--cert-issuer-tp'], help='client certificate issuer thumbprint.')
        c.argument('certificate_common_name', options_list=['--certificate-common-name', '--cert-common-name'], help='client certificate common name.')
        c.argument('admin_client_thumbprints', options_list=['--admin-client-thumbprints', '--admin-client-tps'], nargs='+', help='client certificate thumbprint that only has admin permission.')
        c.argument('readonly_client_thumbprints', options_list=['--readonly-client-thumbprints', '--readonly-client-tps'], nargs='+', help='Space-separated list of client certificate thumbprint that has read only permission.')

    with self.argument_context('sf cluster client-certificate add') as c:
        c.argument('thumbprint', help='client certificate thumbprint.')

    with self.argument_context('sf cluster client-certificate remove') as c:
        c.argument('thumbprints', nargs='+', help='A single or Space-separated list of client certificate thumbprint(s) to be remove.')

    with self.argument_context('sf cluster node') as c:
        c.argument('number_of_nodes_to_add', options_list=['--number-of-nodes-to-add', '--nodes-to-add'], help='number of nodes to add.')
        c.argument('number_of_nodes_to_remove', options_list=['--number-of-nodes-to-remove', '--nodes-to-remove'], help='number of nodes to remove.')

    with self.argument_context('sf cluster node-type') as c:
        c.argument('capacity', help='The capacity tag applied to nodes in the node type. The cluster resource manager uses these tags to understand how much capacity a node has.')
        c.argument('vm_tier', help='VM tier.')

    with self.argument_context('sf cluster') as c:
        c.argument('durability_level', arg_type=get_enum_type(['Bronze', 'Silver', 'Gold']), help='durability level.')

    with self.argument_context('sf cluster setting') as c:
        c.argument('parameter', help='parameter name')
        c.argument('section', help='section name')
        c.argument('value', help='Specify the value')
        c.argument('settings_section_description', options_list=['--settings-section-description', '--settings-section'], help='Specify the value')

    with self.argument_context('sf cluster upgrade-type set') as c:
        c.argument('version', help='cluster code version')
        c.argument('upgrade_mode', arg_type=get_enum_type(['manual', 'automatic']), help='cluster upgrade mode')

    with self.argument_context('sf cluster reliability') as c:
        c.argument('reliability_level', arg_type=get_enum_type(['Bronze', 'Silver', 'Gold', 'Platinum']), help='durability level.')
        c.argument('auto_add_node', help='Add node count automatically when changing reliability.')

    with self.argument_context('sf cluster setting set') as c:
        c.argument('settings_section_description', options_list=['--settings-section-description', '--settings-section'], type=get_json_object,
                   help='JSON encoded parameters configuration. Use @{file} to load from a file. '
                        'For example: [{"section": "NamingService","parameter": "MaxOperationTimeout","value": 1000},{"section": "MaxFileOperationTimeout","parameter": "Max2","value": 1000}]')

    with self.argument_context('sf cluster setting remove') as c:
        c.argument('settings_section_description', options_list=['--settings-section-description', '--settings-section'], type=get_json_object,
                   help='JSON encoded parameters configuration. Use @{file} to load from a file. '
                        'For example: [{"section": "NamingService","parameter": "MaxOperationTimeout"}]')

    with self.argument_context('sf cluster client-certificate remove') as c:
        c.argument('client_certificate_common_names', options_list=['--client-certificate-common-names', '--client-cert-cn'], type=get_json_object,
                   help='JSON encoded parameters configuration. Use @{file} to load from a file. '
                        'For example: [{"certificateCommonName": "test.com","certificateIssuerThumbprint": "22B4AE296B504E512DF880A77A2CAE20200FF922"}]')

    with self.argument_context('sf cluster client-certificate add') as c:
        c.argument('client_certificate_common_names', options_list=['--client-certificate-common-names', '--client-cert-cn'], type=get_json_object,
                   help='JSON encoded parameters configuration. Use @{file} to load from a file. '
                        'For example: [{"isAdmin":true, "certificateCommonName": "test.com", '
                        '"certificateIssuerThumbprint": "22B4AE296B504E512DF880A77A2CAE20200FF922"}]')

    # application-type
    with self.argument_context('sf application-type') as c:
        c.argument('application_type_name', options_list=['--name', '--application-type-name'], help='Specify the application type name.')

    # application-type version
    with self.argument_context('sf application-type version') as c:
        c.argument('version', arg_type=application_type_version)
        c.argument('package_url', arg_type=package_url)

    # application
    with self.argument_context('sf application') as c:
        c.argument('application_name', options_list=['--name', '--application-name'], help='Specify the application name.')

    with self.argument_context('sf application update', validator=validate_update_application) as c:
        c.argument('application_type_version', arg_type=application_type_version)
        c.argument('application_parameters', arg_type=application_parameters)
        c.argument('minimum_nodes', arg_type=minimum_nodes)
        c.argument('maximum_nodes', arg_type=maximum_nodes)
        c.argument('force_restart', arg_type=get_three_state_flag(),
                   help='Indicates that the service host restarts even if the upgrade is a configuration-only change.')
        c.argument('service_type_health_policy_map', options_list=['--service-type-health-policy-map'],
                   help='Specify the map of the health policy to use for different service types as a hash table in the following format: {\"ServiceTypeName\" : \"MaxPercentUnhealthyPartitionsPerService,MaxPercentUnhealthyReplicasPerPartition,MaxPercentUnhealthyServices\"}. For example: @{ \"ServiceTypeName01\" = \"5,10,5\"; \"ServiceTypeName02\" = \"5,5,5\" }')

    with self.argument_context('sf application update', arg_group='Upgrade description') as c:
        c.argument('upgrade_replica_set_check_timeout', options_list=['--replica-check-timeout', '--rep-check-timeout'],
                   help='Specify the maximum time, in seconds, that Service Fabric waits for a service to reconfigure into a safe state, if not already in a safe state, before Service Fabric proceeds with the upgrade.')
        c.argument('failure_action', arg_type=get_enum_type(['Rollback', 'Manual']),
                   help='Specify the action to take if the monitored upgrade fails. The acceptable values for this parameter are Rollback or Manual.')
        c.argument('health_check_retry_timeout', options_list=['--hc-retry-timeout', '--health-check-retry-timeout'],
                   help='Specify the duration, in seconds, after which Service Fabric retries the health check if the previous health check fails.')
        c.argument('health_check_wait_duration', options_list=['--hc-wait-duration', '--health-check-wait-duration'],
                   help='Specify the duration, in seconds, that Service Fabric waits before it performs the initial health check after it finishes the upgrade on the upgrade domain.')
        c.argument('health_check_stable_duration', options_list=['--hc-stable-duration', '--health-check-stable-duration'],
                   help='Specify the duration, in seconds, that Service Fabric waits in order to verify that the application is stable before moving to the next upgrade domain or completing the upgrade. This wait duration prevents undetected changes of health right after the health check is performed.')
        c.argument('upgrade_domain_timeout', options_list=['--ud-timeout', '--upgrade-domain-timeout'],
                   help='Specify the maximum time, in seconds, that Service Fabric takes to upgrade a single upgrade domain. After this period, the upgrade fails.')
        c.argument('upgrade_timeout',
                   help='Specify the maximum time, in seconds, that Service Fabric takes for the entire upgrade. After this period, the upgrade fails.')
        c.argument('consider_warning_as_error', options_list=['--warning-as-error', '--consider-warning-as-error'], arg_type=get_three_state_flag(),
                   help='Indicates whether to treat a warning health event as an error event during health evaluation.')
        c.argument('default_service_type_max_percent_unhealthy_partitions_per_service', options_list=['--max-unhealthy-parts'],
                   help='Specify the maximum percent of unhealthy partitions per service allowed by the health policy for the default service type to use for the monitored upgrade. Allowed values are from 0 to 100.')
        c.argument('default_service_type_max_percent_unhealthy_replicas_per_partition', options_list=['--max-unhealthy-reps'],
                   help='Specify the maximum percent of unhealthy replicas per service allowed by the health policy for the default service type to use for the monitored upgrade. Allowed values are from 0 to 100.')
        c.argument('default_service_type_max_percent_unhealthy_services', options_list=['--max-unhealthy-servs'],
                   help='Specify the maximum percent of unhealthy services allowed by the health policy for the default service type to use for the monitored upgrade. Allowed values are form 0 to 100.')
        c.argument('max_percent_unhealthy_deployed_applications', options_list=['--max-unhealthy-apps'],
                   help='Specify the maximum percentage of the application instances deployed on the nodes in the cluster that have a health state of error before the application health state for the cluster is error. Allowed values are from 0 to 100.')

    with self.argument_context('sf application create', validator=validate_create_application) as c:
        c.argument('application_type_name', options_list=['--type-name', '--application-type-name'], help='Specify the application type name.')
        c.argument('application_type_version', arg_type=application_type_version)
        c.argument('package_url', arg_type=package_url)
        c.argument('application_parameters', arg_type=application_parameters)
        c.argument('minimum_nodes', arg_type=minimum_nodes)
        c.argument('maximum_nodes', arg_type=maximum_nodes)

    # service
    with self.argument_context('sf service') as c:
        c.argument('service_name', options_list=['--name', '--service-name'],
                   help='Specify the name of the service. The application name must be a prefix of the service name, for example: appName~serviceName')

    with self.argument_context('sf service create', validator=validate_create_service) as c:
        c.argument('service_type',
                   help='Specify the service type name of the application, it should exist in the application manifest.')
        c.argument('application_name', options_list=['--application', '--application-name'],
                   help='Specify the name of the service. The application name must be a prefix of the service name, for example: appName~serviceName')
        c.argument('state', arg_type=get_enum_type(['stateless', 'stateful']), help='Specify if the service is stateless or stateful.')
        c.argument('instance_count', help='Specify the instance count for the stateless service. If -1 is used, it means it will run on all the nodes.')
        c.argument('min_replica_set_size', options_list=['--min-replica-set-size', '--min-replica'], help='Specify the min replica set size for the stateful service.')
        c.argument('target_replica_set_size', options_list=['--target-replica-set-size', '--target-replica'], help='Specify the target replica set size for the stateful service.')
        c.argument('default_move_cost', arg_type=get_enum_type(['Zero', 'Low', 'Medium', 'High']),
                   help='Specify the default cost for a move. Higher costs make it less likely that the Cluster Resource Manager will move the replica when trying to balance the cluster.')
        c.argument('partition_scheme', arg_type=get_enum_type(['singleton', 'uniformInt64', 'named']),
                   help='Specify what partition scheme to use. '
                   'Singleton partitions are typically used when the service does not require any additional routing. '
                   'UniformInt64 means that each partition owns a range of int64 keys. '
                   'Named is usually for services with data that can be bucketed, within a bounded set. Some common examples of data fields used as named partition keys would be regions, postal codes, customer groups, or other business boundaries.')

    # managed cluster

    with self.argument_context('sf managed-cluster create', validator=validate_create_managed_cluster) as c:
        c.argument('admin_password', help='Admin password used for the virtual machines.')
        c.argument('admin_user_name', help='Admin user used for the virtual machines.', default='vmadmin')
        c.argument('dns_name', help='Cluster\'s dns name.')
        c.argument('sku', help='Cluster\'s Sku, the options are Basic: it will have a minimum of 3 seed nodes and only allows 1 node type and Standard: it will have a minimum of 5 seed nodes and allows multiple node types.', default='Basic')
        c.argument('client_connection_port', options_list=['--client-connection-port', '--client-port'], help='Port used for client connections to the cluster.', default=19000)
        c.argument('gateway_connection_port', options_list=['--gateway-connection-port', '--gateway-port'], help='Port used for http connections to the cluster.', default=19080)
        c.argument('client_cert_is_admin', options_list=['--client-cert-is-admin', '--cert-is-admin'], arg_type=get_three_state_flag(), help='Client authentication type.')
        c.argument('client_cert_thumbprint', options_list=['--client-cert-thumbprint', '--cert-thumbprint'], help='Client certificate thumbprint.')
        c.argument('client_cert_common_name', options_list=['--client-cert-common-name', '--cert-common-name'], help='Client certificate common name.')
        c.argument('client_cert_issuer_thumbprint', options_list=['--client-cert-issuer-thumbprint', '--cert-issuer-thumbprint', '--cert-issuer-tp'], nargs='+', help='Space-separated list of issuer thumbprints.')
        c.argument('upgrade_mode', arg_type=get_enum_type(ClusterUpgradeMode), options_list=['--cluster-upgrade-mode', '--upgrade-mode'],
                   help='The upgrade mode of the cluster when new Service Fabric runtime version is available '
                   'Automatic: The cluster will be automatically upgraded to the latest Service Fabric runtime version, upgrade_cadence will determine when the upgrade starts after the new version becomes available.'
                   'Manual: The cluster will not be automatically upgraded to the latest Service Fabric runtime version. The cluster is upgraded by setting the code_version property in the cluster resource.')
        c.argument('upgrade_cadence', arg_type=get_enum_type(ClusterUpgradeCadence), options_list=['--cluster-upgrade-cadence', '--upgrade-cadence'],
                   help='The upgrade mode of the cluster when new Service Fabric runtime version is available '
                   'Wave0: Cluster upgrade starts immediately after a new version is rolled out. Recommended for Test/Dev clusters.'
                   'Wave1: Cluster upgrade starts 7 days after a new version is rolled out. Recommended for Pre-prod clusters.'
                   'Wave2: Cluster upgrade starts 14 days after a new version is rolled out. Recommended for Production clusters.')
        c.argument('code_version', options_list=['--cluster-code-version', '--code-version'],
                   help='Cluster service fabric code version. Only use if upgrade mode is Manual.')
        c.argument('tags', arg_type=tags_type)

    with self.argument_context('sf managed-cluster update') as c:
        c.argument('client_connection_port', options_list=['--client-connection-port', '--client-port'], help='Port used for client connections to the cluster.')
        c.argument('gateway_connection_port', options_list=['--gateway-connection-port', '--gateway-port'], help='Port used for http connections to the cluster.')
        c.argument('dns_name', help='Cluster\'s dns name')
        c.argument('tags', arg_type=tags_type)

    with self.argument_context('sf managed-cluster client-certificate add') as c:
        c.argument('is_admin', arg_type=get_three_state_flag(), help='Client authentication type.')
        c.argument('thumbprint', help='Client certificate thumbprint.')
        c.argument('common_name', help='Client certificate common name.')
        c.argument('issuer_thumbprint', nargs='+', help='Space-separated list of issuer thumbprints.')

    with self.argument_context('sf managed-cluster client-certificate delete') as c:
        c.argument('thumbprint', nargs='+', help='A single or Space-separated list of client certificate thumbprint(s) to be remove.')
        c.argument('common_name', nargs='+', help='A single or Space-separated list of client certificate common name(s) to be remove.')

    with self.argument_context('sf managed-cluster network-security-rule', validator=validate_network_security_rule) as c:
        c.argument('name', help='Network security rule name')
        c.argument('access', arg_type=get_enum_type(['allow', 'deny']), help='Allows or denies network traffic')
        c.argument('direction', arg_type=get_enum_type(['inbound', 'outbound']), help='Network security rule direction')
        c.argument('description', help='Network security rule description')
        c.argument('priority', type=int, help='Integer that shows priority for rule')
        c.argument('protocol', arg_type=get_enum_type(['tcp', 'https', 'http', 'udp', 'icmp', 'ah', 'esp', 'any']), help='Network protocol')
        c.argument('source_port_ranges', nargs='+', help='A single or space separated list of source port ranges')
        c.argument('dest_port_ranges', nargs='+', help='A single or space separated list of destination port ranges')
        c.argument('source_port_range', help='The source port or range. Integer or range between 0 and 65535. Asterisk \'*\' can also be used to match all ports.')
        c.argument('dest_port_range', help='The destination port or range. Integer or range between 0 and 65535. Asterisk \'*\' can also be used to match all ports.')
        c.argument('source_addr_prefixes', nargs='+', help='The CIDR or source IP ranges. A single or space separated list of source address prefixes')
        c.argument('dest_addr_prefixes', nargs='+', help='CIDR or destination IP ranges. A single or space separated list of destination address prefixes')
        c.argument('source_addr_prefix', help='The CIDR or source IP range. Asterisk \'*\' can also be used to match all source IPs. Default tags such as \'VirtualNetwork\', \'AzureLoadBalancer\' and \'Internet\' can also be used. If this is an ingress rule, specifies where network traffic originates from.')
        c.argument('dest_addr_prefix', help='The destination address prefix. CIDR or destination IP range. Asterisk \'*\' can also be used to match all source IPs. Default tags such as \'VirtualNetwork\', \'AzureLoadBalancer\' and \'Internet\' can also be used.')

    # managed node type
    capacity = CLIArgumentType(
        options_list=['--capacity'],
        action=AddNodeTypeCapacityAction,
        nargs='+',
        help='Capacity tags applied to the nodes in the node type as key/value pairs, the cluster resource manager uses these tags to understand how much resource a node has. Updating this will override the current values.'
             'for example: --capacity ClientConnections=65536 param2=value2')

    placement_property = CLIArgumentType(
        options_list=['--placement-property'],
        action=AddNodeTypePlacementPropertyAction,
        nargs='+',
        help='Placement tags applied to nodes in the node type as key/value pairs, which can be used to indicate where certain services (workload) should run. Updating this will override the current values.'
             'for example: --placement-property NodeColor=Green SomeProperty=5')

    with self.argument_context('sf managed-node-type') as c:
        c.argument('node_type_name', options_list=['-n', '--name', '--node-type-name'], help='node type name.')

    with self.argument_context('sf managed-node-type create') as c:
        c.argument('instance_count', help='"The number of nodes in the node type.')
        c.argument('primary', arg_type=get_three_state_flag(), help='Specify if the node type is primary. On this node type will run system services. Only one node type should be marked as primary. Primary node type cannot be deleted or changed for existing clusters.')
        c.argument('disk_size', type=int, options_list=['--disk-size', '--data-disk-size'], help='Disk size for each vm in the node type in GBs.', default=100)
        c.argument('disk_type', arg_type=get_enum_type(DiskType), options_list=['--disk-type', '--data-disk-type'],
                   help='Managed data disk type. IOPS and throughput are given by the disk size. To see more information, go to https://learn.microsoft.com/azure/virtual-machines/disks-types. Default: StandardSSD_LRS. '
                   'Standard_LRS: Standard HDD locally redundant storage. Best for backup, non-critical, and infrequent access. '
                   'StandardSSD_LRS: Standard SSD locally redundant storage. Best for web servers, lightly used enterprise applications and dev/test. '
                   'Premium_LRS: Premium SSD locally redundant storage. Best for production and performance sensitive workloads.')
        c.argument('application_start_port', options_list=['--application-start-port', '--app-start-port'], help='Application start port of a range of ports.')
        c.argument('application_end_port', options_list=['--application-end-port', '--app-end-port'], help='Application End port of a range of ports.')
        c.argument('ephemeral_start_port', help='Ephemeral start port of a range of ports.')
        c.argument('ephemeral_end_port', help='Ephemeral end port of a range of ports.')
        c.argument('vm_size', help='The size of virtual machines in the pool. All virtual machines in a pool are the same size.', default='Standard_D2')
        c.argument('vm_image_publisher', help='The publisher of the Azure Virtual Machines Marketplace image.', default='MicrosoftWindowsServer')
        c.argument('vm_image_offer', help='The offer type of the Azure Virtual Machines Marketplace image.', default='WindowsServer')
        c.argument('vm_image_sku', help='The SKU of the Azure Virtual Machines Marketplace image.', default='2019-Datacenter')
        c.argument('vm_image_version', help='The version of the Azure Virtual Machines Marketplace image. ', default='latest')
        c.argument('capacity', arg_type=capacity)
        c.argument('placement_property', arg_type=placement_property)
        c.argument('is_stateless', arg_type=get_three_state_flag(), help='Indicates if the node type can only host Stateless workloads.', default=False)
        c.argument('multiple_placement_groups', options_list=['--multiple-placement-groups', '--multi-place-groups'], arg_type=get_three_state_flag(),
                   help='Indicates if scale set associated with the node type can be composed of multiple placement groups.', default=False)
        c.argument('tags', arg_type=tags_type)

    with self.argument_context('sf managed-node-type update') as c:
        c.argument('instance_count', help='"The number of nodes in the node type.')
        c.argument('application_start_port', options_list=['--application-start-port', '--app-start-port'], help='Application start port of a range of ports.')
        c.argument('application_end_port', options_list=['--application-end-port', '--app-end-port'], help='Application End port of a range of ports.')
        c.argument('ephemeral_start_port', help='Ephemeral start port of a range of ports.')
        c.argument('ephemeral_end_port', help='Ephemeral end port of a range of ports.')
        c.argument('vm_size', help='The size of virtual machines in the pool. All virtual machines in a pool are the same size.')
        c.argument('capacity', arg_type=capacity)
        c.argument('placement_property', arg_type=placement_property)
        c.argument('tags', arg_type=tags_type)

    with self.argument_context('sf managed-node-type node') as c:
        c.argument('node_name', nargs='+', help='list of target nodes to perform the operation.')
        c.argument('force', arg_type=get_three_state_flag(), help='Using this flag will force the operation even if service fabric is unable to disable the nodes. Use with caution as this might cause data loss if stateful workloads are running on the node.')

    with self.argument_context('sf managed-node-type vm-extension') as c:
        c.argument('extension_name', help='extension name.')
        c.argument('force_update_tag', help='If a value is provided and is different from the previous value, the extension handler will be forced to update even if the extension configuration has not changed.')
        c.argument('publisher', help='The name of the extension handler publisher.')
        c.argument('extension_type', help='Specifies the type of the extension; an example is \"CustomScriptExtension\".')
        c.argument('type_handler_version', help='Specifies the version of the script handler.')
        c.argument('auto_upgrade_minor_version', options_list=['--auto-upgrade-minor-version', '--auto-upgrade'], arg_type=get_three_state_flag(), help='Indicates whether the extension should use a newer minor version if one is available at deployment time. Once deployed, however, the extension will not upgrade minor versions unless redeployed, even with this property set to true.')
        c.argument('setting', help='Json formatted public settings for the extension.')
        c.argument('protected_setting', help='The extension can contain either protectedSettings or protectedSettingsFromKeyVault or no protected settings at all.')
        c.argument('provision_after_extension', options_list=['--provision-after-extension', '--provision-after'], help='Collection of extension names after which this extension needs to be provisioned.')

    with self.argument_context('sf managed-node-type vm-secret') as c:
        c.argument('source_vault_id', help='Key Vault resource id containing the certificates.')
        c.argument('certificate_url', help='This is the URL of a certificate that has been uploaded to Key Vault as a secret. For adding a secret to the Key Vault, see [Add a key or secret to the key vault](https://learn.microsoft.com/azure/key-vault/key-vault-get-started/#add). In this case, your certificate needs to be It is the Base64 encoding of the following JSON Object which is encoded in UTF-8: `<br><br> {<br>  \"data\":\"<Base64-encoded-certificate>\",<br>  \"dataType\":\"pfx\",<br>  \"password\":\"<pfx-file-password>\"<br>}/`')
        c.argument('certificate_store', help='Specifies the certificate store on the Virtual Machine to which the certificate should be added. The specified certificate store is implicitly in the LocalMachine account.')

    # managed-application-type
    with self.argument_context('sf managed-application-type') as c:
        c.argument('application_type_name', options_list=['--name', '--application-type-name'], help='Specify the application type name.')
        c.argument('tags', arg_type=tags_type)

    # managed-application-type version
    with self.argument_context('sf managed-application-type version') as c:
        c.argument('version', arg_type=application_type_version)
        c.argument('package_url', arg_type=package_url)
        c.argument('tags', arg_type=tags_type)

    # managed-application
    service_type_health_policy_map = CLIArgumentType(
        options_list=['--service-type-health-policy-map'],
        action=AddServiceTypeHealthPolicyAction,
        nargs='*',
        help='Specify the map of the health policy to use for different service types as key/value pairs in the following format: \"ServiceTypeName\"=\"MaxPercentUnhealthyPartitionsPerService,MaxPercentUnhealthyReplicasPerPartition,MaxPercentUnhealthyServices\". '
        'for example: --service-type-health-policy-map \"ServiceTypeName01\"=\"5,10,5\" \"ServiceTypeName02\"=\"5,5,5\"')

    with self.argument_context('sf managed-application') as c:
        c.argument('application_name', options_list=['--name', '--application-name'], help='Specify the application name.')
        c.argument('tags', arg_type=tags_type)

    with self.argument_context('sf managed-application update', validator=validate_update_managed_application) as c:
        c.argument('application_type_version', arg_type=application_type_version)
        c.argument('application_parameters', arg_type=application_parameters)

    with self.argument_context('sf managed-application update', arg_group='Upgrade description') as c:
        c.argument('force_restart', arg_type=get_three_state_flag(),
                   help='Indicates that the service host restarts even if the upgrade is a configuration-only change.')
        c.argument('recreate_application', arg_type=get_three_state_flag(),
                   help='Determines whether the application should be recreated on update. If value=true, the rest of the upgrade policy parameters are not allowed.')
        c.argument('upgrade_replica_set_check_timeout', options_list=['--replica-check-timeout', '--rep-check-timeout'],
                   help='Specify the maximum time, in seconds, that Service Fabric waits for a service to reconfigure into a safe state, if not already in a safe state, before Service Fabric proceeds with the upgrade.')
        c.argument('instance_close_delay_duration', options_list=['--instance-close-delay-duration'],
                   help='Specify the duration in seconds, to wait before a stateless instance is closed, to allow the active requests to drain gracefully. This would be effective when the instance is closing during the application/cluster upgrade, only for those instances which have a non-zero delay duration configured in the service description.')
        c.argument('failure_action', arg_type=get_enum_type(FailureAction),
                   help='Specify the action to take if the monitored upgrade fails. The acceptable values for this parameter are Rollback or Manual.')
        c.argument('upgrade_mode', arg_type=get_enum_type(RollingUpgradeMode),
                   help='Specify the mode used to monitor health during a rolling upgrade. The values are Monitored, and UnmonitoredAuto.')
        c.argument('health_check_retry_timeout', options_list=['--hc-retry-timeout', '--health-check-retry-timeout'],
                   help='Specify the duration, in seconds, after which Service Fabric retries the health check if the previous health check fails.')
        c.argument('health_check_wait_duration', options_list=['--hc-wait-duration', '--health-check-wait-duration'],
                   help='Specify the duration, in seconds, that Service Fabric waits before it performs the initial health check after it finishes the upgrade on the upgrade domain.')
        c.argument('health_check_stable_duration', options_list=['--hc-stable-duration', '--health-check-stable-duration'],
                   help='Specify the duration, in seconds, that Service Fabric waits in order to verify that the application is stable before moving to the next upgrade domain or completing the upgrade. This wait duration prevents undetected changes of health right after the health check is performed.')
        c.argument('upgrade_domain_timeout', options_list=['--ud-timeout', '--upgrade-domain-timeout'],
                   help='Specify the maximum time, in seconds, that Service Fabric takes to upgrade a single upgrade domain. After this period, the upgrade fails.')
        c.argument('upgrade_timeout',
                   help='Specify the maximum time, in seconds, that Service Fabric takes for the entire upgrade. After this period, the upgrade fails.')
        c.argument('consider_warning_as_error', options_list=['--warning-as-error'], arg_type=get_three_state_flag(),
                   help='Indicates whether to treat a warning health event as an error event during health evaluation.')
        c.argument('default_service_type_max_percent_unhealthy_partitions_per_service', options_list=['--max-unhealthy-parts'],
                   help='Specify the maximum percent of unhealthy partitions per service allowed by the health policy for the default service type to use for the monitored upgrade. Allowed values are from 0 to 100.')
        c.argument('default_service_type_max_percent_unhealthy_replicas_per_partition', options_list=['--max-unhealthy-reps'],
                   help='Specify the maximum percent of unhealthy replicas per service allowed by the health policy for the default service type to use for the monitored upgrade. Allowed values are from 0 to 100.')
        c.argument('default_service_type_max_percent_unhealthy_services', options_list=['--max-unhealthy-servs'],
                   help='Specify the maximum percent of unhealthy services allowed by the health policy for the default service type to use for the monitored upgrade. Allowed values are from 0 to 100.')
        c.argument('service_type_health_policy_map', arg_type=service_type_health_policy_map)
        c.argument('max_percent_unhealthy_deployed_applications', options_list=['--max-unhealthy-apps'],
                   help='Specify the maximum percentage of the application instances deployed on the nodes in the cluster that have a health state of error before the application health state for the cluster is error. Allowed values are from 0 to 100.')

    with self.argument_context('sf managed-application create', validator=validate_create_managed_application) as c:
        c.argument('application_type_name', options_list=['--type-name', '--application-type-name'], help='Specify the application type name.')
        c.argument('application_type_version', arg_type=application_type_version)
        c.argument('package_url', arg_type=package_url)
        c.argument('application_parameters', arg_type=application_parameters)

    # managed-service
    partition_names = CLIArgumentType(
        nargs='+',
        help='Specify the array for the names of the partitions. This is only used with Named partition scheme.')

    with self.argument_context('sf managed-service') as c:
        c.argument('service_name', options_list=['--name', '--service-name'],
                   help='Specify the name of the service.')
        c.argument('application_name', options_list=['--application', '--application-name'],
                   help='Specify the name of the service.')
        c.argument('tags', arg_type=tags_type)

    with self.argument_context('sf managed-service create', validator=validate_create_managed_service) as c:
        c.argument('service_type', options_list=['--type', '--service-type'],
                   help='Specify the service type name of the application, it should exist in the application manifest.')
        c.argument('default_move_cost', arg_type=get_enum_type(MoveCost),
                   help='Specify the default cost for a move. Higher costs make it less likely that the Cluster Resource Manager will move the replica when trying to balance the cluster.')
        c.argument('placement_constraints',
                   help='Specify the placement constraints as a string. Placement constraints are boolean expressions on node properties and allow for restricting a service to particular nodes based on the service requirements. For example, to place a service on nodes where NodeType is blue specify the following: \"NodeColor == blue)\".')
        c.argument('service_package_activation_mode', options_list=['--service-package-activation-mode', '--package-activation-mode', '--activation-mode'],
                   help='Specify the activation mode of the service package.')
        c.argument('state', arg_type=get_enum_type(ServiceKind), help='Specify if the service is stateless or stateful.')
        # Stateful arguments
        c.argument('min_replica_set_size', options_list=['--min-replica-set-size', '--min-replica'], help='Specify the min replica set size for the stateful service.')
        c.argument('target_replica_set_size', options_list=['--target-replica-set-size', '--target-replica'], help='Specify the target replica set size for the stateful service.')
        c.argument('has_persisted_state', arg_type=get_three_state_flag(),
                   help='Determines whether this is a persistent service which stores states on the local disk. If it is then the value of this property is true, if not it is false.')
        c.argument('service_placement_time_limit', options_list=['--service-placement-time-limit', '--plcmt-time-limit'],
                   help='Specify the duration for which replicas can stay InBuild before reporting that build is stuck, represented in ISO 8601 format "hh:mm:ss".')
        c.argument('stand_by_replica_keep_duration', options_list=['--stand-by-replica-keep-duration', '--stand-by-keep-duration', '--keep-duration'],
                   help='Specify the definition on how long StandBy replicas should be maintained before being removed, represented in ISO 8601 format "hh:mm:ss".')
        c.argument('quorum_loss_wait_duration', options_list=['--quorum-loss-wait-duration', '--quorum-loss-wait'],
                   help='Specify the maximum duration for which a partition is allowed to be in a state of quorum loss, represented in ISO 8601 format "hh:mm:ss".')
        c.argument('replica_restart_wait_duration', options_list=['--replica-restart-wait-duration', '--replica-restart-wait'],
                   help='Specify the duration between when a replica goes down and when a new replica is created, represented in ISO 8601 format "hh:mm:ss".')
        # Stateless arguments
        c.argument('instance_count', help='Specify the instance count for the stateless service. If -1 is used, it means it will run on all the nodes.')
        c.argument('min_instance_count', help='Specify the minimum number of instances that must be up to meet the EnsureAvailability safety check during operations like upgrade or deactivate node. The actual number that is used is max( MinInstanceCount, ceil( MinInstancePercentage/100.0 * InstanceCount) ). Note, if InstanceCount is set to -1, during MinInstanceCount computation -1 is first converted into the number of nodes on which the instances are allowed to be placed according to the placement constraints on the service.')
        c.argument('min_instance_percentage', options_list=['--min-instance-percentage', '--min-inst-pct'],
                   help='Specify the minimum percentage of InstanceCount that must be up to meet the EnsureAvailability safety check during operations like upgrade or deactivate node. The actual number that is used is max( MinInstanceCount, ceil( MinInstancePercentage/100.0 * InstanceCount) ). Note, if InstanceCount is set to -1, during MinInstancePercentage computation, -1 is first converted into the number of nodes on which the instances are allowed to be placed according to the placement constraints on the service. Allowed values are from 0 to 100.')
        # Partition arguments
        c.argument('partition_scheme', arg_type=get_enum_type(PartitionScheme),
                   help='Specify what partition scheme to use. '
                   'Singleton partitions are typically used when the service does not require any additional routing. '
                   'UniformInt64 means that each partition owns a range of int64 keys. '
                   'Named is usually for services with data that can be bucketed, within a bounded set. Some common examples of data fields used as named partition keys would be regions, postal codes, customer groups, or other business boundaries.')
        c.argument('partition_count',
                   help='Specify the number of partitions. This is only used with UniformInt64 partition scheme.')
        c.argument('low_key',
                   help='Specify the lower bound of the partition key range that should be split between the partition ‘Count’ This is only used with UniformInt64 partition scheme.')
        c.argument('high_key',
                   help='Specify the upper bound of the partition key range that should be split between the partition ‘Count’ This is only used with UniformInt64 partition scheme.')
        c.argument('partition_names', arg_type=partition_names)

    with self.argument_context('sf managed-service update', validator=validate_update_managed_service) as c:
        c.argument('default_move_cost', arg_type=get_enum_type(MoveCost),
                   help='Specify the default cost for a move. Higher costs make it less likely that the Cluster Resource Manager will move the replica when trying to balance the cluster.')
        c.argument('placement_constraints',
                   help='Specify the placement constraints as a string. Placement constraints are boolean expressions on node properties and allow for restricting a service to particular nodes based on the service requirements. For example, to place a service on nodes where NodeType is blue specify the following: \"(NodeColor == blue)\".')
        # Stateful arguments
        c.argument('min_replica_set_size', options_list=['--min-replica-set-size', '--min-replica'], help='Specify the min replica set size for the stateful service.')
        c.argument('target_replica_set_size', options_list=['--target-replica-set-size', '--target-replica'], help='Specify the target replica set size for the stateful service.')
        c.argument('service_placement_time_limit', options_list=['--service-placement-time-limit', '--plcmt-time-limit'],
                   help='Specify the duration for which replicas can stay InBuild before reporting that build is stuck, represented in ISO 8601 format "hh:mm:ss".')
        c.argument('stand_by_replica_keep_duration', options_list=['--stand-by-replica-keep-duration', '--stand-by-keep-duration', '--keep-duration'],
                   help='Specify the definition on how long StandBy replicas should be maintained before being removed, represented in ISO 8601 format "hh:mm:ss".')
        c.argument('quorum_loss_wait_duration', options_list=['--quorum-loss-wait-duration', '--quorum-loss-wait'],
                   help='Specify the maximum duration for which a partition is allowed to be in a state of quorum loss, represented in ISO 8601 format "hh:mm:ss".')
        c.argument('replica_restart_wait_duration', options_list=['--replica-restart-wait-duration', '--replica-restart-wait'],
                   help='Specify the duration between when a replica goes down and when a new replica is created, represented in ISO 8601 format "hh:mm:ss".')
        # Stateless arguments
        c.argument('instance_count', help='Specify the instance count for the stateless service. If -1 is used, it means it will run on all the nodes.')
        c.argument('min_instance_count', help='Specify the minimum number of instances that must be up to meet the EnsureAvailability safety check during operations like upgrade or deactivate node. The actual number that is used is max( MinInstanceCount, ceil( MinInstancePercentage/100.0 * InstanceCount) ). Note, if InstanceCount is set to -1, during MinInstanceCount computation -1 is first converted into the number of nodes on which the instances are allowed to be placed according to the placement constraints on the service.')
        c.argument('min_instance_percentage', options_list=['--min-instance-percentage', '--min-inst-pct'],
                   help='Specify the minimum percentage of InstanceCount that must be up to meet the EnsureAvailability safety check during operations like upgrade or deactivate node. The actual number that is used is max( MinInstanceCount, ceil( MinInstancePercentage/100.0 * InstanceCount) ). Note, if InstanceCount is set to -1, during MinInstancePercentage computation, -1 is first converted into the number of nodes on which the instances are allowed to be placed according to the placement constraints on the service. Allowed values are from 0 to 100.')

    with self.argument_context('sf managed-service correlation-scheme create', validator=validate_create_managed_service_correlation) as c:
        c.argument('correlated_service_name', options_list=['--correlated-service-name', '--correlated-name'],
                   help='Specify the Arm Resource ID of the service that the correlation relationship is established with.')
        c.argument('scheme', help='Specify the ServiceCorrelationScheme which describes the relationship between this service and the service specified via correlated_service_name.')

    with self.argument_context('sf managed-service correlation-scheme update', validator=validate_update_managed_service_correlation) as c:
        c.argument('correlated_service_name', options_list=['--correlated-service-name', '--correlated-name'],
                   help='Specify the Arm Resource ID of the service that the correlation relationship is established with.')
        c.argument('scheme', help='Specify the ServiceCorrelationScheme which describes the relationship between this service and the service specified via correlated_service_name.')

    with self.argument_context('sf managed-service correlation-scheme delete') as c:
        c.argument('correlated_service_name', options_list=['--correlated-service-name', '--correlated-name'],
                   help='Specify the Arm Resource ID of the service that the correlation relationship is established with.')

    with self.argument_context('sf managed-service load-metrics create', validator=validate_create_managed_service_load_metric) as c:
        c.argument('metric_name', help='Specify the name of the metric.')
        c.argument('weight', help='Specify the service load metric relative weight, compared to other metrics configured for this service, as a number.')
        c.argument('primary_default_load', help='Specify the default amount of load, as a number, that this service creates for this metric when it is a Primary replica. Used only for Stateful services.')
        c.argument('secondary_default_load', help='Specify the default amount of load, as a number, that this service creates for this metric when it is a Secondary replica. Used only for Stateful services.')
        c.argument('default_load', help='Specify the default amount of load, as a number, that this service creates for this metric. Used only for Stateless services.')

    with self.argument_context('sf managed-service load-metrics update', validator=validate_update_managed_service_load_metric) as c:
        c.argument('metric_name', help='Specify the name of the metric.')
        c.argument('weight', help='Specify the service load metric relative weight, compared to other metrics configured for this service, as a number.')
        c.argument('primary_default_load', help='Specify the default amount of load, as a number, that this service creates for this metric when it is a Primary replica. Used only for Stateful services.')
        c.argument('secondary_default_load', help='Specify the default amount of load, as a number, that this service creates for this metric when it is a Secondary replica. Used only for Stateful services.')
        c.argument('default_load', help='Specify the default amount of load, as a number, that this service creates for this metric. Used only for Stateless services.')

    with self.argument_context('sf managed-service load-metrics delete') as c:
        c.argument('metric_name', help='Specify the name of the metric.')


def paramToDictionary(values):
    params = {}
    for item in values:
        key, value = item.split('=', 1)
        params[key] = value
    return params


# pylint: disable=protected-access
# pylint: disable=too-few-public-methods
class AddAppParamsAction(argparse._AppendAction):

    def __call__(self, parser, namespace, values, option_string=None):
        try:
            namespace.application_parameters = paramToDictionary(values)
        except ValueError:
            raise CLIError('usage error: {} KEY=VALUE [KEY=VALUE ...]'.format(option_string))


# pylint: disable=protected-access
# pylint: disable=too-few-public-methods
class AddServiceTypeHealthPolicyAction(argparse._AppendAction):

    def __call__(self, parser, namespace, values, option_string=None):
        try:
            namespace.service_type_health_policy_map = paramToDictionary(values)
        except ValueError:
            raise CLIError('usage error: {} KEY=VALUE1,VALUE2,VALUE3 [KEY=VALUE1,VALUE2,VALUE3 ...]'.format(option_string))


class ManagedClusterClientCertAddAction(argparse._AppendAction):

    def __call__(self, parser, namespace, values, option_string=None):
        ClientCertificate = namespace._cmd.get_models('ClientCertificate')
        try:
            kwargs = paramToDictionary(values.split())
            return ClientCertificate(**kwargs)
        except ValueError:
            raise CLIError('usage error: {} KEY=VALUE [KEY=VALUE ...]'.format(option_string))


# pylint: disable=protected-access
# pylint: disable=too-few-public-methods
class AddNodeTypeCapacityAction(argparse._AppendAction):

    def __call__(self, parser, namespace, values, option_string=None):
        try:
            namespace.capacity = paramToDictionary(values)
        except ValueError:
            raise CLIError('usage error: {} KEY=VALUE [KEY=VALUE ...]'.format(option_string))


# pylint: disable=protected-access
# pylint: disable=too-few-public-methods
class AddNodeTypePlacementPropertyAction(argparse._AppendAction):

    def __call__(self, parser, namespace, values, option_string=None):
        try:
            namespace.placement_property = paramToDictionary(values)
        except ValueError:
            raise CLIError('usage error: {} KEY=VALUE [KEY=VALUE ...]'.format(option_string))
