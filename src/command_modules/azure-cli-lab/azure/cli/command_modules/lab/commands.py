# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from collections import OrderedDict
from azure.cli.core.sdk.util import (ServiceGroup, create_service_adapter)
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


custom_path = 'azure.cli.command_modules.lab.custom'
mgmt_operations_path = 'azure.mgmt.devtestlabs.operations.{}'


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


# Custom Command's service adapter
custom_operations = create_service_adapter(custom_path)

# Virtual Machine Operations Commands
virtual_machine_operations = create_service_adapter(
    mgmt_operations_path.format('virtual_machines_operations'),
    'VirtualMachinesOperations')

with ServiceGroup(__name__, get_devtestlabs_virtual_machine_operation,
                  virtual_machine_operations) as s:
    with s.group('lab vm') as c:
        c.command('show', 'get', table_transformer=transform_vm)
        c.command('delete', 'delete')
        c.command('start', 'start')
        c.command('stop', 'stop')
        c.command('apply-artifacts', 'apply_artifacts')

# Virtual Machine Operations Custom Commands
with ServiceGroup(__name__, get_devtestlabs_virtual_machine_operation,
                  custom_operations) as s:
    with s.group('lab vm') as c:
        c.command('list', 'list_vm', table_transformer=transform_vm_list)
        c.command('claim', 'claim_vm')

# Lab Operations Custom Commands
with ServiceGroup(__name__, get_devtestlabs_lab_operation,
                  custom_operations) as s:
    with s.group('lab vm') as c:
        c.command('create', 'create_lab_vm')

lab_operations = create_service_adapter(mgmt_operations_path.format('labs_operations'),
                                        'LabsOperations')

# Lab Operations Commands
with ServiceGroup(__name__, get_devtestlabs_lab_operation,
                  lab_operations) as s:
    with s.group('lab') as c:
        c.command('get', 'get')
        c.command('delete', 'delete')

# Custom Image Operations Commands
custom_image_operations = create_service_adapter(
    mgmt_operations_path.format('custom_images_operations'),
    'CustomImagesOperations')

with ServiceGroup(__name__, get_devtestlabs_custom_image_operation,
                  custom_image_operations) as s:
    with s.group('lab custom-image') as c:
        c.command('show', 'get')
        c.command('list', 'list')
        c.command('delete', 'delete')

# Gallery Image Operations Commands
gallery_image_operations = create_service_adapter(
    mgmt_operations_path.format('gallery_images_operations'),
    'GalleryImagesOperations')

with ServiceGroup(__name__, get_devtestlabs_gallery_image_operation,
                  gallery_image_operations) as s:
    with s.group('lab gallery-image') as c:
        c.command('list', 'list')

# Artifact Operations Commands
artifact_operations = create_service_adapter(
    mgmt_operations_path.format('artifacts_operations'),
    'ArtifactsOperations')

with ServiceGroup(__name__, get_devtestlabs_artifact_operation,
                  artifact_operations) as s:
    with s.group('lab artifact') as c:
        c.command('list', 'list')

# Artifact Source Operations Commands
artifact_source_operations = create_service_adapter(
    mgmt_operations_path.format('artifact_sources_operations'),
    'ArtifactSourcesOperations')

with ServiceGroup(__name__, get_devtestlabs_artifact_source_operation,
                  artifact_source_operations) as s:
    with s.group('lab artifact-source') as c:
        c.command('list', 'list', table_transformer=transform_artifact_source_list)
        c.command('show', 'get', table_transformer=transform_artifact_source)

# Virtual Network Operations Commands
virtual_network_operations = create_service_adapter(
    mgmt_operations_path.format('virtual_networks_operations'),
    'VirtualNetworksOperations')

with ServiceGroup(__name__, get_devtestlabs_virtual_network_operation,
                  virtual_network_operations) as s:
    with s.group('lab vnet') as c:
        c.command('list', 'list')
        c.command('get', 'get')

# Formula Operations Commands
formula_operations = create_service_adapter(
    mgmt_operations_path.format('formulas_operations'),
    'FormulasOperations')

with ServiceGroup(__name__, get_devtestlabs_formula_operation,
                  formula_operations) as s:
    with s.group('lab formula') as c:
        c.command('show', 'get')
        c.command('list', 'list')
        c.command('delete', 'delete')
        c.command('export-artifacts', 'get', transform=_export_artifacts)

# Secret Operations Commands
secret_operations = create_service_adapter(
    mgmt_operations_path.format('secrets_operations'),
    'SecretsOperations')

with ServiceGroup(__name__, get_devtestlabs_secret_operation,
                  secret_operations) as s:
    with s.group('lab secret') as c:
        c.command('set', 'create_or_update')
        c.command('show', 'get')
        c.command('list', 'list')
        c.command('delete', 'delete')

# Environment Operations Commands
environment_operations = create_service_adapter(
    mgmt_operations_path.format('environments_operations'),
    'EnvironmentsOperations')

with ServiceGroup(__name__, get_devtestlabs_environment_operation,
                  environment_operations) as s:
    with s.group('lab environment') as c:
        c.command('show', 'get')
        c.command('list', 'list')
        c.command('delete', 'delete')
        c.command('create', 'create_or_update')

# Environment Operations Custom Commands
with ServiceGroup(__name__, get_devtestlabs_environment_operation,
                  custom_operations) as s:
    with s.group('lab environment') as c:
        c.command('create', 'create_environment')

# ARM Templates Operations Commands
arm_template_operations = create_service_adapter(
    mgmt_operations_path.format('arm_templates_operations'),
    'ArmTemplatesOperations')

with ServiceGroup(__name__, get_devtestlabs_arm_template_operation,
                  arm_template_operations) as s:
    with s.group('lab arm-template') as c:
        c.command('list', 'list', table_transformer=transform_arm_template_list)

# ARM Templates Operations Custom Commands
with ServiceGroup(__name__, get_devtestlabs_arm_template_operation,
                  custom_operations) as s:
    with s.group('lab arm-template') as c:
        c.command('show', 'show_arm_template', table_transformer=transform_arm_template)
