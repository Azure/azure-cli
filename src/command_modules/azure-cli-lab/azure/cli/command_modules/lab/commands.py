# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from collections import OrderedDict
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


# pylint: disable=too-many-locals, too-many-statements
def load_command_table(self, _):
    def _export_artifacts(formula):
        """ Exports artifacts from the given formula. This method removes some of the properties of the
            artifact model as they do not play important part for users in create or read context.
        """
        artifacts = []
        if formula and formula.formula_content and formula.formula_content.artifacts:
            artifacts = formula.formula_content.artifacts
            for artifact in formula.formula_content.artifacts:
                del artifact.status
                del artifact.deployment_status_message
                del artifact.vm_extension_status_message
                del artifact.install_time
        return artifacts

    def transform_artifact_source_list(artifact_source_list):
        return [transform_artifact_source(v) for v in artifact_source_list]

    def transform_artifact_source(result):
        return OrderedDict([('name', result['name']),
                            ('sourceType', result['sourceType']),
                            ('status', result.get('status')),
                            ('uri', result.get('uri'))])

    def transform_arm_template_list(arm_template_list):
        return [transform_arm_template(v) for v in arm_template_list]

    def transform_arm_template(result):
        return OrderedDict([('name', result['name']),
                            ('resourceGroup', result['resourceGroup']),
                            ('publisher', result.get('publisher'))])

    def transform_vm_list(vm_list):
        return [transform_vm(v) for v in vm_list]

    def transform_vm(result):
        return OrderedDict([('name', result['name']),
                            ('location', result['location']),
                            ('osType', result['osType'])])

    # Virtual Machine Operations Commands
    virtual_machine_operations = CliCommandType(
        operations_tmpl='azure.mgmt.devtestlabs.operations.virtual_machines_operations#VirtualMachinesOperations.{}',
        client_factory=get_devtestlabs_virtual_machine_operation
    )

    with self.command_group('lab vm', virtual_machine_operations) as g:
        g.command('show', 'get', table_transformer=transform_vm)
        g.command('delete', 'delete')
        g.command('start', 'start')
        g.command('stop', 'stop')
        g.command('apply-artifacts', 'apply_artifacts')
        g.custom_command('list', 'list_vm', client_factory=get_devtestlabs_virtual_machine_operation,
                         validator=validate_lab_vm_list)
        g.custom_command('claim', 'claim_vm', client_factory=get_devtestlabs_virtual_machine_operation,
                         validator=validate_claim_vm)
        g.custom_command('create', 'create_lab_vm', client_factory=get_devtestlabs_lab_operation,
                         validator=validate_lab_vm_create)

    # Lab Operations Commands
    lab_operations = CliCommandType(
        operations_tmpl='azure.mgmt.devtestlabs.operations.labs_operations#LabsOperations.{}',
        client_factory=get_devtestlabs_lab_operation
    )

    with self.command_group('lab', lab_operations) as g:
        g.command('get', 'get')
        g.command('delete', 'delete')

    # Custom Image Operations Commands

    custom_image_operations = CliCommandType(
        operations_tmpl='azure.mgmt.devtestlabs.operations.custom_images_operations#CustomImagesOperations.{}',
        client_factory=get_devtestlabs_custom_image_operation
    )

    with self.command_group('lab custom-image', custom_image_operations) as g:
        g.command('show', 'get')
        g.command('list', 'list')
        g.command('delete', 'delete')
        g.custom_command('create', 'create_custom_image', client_factory=get_devtestlabs_custom_image_operation)

    # Gallery Image Operations Commands
    gallery_image_operations = CliCommandType(
        operations_tmpl='azure.mgmt.devtestlabs.operations.gallery_images_operations#GalleryImagesOperations.{}',
        client_factory=get_devtestlabs_gallery_image_operation
    )

    with self.command_group('lab gallery-image', gallery_image_operations) as g:
        g.command('list', 'list')

    # Artifact Operations Commands
    artifact_operations = CliCommandType(
        operations_tmpl='azure.mgmt.devtestlabs.operations.artifacts_operations#ArtifactsOperations.{}',
        client_factory=get_devtestlabs_artifact_operation
    )

    with self.command_group('lab artifact', artifact_operations) as g:
        g.command('list', 'list')

    # Artifact Source Operations Commands
    artifact_source_operations = CliCommandType(
        operations_tmpl='azure.mgmt.devtestlabs.operations.artifact_sources_operations#ArtifactSourcesOperations.{}',
        client_factory=get_devtestlabs_artifact_source_operation
    )

    with self.command_group('lab artifact-source', artifact_source_operations) as g:
        g.command('list', 'list', table_transformer=transform_artifact_source_list)
        g.command('show', 'get', table_transformer=transform_artifact_source)

    # Virtual Network Operations Commands
    virtual_network_operations = CliCommandType(
        operations_tmpl='azure.mgmt.devtestlabs.operations.virtual_networks_operations#VirtualNetworksOperations.{}',
        client_factory=get_devtestlabs_virtual_network_operation
    )

    with self.command_group('lab vnet', virtual_network_operations) as g:
        g.command('list', 'list')
        g.command('get', 'get')

    # Formula Operations Commands
    formula_operations = CliCommandType(
        operations_tmpl='azure.mgmt.devtestlabs.operations.formulas_operations#FormulasOperations.{}',
        client_factory=get_devtestlabs_formula_operation
    )

    with self.command_group('lab formula', formula_operations) as g:
        g.command('show', 'get')
        g.command('list', 'list')
        g.command('delete', 'delete')
        g.command('export-artifacts', 'get', transform=_export_artifacts)

    # Secret Operations Commands
    secret_operations = CliCommandType(
        operations_tmpl='azure.mgmt.devtestlabs.operations.secrets_operations#.SecretsOperations{}',
        client_factory=get_devtestlabs_secret_operation,
        validator=validate_user_name
    )

    with self.command_group('lab secret', secret_operations) as g:
        g.command('set', 'create_or_update')
        g.command('show', 'get')
        g.command('list', 'list')
        g.command('delete', 'delete')

    # Environment Operations Commands
    environment_operations = CliCommandType(
        operations_tmpl='azure.mgmt.devtestlabs.operations.environments_operations#EnvironmentsOperations.{}',
        client_factory=get_devtestlabs_environment_operation,
        validator=validate_user_name
    )

    with self.command_group('lab environment', environment_operations) as g:
        g.command('show', 'get')
        g.command('list', 'list')
        g.command('delete', 'delete')
        g.command('create', 'create_or_update')
        g.custom_command('create', 'create_environment', client_factory=get_devtestlabs_environment_operation)

    # ARM Templates Operations Commands
    arm_template_operations = CliCommandType(
        operations_tmpl='azure.mgmt.devtestlabs.operations.arm_templates_operations#ArmTemplatesOperations.{}',
        client_factory=get_devtestlabs_arm_template_operation
    )

    with self.command_group('lab arm-template', arm_template_operations) as g:
        g.command('list', 'list', table_transformer=transform_arm_template_list)
        g.custom_command('show', 'show_arm_template', table_transformer=transform_arm_template,
                         client_factory=get_devtestlabs_arm_template_operation)
