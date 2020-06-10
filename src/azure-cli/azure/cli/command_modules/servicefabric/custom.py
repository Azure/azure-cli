# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long,too-many-lines

import os
import time

from OpenSSL import crypto

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse  # pylint: disable=import-error

from msrestazure.azure_exceptions import CloudError

from azure.cli.core.util import CLIError, get_file_json, b64_to_hex, sdk_no_wait
from azure.cli.core.commands import LongRunningOperation
from azure.graphrbac import GraphRbacManagementClient
from azure.cli.core.profiles import ResourceType, get_sdk, get_api_version
from azure.keyvault import KeyVaultAuthentication, KeyVaultClient
from azure.cli.command_modules.servicefabric._arm_deployment_utils import validate_and_deploy_arm_template

from azure.mgmt.servicefabric.models import (ClusterUpdateParameters,
                                             ClientCertificateThumbprint,
                                             ClientCertificateCommonName,
                                             SettingsSectionDescription,
                                             SettingsParameterDescription,
                                             NodeTypeDescription,
                                             EndpointRangeDescription)
from azure.mgmt.network.models import (PublicIPAddress,
                                       Subnet,
                                       SubResource as NetworkSubResource,
                                       InboundNatPool,
                                       Probe,
                                       PublicIPAddressDnsSettings,
                                       LoadBalancer,
                                       FrontendIPConfiguration,
                                       BackendAddressPool,
                                       LoadBalancingRule)
from azure.mgmt.compute.models import (VaultCertificate,
                                       Sku as ComputeSku,
                                       UpgradePolicy,
                                       ImageReference,
                                       ApiEntityReference,
                                       VaultSecretGroup,
                                       VirtualMachineScaleSetOSDisk,
                                       VirtualMachineScaleSetVMProfile,
                                       VirtualMachineScaleSetExtensionProfile,
                                       VirtualMachineScaleSetOSProfile,
                                       VirtualMachineScaleSetStorageProfile,
                                       VirtualMachineScaleSet,
                                       VirtualMachineScaleSetNetworkConfiguration,
                                       VirtualMachineScaleSetIPConfiguration,
                                       VirtualMachineScaleSetNetworkProfile,
                                       SubResource,
                                       UpgradeMode)
from azure.mgmt.storage.models import StorageAccountCreateParameters

from knack.log import get_logger

from ._client_factory import (resource_client_factory,
                              keyvault_client_factory,
                              compute_client_factory,
                              storage_client_factory,
                              network_client_factory)
logger = get_logger(__name__)

DEFAULT_ADMIN_USER_NAME = "adminuser"
DEFAULT_SKU = "Standard_D2_V2"
DEFAULT_TIER = "Standard"
DEFAULT_OS = "WindowsServer2016Datacenter"
DEFAULT_CLUSTER_SIZE = 5
DEFAULT_DURABILITY_LEVEL = "Bronze"
DEFAULT_APPLICATION_START_PORT = 20000
DEFAULT_APPLICATION_END_PORT = 30000
DEFAULT_EPHEMERAL_START = 49152
DEFAULT_EPHEMERAL_END = 65534
DEFAULT_CLIENT_CONNECTION_ENDPOINT = 19000
DEFAULT_HTTP_GATEWAY_ENDPOINT = 19080
DEFAULT_TCP_PORT = 19000
DEFAULT_HTTP_PORT = 19080
DEFAULT_FRONTEND_PORT_RANGE_START = 3389
DEFAULT_FRONTEND_PORT_RANGE_END = 4500
DEFAULT_BACKEND_PORT = 3389
SERVICE_FABRIC_WINDOWS_NODE_EXT_NAME = "servicefabricnode"
SERVICE_FABRIC_LINUX_NODE_EXT_NAME = "servicefabriclinuxnode"

SOURCE_VAULT_VALUE = "sourceVaultValue"
CERTIFICATE_THUMBPRINT = "certificateThumbprint"
CERTIFICATE_URL_VALUE = "certificateUrlValue"
SEC_SOURCE_VAULT_VALUE = "secSourceVaultValue"
SEC_CERTIFICATE_THUMBPRINT = "secCertificateThumbprint"
SEC_CERTIFICATE_URL_VALUE = "secCertificateUrlValue"

os_dic = {'WindowsServer2012R2Datacenter': '2012-R2-Datacenter',
          'UbuntuServer1604': '16.04-LTS',
          'WindowsServer2016DatacenterwithContainers': '2016-Datacenter-with-Containers',
          'WindowsServer2016Datacenter': '2016-Datacenter',
          'WindowsServer1709': "Datacenter-Core-1709-smalldisk",
          'WindowsServer1709withContainers': "Datacenter-Core-1709-with-Containers-smalldisk",
          'WindowsServer1803withContainers': "Datacenter-Core-1803-with-Containers-smalldisk",
          'WindowsServer1809withContainers': "Datacenter-Core-1809-with-Containers-smalldisk",
          'WindowsServer2019Datacenter': "2019-Datacenter",
          'WindowsServer2019DatacenterwithContainers': "2019-Datacenter-Core-with-Containers"}


def list_cluster(client, resource_group_name=None):
    cluster_list = client.list_by_resource_group(resource_group_name=resource_group_name) \
        if resource_group_name else client.list()
    return cluster_list


# pylint:disable=too-many-locals, too-many-statements, too-many-boolean-expressions, too-many-branches
def new_cluster(cmd,
                client,
                resource_group_name,
                location,
                certificate_subject_name=None,
                parameter_file=None,
                template_file=None,
                cluster_name=None,
                vault_resource_group_name=None,
                vault_name=None,
                certificate_file=None,
                certificate_password=None,
                certificate_output_folder=None,
                secret_identifier=None,
                vm_user_name=None,
                vm_password=None,
                cluster_size=None,
                vm_sku=None,
                vm_os=None):
    cli_ctx = cmd.cli_ctx
    if certificate_subject_name is None and certificate_file is None and secret_identifier is None:
        raise CLIError(
            '\'--certificate-subject-name\', \'--certificate-file\', \'--secret-identifier\', one of them must be specified')
    if certificate_output_folder and certificate_file:
        raise CLIError(
            '\'--certificate-output-folder\' and \'--certificate-file\' can not be specified at same time')
    if secret_identifier:
        if certificate_output_folder or certificate_file or certificate_output_folder or vault_resource_group_name or certificate_password:
            raise CLIError(
                '\'--certificate-output-folder\' , \'--certificate-file\', \'certificate_output_folder\', \'vault_resource_group_name\', \'certificate_password\' can not be specified, ' +
                'when \'--secret-identifier\' is specified')
    if parameter_file or template_file:
        if parameter_file is None or template_file is None:
            raise CLIError('If using customize template to deploy,both \'--parameter-file\' and \'--template-file\' can not be None ' + '\n For example:\n az sf cluster create --resource-group myRg --location westus --certificate-subject-name test.com --parameter-file c:\\parameter.json --template-file c:\\template.json' +
                           '\n az sf cluster create --resource-group myRg --location westus --parameter-file c:\\parameter.json --template-file c:\\template.json --certificate_file c:\\test.pfx' + '\n az sf cluster create --resource-group myRg --location westus --certificate-subject-name test.com --parameter-file c:\\parameter.json --template-file c:\\template.json --certificate-output-folder c:\\certoutput')
        if cluster_size or vm_sku or vm_user_name:
            raise CLIError('\'cluster_size\',\'vm_sku\',\'vm_os\',\'vm_user_name\' can not be specified when using customize template deployment')

    else:
        if vm_password is None:
            raise CLIError('\'--vm-password\' could not be None')

    if cluster_size is None:
        cluster_size = DEFAULT_CLUSTER_SIZE
    if vm_sku is None:
        vm_sku = DEFAULT_SKU
    if vm_os is None:
        vm_os = DEFAULT_OS
    if vm_user_name is None:
        vm_user_name = DEFAULT_ADMIN_USER_NAME

    rg = _get_resource_group_by_name(cli_ctx, resource_group_name)
    if rg is None:
        _create_resource_group_name(cli_ctx, resource_group_name, location)

    if vault_name is None:
        vault_name = resource_group_name
        name = ""
        for n in vault_name:
            if n.isalpha() or n == '-' or n.isdigit():
                name += n
            if len(name) >= 21:
                break
        vault_name = name
    if vault_resource_group_name is None:
        vault_resource_group_name = resource_group_name
    if cluster_name is None:
        cluster_name = resource_group_name

    if certificate_file:
        _, file_extension = os.path.splitext(certificate_file)
        if file_extension is None or file_extension.lower() != '.pfx'.lower():
            raise CLIError('\'--certificate_file\' should be a valid pfx file')

    vault_id = None
    certificate_uri = None
    cert_thumbprint = None
    output_file = None
    if parameter_file is None:
        vm_os = os_dic[vm_os]
        reliability_level = _get_reliability_level(cluster_size)
        result = _create_certificate(cmd,
                                     cli_ctx,
                                     resource_group_name,
                                     certificate_file,
                                     certificate_password,
                                     vault_name,
                                     vault_resource_group_name,
                                     certificate_output_folder,
                                     certificate_subject_name,
                                     secret_identifier)
        vault_id = result[0]
        certificate_uri = result[1]
        cert_thumbprint = result[2]
        output_file = result[3]

        linux = None
        if vm_os == '16.04-LTS':
            linux = True
        template = _modify_template(linux)
        parameters = _set_parameters_for_default_template(cluster_location=location,
                                                          cluster_name=cluster_name,
                                                          admin_password=vm_password,
                                                          certificate_thumbprint=cert_thumbprint,
                                                          vault_id=vault_id,
                                                          certificate_id=certificate_uri,
                                                          reliability_level=reliability_level,
                                                          admin_name=vm_user_name,
                                                          cluster_size=cluster_size,
                                                          durability_level=DEFAULT_DURABILITY_LEVEL,
                                                          vm_sku=vm_sku,
                                                          os_type=vm_os,
                                                          linux=linux)
    else:
        parameters, output_file = _set_parameters_for_customize_template(cmd,
                                                                         cli_ctx,
                                                                         resource_group_name,
                                                                         certificate_file,
                                                                         certificate_password,
                                                                         vault_name,
                                                                         vault_resource_group_name,
                                                                         certificate_output_folder,
                                                                         certificate_subject_name,
                                                                         secret_identifier,
                                                                         parameter_file)

        vault_id = parameters[SOURCE_VAULT_VALUE]['value']
        certificate_uri = parameters[CERTIFICATE_URL_VALUE]['value']
        cert_thumbprint = parameters[CERTIFICATE_THUMBPRINT]['value']
        template = get_file_json(template_file)

    validate_and_deploy_arm_template(cmd, resource_group_name, template, parameters)

    output_dict = {}
    output_dict['vm_user_name'] = vm_user_name
    output_dict['cluster'] = client.get(resource_group_name, cluster_name)
    output_dict['certificate'] = {'certificate_file': output_file,
                                  'vault_id': vault_id,
                                  'certificate_identifier': certificate_uri,
                                  'thumbprint': cert_thumbprint}

    return output_dict


