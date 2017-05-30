# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


# MANAGEMENT CLIENT FACTORIES
def get_devtestlabs_management_client(_):
    from azure.mgmt.devtestlabs import DevTestLabsClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(DevTestLabsClient)


def get_devtestlabs_virtual_machine_operation(kwargs):
    return get_devtestlabs_management_client(kwargs).virtual_machines


def get_devtestlabs_lab_operation(kwargs):
    return get_devtestlabs_management_client(kwargs).labs


def get_devtestlabs_custom_image_operation(kwargs):
    return get_devtestlabs_management_client(kwargs).custom_images


def get_devtestlabs_gallery_image_operation(kwargs):
    return get_devtestlabs_management_client(kwargs).gallery_images


def get_devtestlabs_artifact_operation(kwargs):
    return get_devtestlabs_management_client(kwargs).artifacts


def get_devtestlabs_artifact_source_operation(kwargs):
    return get_devtestlabs_management_client(kwargs).artifact_sources


def get_devtestlabs_virtual_network_operation(kwargs):
    return get_devtestlabs_management_client(kwargs).virtual_networks


def get_devtestlabs_formula_operation(kwargs):
    return get_devtestlabs_management_client(kwargs).formulas


def get_devtestlabs_secret_operation(kwargs):
    return get_devtestlabs_management_client(kwargs).secrets


def get_devtestlabs_environment_operation(kwargs):
    return get_devtestlabs_management_client(kwargs).environments


def get_devtestlabs_arm_template_operation(kwargs):
    return get_devtestlabs_management_client(kwargs).arm_templates
