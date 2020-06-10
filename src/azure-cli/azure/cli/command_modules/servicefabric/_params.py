# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
import argparse
from azure.cli.core.util import CLIError
from azure.cli.core.commands.validators import get_default_location_from_resource_group
from azure.cli.core.commands.parameters import resource_group_name_type, get_enum_type, get_three_state_flag
from azure.cli.core.util import get_json_object
from azure.cli.command_modules.servicefabric._validators import validate_create_service, validate_update_application, validate_create_application
from knack.arguments import CLIArgumentType


def load_arguments(self, _):  # pylint: disable=too-many-statements
    # PARAMETER REGISTRATION
    application_parameters = CLIArgumentType(
        options_list=['--parameters', '--application-parameters'],
        action=addAppParamsAction,
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
        c.argument('certificate_output_folder', help='The folder of the new certificate file to be created.')
        c.argument('certificate_password', help='The password of the certificate file.')
        c.argument('certificate_subject_name', help='The subject name of the certificate to be created.')
        c.argument('vault_resource_group_name', options_list=['--vault-resource-group'], help='Key vault resource group name, if not given it will be cluster resource group name')
        c.argument('vault_name', help='Azure key vault name, it not given it will be the cluster resource group name')
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
        c.argument('admin_client_thumbprints', nargs='+', help='Space-separated list of client certificate thumbprint that only has admin permission, ')
        c.argument('certificate_issuer_thumbprint', help='client certificate issuer thumbprint.')

    with self.argument_context('sf cluster certificate') as c:
        c.argument('thumbprint', help='The cluster certificate thumbprint to be removed')

    with self.argument_context('sf cluster client-certificate') as c:
        c.argument('is_admin', help='Client authentication type.')
        c.argument('certificate_issuer_thumbprint', help='client certificate issuer thumbprint.')
        c.argument('certificate_common_name', help='client certificate common name.')
        c.argument('admin_client_thumbprints', nargs='+', help='client certificate thumbprint that only has admin permission.')
        c.argument('readonly_client_thumbprints', nargs='+', help='Space-separated list of client certificate thumbprint that has read only permission.')

    with self.argument_context('sf cluster client-certificate add') as c:
        c.argument('thumbprint', help='client certificate thumbprint.')

    with self.argument_context('sf cluster client-certificate remove') as c:
        c.argument('thumbprints', nargs='+', help='A single or Space-separated list of client certificate thumbprint(s) to be remove.')

    with self.argument_context('sf cluster node') as c:
        c.argument('number_of_nodes_to_add', help='number of nodes to add.')
        c.argument('number_of_nodes_to_remove', help='number of nodes to remove.')

    with self.argument_context('sf cluster node-type') as c:
        c.argument('capacity', help='The capacity tag applied to nodes in the node type. The cluster resource manager uses these tags to understand how much capacity a node has.')
        c.argument('vm_tier', help='VM tier.')

    with self.argument_context('sf cluster') as c:
        c.argument('durability_level', arg_type=get_enum_type(['Bronze', 'Silver', 'Gold']), help='durability level.')

    with self.argument_context('sf cluster setting') as c:
        c.argument('parameter', help='parameter name')
        c.argument('section', help='section name')
        c.argument('value', help='Specify the value')
        c.argument('settings_section_description', help='Specify the value')

    with self.argument_context('sf cluster upgrade-type set') as c:
        c.argument('version', help='cluster code version')
        c.argument('upgrade_mode', arg_type=get_enum_type(['manual', 'automatic']), help='cluster upgrade mode')

    with self.argument_context('sf cluster reliability') as c:
        c.argument('reliability_level', arg_type=get_enum_type(['Bronze', 'Silver', 'Gold', 'Platinum']), help='durability level.')
        c.argument('auto_add_node', help='Add node count automatically when changing reliability.')

    with self.argument_context('sf cluster setting set') as c:
        c.argument('settings_section_description', type=get_json_object,
                   help='JSON encoded parameters configuration. Use @{file} to load from a file. '
                        'For example: [{"section": "NamingService","parameter": "MaxOperationTimeout","value": 1000},{"section": "MaxFileOperationTimeout","parameter": "Max2","value": 1000]')

    with self.argument_context('sf cluster setting remove') as c:
        c.argument('settings_section_description', type=get_json_object,
                   help='JSON encoded parameters configuration. Use @{file} to load from a file. '
                        'For example: [{"section": "NamingService","parameter": "MaxOperationTimeout"}]')

    with self.argument_context('sf cluster client-certificate remove') as c:
        c.argument('client_certificate_common_names', type=get_json_object,
                   help='JSON encoded parameters configuration. Use @{file} to load from a file. '
                        'For example: [{"certificateCommonName": "test.com","certificateIssuerThumbprint": "22B4AE296B504E512DF880A77A2CAE20200FF922"}]')

    with self.argument_context('sf cluster client-certificate add') as c:
        c.argument('client_certificate_common_names', type=get_json_object,
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
        c.argument('service_type_health_policy_map',
                   help='Specify the map of the health policy to use for different service types as a hash table in the following format: {\"ServiceTypeName\" : \"MaxPercentUnhealthyPartitionsPerService,MaxPercentUnhealthyReplicasPerPartition,MaxPercentUnhealthyServices\"}. For example: @{ \"ServiceTypeName01\" = \"5,10,5\"; \"ServiceTypeName02\" = \"5,5,5\" }')

    with self.argument_context('sf application update', arg_group='Upgrade description') as c:
        c.argument('upgrade_replica_set_check_timeout',
                   help='Specify the maximum time, in seconds, that Service Fabric waits for a service to reconfigure into a safe state, if not already in a safe state, before Service Fabric proceeds with the upgrade.')
        c.argument('failure_action', arg_type=get_enum_type(['Rollback', 'Manual']),
                   help='Specify the action to take if the monitored upgrade fails. The acceptable values for this parameter are Rollback or Manual.')
        c.argument('health_check_retry_timeout', options_list=['--hc-retry-timeout', '--health-check-retry-timeout'],
                   help='Specify the duration, in seconds, after which Service Fabric retries the health check if the previous health check fails.')
        c.argument('health_check_wait_duration', options_list=['--hc-wait-duration', '--health-check-wait-duration'],
                   help='Specify the duration, in seconds, that Service Fabric waits before it performs the initial health check after it finishes the upgrade on the upgrade domain.')
        c.argument('health_check_stable_duration', options_list=['--hc-stable-duration', '--health-check-stable-duration'],
                   help='Specify the duration, in seconds, that Service Fabric waits in order to verify that the application is stable before moving to the next upgrade domain or completing the upgrade. This wait duration prevents undetected changes of health right after the health check is performed.')
        c.argument('upgrade_domain_timeout', options_list=['--ud_timeout', '--upgrade-domain-timeout'],
                   help='Specify the maximum time, in seconds, that Service Fabric takes to upgrade a single upgrade domain. After this period, the upgrade fails.')
        c.argument('upgrade_timeout',
                   help='Specify the maximum time, in seconds, that Service Fabric takes for the entire upgrade. After this period, the upgrade fails.')
        c.argument('consider_warning_as_error', options_list=['--warning-as-error', '--consider-warning-as-error'], arg_type=get_three_state_flag(),
                   help='Indicates whether to treat a warning health event as an error event during health evaluation.')
        c.argument('default_service_type_max_percent_unhealthy_partitions_per_service', options_list=['--max-porcent-unhealthy-partitions'],
                   help='Specify the maximum percent of unhelthy partitions per service allowed by the health policy for the default service type to use for the monitored upgrade. Allowed values are form 0 to 100.')
        c.argument('default_service_type_max_percent_unhealthy_replicas_per_partition', options_list=['--max-porcent-unhealthy-replicas'],
                   help='Specify the maximum percent of unhelthy replicas per service allowed by the health policy for the default service type to use for the monitored upgrade. Allowed values are form 0 to 100.')
        c.argument('default_service_type_max_percent_unhealthy_services', options_list=['--max-porcent-unhealthy-services'],
                   help='Specify the maximum percent of unhelthy services allowed by the health policy for the default service type to use for the monitored upgrade. Allowed values are form 0 to 100.')
        c.argument('max_percent_unhealthy_deployed_applications', options_list=['--max-porcent-unhealthy-apps'],
                   help='Specify the mximum percentage of the application instances deployed on the nodes in the cluster that have a health state of error before the application health state for the cluster is error. Allowed values are form 0 to 100.')

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
        c.argument('min_replica_set_size', help='Specify the min replica set size for the stateful service.')
        c.argument('target_replica_set_size', help='Specify the target replica set size for the stateful service.')
        c.argument('default_move_cost', arg_type=get_enum_type(['Zero', 'Low', 'Medium', 'High']),
                   help='Specify the default cost for a move. Higher costs make it less likely that the Cluster Resource Manager will move the replica when trying to balance the cluster.')
        c.argument('partition_scheme', arg_type=get_enum_type(['singleton', 'uniformInt64', 'named']),
                   help='Specify what partition scheme to use. '
                   'Singleton partitions are typically used when the service does not require any additional routing. '
                   'UniformInt64 means that each partition owns a range of int64 keys. '
                   'Named is usually for services with data that can be bucketed, within a bounded set. Some common examples of data fields used as named partition keys would be regions, postal codes, customer groups, or other business boundaries.')


# pylint: disable=protected-access
# pylint: disable=too-few-public-methods
class addAppParamsAction(argparse._AppendAction):

    def __call__(self, parser, namespace, values, option_string=None):
        params = {}
        for item in values:
            try:
                key, value = item.split('=', 1)
                params[key] = value
            except ValueError:
                raise CLIError('usage error: {} KEY=VALUE [KEY=VALUE ...]'.format(option_string))
        namespace.application_parameters = params
