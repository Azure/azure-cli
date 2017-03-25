# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ._client_factory import (get_devtestlabs_virtual_machine_operation,
                              get_devtestlabs_custom_image_operation,
                              get_devtestlabs_gallery_image_operation,
                              get_devtestlabs_artifact_operation,
                              get_devtestlabs_artifact_source_operation,
                              get_devtestlabs_lab_operation,
                              get_devtestlabs_virtual_network_operation,
                              get_devtestlabs_formula_operation)
from azure.cli.core.sdk.util import (ServiceGroup, create_service_adapter)


custom_path = 'azure.cli.command_modules.lab.custom'
mgmt_operations_path = 'azure.cli.command_modules.lab.sdk.devtestlabs.operations.{}'


# Custom Command's service adapter
custom_operations = create_service_adapter(custom_path)

# Virtual Machine Operations Commands
virtual_machine_operations = create_service_adapter(
    mgmt_operations_path.format('virtual_machine_operations'),
    'VirtualMachineOperations')

with ServiceGroup(__name__, get_devtestlabs_virtual_machine_operation,
                  virtual_machine_operations) as s:
    with s.group('lab vm') as c:
        c.command('show', 'get_resource')
        c.command('list', 'list')
        c.command('delete', 'delete_resource')
        c.command('start', 'start')
        c.command('stop', 'stop')
        c.command('apply-artifacts', 'apply_artifacts')

# Virtual Machine Operations Custom Commands
with ServiceGroup(__name__, get_devtestlabs_virtual_machine_operation,
                  custom_operations) as s:
    with s.group('lab vm') as c:
        c.command('list', 'list_vm')

# Lab Operations Custom Commands
with ServiceGroup(__name__, get_devtestlabs_lab_operation,
                  custom_operations) as s:
    with s.group('lab vm') as c:
        c.command('create', 'create_lab_vm')

lab_operations = create_service_adapter(mgmt_operations_path.format('lab_operations'),
                                        'LabOperations')

# Lab Operations Commands
with ServiceGroup(__name__, get_devtestlabs_lab_operation,
                  lab_operations) as s:
    with s.group('lab') as c:
        c.command('get', 'get_resource')

# Custom Image Operations Commands
custom_image_operations = create_service_adapter(
    mgmt_operations_path.format('custom_image_operations'),
    'CustomImageOperations')

with ServiceGroup(__name__, get_devtestlabs_custom_image_operation,
                  custom_image_operations) as s:
    with s.group('lab custom-image') as c:
        c.command('show', 'get_resource')
        c.command('list', 'list')
        c.command('delete', 'delete_resource')

# Gallery Image Operations Commands
gallery_image_operations = create_service_adapter(
    mgmt_operations_path.format('gallery_image_operations'),
    'GalleryImageOperations')

with ServiceGroup(__name__, get_devtestlabs_gallery_image_operation,
                  gallery_image_operations) as s:
    with s.group('lab gallery-image') as c:
        c.command('list', 'list')

# Artifact Operations Commands
artifact_operations = create_service_adapter(
    mgmt_operations_path.format('artifact_operations'),
    'ArtifactOperations')

with ServiceGroup(__name__, get_devtestlabs_artifact_operation,
                  artifact_operations) as s:
    with s.group('lab artifact') as c:
        c.command('list', 'list')

# Artifact Source Operations Commands
artifact_source_operations = create_service_adapter(
    mgmt_operations_path.format('artifact_source_operations'),
    'ArtifactSourceOperations')

with ServiceGroup(__name__, get_devtestlabs_artifact_source_operation,
                  artifact_source_operations) as s:
    with s.group('lab artifact-source') as c:
        c.command('list', 'list')
        c.command('get', 'get_resource')

# Virtual Network Operations Commands
virtual_network_operations = create_service_adapter(
    mgmt_operations_path.format('virtual_network_operations'),
    'VirtualNetworkOperations')

with ServiceGroup(__name__, get_devtestlabs_virtual_network_operation,
                  virtual_network_operations) as s:
    with s.group('lab vnet') as c:
        c.command('list', 'list')
        c.command('get', 'get_resource')

# Formula Operations Commands
formula_operations = create_service_adapter(
    mgmt_operations_path.format('formula_operations'),
    'FormulaOperations')

with ServiceGroup(__name__, get_devtestlabs_formula_operation,
                  formula_operations) as s:
    with s.group('lab formula') as c:
        c.command('get', 'get_resource')
        c.command('list', 'list')
        c.command('delete', 'delete_resource')