def _build_detailed_error(top_error, output_list):
    if output_list:
        output_list.append(' Inner Error - Code: "{}" Message: "{}"'.format(top_error.code, top_error.message))
    else:
        output_list.append('Error - Code: "{}" Message: "{}"'.format(top_error.code, top_error.message))

    if top_error.details:
        for error in top_error.details:
            _build_detailed_error(error, output_list)

    return output_list


def add_app_cert(cmd,
                 client,
                 resource_group_name,
                 cluster_name,
                 certificate_file=None,
                 certificate_password=None,
                 vault_name=None,
                 vault_resource_group_name=None,
                 certificate_output_folder=None,
                 certificate_subject_name=None,
                 secret_identifier=None):
    cli_ctx = cmd.cli_ctx
    result = _create_certificate(cmd,
                                 cli_ctx,
                                 resource_group_name,
                                 certificate_file,
                                 certificate_password,
                                 vault_name,
                                 vault_resource_group_name,
                                 certificate_output_folder,
                                 certificate_subject_name,
                                 secret_identifier)

    _add_cert_to_all_vmss(cli_ctx, resource_group_name, None, result[0], result[1])
    return client.get(resource_group_name, cluster_name)


def add_client_cert(client,
                    resource_group_name,
                    cluster_name,
                    is_admin=False,
                    thumbprint=None,
                    certificate_common_name=None,
                    certificate_issuer_thumbprint=None,
                    admin_client_thumbprints=None,
                    readonly_client_thumbprints=None,
                    client_certificate_common_names=None):
    if thumbprint:
        if certificate_common_name or certificate_issuer_thumbprint or admin_client_thumbprints or readonly_client_thumbprints or client_certificate_common_names:
            raise CLIError(
                "--thumbprint can only specified alone or with --is-admin")
    if certificate_common_name or certificate_issuer_thumbprint:
        if certificate_issuer_thumbprint is None or certificate_common_name is None:
            raise CLIError(
                "Both \'--certificate-common-name\' and \'--certificate-issuer-thumbprint should not be None'")
        if thumbprint or admin_client_thumbprints or readonly_client_thumbprints or client_certificate_common_names or is_admin:
            raise CLIError(
                "Only \'--certificate-common-name\' and \'--certificate-issuer-thumbprint\' can be specified together")
    if admin_client_thumbprints or readonly_client_thumbprints:
        if thumbprint or certificate_common_name or certificate_issuer_thumbprint or client_certificate_common_names or is_admin:
            raise CLIError(
                "Only \'--admin-client-thumbprints\' and \'--readonly-client-thumbprints\' can be specified together")
    if client_certificate_common_names:
        if is_admin or thumbprint or certificate_common_name or certificate_issuer_thumbprint or admin_client_thumbprints or readonly_client_thumbprints:  # pylint: disable=too-many-boolean-expressions
            raise CLIError(
                "\'--client-certificate-commonNames\' can only be specified alone")

    cluster = client.get(resource_group_name, cluster_name)

    def _add_thumbprint(cluster, is_admin, thumbprint):
        remove = []
        for t in cluster.client_certificate_thumbprints:
            if t.certificate_thumbprint.lower() == thumbprint.lower():
                remove.append(t)
        for t in remove:
            cluster.client_certificate_thumbprints.remove(t)
        cluster.client_certificate_thumbprints.append(
            ClientCertificateThumbprint(is_admin, thumbprint))

    def _add_common_name(cluster, is_admin, certificate_common_name, certificate_issuer_thumbprint):
        for t in cluster.client_certificate_common_names:
            if t.certificate_common_name.lower() == certificate_common_name.lower() and t.certificate_issuer_thumbprint.lower() == certificate_issuer_thumbprint.lower():
                remove = t
        if remove:
            cluster.client_certificate_common_names.remove(remove)
        cluster.client_certificate_common_names.add(ClientCertificateCommonName(
            is_admin, certificate_common_name, certificate_issuer_thumbprint))
        return cluster.client_certificate_common_names

    if thumbprint:
        _add_thumbprint(cluster, is_admin, thumbprint)
    if admin_client_thumbprints or readonly_client_thumbprints:
        if admin_client_thumbprints:
            for t in admin_client_thumbprints:
                _add_thumbprint(cluster, True, t)
        if readonly_client_thumbprints:
            for t in readonly_client_thumbprints:
                _add_thumbprint(cluster, False, t)
    if certificate_common_name:
        _add_common_name(cluster, is_admin, certificate_common_name,
                         certificate_issuer_thumbprint)
    if client_certificate_common_names:
        for common_name in client_certificate_common_names:
            if 'certificateCommonName' in common_name and 'certificateIssuerThumbprint' in common_name and 'isAdmin' in common_name:
                cluster.client_certificate_common_names = _add_common_name(
                    cluster, common_name['isAdmin'], common_name['certificateCommonName'], common_name['certificateIssuerThumbprint'])
            else:
                raise CLIError('client_certificate_common_names is invalid')

    patch_request = ClusterUpdateParameters(client_certificate_thumbprints=cluster.client_certificate_thumbprints,
                                            client_certificate_common_names=cluster.client_certificate_common_names)
    return client.update(resource_group_name, cluster_name, patch_request)


def remove_client_cert(client,
                       resource_group_name,
                       cluster_name,
                       thumbprints=None,
                       certificate_common_name=None,
                       certificate_issuer_thumbprint=None,
                       client_certificate_common_names=None):
    if thumbprints:
        if certificate_common_name or certificate_issuer_thumbprint or client_certificate_common_names:
            raise CLIError("--thumbprint can only specified alone")
    if certificate_common_name or certificate_issuer_thumbprint:
        if certificate_issuer_thumbprint is None or certificate_common_name is None:
            raise CLIError(
                "Both \'--certificate-common-name\' and \'--certificate-issuer-thumbprint should not be None'")
        if thumbprints or client_certificate_common_names:
            raise CLIError(
                "Only \'--certificate-common-name\' and \'--certificate-issuer-thumbprint\' can be specified together")
    if client_certificate_common_names:
        if thumbprints or certificate_common_name or certificate_issuer_thumbprint:
            raise CLIError(
                "\'--client-certificate-commonNames\' can only be specified alone")

    cluster = client.get(resource_group_name, cluster_name)

    def _remove_thumbprint(cluster, thumbprint):
        remove = None
        for t in cluster.client_certificate_thumbprints:
            if t.certificate_thumbprint.lower() == thumbprint.lower():
                remove = t
        if remove:
            cluster.client_certificate_thumbprints.remove(remove)
        return cluster.client_certificate_thumbprints

    def _remove_common_name(cluster, certificate_common_name, certificate_issuer_thumbprint):
        remove = None
        for t in cluster.client_certificate_common_names:
            if t.certificate_common_name.lower() == certificate_common_name.lower() and t.certificate_issuer_thumbprint.lower() == certificate_issuer_thumbprint.lower():
                remove = t
        if remove:
            cluster.client_certificate_common_names.remove(remove)
        return cluster.certificate_issuer_thumbprint

    if isinstance(thumbprints, list) is False:
        _remove_thumbprint(cluster, thumbprints)
    if isinstance(thumbprints, list) is True:
        for t in thumbprints:
            cluster.client_certificate_thumbprints = _remove_thumbprint(
                cluster, t)
    if certificate_common_name:
        _remove_common_name(cluster, certificate_common_name,
                            certificate_issuer_thumbprint)
    if client_certificate_common_names:
        for common_name in client_certificate_common_names:
            if 'certificateCommonName' in common_name and 'certificateIssuerThumbprint' in common_name:
                cluster.client_certificate_common_names = _remove_common_name(cluster,
                                                                              common_name['certificateCommonName'],
                                                                              common_name['certificateIssuerThumbprint'])
            else:
                raise CLIError('client_certificate_common_names is invalid')
    patch_request = ClusterUpdateParameters(client_certificate_thumbprints=cluster.client_certificate_thumbprints,
                                            client_certificate_common_names=cluster.client_certificate_common_names)

    return client.update(resource_group_name, cluster_name, patch_request)


def add_cluster_cert(cmd,
                     client,
                     resource_group_name,
                     cluster_name,
                     certificate_file=None,
                     certificate_password=None,
                     vault_name=None,
                     vault_resource_group_name=None,
                     certificate_output_folder=None,
                     certificate_subject_name=None,
                     secret_identifier=None):
    cli_ctx = cmd.cli_ctx
    cluster = client.get(resource_group_name, cluster_name)
    if cluster.certificate is None:
        raise CLIError("Unsecure cluster is not allowed to add certificate")

    result = _create_certificate(cmd,
                                 cli_ctx,
                                 resource_group_name,
                                 certificate_file,
                                 certificate_password,
                                 vault_name,
                                 vault_resource_group_name,
                                 certificate_output_folder,
                                 certificate_subject_name,
                                 secret_identifier)

    vault_id = result[0]
    secret_url = result[1]
    thumbprint = result[2]

    compute_client = compute_client_factory(cli_ctx)
    primary_node_type = [n for n in cluster.node_types if n.is_primary is True][0]
    vmss = _get_cluster_vmss_by_node_type(compute_client, resource_group_name, cluster.cluster_id, primary_node_type.name)
    fabric_ext = _get_sf_vm_extension(vmss)
    if fabric_ext is None:
        raise CLIError("Failed to find service fabric extension")

    # add cert to sf extension
    import json
    seconday_setting = json.loads(
        '{{"thumbprint":"{0}","x509StoreName":"{1}"}}'.format(thumbprint, 'my'))
    fabric_ext.settings["certificateSecondary"] = seconday_setting

    # add cert and star vmss update
    _add_cert_to_all_vmss(cli_ctx, resource_group_name, cluster.cluster_id, vault_id, secret_url)

    # cluser update
    patch_request = ClusterUpdateParameters(certificate=cluster.certificate)
    patch_request.certificate.thumbprint_secondary = thumbprint
    return client.update(resource_group_name, cluster_name, patch_request)


