# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliCommandType
from ._client_factory import (get_devtestlabs_virtual_machine_operation,
                              get_devtestlabs_custom_image_operation,
                              get_devtestlabs_gallery_image_operation,
                              get_devtestlabs_artifact_operation,
                              get_devtestlabs_artifact_source_operation,
                              get_devtestlabs_lab_operation,
                              get_devtestlabs_virtual_network_operation,
                              get_devtestlabs_formula_operation,
                              get_devtestlabs_secret_operation,
                              get_devtestlabs_environment_operation,
                              get_devtestlabs_arm_template_operation)
from .validators import validate_lab_vm_create, validate_lab_vm_list, validate_claim_vm, validate_user_name
from ._format import (transform_artifact_source_list, transform_artifact_source, transform_arm_template_list,
                      transform_arm_template, transform_vm_list, transform_vm, export_artifacts)


# pylint: disable=too-many-locals, too-many-statements
def load_command_table(self, _):

    virtual_machine_operations = CliCommandType(
        operations_tmpl='azure.mgmt.devtestlabs.operations#VirtualMachinesOperations.{}',
        client_factory=get_devtestlabs_virtual_machine_operation
    )

    lab_operations = CliCommandType(
        operations_tmpl='azure.mgmt.devtestlabs.operations#LabsOperations.{}',
        client_factory=get_devtestlabs_lab_operation
    )

    custom_image_operations = CliCommandType(
        operations_tmpl='azure.mgmt.devtestlabs.operations#CustomImagesOperations.{}',
        client_factory=get_devtestlabs_custom_image_operation
    )

    gallery_image_operations = CliCommandType(
        operations_tmpl='azure.mgmt.devtestlabs.operations#GalleryImagesOperations.{}',
        client_factory=get_devtestlabs_gallery_image_operation
    )

    artifact_operations = CliCommandType(
        operations_tmpl='azure.mgmt.devtestlabs.operations#ArtifactsOperations.{}',
        client_factory=get_devtestlabs_artifact_operation
    )

    artifact_source_operations = CliCommandType(
        operations_tmpl='azure.mgmt.devtestlabs.operations#ArtifactSourcesOperations.{}',
        client_factory=get_devtestlabs_artifact_source_operation
    )

    virtual_network_operations = CliCommandType(
        operations_tmpl='azure.mgmt.devtestlabs.operations#VirtualNetworksOperations.{}',
        client_factory=get_devtestlabs_virtual_network_operation
    )

    formula_operations = CliCommandType(
        operations_tmpl='azure.mgmt.devtestlabs.operations#FormulasOperations.{}',
        client_factory=get_devtestlabs_formula_operation
    )

    secret_operations = CliCommandType(
        operations_tmpl='azure.mgmt.devtestlabs.operations#SecretsOperations.{}',
        client_factory=get_devtestlabs_secret_operation,
        validator=validate_user_name
    )

    environment_operations = CliCommandType(
        operations_tmpl='azure.mgmt.devtestlabs.operations#EnvironmentsOperations.{}',
        client_factory=get_devtestlabs_environment_operation,
        validator=validate_user_name
    )

    arm_template_operations = CliCommandType(
        operations_tmpl='azure.mgmt.devtestlabs.operations#ArmTemplatesOperations.{}',
        client_factory=get_devtestlabs_arm_template_operation
    )

    # Virtual Machine Operations Commands
    with self.command_group('lab vm', virtual_machine_operations,
                            client_factory=get_devtestlabs_virtual_machine_operation) as g:
        g.show_command('show', 'get', table_transformer=transform_vm)
        g.command('delete', 'delete')
        g.command('start', 'start')
        g.command('stop', 'stop')
        g.command('apply-artifacts', 'apply_artifacts')
        g.custom_command('list', 'list_vm', validator=validate_lab_vm_list, table_transformer=transform_vm_list)
        g.custom_command('claim', 'claim_vm', validator=validate_claim_vm)
        g.custom_command('create', 'create_lab_vm', client_factory=get_devtestlabs_lab_operation,
                         validator=validate_lab_vm_create)

    # Lab Operations Commands
    with self.command_group('lab', lab_operations) as g:
        g.command('get', 'get')
        g.command('delete', 'delete')

    # Custom Image Operations Commands
    with self.command_group('lab custom-image', custom_image_operations) as g:
        g.show_command('show', 'get')
        g.command('list', 'list')
        g.command('delete', 'delete')
        g.custom_command('create', 'create_custom_image', client_factory=get_devtestlabs_custom_image_operation)

    # Gallery Image Operations Commands
    with self.command_group('lab gallery-image', gallery_image_operations) as g:
        g.command('list', 'list')

    # Artifact Operations Commands
    with self.command_group('lab artifact', artifact_operations) as g:
        g.command('list', 'list')

    # Artifact Source Operations Commands
    with self.command_group('lab artifact-source', artifact_source_operations) as g:
        g.command('list', 'list', table_transformer=transform_artifact_source_list)
        g.show_command('show', 'get', table_transformer=transform_artifact_source)

    # Virtual Network Operations Commands
    with self.command_group('lab vnet', virtual_network_operations) as g:
        g.command('list', 'list')
        g.command('get', 'get')

    # Formula Operations Commands
    with self.command_group('lab formula', formula_operations) as g:
        g.show_command('show', 'get')
        g.command('list', 'list')
        g.command('delete', 'delete')
        g.command('export-artifacts', 'get', transform=export_artifacts)

    # Secret Operations Commands
    with self.command_group('lab secret', secret_operations) as g:
        g.command('set', 'create_or_update')
        g.show_command('show', 'get')
        g.command('list', 'list')
        g.command('delete', 'delete')

    # Environment Operations Commands
    with self.command_group('lab environment', environment_operations) as g:
        g.show_command('show', 'get')
        g.command('list', 'list')
        g.command('delete', 'delete')
        g.command('create', 'create_or_update')
        g.custom_command('create', 'create_environment', client_factory=get_devtestlabs_environment_operation)

    # ARM Templates Operations Commands
    with self.command_group('lab arm-template', arm_template_operations) as g:
        g.command('list', 'list', table_transformer=transform_arm_template_list)
        g.custom_show_command('show', 'show_arm_template', table_transformer=transform_arm_template,
                              client_factory=get_devtestlabs_arm_template_operation)

    with self.command_group('lab', is_preview=True):
        pass
