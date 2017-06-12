# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import getpass


# pylint: disable=too-many-locals, unused-argument, too-many-statements

def create_lab_vm(client, resource_group, lab_name, name, notes=None, image=None, image_type=None,
                  size=None, admin_username=getpass.getuser(), admin_password=None,
                  ssh_key=None, authentication_type='password',
                  vnet_name=None, subnet=None, disallow_public_ip_address=None, artifacts=None,
                  location=None, tags=None, custom_image_id=None, lab_virtual_network_id=None,
                  gallery_image_reference=None, generate_ssh_keys=None, allow_claim=False,
                  disk_type=None, expiration_date=None, formula=None, ip_configuration=None,
                  network_interface=None, os_type=None, saved_secret=None):
    """ Command to create vm of in the Azure DevTest Lab """
    from azure.mgmt.devtestlabs.models.lab_virtual_machine_creation_parameter import \
        LabVirtualMachineCreationParameter

    is_ssh_authentication = authentication_type == 'ssh'

    lab_virtual_machine = LabVirtualMachineCreationParameter(
        name=name,
        notes=notes,
        custom_image_id=custom_image_id,
        size=size,
        user_name=admin_username,
        password=admin_password,
        ssh_key=ssh_key,
        is_authentication_with_ssh_key=is_ssh_authentication,
        lab_subnet_name=subnet,
        lab_virtual_network_id=lab_virtual_network_id,
        disallow_public_ip_address=disallow_public_ip_address,
        network_interface=network_interface,
        artifacts=artifacts,
        gallery_image_reference=gallery_image_reference,
        location=location,
        tags=tags,
        allow_claim=allow_claim,
        storage_type=disk_type,
        expiration_date=expiration_date)

    return client.create_environment(resource_group, lab_name, lab_virtual_machine)


# pylint: disable=redefined-builtin
def list_vm(client, resource_group, lab_name, order_by=None, top=None,
            filters=None, all=None, claimable=None, environment=None, expand=None, object_id=None):
    """ Command to list vms by resource group in the Azure DevTest Lab """

    return client.list(resource_group, lab_name,
                       expand=expand, filter=filters, top=top, order_by=order_by)


def claim_vm(client, lab_name=None, name=None, resource_group=None):
    """ Command to claim a VM in the Azure DevTest Lab"""

    if name is not None:
        return client.claim(resource_group, lab_name, name)

    from ._client_factory import get_devtestlabs_lab_operation
    return get_devtestlabs_lab_operation(None).claim_any_vm(resource_group, lab_name)


# pylint: disable=too-many-locals, unused-argument
def create_environment(client, resource_group, lab_name, name, arm_template, parameters=None,
                       artifact_source_name=None, user_name=None, tags=None):
    """ Command to create an environment the Azure DevTest Lab """

    from azure.mgmt.devtestlabs.models.environment_deployment_properties \
        import EnvironmentDeploymentProperties
    from azure.mgmt.devtestlabs.models.dtl_environment import DtlEnvironment

    environment_deployment_properties = EnvironmentDeploymentProperties(arm_template, parameters)
    dtl_environment = DtlEnvironment(tags=tags,
                                     deployment_properties=environment_deployment_properties)

    return client.create_or_update(resource_group, lab_name, user_name, name, dtl_environment)


def show_arm_template(client, resource_group, lab_name, name,
                      artifact_source_name, export_parameters=False):
    """ Command to show azure resource manager template in the Azure DevTest Lab """

    arm_template = client.get(resource_group, lab_name, artifact_source_name, name)
    if export_parameters:
        return _export_parameters(arm_template)
    return arm_template


def _export_parameters(arm_template):
    parameters = []
    if arm_template and arm_template.contents and arm_template.contents['parameters']:
        if arm_template.parameters_value_files_info:
            default_values = dict()
            for parameter_value_file_info in arm_template.parameters_value_files_info:
                if isinstance(parameter_value_file_info.parameters_value_info, dict):
                    for k in parameter_value_file_info.parameters_value_info:
                        default_values[k] = parameter_value_file_info.parameters_value_info[k].get('value', "")

        if isinstance(arm_template.contents['parameters'], dict):
            for k in arm_template.contents['parameters']:
                param = dict()
                param['name'] = k
                param['value'] = default_values.get(k, "")
                parameters.append(param)
    return parameters