def remove_cluster_cert(client, resource_group_name, cluster_name, thumbprint):
    cluster = client.get(resource_group_name, cluster_name)
    if cluster.certificate is None:
        raise CLIError("Unsecure cluster is not allowed to remove certificate")
    if cluster.certificate.thumbprint_secondary.lower() == thumbprint.lower():
        cluster.certificate.thumbprint_secondary = None
    else:
        if cluster.certificate.thumbprint.lower() == thumbprint.lower():
            cluster.certificate.thumbprint = cluster.certificate.thumbprint_secondary
            cluster.certificate.thumbprint_secondary = None
        else:
            raise CLIError(
                "Unable to find the certificate with the thumbprint {} in the cluster".format(thumbprint))

    patch_request = ClusterUpdateParameters(certificate=cluster.certificate)
    patch_request.certificate = cluster.certificate
    return client.update(resource_group_name, cluster_name, patch_request)


def add_cluster_node(cmd, client, resource_group_name, cluster_name, node_type, number_of_nodes_to_add):
    cli_ctx = cmd.cli_ctx
    number_of_nodes_to_add = int(number_of_nodes_to_add)
    if number_of_nodes_to_add <= 0:
        raise CLIError("--number-of-nodes-to-add must be greater than 0")
    compute_client = compute_client_factory(cli_ctx)
    cluster = client.get(resource_group_name, cluster_name)
    node_types = [n for n in cluster.node_types if n.name.lower() == node_type.lower()]
    if node_types is None:
        raise CLIError("Failed to find the node type in the cluster")
    node_type = node_types[0]

    vmss = _get_cluster_vmss_by_node_type(compute_client, resource_group_name, cluster.cluster_id, node_type.name)
    vmss.sku.capacity = vmss.sku.capacity + number_of_nodes_to_add

    # update vmss
    vmss_poll = compute_client.virtual_machine_scale_sets.create_or_update(
        resource_group_name, vmss.name, vmss)
    LongRunningOperation(cli_ctx)(vmss_poll)

    # update cluster
    node_type.vm_instance_count = vmss.sku.capacity
    patch_request = ClusterUpdateParameters(node_types=cluster.node_types)

    return client.update(resource_group_name, cluster_name, patch_request)


def remove_cluster_node(cmd, client, resource_group_name, cluster_name, node_type, number_of_nodes_to_remove):
    cli_ctx = cmd.cli_ctx
    number_of_nodes_to_remove = int(number_of_nodes_to_remove)
    if number_of_nodes_to_remove <= 0:
        raise CLIError("--number-of-nodes-to-remove must be greater than 0")
    compute_client = compute_client_factory(cli_ctx)
    cluster = client.get(resource_group_name, cluster_name)
    node_types = [n for n in cluster.node_types if n.name.lower() == node_type.lower()]
    if node_types is None:
        raise CLIError("Failed to find the node type in the cluster")

    node_type = node_types[0]
    reliability_required_instance_count = _get_target_instance(cluster.reliability_level)
    vmss = _get_cluster_vmss_by_node_type(compute_client, resource_group_name, cluster.cluster_id, node_type.name)
    vmss.sku.capacity = vmss.sku.capacity - number_of_nodes_to_remove
    if vmss.sku.capacity < reliability_required_instance_count:
        raise CLIError("Can't delete node since current reliability level is {} requires at least {} nodes.".format(
            cluster.reliability_level,
            reliability_required_instance_count))

    # update vmss
    vmss_poll = compute_client.virtual_machine_scale_sets.create_or_update(
        resource_group_name, vmss.name, vmss)
    LongRunningOperation(cli_ctx)(vmss_poll)

    # update cluster
    node_type.vm_instance_count = vmss.sku.capacity
    patch_request = ClusterUpdateParameters(node_types=cluster.node_types)

    return client.update(resource_group_name, cluster_name, patch_request)


def update_cluster_durability(cmd, client, resource_group_name, cluster_name, node_type, durability_level):
    cli_ctx = cmd.cli_ctx

    # get cluster node type durablity
    cluster = client.get(resource_group_name, cluster_name)
    node_type_refs = [n for n in cluster.node_types if n.name.lower() == node_type.lower()]
    if not node_type_refs:
        raise CLIError("Failed to find the node type in the cluster.")
    node_type_ref = node_type_refs[0]
    curr_node_type_durability = node_type_ref.durability_level

    # get vmss extension durability
    compute_client = compute_client_factory(cli_ctx)
    vmss = _get_cluster_vmss_by_node_type(compute_client, resource_group_name, cluster.cluster_id, node_type)
    _get_sf_vm_extension(vmss)
    fabric_ext_ref = _get_sf_vm_extension(vmss)
    if fabric_ext_ref is None:
        raise CLIError("Failed to find service fabric extension.")

    curr_vmss_durability_level = fabric_ext_ref.settings['durabilityLevel']

    # check upgrade
    if curr_node_type_durability.lower() != curr_vmss_durability_level.lower():
        logger.warning(
            "The durability level is currently mismatched between the cluster ('%s') and the VM extension ('%s').",
            curr_node_type_durability,
            curr_vmss_durability_level)

    # update cluster node type durability
    if curr_node_type_durability.lower() != durability_level.lower():
        node_type_ref.durability_level = durability_level
        patch_request = ClusterUpdateParameters(node_types=cluster.node_types)
        update_cluster_poll = client.update(resource_group_name, cluster_name, patch_request)
        LongRunningOperation(cli_ctx)(update_cluster_poll)

    # update vmss sf extension durability
    if curr_vmss_durability_level.lower() != durability_level.lower():
        fabric_ext_ref.settings['durabilityLevel'] = durability_level
        fabric_ext_ref.settings['enableParallelJobs'] = True
        vmss_poll = compute_client.virtual_machine_scale_sets.create_or_update(resource_group_name, vmss.name, vmss)
        LongRunningOperation(cli_ctx)(vmss_poll)

    return client.get(resource_group_name, cluster_name)


def update_cluster_upgrade_type(client,
                                resource_group_name,
                                cluster_name,
                                upgrade_mode,
                                version=None):
    if upgrade_mode.lower() != 'manual' and upgrade_mode.lower() != 'automatic':
        raise CLIError(
            '--upgrade-mode can either be \'manual\' or \'automatic\'')

    cluster = client.get(resource_group_name, cluster_name)
    patch_request = ClusterUpdateParameters(node_types=cluster.node_types)
    if upgrade_mode.lower() == 'manual':
        if version is None:
            raise CLIError(
                'When \'--upgrade-mode\' set to \'manual\', --version must be given')
        patch_request.cluster_code_version = version

    patch_request.upgrade_mode = upgrade_mode
    return client.update(resource_group_name, cluster_name, patch_request)


def set_cluster_setting(client,
                        resource_group_name,
                        cluster_name,
                        section=None,
                        parameter=None,
                        value=None,
                        settings_section_description=None):
    def _set(setting_dict, section, parameter, value):
        if section not in setting_dict:
            setting_dict[section] = {}
        setting_dict[section][parameter] = value
        return setting_dict
    if settings_section_description and (section or parameter or value):
        raise CLIError(
            'Only can use either \'--settings-section-description\' or \'--section\', \'--parameter\' and \'--value\' to set the settings')
    if section or parameter or value:
        if section is None or parameter is None or value is None:
            raise CLIError(
                '\'--section\' , \'--parameter\' and \'--value\' can not be None')
    cluster = client.get(resource_group_name, cluster_name)
    setting_dict = _fabric_settings_to_dict(cluster.fabric_settings)
    if settings_section_description:
        for setting in settings_section_description:
            if 'section' in setting and 'parameter' in setting and 'value' in setting:
                setting_dict = _set(setting_dict, setting['section'],
                                    setting['parameter'], setting['value'])
            else:
                raise CLIError('settings_section_description is invalid')
    else:
        setting_dict = _set(setting_dict, section, parameter, value)
    settings = _dict_to_fabric_settings(setting_dict)
    patch_request = ClusterUpdateParameters(fabric_settings=settings)
    return client.update(resource_group_name, cluster_name, patch_request)


def remove_cluster_setting(client,
                           resource_group_name,
                           cluster_name,
                           section=None,
                           parameter=None,
                           settings_section_description=None):
    def _remove(setting_dict, section, parameter):
        if section not in setting_dict:
            raise CLIError(
                "Can't find the section {} in the settings".format(section))
        if parameter not in setting_dict[section]:
            raise CLIError(
                "Can't find the parameter {} in the settings".format(parameter))
        del setting_dict[section][parameter]
        return setting_dict

    if settings_section_description and (section or parameter):
        raise CLIError(
            'Only can use either \'--settings-section-description\' or \'--section\' and \'--parameter \' to set the settings')
    cluster = client.get(resource_group_name, cluster_name)
    setting_dict = _fabric_settings_to_dict(cluster.fabric_settings)
    if settings_section_description:
        for setting in settings_section_description:
            if 'section' in setting and 'parameter' in setting:
                setting_dict = _remove(setting_dict, setting['section'], setting['parameter'])
            else:
                raise CLIError('settings_section_description is invalid')
    else:
        setting_dict = _remove(setting_dict, section, parameter)

    settings = _dict_to_fabric_settings(setting_dict)
    patch_request = ClusterUpdateParameters(fabric_settings=settings)
    return client.update(resource_group_name, cluster_name, patch_request)


def update_cluster_reliability_level(cmd,
                                     client,
                                     resource_group_name,
                                     cluster_name, reliability_level,
                                     auto_add_node=False):
    cli_ctx = cmd.cli_ctx
    reliability_level = reliability_level.lower()
    cluster = client.get(resource_group_name, cluster_name)
    instance_now = _get_target_instance(cluster.reliability_level)
    instance_target = _get_target_instance(reliability_level)
    node_types = [n for n in cluster.node_types if n.is_primary]
    if node_types is None:
        raise CLIError("Failed to find the node type in the cluster")
    node_type = node_types[0]
    compute_client = compute_client_factory(cli_ctx)
    vmss = _get_cluster_vmss_by_node_type(compute_client, resource_group_name, cluster.cluster_id, node_type.name)
    if instance_target == instance_now:
        return cluster
    if instance_target > instance_now:
        if vmss.sku.capacity < instance_target:
            if auto_add_node is not True:
                raise CLIError('Please use --auto_add_node to automatically increase the nodes,{} requires {} nodes, but currenty there are {}'.
                               format(reliability_level, instance_target, vmss.sku.capacity))
            vmss.sku.capacity = instance_target
            vmss_poll = compute_client.virtual_machine_scale_sets.create_or_update(
                resource_group_name, vmss.name, vmss)
            LongRunningOperation(cli_ctx)(vmss_poll)

    node_type.vm_instance_count = vmss.sku.capacity
    patch_request = ClusterUpdateParameters(
        node_types=cluster.node_types, reliability_level=reliability_level)
    return client.update(resource_group_name, cluster_name, patch_request)


