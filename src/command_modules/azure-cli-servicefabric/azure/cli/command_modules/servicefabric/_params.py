# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import \
    (register_cli_argument)
import azure.cli.core.commands.arm  # pylint: disable=unused-import
from azure.cli.core.commands.validators import get_default_location_from_resource_group
from azure.cli.core.commands.parameters import (
    resource_group_name_type,
    enum_choice_list
)
from azure.cli.core.util import get_json_object

# PARAMETER REGISTRATIONS

register_cli_argument('sf cluster list', 'resource_group_name', resource_group_name_type,
                      id_part=None, help='The resource group name')

register_cli_argument('sf', 'resource_group_name', resource_group_name_type,
                      id_part=None, help='The resource group name')
register_cli_argument('sf', 'cluster_name', options_list=('--name', '--cluster-name', '-n'),
                      help='Specify the name of the cluster, if not given it will be same as resource group name')
register_cli_argument('sf', 'location',
                      validator=get_default_location_from_resource_group)

register_cli_argument('sf', 'secret_identifier', options_list=('--secret-identifier'),
                      help='The existing Azure key vault secret URL')
register_cli_argument('sf', 'certificate_file', options_list=('--certificate-file'),
                      help='The existing certificate file path for the primary cluster certificate.')
register_cli_argument('sf', 'parameter_file', options_list=('--parameter-file'),
                      help='The path to the template parameter file.')
register_cli_argument('sf', 'template_file', options_list=('--template-file'),
                      help='The path to the template file.')
register_cli_argument('sf', 'vm_password', options_list=('--vm-password'),
                      help='The password of the Vm')
register_cli_argument('sf', 'certificate_output_folder', options_list=('--certificate-output-folder'),
                      help='The folder of the new certificate file to be created.')
register_cli_argument('sf', 'certificate_password', options_list=('--certificate-password'),
                      help='The password of the certificate file.')
register_cli_argument('sf', 'certificate_subject_name', options_list=('--certificate-subject-name'),
                      help='The subject name of the certificate to be created.')
register_cli_argument('sf', 'vault_resource_group_name', options_list=('--vault-resource-group'),
                      help='Key vault resource group name,if not given it will be cluster resource group name')
register_cli_argument('sf', 'vault_name', options_list=('--vault-name'),
                      help='Azure key vault name, it not given it will be the cluster resource group name')
register_cli_argument('sf', 'cluster_size', options_list=('--cluster-size', '-s'),
                      help='The number of nodes in the cluster. Default are 5 nodes')
register_cli_argument('sf', 'vm_sku', options_list=(
    '--vm-sku'), help='The Vm Sku')
register_cli_argument('sf', 'vm_user_name', options_list=(
    '--vm-user-name'), help='The user name for logging to Vm. Default will be adminuser')
register_cli_argument('sf', 'vm_os', default='WindowsServer2016Datacenter', options_list=('--vm-os', '--os'),
                      help='The Operating System of the VMs that make up the cluster.',
                      **enum_choice_list(['WindowsServer2012R2Datacenter',
                                          'WindowsServer2016Datacenter',
                                          'WindowsServer2016DatacenterwithContainers',
                                          'UbuntuServer1604']))

register_cli_argument('sf client certificate', 'certificate_common_name',
                      help='client certificate common name.')
register_cli_argument('sf client certificate', 'admin_client_thumbprints', nargs='+',
                      help='Space separated list of client certificate thumbprint that only has admin permission, ')
register_cli_argument('sf client certificate', 'certificate_issuer_thumbprint',
                      help='client certificate issuer thumbprint.')

register_cli_argument('sf cluster certificate', 'thumbprint',
                      help='The cluster certificate thumbprint to be removed')

register_cli_argument('sf cluster client-certificate', 'is_admin',
                      help='Client authentication type.')
register_cli_argument('sf cluster client-certificate', 'certificate_issuer_thumbprint',
                      help='client certificate issuer thumbprint.')
register_cli_argument('sf cluster client-certificate', 'certificate_common_name',
                      help='client certificate common name.')
register_cli_argument('sf cluster client-certificate', 'admin_client_thumbprints', nargs='+',
                      help='client certificate thumbprint that only has admin permission.')
register_cli_argument('sf cluster client-certificate', 'readonly_client_thumbprints', nargs='+',
                      help='Space separated list of client certificate thumbprint that has read only permission.')
register_cli_argument('sf cluster client-certificate add', 'thumbprint',
                      help='client certificate thumbprint.')
register_cli_argument('sf cluster client-certificate remove', 'thumbprints', nargs='+',
                      help='A single or Space separated list of client certificate thumbprint(s) to be remove.')

register_cli_argument('sf', 'node_type', help='the Node type name.')

register_cli_argument(
    'sf cluster node', 'number_of_nodes_to_add', help='number of nodes to add.')
register_cli_argument(
    'sf cluster node', 'number_of_nodes_to_remove', help='number of nodes to remove.')

register_cli_argument('sf cluster durability', 'durability_level',
                      help='durability level.', **enum_choice_list(['Bronze', 'Silver', 'Gold']))

register_cli_argument('sf cluster setting', 'parameter', help='parameter name')
register_cli_argument('sf cluster setting', 'section', help='section name')
register_cli_argument('sf cluster setting', 'value', help='Specify the value')

register_cli_argument('sf cluster setting',
                      'settings_section_description', help='Specify the value')

register_cli_argument('sf cluster upgrade-type set',
                      'version', help='cluster code version')
register_cli_argument('sf cluster upgrade-type set', 'upgrade_mode',
                      help='cluster upgrade mode', **enum_choice_list(['manual', 'automatic']))

register_cli_argument('sf cluster reliability', 'reliability_level',
                      help='durability level.', **enum_choice_list(['Bronze', 'Silver', 'Gold']))

register_cli_argument('sf cluster reliability', 'auto_add_node',
                      help='Add node count automatically when changing reliability.')

register_cli_argument('sf cluster setting set', 'settings_section_description', type=get_json_object,
                      help='JSON encoded parameters configuration. Use @{file} to load from a file.'
                      """for example: [{"section": "NamingService","parameter": "MaxOperationTimeout","value": 1000},{"section": "MaxFileOperationTimeout","parameter": "Max2","value": 1000]""")  # pylint: disable=line-too-long

register_cli_argument('sf cluster setting remove', 'settings_section_description', type=get_json_object,
                      help='JSON encoded parameters configuration. Use @{file} to load from a file.'
                      """for example: [{"section": "NamingService","parameter": "MaxOperationTimeout"}]""")

register_cli_argument('sf cluster client-certificate remove', 'client_certificate_common_names', type=get_json_object,
                      help='JSON encoded parameters configuration. Use @{file} to load from a file.'
                      """for example: [{"certificateCommonName": "test.com","certificateIssuerThumbprint": "22B4AE296B504E512DF880A77A2CAE20200FF922"}]""")

register_cli_argument('sf cluster client-certificate add', 'client_certificate_common_names', type=get_json_object,
                      help='JSON encoded parameters configuration. Use @{file} to load from a file.'
                      """for example: [{"isAdmin":true, "certificateCommonName": "test.com",
                         "certificateIssuerThumbprint": "22B4AE296B504E512DF880A77A2CAE20200FF922"}]""")
