# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import getpass
from azure.cli.core._util import CLIError
import azure.cli.core.azlogging as azlogging
from azure.graphrbac import GraphRbacManagementClient

logger = azlogging.get_az_logger(__name__)


# pylint: disable=too-many-locals, unused-argument, too-many-statements
def create_lab_vm(client, resource_group, lab_name, name, notes=None, image=None, size=None,
                  admin_username=getpass.getuser(), admin_password=None,
                  ssh_key=None, authentication_type='password',
                  vnet_name=None, subnet=None, disallow_public_ip_address=None, artifacts=None,
                  location=None, tags=None, custom_image_id=None,
                  is_authentication_with_ssh_key=False, lab_virtual_network_id=None,
                  os_publisher=None, os_offer=None, os_sku=None, os_version=None, os_type=None,
                  gallery_image_reference=None, generate_ssh_keys=None):
    """
    :param client: Virtual machine client
    :param resource_group: Name of the lab resource group
    :param lab_name: Name of lab
    :param name: Name of the virtual machine
    :param notes: Notes for the virtual machine
    :param image: The name of the operating system image (Custom Image ID or Gallery Image Name of the lab).
                  Use az lab gallery-image list for available Gallery Images or
                  Use az lab custom-image list for available Custom Images
    :param size: The VM size to be created
    :param admin_username: Username for the VM
    :param admin_password: Password for the VM
    :param ssh_key: The SSH public key or public key file path
    :param authentication_type: Type of authentication to use with the VM. Allowed values: password, ssh
    :param vnet_name: Name of the virtual network to reference an existing one in lab. If omitted, lab's existing one
                      VNet and subnet will be selected automatically
    :param subnet: Name of the subnet to reference an existing one in lab. If omitted, lab's existing one subnet will be
                   selected automatically
    :param disallow_public_ip_address: To allow public ip address set to true or false. If omitted, based on the
                                        defaulted subnet this will be set to true or false
    :param artifacts: JSON encoded array of artifacts to be applied. Use @{file} to load from a file
    :param location: Location where to create VM. Defaults to the location of the lab
    :param tags: Space separated tags in 'key[=value]' format. Use "" to clear existing tags
    :param custom_image_id:
    :param is_authentication_with_ssh_key:
    :param lab_virtual_network_id:
    :param os_publisher:
    :param os_offer:
    :param os_sku:
    :param os_version:
    :param os_type:
    :param gallery_image_reference:
    :param generate_ssh_keys:
    :return:
    """
    from azure.mgmt.devtestlabs.models.lab_virtual_machine import LabVirtualMachine

    is_authentication_with_ssh_key = True if authentication_type == 'ssh' else False

    lab_virtual_machine = LabVirtualMachine(notes=notes,
                                            custom_image_id=custom_image_id,
                                            size=size,
                                            user_name=admin_username,
                                            password=admin_password,
                                            ssh_key=ssh_key,
                                            is_authentication_with_ssh_key=is_authentication_with_ssh_key,
                                            lab_subnet_name=subnet,
                                            lab_virtual_network_id=lab_virtual_network_id,
                                            disallow_public_ip_address=disallow_public_ip_address,
                                            artifacts=artifacts,
                                            gallery_image_reference=gallery_image_reference,
                                            name=name,
                                            location=location,
                                            tags=tags)

    return client.create_environment(resource_group, lab_name, lab_virtual_machine)


def list_vm(client, lab_name, resource_group, order_by=None, top=None,
            filters=None, my_vms=None, my_claimable_vms=None):
    """
    List virtual machines
    :param client: Virtual machine client
    :param lab_name: Name of the lab
    :param resource_group: Name of the lab resource group
    :param order_by: The ordering expression for the results, using OData notation
    :param top: The maximum number of resources to return from the operation
    :param filters: The filter to apply on the operation
    :param my_vms: List of viewable labs virtual machines. Cannot be used with --filters
    :param my_claimable_vms: List of claimable labs virtual machines. Cannot be used with --filters
    :return:
    """

    collection = [filters, my_vms, my_claimable_vms]
    if not _single(collection):
        raise CLIError("usage error: [--filters FILTER | --my-vms | --my-claimable-vms]")

    if my_vms:
        # Find out owner object id
        from azure.cli.core._profile import Profile, CLOUD
        profile = Profile()
        cred, _, tenant_id = profile.get_login_credentials(
            resource=CLOUD.endpoints.active_directory_graph_resource_id)
        graph_client = GraphRbacManagementClient(cred,
                                                 tenant_id,
                                                 base_url=CLOUD.endpoints.active_directory_graph_resource_id)
        subscription = profile.get_subscription()
        object_id = _get_object_id(graph_client, subscription=subscription)
        odata_filter = "Properties/ownerObjectId eq '{}'".format(object_id)
    elif my_claimable_vms:
        odata_filter = 'properties/allowClaim'
    else:
        odata_filter = filters

    return client.list(resource_group, lab_name, odata_filter, top, order_by)

# TODO: Following methods can be extracted into common utils shared by other command modules


def _single(collection):
    return len([x for x in collection if x]) == 1


def _get_object_id(graph_client, subscription=None, spn=None, upn=None):
    if spn:
        return _get_object_id_by_spn(graph_client, spn)
    if upn:
        return _get_object_id_by_upn(graph_client, upn)
    return _get_object_id_from_subscription(graph_client, subscription)


def _get_object_id_from_subscription(graph_client, subscription):
    if subscription['user']:
        if subscription['user']['type'] == 'user':
            return _get_object_id_by_upn(graph_client, subscription['user']['name'])
        elif subscription['user']['type'] == 'servicePrincipal':
            return _get_object_id_by_spn(graph_client, subscription['user']['name'])
        else:
            logger.warning("Unknown user type '%s'", subscription['user']['type'])
    else:
        logger.warning('Current credentials are not from a user or service principal. '
                       'Azure Key Vault does not work with certificate credentials.')


def _get_object_id_by_spn(graph_client, spn):
    accounts = list(graph_client.service_principals.list(
        filter="servicePrincipalNames/any(c:c eq '{}')".format(spn)))
    if not accounts:
        logger.warning("Unable to find user with spn '%s'", spn)
        return
    if len(accounts) > 1:
        logger.warning("Multiple service principals found with spn '%s'. "
                       "You can avoid this by specifying object id.", spn)
        return
    return accounts[0].object_id


def _get_object_id_by_upn(graph_client, upn):
    accounts = list(graph_client.users.list(filter="userPrincipalName eq '{}'".format(upn)))
    if not accounts:
        logger.warning("Unable to find user with upn '%s'", upn)
        return
    if len(accounts) > 1:
        logger.warning("Multiple users principals found with upn '%s'. "
                       "You can avoid this by specifying object id.", upn)
        return
    return accounts[0].object_id