def add_cluster_node_type(cmd,
                          client,
                          resource_group_name,
                          cluster_name,
                          node_type,
                          capacity,
                          vm_user_name,
                          vm_password,
                          vm_sku=DEFAULT_SKU,
                          vm_tier=DEFAULT_TIER,
                          durability_level=DEFAULT_DURABILITY_LEVEL):
    if durability_level.lower() == 'gold':
        if vm_sku.lower() != 'standard_d15_v2' and vm_sku.lower() != 'standard_g5':
            raise CLIError(
                'Only Standard_D15_v2 and Standard_G5 supports Gold durability, please specify --vm-sku to right value')
    cluster = client.get(resource_group_name, cluster_name)
    if any(n for n in cluster.node_types if n.name.lower() == node_type):
        raise CLIError("node type {} already exists in the cluster".format(node_type))

    _create_vmss(cmd, resource_group_name, cluster_name, cluster, node_type, durability_level, vm_password, vm_user_name, vm_sku, vm_tier, capacity)
    _add_node_type_to_sfrp(cmd, client, resource_group_name, cluster_name, cluster, node_type, capacity, durability_level)

    return client.get(resource_group_name, cluster_name)


def _add_node_type_to_sfrp(cmd, client, resource_group_name, cluster_name, cluster, node_type_name, capacity, durability_level):
    cluster.node_types.append(NodeTypeDescription(name=node_type_name,
                                                  client_connection_endpoint_port=DEFAULT_CLIENT_CONNECTION_ENDPOINT,
                                                  http_gateway_endpoint_port=DEFAULT_HTTP_GATEWAY_ENDPOINT,
                                                  is_primary=False,
                                                  vm_instance_count=int(capacity),
                                                  durability_level=durability_level,
                                                  application_ports=EndpointRangeDescription(
                                                      start_port=DEFAULT_APPLICATION_START_PORT, end_port=DEFAULT_APPLICATION_END_PORT),
                                                  ephemeral_ports=EndpointRangeDescription(
                                                      start_port=DEFAULT_EPHEMERAL_START, end_port=DEFAULT_EPHEMERAL_END)))

    patch_request = ClusterUpdateParameters(node_types=cluster.node_types)
    poller = client.update(resource_group_name, cluster_name, patch_request)
    LongRunningOperation(cmd.cli_ctx)(poller)


def _create_vmss(cmd, resource_group_name, cluster_name, cluster, node_type_name, durability_level, vm_password, vm_user_name, vm_sku, vm_tier, capacity):
    cli_ctx = cmd.cli_ctx
    subnet_name = "subnet_{}".format(1)
    network_client = network_client_factory(cli_ctx)
    location = _get_resource_group_by_name(cli_ctx, resource_group_name).location
    virtual_network = list(
        network_client.virtual_networks.list(resource_group_name))[0]
    subnets = list(network_client.subnets.list(
        resource_group_name, virtual_network.name))
    address_prefix = None
    index = None
    for x in range(1, 255):
        address_prefix = '10.0.{}.0/24'.format(x)
        index = x
        found = False
        for s in subnets:
            if address_prefix == s.address_prefix:
                found = True
            if subnet_name.lower() == s.name.lower():
                subnet_name = "subnet_{}".format(x)
        if found is False:
            break

    if address_prefix is None:
        raise CLIError("Failed to generate the address prefix")
    poller = network_client.subnets.create_or_update(resource_group_name,
                                                     virtual_network.name,
                                                     subnet_name,
                                                     Subnet(address_prefix=address_prefix))

    subnet = LongRunningOperation(cli_ctx)(poller)

    public_address_name = 'LBIP-{}-{}{}'.format(
        cluster_name.lower(), node_type_name.lower(), index)
    dns_label = '{}-{}{}'.format(cluster_name.lower(),
                                 node_type_name.lower(), index)
    lb_name = 'LB-{}-{}{}'.format(cluster_name.lower(),
                                  node_type_name.lower(), index)
    if len(lb_name) >= 24:
        lb_name = '{}{}'.format(lb_name[0:21], index)
    poller = network_client.public_ip_addresses.create_or_update(resource_group_name,
                                                                 public_address_name,
                                                                 PublicIPAddress(public_ip_allocation_method='Dynamic',
                                                                                 location=location,
                                                                                 dns_settings=PublicIPAddressDnsSettings(domain_name_label=dns_label)))

    publicIp = LongRunningOperation(cli_ctx)(poller)
    from azure.cli.core.commands.client_factory import get_subscription_id
    subscription_id = get_subscription_id(cli_ctx)
    new_load_balancer_id = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/loadBalancers/{}'.format(
        subscription_id, resource_group_name, lb_name)
    backend_address_poll_name = "LoadBalancerBEAddressPool"
    frontendip_configuration_name = "LoadBalancerIPConfig"
    probe_name = "FabricGatewayProbe"
    probe_http_name = "FabricHttpGatewayProbe"
    inbound_nat_pools_name = "LoadBalancerBEAddressNatPool"

    new_load_balancer = LoadBalancer(id=new_load_balancer_id,
                                     location=location,
                                     frontend_ip_configurations=[FrontendIPConfiguration(name=frontendip_configuration_name,
                                                                                         public_ip_address=PublicIPAddress(id=publicIp.id))],
                                     backend_address_pools=[BackendAddressPool(
                                         name=backend_address_poll_name)],
                                     load_balancing_rules=[LoadBalancingRule(name='LBRule',
                                                                             backend_address_pool=NetworkSubResource(id='/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/loadBalancers/{}/backendAddressPools/{}'.
                                                                                                                     format(subscription_id,
                                                                                                                            resource_group_name,
                                                                                                                            lb_name,
                                                                                                                            backend_address_poll_name)),
                                                                             backend_port=DEFAULT_TCP_PORT,
                                                                             enable_floating_ip=False,
                                                                             frontend_ip_configuration=NetworkSubResource(id='/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/loadBalancers/{}/frontendIPConfigurations/{}'.format(subscription_id,
                                                                                                                                                                                                                                                   resource_group_name,
                                                                                                                                                                                                                                                   lb_name,
                                                                                                                                                                                                                                                   frontendip_configuration_name)),
                                                                             frontend_port=DEFAULT_TCP_PORT,
                                                                             idle_timeout_in_minutes=5,
                                                                             protocol='tcp',
                                                                             probe=NetworkSubResource(id='/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/loadBalancers/{}/probes/{}'.format(subscription_id,
                                                                                                                                                                                                             resource_group_name,
                                                                                                                                                                                                             lb_name,
                                                                                                                                                                                                             probe_name))),
                                                           LoadBalancingRule(name='LBHttpRule',
                                                                             backend_address_pool=NetworkSubResource(id='/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/loadBalancers/{}/backendAddressPools/{}'.format(subscription_id,
                                                                                                                                                                                                                                         resource_group_name,
                                                                                                                                                                                                                                         lb_name,
                                                                                                                                                                                                                                         backend_address_poll_name)),
                                                                             backend_port=DEFAULT_HTTP_PORT,
                                                                             enable_floating_ip=False,
                                                                             frontend_ip_configuration=NetworkSubResource(id='/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/loadBalancers/{}/frontendIPConfigurations/{}'.format(subscription_id,
                                                                                                                                                                                                                                                   resource_group_name,
                                                                                                                                                                                                                                                   lb_name,
                                                                                                                                                                                                                                                   frontendip_configuration_name)),
                                                                             frontend_port=DEFAULT_HTTP_PORT,
                                                                             idle_timeout_in_minutes=5,
                                                                             protocol='tcp',
                                                                             probe=NetworkSubResource(id='/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/loadBalancers/{}/probes/{}'.format(subscription_id,
                                                                                                                                                                                                             resource_group_name,
                                                                                                                                                                                                             lb_name,
                                                                                                                                                                                                             probe_http_name)))],
                                     probes=[Probe(protocol='tcp',
                                                   name=probe_name,
                                                   interval_in_seconds=5,
                                                   number_of_probes=2,
                                                   port=DEFAULT_TCP_PORT),
                                             Probe(protocol='tcp',
                                                   name=probe_http_name,
                                                   interval_in_seconds=5,
                                                   number_of_probes=2,
                                                   port=DEFAULT_HTTP_PORT)],

                                     inbound_nat_pools=[InboundNatPool(protocol='tcp',
                                                                       name=inbound_nat_pools_name,
                                                                       backend_port=DEFAULT_BACKEND_PORT,
                                                                       frontend_ip_configuration=NetworkSubResource(id='/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/loadBalancers/{}/frontendIPConfigurations/{}'.format(subscription_id,
                                                                                                                                                                                                                                             resource_group_name,
                                                                                                                                                                                                                                             lb_name,
                                                                                                                                                                                                                                             frontendip_configuration_name)),
                                                                       frontend_port_range_start=DEFAULT_FRONTEND_PORT_RANGE_START,
                                                                       frontend_port_range_end=DEFAULT_FRONTEND_PORT_RANGE_END)])

    poller = network_client.load_balancers.create_or_update(
        resource_group_name, lb_name, new_load_balancer)
    LongRunningOperation(cli_ctx)(poller)

    new_load_balancer = network_client.load_balancers.get(
        resource_group_name, lb_name)
    backend_address_pools = []
    inbound_nat_pools = []
    for p in new_load_balancer.backend_address_pools:
        backend_address_pools.append(SubResource(id=p.id))
    for p in new_load_balancer.inbound_nat_pools:
        inbound_nat_pools.append(SubResource(id=p.id))

    network_config_name = 'NIC-{}-{}'.format(node_type_name.lower(), node_type_name.lower())
    if len(network_config_name) >= 24:
        network_config_name = network_config_name[0:22]

    ip_config_name = 'Nic-{}'.format(node_type_name.lower())
    if len(ip_config_name) >= 24:
        ip_config_name = network_config_name[0:22]
    vm_network_profile = VirtualMachineScaleSetNetworkProfile(network_interface_configurations=[VirtualMachineScaleSetNetworkConfiguration(name=network_config_name,
                                                                                                                                           primary=True,
                                                                                                                                           ip_configurations=[VirtualMachineScaleSetIPConfiguration(name=ip_config_name,
                                                                                                                                                                                                    load_balancer_backend_address_pools=backend_address_pools,
                                                                                                                                                                                                    load_balancer_inbound_nat_pools=inbound_nat_pools,
                                                                                                                                                                                                    subnet=ApiEntityReference(id=subnet.id))])])
    compute_client = compute_client_factory(cli_ctx)

    node_type_name_ref = cluster.node_types[0].name
    vmss_reference = _get_cluster_vmss_by_node_type(compute_client, resource_group_name, cluster.cluster_id, node_type_name_ref)

    def create_vhd(cli_ctx, resource_group_name, cluster_name, node_type, location):
        storage_name = '{}{}'.format(cluster_name.lower(), node_type.lower())
        name = ""
        vhds = []
        for n in storage_name:
            if n.isalpha() or n.isdigit():
                name += n
            if len(name) >= 21:
                break
        for i in range(1, 6):
            acc = create_storage_account(
                cli_ctx, resource_group_name.lower(), '{}{}'.format(name, i), location)
            vhds.append('{}{}'.format(acc[0].primary_endpoints.blob, 'vhd'))
        return vhds

    def create_storage_account(cli_ctx, resource_group_name, storage_name, location):
        from azure.mgmt.storage.models import Sku, SkuName
        storage_client = storage_client_factory(cli_ctx)
        LongRunningOperation(cli_ctx)(storage_client.storage_accounts.create(resource_group_name,
                                                                             storage_name,
                                                                             StorageAccountCreateParameters(sku=Sku(name=SkuName.standard_lrs),
                                                                                                            kind='storage',
                                                                                                            location=location)))

        acc_prop = storage_client.storage_accounts.get_properties(
            resource_group_name, storage_name)
        acc_keys = storage_client.storage_accounts.list_keys(
            resource_group_name, storage_name)
        return acc_prop, acc_keys

    publisher = 'MicrosoftWindowsServer'
    offer = 'WindowsServer'
    version = 'latest'
    sku = os_dic[DEFAULT_OS]
    if cluster.vm_image.lower() == 'linux':
        publisher = 'Canonical'
        offer = 'UbuntuServer'
        version = 'latest'
        sku = os_dic['UbuntuServer1604']
    storage_profile = VirtualMachineScaleSetStorageProfile(image_reference=ImageReference(publisher=publisher,
                                                                                          offer=offer,
                                                                                          sku=sku,
                                                                                          version=version),
                                                           os_disk=VirtualMachineScaleSetOSDisk(caching='ReadOnly',
                                                                                                create_option='FromImage',
                                                                                                name='vmssosdisk',
                                                                                                vhd_containers=create_vhd(cli_ctx, resource_group_name, cluster_name, node_type_name, location)))

    os_profile = VirtualMachineScaleSetOSProfile(computer_name_prefix=node_type_name,
                                                 admin_password=vm_password,
                                                 admin_username=vm_user_name,
                                                 secrets=vmss_reference.virtual_machine_profile.os_profile.secrets)

    diagnostics_storage_name = cluster.diagnostics_storage_account_config.storage_account_name

    diagnostics_ext = None
    fabric_ext = None
    diagnostics_exts = [e for e in vmss_reference.virtual_machine_profile.extension_profile.extensions if e.type1.lower(
    ) == 'IaaSDiagnostics'.lower()]
    if any(diagnostics_exts):
        diagnostics_ext = diagnostics_exts[0]
        diagnostics_account = diagnostics_ext.settings['StorageAccount']
        storage_client = storage_client_factory(cli_ctx)
        list_results = storage_client.storage_accounts.list_keys(
            resource_group_name, diagnostics_account)
        import json
        json_data = json.loads(
            '{"storageAccountName": "", "storageAccountKey": "", "storageAccountEndPoint": ""}')
        json_data['storageAccountName'] = diagnostics_account
        json_data['storageAccountKey'] = list_results.keys[0].value
        json_data['storageAccountEndPoint'] = "https://core.windows.net/"
        diagnostics_ext.protected_settings = json_data

    fabric_exts = [e for e in vmss_reference.virtual_machine_profile.extension_profile.extensions if e.type1.lower(
    ) == SERVICE_FABRIC_WINDOWS_NODE_EXT_NAME or e.type1.lower() == SERVICE_FABRIC_LINUX_NODE_EXT_NAME]
    if any(fabric_exts):
        fabric_ext = fabric_exts[0]

    if fabric_ext is None:
        raise CLIError("No valid fabric extension found")

    fabric_ext.settings['nodeTypeRef'] = node_type_name
    fabric_ext.settings['durabilityLevel'] = durability_level
    if 'nicPrefixOverride' not in fabric_ext.settings:
        fabric_ext.settings['nicPrefixOverride'] = address_prefix
    storage_client = storage_client_factory(cli_ctx)
    list_results = storage_client.storage_accounts.list_keys(
        resource_group_name, diagnostics_storage_name)
    import json
    json_data = json.loads(
        '{"StorageAccountKey1": "", "StorageAccountKey2": ""}')
    fabric_ext.protected_settings = json_data
    fabric_ext.protected_settings['StorageAccountKey1'] = list_results.keys[0].value
    fabric_ext.protected_settings['StorageAccountKey2'] = list_results.keys[1].value

    extensions = [fabric_ext]
    if diagnostics_ext:
        extensions.append(diagnostics_ext)
    vm_ext_profile = VirtualMachineScaleSetExtensionProfile(
        extensions=extensions)

    virtual_machine_scale_set_profile = VirtualMachineScaleSetVMProfile(extension_profile=vm_ext_profile,
                                                                        os_profile=os_profile,
                                                                        storage_profile=storage_profile,
                                                                        network_profile=vm_network_profile)

    poller = compute_client.virtual_machine_scale_sets.create_or_update(resource_group_name,
                                                                        node_type_name,
                                                                        VirtualMachineScaleSet(location=location,
                                                                                               sku=ComputeSku(
                                                                                                   name=vm_sku, tier=vm_tier, capacity=capacity),
                                                                                               overprovision=False,
                                                                                               upgrade_policy=UpgradePolicy(
                                                                                                   mode=UpgradeMode.automatic),
                                                                                               virtual_machine_profile=virtual_machine_scale_set_profile))
    LongRunningOperation(cli_ctx)(poller)


