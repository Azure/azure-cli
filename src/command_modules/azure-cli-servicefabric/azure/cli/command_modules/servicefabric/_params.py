# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from azure.cli.core.commands.validators import get_default_location_from_resource_group
from azure.cli.core.commands.parameters import resource_group_name_type, get_enum_type
from azure.cli.core.util import get_json_object


def load_arguments(self, _):  # pylint: disable=too-many-statements
    with self.argument_context('sf') as c:
        c.argument('resource_group_name', arg_type=resource_group_name_type, id_part=None, help='The resource group name')
        c.argument('cluster_name', options_list=['--name', '--cluster-name', '-n'], help='Specify the name of the cluster, if not given it will be same as resource group name')
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('secret_identifier', help='The existing Azure key vault secret URL')
        c.argument('certificate_file', help='The existing certificate file path for the primary cluster certificate.')
        c.argument('parameter_file', help='The path to the template parameter file.')
        c.argument('template_file', help='The path to the template file.')
        c.argument('vm_password', help='The password of the Vm')
        c.argument('certificate_output_folder', help='The folder of the new certificate file to be created.')
        c.argument('certificate_password', help='The password of the certificate file.')
        c.argument('certificate_subject_name', help='The subject name of the certificate to be created.')
        c.argument('vault_resource_group_name', options_list=['--vault-resource-group'], help='Key vault resource group name,if not given it will be cluster resource group name')
        c.argument('vault_name', help='Azure key vault name, it not given it will be the cluster resource group name')
        c.argument('cluster_size', options_list=['--cluster-size', '-s'], help='The number of nodes in the cluster. Default are 5 nodes')
        c.argument('vm_sku', help='The Vm Sku')
        c.argument('vm_user_name', help='The user name for logging to Vm. Default will be adminuser')
        c.argument('vm_os', arg_type=get_enum_type(['WindowsServer2012R2Datacenter',
                                                    'WindowsServer2016Datacenter',
                                                    'WindowsServer2016DatacenterwithContainers',
                                                    'UbuntuServer1604']),
                   default='WindowsServer2016Datacenter', options_list=['--vm-os', '--os'],
                   help='The Operating System of the VMs that make up the cluster.')
        c.argument('node_type', help='the Node type name.')

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

    with self.argument_context('sf cluster durability') as c:
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
        c.argument('reliability_level', arg_type=get_enum_type(['Bronze', 'Silver', 'Gold']), help='durability level.')
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
