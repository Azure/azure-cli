# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


# MANAGEMENT CLIENT FACTORIES
def get_devtestlabs_management_client(cli_ctx, _):
    from azure.mgmt.devtestlabs import DevTestLabsClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(cli_ctx, DevTestLabsClient)


def get_devtestlabs_virtual_machine_operation(cli_ctx, _):
    return get_devtestlabs_management_client(cli_ctx, _).virtual_machines


def get_devtestlabs_lab_operation(cli_ctx, _):
    return get_devtestlabs_management_client(cli_ctx, _).labs


def get_devtestlabs_custom_image_operation(cli_ctx, _):
    return get_devtestlabs_management_client(cli_ctx, _).custom_images


def get_devtestlabs_gallery_image_operation(cli_ctx, _):
    return get_devtestlabs_management_client(cli_ctx, _).gallery_images


def get_devtestlabs_artifact_operation(cli_ctx, _):
    return get_devtestlabs_management_client(cli_ctx, _).artifacts


def get_devtestlabs_artifact_source_operation(cli_ctx, _):
    return get_devtestlabs_management_client(cli_ctx, _).artifact_sources


def get_devtestlabs_virtual_network_operation(cli_ctx, _):
    return get_devtestlabs_management_client(cli_ctx, _).virtual_networks


def get_devtestlabs_formula_operation(cli_ctx, _):
    return get_devtestlabs_management_client(cli_ctx, _).formulas


def get_devtestlabs_secret_operation(cli_ctx, _):
    return get_devtestlabs_management_client(cli_ctx, _).secrets


def get_devtestlabs_environment_operation(cli_ctx, _):
    return get_devtestlabs_management_client(cli_ctx, _).environments


def get_devtestlabs_arm_template_operation(cli_ctx, _):
    return get_devtestlabs_management_client(cli_ctx, _).arm_templates