def _get_cluster_vmss_by_node_type(compute_client, resource_group_name, cluster_id, node_type_name):

    vmsses = list(compute_client.virtual_machine_scale_sets.list(resource_group_name))

    for vmss in vmsses:
        fabric_ext = _get_sf_vm_extension(vmss)
        if fabric_ext is not None:
            curr_cluster_id = _get_cluster_id_in_sf_extension(fabric_ext)
            if curr_cluster_id.lower() == cluster_id.lower() and fabric_ext.settings["nodeTypeRef"].lower() == node_type_name.lower():
                return vmss
    raise CLIError("Failed to find vmss in resource group {} for cluster id {} and node type {}".format(resource_group_name, cluster_id, node_type_name))


def _verify_cert_function_parameter(certificate_file=None,
                                    certificate_password=None,
                                    vault_name=None,  # pylint: disable=unused-argument
                                    vault_resource_group_name=None,  # pylint: disable=unused-argument
                                    certificate_output_folder=None,
                                    certificate_subject_name=None,
                                    secret_identifier=None):
    if certificate_file:
        if certificate_subject_name:
            raise CLIError(
                '\'--certificate-subject-name\' is ingored if \'--certificate-file\' is present')
        if certificate_output_folder:
            raise CLIError(
                '\'--certificate-output-folder\' is ingored if \'--certificate-file\' is present')
    else:
        if secret_identifier:
            if certificate_file:
                raise CLIError(
                    '\'--certificate-file\' is ingored if \'--secret-identifier\' is present')
            if certificate_password:
                raise CLIError(
                    '\'--certificate-password\' is ingored if \'--secret-identifier\' is present')
            if certificate_output_folder:
                raise CLIError(
                    '\'--certificate-output-folder\' is ingored if \'--secret-identifier\' is present')
            if certificate_subject_name:
                raise CLIError(
                    '\'--certificate-subject-name\' is ingored if \'--secret-identifier\' is present')
        else:
            if certificate_subject_name:
                if certificate_file:
                    raise CLIError(
                        '\'--certificate-file\' is ingored if \'--secret-identifier\' is present')
                if secret_identifier:
                    raise CLIError(
                        '\'--secret-identifier\' is ingored if \'--secret-identifier\' is present')
            else:
                raise CLIError("Invalid input")


def _create_certificate(cmd,
                        cli_ctx,
                        resource_group_name,
                        certificate_file=None,
                        certificate_password=None,
                        vault_name=None,
                        vault_resource_group_name=None,
                        certificate_output_folder=None,
                        certificate_subject_name=None,
                        secret_identifier=None):
    _verify_cert_function_parameter(certificate_file, certificate_password,
                                    vault_name, vault_resource_group_name,
                                    certificate_output_folder,
                                    certificate_subject_name,
                                    secret_identifier)

    output_file = None
    rg = _get_resource_group_by_name(cli_ctx, resource_group_name)
    location = rg.location

    vault_id = None
    secret_url = None
    certificate_thumbprint = None

    VaultProperties = cmd.get_models('VaultProperties', resource_type=ResourceType.MGMT_KEYVAULT)
    _create_keyvault.__doc__ = VaultProperties.__doc__

    if secret_identifier is not None:
        vault = _get_vault_from_secret_identifier(cli_ctx, secret_identifier)
        vault_id = vault.id
        certificate_thumbprint = _get_thumbprint_from_secret_identifier(
            cli_ctx, vault, secret_identifier)
        secret_url = secret_identifier

    else:
        if vault_resource_group_name is None:
            logger.info("vault_resource_group_name not set, using %s.", resource_group_name)
            vault_resource_group_name = resource_group_name

        if vault_name is None:
            logger.info("vault_name not set using '%s' as vault name.", vault_resource_group_name)
            vault_name = vault_resource_group_name

        vault = _safe_get_vault(cli_ctx, vault_resource_group_name, vault_name)

        if certificate_file is not None:
            if vault is None:
                logger.info("Creating key vault")
                vault = _create_keyvault(
                    cmd, cli_ctx, vault_resource_group_name, vault_name, location, enabled_for_deployment=True).result()
            vault_uri = vault.properties.vault_uri
            certificate_name = _get_certificate_name(certificate_subject_name, resource_group_name)
            logger.info("Import certificate")
            result = import_certificate(
                cli_ctx, vault_uri, certificate_name, certificate_file, password=certificate_password)
            vault_id = vault.id
            secret_url = result.sid
            import base64
            certificate_thumbprint = b64_to_hex(
                base64.b64encode(result.x509_thumbprint))

        else:
            if vault is None:
                logger.info("Creating key vault")
                if cmd.supported_api_version(resource_type=ResourceType.MGMT_KEYVAULT, min_api='2018-02-14'):
                    vault = _create_keyvault(
                        cmd, cli_ctx, vault_resource_group_name, vault_name, location, enabled_for_deployment=True).result()
                else:
                    vault = _create_keyvault(
                        cmd, cli_ctx, vault_resource_group_name, vault_name, location, enabled_for_deployment=True)
                logger.info("Wait for key vault ready")
                time.sleep(20)
            vault_uri = vault.properties.vault_uri
            certificate_name = _get_certificate_name(certificate_subject_name, resource_group_name)

            policy = _get_default_policy(cli_ctx, certificate_subject_name)
            logger.info("Creating self-signed certificate")
            _create_self_signed_key_vault_certificate.__doc__ = get_sdk(cli_ctx, ResourceType.DATA_KEYVAULT, 'key_vault_client#KeyVaultClient').__doc__
            result = _create_self_signed_key_vault_certificate(
                cli_ctx, vault_uri, certificate_name, policy, certificate_output_folder=certificate_output_folder)
            kv_result = result[0]
            output_file = result[1]
            vault_id = vault.id
            secret_url = kv_result.sid
            import base64
            certificate_thumbprint = b64_to_hex(
                base64.b64encode(kv_result.x509_thumbprint))

    return vault_id, secret_url, certificate_thumbprint, output_file


# pylint: disable=inconsistent-return-statements
def _add_cert_to_vmss(cli_ctx, vmss, resource_group_name, vault_id, secret_url):
    compute_client = compute_client_factory(cli_ctx)
    secrets = [
        s for s in vmss.virtual_machine_profile.os_profile.secrets if s.source_vault.id == vault_id]
    if secrets is None or secrets == []:
        if vmss.virtual_machine_profile.os_profile.secrets is None:
            vmss.virtual_machine_profile.os_profile.secrets = []
        new_vault_certificates = []
        new_vault_certificates.append(VaultCertificate(certificate_url=secret_url, certificate_store='my'))
        new_source_vault = SubResource(id=vault_id)
        vmss.virtual_machine_profile.os_profile.secrets.append(VaultSecretGroup(source_vault=new_source_vault,
                                                                                vault_certificates=new_vault_certificates))
    else:
        if secrets[0].vault_certificates is not None:
            certs = [
                c for c in secrets[0].vault_certificates if c.certificate_url == secret_url]
            if certs is None or certs == []:
                secrets[0].vault_certificates.append(
                    VaultCertificate(certificate_url=secret_url, certificate_store='my'))
            else:
                return
        else:
            secrets[0].vault_certificates = []
            secrets[0].vault_certificates.append(
                VaultCertificate(secret_url, 'my'))

    poller = compute_client.virtual_machine_scale_sets.create_or_update(
        resource_group_name, vmss.name, vmss)
    return LongRunningOperation(cli_ctx)(poller)


def _get_sf_vm_extension(vmss):
    fabric_ext = [ext for ext in vmss.virtual_machine_profile.extension_profile.extensions
                  if ext.type1 is not None and (ext.type1.lower() == SERVICE_FABRIC_WINDOWS_NODE_EXT_NAME or ext.type1.lower() == SERVICE_FABRIC_LINUX_NODE_EXT_NAME)]
    if fabric_ext is None or fabric_ext == []:
        return None
    return fabric_ext[0]


def _get_cluster_id_in_sf_extension(fabric_ext):
    cluster_endpoint = fabric_ext.settings["clusterEndpoint"]
    endpoint_list = cluster_endpoint.split('/')
    cluster_id = endpoint_list[len(endpoint_list) - 1]
    return cluster_id


def _add_cert_to_all_vmss(cli_ctx, resource_group_name, cluster_id, vault_id, secret_url):
    threads = []
    import threading
    compute_client = compute_client_factory(cli_ctx)
    vmsses = list(compute_client.virtual_machine_scale_sets.list(resource_group_name))
    if vmsses is not None:
        for vmss in vmsses:
            fabric_ext = _get_sf_vm_extension(vmss)
            if fabric_ext is not None and (cluster_id is None or _get_cluster_id_in_sf_extension(fabric_ext).lower() == cluster_id.lower()):
                t = threading.Thread(target=_add_cert_to_vmss, args=[cli_ctx, vmss, resource_group_name, vault_id, secret_url])
                t.start()
                threads.append(t)

    for t in threads:
        t.join()


def _get_resource_group_by_name(cli_ctx, resource_group_name):
    try:
        resouce_client = resource_client_factory(cli_ctx).resource_groups
        return resouce_client.get(resource_group_name)
    except Exception as ex:  # pylint: disable=broad-except
        error = getattr(ex, 'Azure Error', ex)
        if error != 'ResourceGroupNotFound':
            return None
        raise


def _create_resource_group_name(cli_ctx, rg_name, location, tags=None):
    ResourceGroup = get_sdk(cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES, 'ResourceGroup', mod='models')
    client = resource_client_factory(cli_ctx).resource_groups
    parameters = ResourceGroup(location=location, tags=tags)
    client.create_or_update(rg_name, parameters)


# pylint: disable=inconsistent-return-statements
def _get_target_instance(reliability_level):
    level = reliability_level.lower()
    if level == 'none':
        return 1
    if level == 'bronze':
        return 3
    if level == 'silver':
        return 5
    if level == 'gold':
        return 7
    if level == 'platinum':
        return 9


# pylint: disable=inconsistent-return-statements
def _get_reliability_level(cluster_size):
    size = int(cluster_size)
    if size > 0 and size < 3:
        return 'None'
    if size >= 3 and size < 5:
        return 'Bronze'
    if size >= 5 and size < 7:
        return 'Silver'
    if size >= 7 and size < 9:
        return 'Gold'
    if size >= 9:
        return 'Platinum'


def _fabric_settings_to_dict(fabric_settings):
    d = {}
    if fabric_settings:
        for s1 in fabric_settings:
            section_name = s1.name
            if section_name not in d:
                d[section_name] = {}
            if s1.parameters:
                for s2 in s1.parameters:
                    parameter_name = s2.name
                    d[section_name][parameter_name] = s2.value
    return d


def _dict_to_fabric_settings(setting_dict):
    settings = []
    if setting_dict and any(setting_dict):
        for k, v in setting_dict.items():
            parameters = []
            setting_des = SettingsSectionDescription(name=k, parameters=parameters)
            for kk, vv in v.items():
                setting_des.parameters.append(
                    SettingsParameterDescription(name=kk, value=vv))
            if setting_des.parameters and any(setting_des.parameters):
                settings.append(setting_des)
    return settings


def _deploy_arm_template_core(cli_ctx,
                              resource_group_name,
                              template,
                              parameters,
                              deployment_name=None,
                              mode='incremental',
                              validate_only=False,
                              no_wait=False):
    DeploymentProperties = get_sdk(cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES, 'DeploymentProperties', mod='models')

    properties = DeploymentProperties(
        template=template, template_link=None, parameters=parameters, mode=mode)
    client = resource_client_factory(cli_ctx)
    if validate_only:
        return sdk_no_wait(no_wait, client.deployments.validate, resource_group_name, deployment_name, properties)

    deploy_poll = sdk_no_wait(no_wait, client.deployments.create_or_update, resource_group_name,
                              deployment_name, properties)
    result = LongRunningOperation(cli_ctx)(deploy_poll)
    return result


def _get_vault_name(resource_group_name, vault_name):
    if not vault_name:
        return resource_group_name
    return vault_name


def _get_certificate_name(certificate_subject_name, resource_group_name):
    if certificate_subject_name is None:
        certificate_name = resource_group_name
    else:
        certificate_name = certificate_subject_name

    name = ""
    for n in certificate_name:
        if n.isalpha() or n == '-' or n.isdigit():
            name += n
    certificate_name = name

    if certificate_subject_name is None:
        import datetime
        suffix = datetime.datetime.now().strftime("%Y%m%d%H%M")
        certificate_name = "{}{}".format(certificate_name, suffix)

    return certificate_name


# pylint: disable=inconsistent-return-statements
def _get_vault_from_secret_identifier(cli_ctx, secret_identifier):
    key_vault_client = keyvault_client_factory(cli_ctx).vaults
    vault_name = urlparse(secret_identifier).hostname.split('.')[0]
    vaults = key_vault_client.list()
    if vaults is not None:
        vault = [v for v in vaults if v.name.lower() == vault_name.lower()]
        if vault:
            return vault[0]
    raise CLIError("Unable to find vault with name '{}'. Please make sure the secret identifier '{}' is correct.".format(vault_name, secret_identifier))


def _get_vault_uri_and_resource_group_name(cli_ctx, vault):
    client = keyvault_client_factory(cli_ctx).vaults
    vault_resource_group_name = vault.id.split('/')[4]
    v = client.get(vault_resource_group_name, vault.name)
    vault_uri = v.properties.vault_uri
    return vault_uri, vault_resource_group_name


def _safe_get_vault(cli_ctx, resource_group_name, vault_name):
    key_vault_client = keyvault_client_factory(cli_ctx).vaults
    try:
        vault = key_vault_client.get(resource_group_name, vault_name)
        return vault
    except CloudError as ex:
        if ex.error.error == 'ResourceNotFound':
            return None
        raise


def _asn1_to_iso8601(asn1_date):
    import dateutil.parser
    if isinstance(asn1_date, bytes):
        asn1_date = asn1_date.decode('utf-8')
    return dateutil.parser.parse(asn1_date)


def _get_thumbprint_from_secret_identifier(cli_ctx, vault, secret_identifier):
    secret_uri = urlparse(secret_identifier)
    path = secret_uri.path
    segment = path.split('/')
    secret_name = segment[2]
    secret_version = segment[3]
    vault_uri_group = _get_vault_uri_and_resource_group_name(cli_ctx, vault)
    vault_uri = vault_uri_group[0]
    client_not_arm = _get_keyVault_not_arm_client(cli_ctx)
    secret = client_not_arm.get_secret(vault_uri, secret_name, secret_version)
    cert_bytes = secret.value
    x509 = None
    import base64
    decoded = base64.b64decode(cert_bytes)
    try:
        x509 = crypto.load_pkcs12(decoded).get_certificate()
    except (ValueError, crypto.Error):
        pass

    if not x509:
        x509 = crypto.load_certificate(crypto.FILETYPE_PEM, cert_bytes)

    if not x509:
        raise Exception('invalid certificate')

    thumbprint = x509.digest("sha1").decode("utf-8").replace(':', '')
    return thumbprint


def _get_certificate(client, vault_base_url, certificate_name):
    """ Download a certificate from a KeyVault. """
    cert = client.get_certificate(vault_base_url, certificate_name, '')
    return cert


def import_certificate(cli_ctx, vault_base_url, certificate_name, certificate_data,
                       disabled=False, password=None, certificate_policy=None, tags=None):
    CertificateAttributes = get_sdk(cli_ctx, ResourceType.DATA_KEYVAULT, 'models.certificate_attributes#CertificateAttributes')
    CertificatePolicy = get_sdk(cli_ctx, ResourceType.DATA_KEYVAULT, 'models.certificate_policy#CertificatePolicy')
    SecretProperties = get_sdk(cli_ctx, ResourceType.DATA_KEYVAULT, 'models.secret_properties#SecretProperties')
    import binascii
    certificate_data = open(certificate_data, 'rb').read()
    x509 = None
    content_type = None
    try:
        x509 = crypto.load_certificate(crypto.FILETYPE_PEM, certificate_data)
        # if we get here, we know it was a PEM file
        content_type = 'application/x-pem-file'
        try:
            # for PEM files (including automatic endline conversion for
            # Windows)
            certificate_data = certificate_data.decode(
                'utf-8').replace('\r\n', '\n')
        except UnicodeDecodeError:
            certificate_data = binascii.b2a_base64(
                certificate_data).decode('utf-8')
    except (ValueError, crypto.Error):
        pass

    if not x509:
        try:
            if password:
                x509 = crypto.load_pkcs12(
                    certificate_data, password).get_certificate()
            else:
                x509 = crypto.load_pkcs12(certificate_data).get_certificate()
            content_type = 'application/x-pkcs12'
            certificate_data = binascii.b2a_base64(
                certificate_data).decode('utf-8')
        except crypto.Error:
            raise CLIError(
                'We could not parse the provided certificate as .pem or .pfx. '
                'Please verify the certificate with OpenSSL.')

    not_before, not_after = None, None

    if x509.get_notBefore():
        not_before = _asn1_to_iso8601(x509.get_notBefore())

    if x509.get_notAfter():
        not_after = _asn1_to_iso8601(x509.get_notAfter())

    cert_attrs = CertificateAttributes(enabled=not disabled,
                                       not_before=not_before,
                                       expires=not_after)

    if certificate_policy:
        secret_props = certificate_policy.get('secret_properties')
        if secret_props:
            secret_props['content_type'] = content_type
        elif certificate_policy and not secret_props:
            certificate_policy['secret_properties'] = SecretProperties(
                content_type=content_type)
    else:
        certificate_policy = CertificatePolicy(
            secret_properties=SecretProperties(content_type=content_type))

    logger.info("Starting 'keyvault certificate import'")
    client_not_arm = _get_keyVault_not_arm_client(cli_ctx)
    result = client_not_arm.import_certificate(cli_ctx=cli_ctx,
                                               vault_base_url=vault_base_url,
                                               certificate_name=certificate_name,
                                               base64_encoded_certificate=certificate_data,
                                               certificate_attributes=cert_attrs,
                                               certificate_policy=certificate_policy,
                                               tags=tags,
                                               password=password)

    logger.info("Finished 'keyvault certificate import'")
    return result


def _download_secret(cli_ctx, vault_base_url, secret_name, pem_path, pfx_path, secret_version=''):
    client = _get_keyVault_not_arm_client(cli_ctx)
    secret = client.get_secret(vault_base_url, secret_name, secret_version)
    secret_value = secret.value
    if pem_path:
        try:
            import base64
            decoded = base64.b64decode(secret_value)
            p12 = crypto.load_pkcs12(decoded)
            f_pem = open(pem_path, 'wb')
            f_pem.write(crypto.dump_privatekey(
                crypto.FILETYPE_PEM, p12.get_privatekey()))
            f_pem.write(crypto.dump_certificate(
                crypto.FILETYPE_PEM, p12.get_certificate()))
            ca = p12.get_ca_certificates()
            if ca is not None:
                for cert in ca:
                    f_pem.write(crypto.dump_certificate(
                        crypto.FILETYPE_PEM, cert))
            f_pem.close()
        except Exception as ex:  # pylint: disable=broad-except
            if os.path.isfile(pem_path):
                os.remove(pem_path)
            raise ex

    if pfx_path:
        try:
            import base64
            decoded = base64.b64decode(secret_value)
            p12 = crypto.load_pkcs12(decoded)
            with open(pfx_path, 'wb') as f:
                f.write(decoded)
        except Exception as ex:  # pylint: disable=broad-except
            if os.path.isfile(pfx_path):
                os.remove(pfx_path)
            raise ex


def _get_default_policy(cli_ctx, subject):
    if subject.lower().startswith('cn') is not True:
        subject = "CN={0}".format(subject)
    return _default_certificate_profile(cli_ctx, subject)


def _default_certificate_profile(cli_ctx, subject):
    CertificateAttributes = get_sdk(cli_ctx, ResourceType.DATA_KEYVAULT, 'models.certificate_attributes#CertificateAttributes')
    CertificatePolicy = get_sdk(cli_ctx, ResourceType.DATA_KEYVAULT, 'models.certificate_policy#CertificatePolicy')
    ActionType = get_sdk(cli_ctx, ResourceType.DATA_KEYVAULT, 'models.key_vault_client_enums#ActionType')
    KeyUsageType = get_sdk(cli_ctx, ResourceType.DATA_KEYVAULT, 'models.key_vault_client_enums#KeyUsageType')
    IssuerParameters = get_sdk(cli_ctx, ResourceType.DATA_KEYVAULT, 'models.issuer_parameters#IssuerParameters')
    KeyProperties = get_sdk(cli_ctx, ResourceType.DATA_KEYVAULT, 'models.key_properties#KeyProperties')
    LifetimeAction = get_sdk(cli_ctx, ResourceType.DATA_KEYVAULT, 'models.lifetime_action#LifetimeAction')
    SecretProperties = get_sdk(cli_ctx, ResourceType.DATA_KEYVAULT, 'models.secret_properties#SecretProperties')
    X509CertificateProperties = get_sdk(cli_ctx, ResourceType.DATA_KEYVAULT, 'models.x509_certificate_properties#X509CertificateProperties')
    Trigger = get_sdk(cli_ctx, ResourceType.DATA_KEYVAULT, 'models.trigger#Trigger')
    Action = get_sdk(cli_ctx, ResourceType.DATA_KEYVAULT, 'models.action#Action')
    template = CertificatePolicy(key_properties=KeyProperties(exportable=True,
                                                              key_type=u'RSA',
                                                              key_size=2048,
                                                              reuse_key=True),
                                 secret_properties=SecretProperties(
                                     content_type=u'application/x-pkcs12'),
                                 x509_certificate_properties=X509CertificateProperties(key_usage=[KeyUsageType.c_rl_sign,
                                                                                                  KeyUsageType.data_encipherment,
                                                                                                  KeyUsageType.digital_signature,
                                                                                                  KeyUsageType.key_encipherment,
                                                                                                  KeyUsageType.key_agreement,
                                                                                                  KeyUsageType.key_cert_sign],
                                                                                       subject=subject,
                                                                                       validity_in_months=12),
                                 lifetime_actions=[LifetimeAction(trigger=Trigger(days_before_expiry=90),
                                                                  action=Action(action_type=ActionType.auto_renew))],
                                 issuer_parameters=IssuerParameters(
                                     name=u'Self',),
                                 attributes=CertificateAttributes(enabled=True))

    return template


def _create_self_signed_key_vault_certificate(cli_ctx, vault_base_url, certificate_name, certificate_policy, certificate_output_folder=None, disabled=False, tags=None, validity=None):
    CertificateAttributes = get_sdk(cli_ctx, ResourceType.DATA_KEYVAULT, 'models.certificate_attributes#CertificateAttributes')
    cert_attrs = CertificateAttributes(enabled=not disabled)
    logger.info("Starting long-running operation 'keyvault certificate create'")
    if validity is not None:
        certificate_policy['x509_certificate_properties']['validity_in_months'] = validity
    client = _get_keyVault_not_arm_client(cli_ctx)
    client.create_certificate(
        vault_base_url, certificate_name, certificate_policy, cert_attrs, tags)

    # otherwise loop until the certificate creation is complete
    while True:
        check = client.get_certificate_operation(
            vault_base_url, certificate_name)
        if check.status != 'inProgress':
            logger.info("Long-running operation 'keyvault certificate create' finished with result %s.",
                        check)
            break
        try:
            time.sleep(10)
        except KeyboardInterrupt:
            logger.info("Long-running operation wait cancelled.")
            raise
        except Exception as client_exception:
            message = getattr(client_exception, 'message', client_exception)
            import json
            try:
                message = str(message) + ' ' + json.loads(
                    client_exception.response.text)['error']['details'][0]['message']   # pylint: disable=no-member
            except:  # pylint: disable=bare-except
                pass

            raise CLIError('{}'.format(message))

    pem_output_folder = None
    if certificate_output_folder is not None:
        os.makedirs(certificate_output_folder, exist_ok=True)
        pem_output_folder = os.path.join(
            certificate_output_folder, certificate_name + '.pem')
        pfx_output_folder = os.path.join(
            certificate_output_folder, certificate_name + '.pfx')
        _download_secret(cli_ctx, vault_base_url, certificate_name,
                         pem_output_folder, pfx_output_folder)
    return client.get_certificate(vault_base_url, certificate_name, ''), pem_output_folder


def _get_keyVault_not_arm_client(cli_ctx):
    from azure.cli.core._profile import Profile
    version = str(get_api_version(cli_ctx, ResourceType.DATA_KEYVAULT))

    def get_token(server, resource, scope):  # pylint: disable=unused-argument
        return Profile(cli_ctx=cli_ctx).get_login_credentials(resource)[0]._token_retriever()  # pylint: disable=protected-access

    client = KeyVaultClient(KeyVaultAuthentication(get_token), api_version=version)
    return client


def _create_keyvault(cmd,
                     cli_ctx,
                     resource_group_name,
                     vault_name,
                     location=None,
                     sku=None,
                     enabled_for_deployment=True,
                     enabled_for_disk_encryption=None,
                     enabled_for_template_deployment=None,
                     no_self_perms=None, tags=None):

    from azure.cli.core._profile import Profile
    from azure.graphrbac.models import GraphErrorException
    profile = Profile(cli_ctx=cli_ctx)
    cred, _, tenant_id = profile.get_login_credentials(
        resource=cli_ctx.cloud.endpoints.active_directory_graph_resource_id)
    graph_client = GraphRbacManagementClient(cred,
                                             tenant_id,
                                             base_url=cli_ctx.cloud.endpoints.active_directory_graph_resource_id)
    subscription = profile.get_subscription()
    VaultCreateOrUpdateParameters = cmd.get_models('VaultCreateOrUpdateParameters', resource_type=ResourceType.MGMT_KEYVAULT)
    VaultProperties = cmd.get_models('VaultProperties', resource_type=ResourceType.MGMT_KEYVAULT)
    KeyVaultSku = cmd.get_models('Sku', resource_type=ResourceType.MGMT_KEYVAULT)
    AccessPolicyEntry = cmd.get_models('AccessPolicyEntry', resource_type=ResourceType.MGMT_KEYVAULT)
    Permissions = cmd.get_models('Permissions', resource_type=ResourceType.MGMT_KEYVAULT)
    CertificatePermissions = get_sdk(cli_ctx, ResourceType.MGMT_KEYVAULT, 'models#CertificatePermissions')
    KeyPermissions = get_sdk(cli_ctx, ResourceType.MGMT_KEYVAULT, 'models#KeyPermissions')
    SecretPermissions = get_sdk(cli_ctx, ResourceType.MGMT_KEYVAULT, 'models#SecretPermissions')
    KeyVaultSkuName = cmd.get_models('SkuName', resource_type=ResourceType.MGMT_KEYVAULT)

    if not sku:
        sku = KeyVaultSkuName.standard.value

    if no_self_perms:
        access_policies = []
    else:
        permissions = Permissions(keys=[KeyPermissions.get,
                                        KeyPermissions.create,
                                        KeyPermissions.delete,
                                        KeyPermissions.list,
                                        KeyPermissions.update,
                                        KeyPermissions.import_enum,
                                        KeyPermissions.backup,
                                        KeyPermissions.restore],
                                  secrets=[SecretPermissions.get,
                                           SecretPermissions.list,
                                           SecretPermissions.set,
                                           SecretPermissions.delete,
                                           SecretPermissions.backup,
                                           SecretPermissions.restore,
                                           SecretPermissions.recover],
                                  certificates=[CertificatePermissions.get,
                                                CertificatePermissions.list,
                                                CertificatePermissions.delete,
                                                CertificatePermissions.create,
                                                CertificatePermissions.import_enum,
                                                CertificatePermissions.update,
                                                CertificatePermissions.managecontacts,
                                                CertificatePermissions.getissuers,
                                                CertificatePermissions.listissuers,
                                                CertificatePermissions.setissuers,
                                                CertificatePermissions.deleteissuers,
                                                CertificatePermissions.manageissuers,
                                                CertificatePermissions.recover])
        try:
            object_id = _get_current_user_object_id(graph_client)
        except GraphErrorException:
            object_id = _get_object_id(graph_client, subscription=subscription)
        if not object_id:
            raise CLIError('Cannot create vault.\n'
                           'Unable to query active directory for information '
                           'about the current user.\n'
                           'You may try the --no-self-perms flag to create a vault'
                           ' without permissions.')
        access_policies = [AccessPolicyEntry(tenant_id=tenant_id,
                                             object_id=object_id,
                                             permissions=permissions)]
    properties = VaultProperties(tenant_id=tenant_id,
                                 sku=KeyVaultSku(name=sku),
                                 access_policies=access_policies,
                                 vault_uri=None,
                                 enabled_for_deployment=enabled_for_deployment,
                                 enabled_for_disk_encryption=enabled_for_disk_encryption,
                                 enabled_for_template_deployment=enabled_for_template_deployment)
    parameters = VaultCreateOrUpdateParameters(location=location,
                                               tags=tags,
                                               properties=properties)
    client = keyvault_client_factory(cli_ctx).vaults
    return client.create_or_update(resource_group_name=resource_group_name,
                                   vault_name=vault_name,
                                   parameters=parameters)


# pylint: disable=inconsistent-return-statements
def _get_current_user_object_id(graph_client):
    try:
        current_user = graph_client.signed_in_user.get()
        if current_user and current_user.object_id:  # pylint:disable=no-member
            return current_user.object_id  # pylint:disable=no-member
    except CloudError:
        pass


def _get_object_id_by_spn(graph_client, spn):
    accounts = list(graph_client.service_principals.list(
        filter="servicePrincipalNames/any(c:c eq '{}')".format(spn)))
    if not accounts:
        logger.warning("Unable to find user with spn '%s'", spn)
        return None
    if len(accounts) > 1:
        logger.warning("Multiple service principals found with spn '%s'. "
                       "You can avoid this by specifying object id.", spn)
        return None
    return accounts[0].object_id


def _get_object_id_by_upn(graph_client, upn):
    accounts = list(graph_client.users.list(
        filter="userPrincipalName eq '{}'".format(upn)))
    if not accounts:
        logger.warning("Unable to find user with upn '%s'", upn)
        return None
    if len(accounts) > 1:
        logger.warning("Multiple users principals found with upn '%s'. "
                       "You can avoid this by specifying object id.", upn)
        return None
    return accounts[0].object_id


def _get_object_id_from_subscription(graph_client, subscription):
    if subscription['user']:
        if subscription['user']['type'] == 'user':
            return _get_object_id_by_upn(graph_client, subscription['user']['name'])
        if subscription['user']['type'] == 'servicePrincipal':
            return _get_object_id_by_spn(graph_client, subscription['user']['name'])
        logger.warning("Unknown user type '%s'",
                       subscription['user']['type'])
    else:
        logger.warning('Current credentials are not from a user or service principal. '
                       'Azure Key Vault does not work with certificate credentials.')


def _get_object_id(graph_client, subscription=None, spn=None, upn=None):
    if spn:
        return _get_object_id_by_spn(graph_client, spn)
    if upn:
        return _get_object_id_by_upn(graph_client, upn)
    return _get_object_id_from_subscription(graph_client, subscription)


def _get_template_file_and_parameters_file(linux=None):
    script_dir = os.path.dirname(os.path.realpath(__file__))
    template_parameter_folder = ""
    if linux:
        template_parameter_folder = os.path.join('template', 'linux')
    else:
        template_parameter_folder = os.path.join('template', 'windows')
    parameter_file = os.path.join(
        script_dir, template_parameter_folder, 'parameter.json')
    template_file = os.path.join(
        script_dir, template_parameter_folder, 'template.json')
    return parameter_file, template_file


def _set_parameters_for_default_template(cluster_location,
                                         cluster_name,
                                         admin_password,
                                         certificate_thumbprint,
                                         vault_id,
                                         certificate_id,
                                         reliability_level,
                                         admin_name,
                                         cluster_size,
                                         durability_level,
                                         vm_sku,
                                         os_type,
                                         linux):
    parameter_file, _ = _get_template_file_and_parameters_file(linux)
    parameters = get_file_json(parameter_file)['parameters']
    if parameters is None:
        raise CLIError('Invalid parameters file')
    parameters['clusterLocation']['value'] = cluster_location
    parameters['clusterName']['value'] = cluster_name
    parameters['adminUserName']['value'] = admin_name
    parameters['adminPassword']['value'] = admin_password
    parameters['certificateThumbprint']['value'] = certificate_thumbprint
    parameters['sourceVaultvalue']['value'] = vault_id
    parameters['certificateUrlvalue']['value'] = certificate_id
    parameters['reliabilityLevel']['value'] = reliability_level
    parameters['nt0InstanceCount']['value'] = int(cluster_size)
    parameters['durabilityLevel']['value'] = durability_level
    parameters['vmSku']['value'] = vm_sku
    parameters['vmImageSku']['value'] = os_type
    if "Datacenter-Core-1709" in os_type:
        parameters['vmImageOffer']['value'] = 'WindowsServerSemiAnnual'
    return parameters


def _set_parameters_for_customize_template(cmd,
                                           cli_ctx,
                                           resource_group_name,
                                           certificate_file,
                                           certificate_password,
                                           vault_name,
                                           vault_resource_group_name,
                                           certificate_output_folder,
                                           certificate_subject_name,
                                           secret_identifier,
                                           parameter_file):
    cli_ctx = cli_ctx
    parameters = get_file_json(parameter_file)['parameters']
    if parameters is None:
        raise CLIError('Invalid parameters file')
    if SOURCE_VAULT_VALUE in parameters and CERTIFICATE_THUMBPRINT in parameters and CERTIFICATE_URL_VALUE in parameters:
        logger.info('Found primary certificate parameters in parameters file')
        result = _create_certificate(cmd,
                                     cli_ctx,
                                     resource_group_name,
                                     certificate_file,
                                     certificate_password,
                                     vault_name,
                                     vault_resource_group_name,
                                     certificate_output_folder,
                                     certificate_subject_name,
                                     secret_identifier)
        parameters[SOURCE_VAULT_VALUE]['value'] = result[0]
        parameters[CERTIFICATE_URL_VALUE]['value'] = result[1]
        parameters[CERTIFICATE_THUMBPRINT]['value'] = result[2]
        output_file = result[3]
    else:
        logger.info('Primary certificate parameters are not present in parameters file')
        raise CLIError('The primary certificate parameters names in the parameters file should be specified with' + '\'sourceVaultValue\',\'certificateThumbprint\',\'certificateUrlValue\',' +
                       'if the secondary certificate parameters are specified in the parameters file, the parameters names should be specified with' + '\'secSourceVaultValue\',\'secCertificateThumbprint\',\'secCertificateUrlValue\'')

    if SEC_SOURCE_VAULT_VALUE in parameters and SEC_CERTIFICATE_THUMBPRINT in parameters and SEC_CERTIFICATE_URL_VALUE in parameters:
        logger.info('Found secondary certificate parameters in parameters file')
        result = _create_certificate(cmd,
                                     cli_ctx,
                                     resource_group_name,
                                     certificate_file,
                                     certificate_password,
                                     vault_name,
                                     vault_resource_group_name,
                                     certificate_output_folder,
                                     certificate_subject_name,
                                     secret_identifier)
        parameters[SOURCE_VAULT_VALUE]['value'] = result[0]
        parameters[CERTIFICATE_URL_VALUE]['value'] = result[1]
        parameters[CERTIFICATE_THUMBPRINT]['value'] = result[2]
    else:
        if SEC_SOURCE_VAULT_VALUE not in parameters and SEC_CERTIFICATE_THUMBPRINT not in parameters and SEC_CERTIFICATE_URL_VALUE not in parameters:
            logger.info(
                'Secondary certificate parameters are not present in parameters file')
        else:
            raise CLIError('The primary certificate parameters names in the parameters file should be specified with' + '\'sourceVaultValue\',\'certificateThumbprint\',\'certificateUrlValue\',' +
                           'if the secondary certificate parameters are specified in the parameters file, the parameters names should be specified with' + '\'secSourceVaultValue\',\'secCertificateThumbprint\',\'secCertificateUrlValue\'')
    return parameters, output_file


def _modify_template(linux):
    _, template_file = _get_template_file_and_parameters_file(linux)
    template = get_file_json(template_file)
    return template
