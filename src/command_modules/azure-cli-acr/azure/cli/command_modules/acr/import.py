# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError
from msrestazure.tools import is_valid_resource_id

from ._utils import (
    validate_managed_registry,
    get_registry_from_name_or_login_server
)

SOURCE_REGISTRY_NOT_FOUND = "The source container registry can not be found. " \
                            "Please provide a valid address or use the resource ID and try again."
IMPORT_NOT_SUPPORTED = "Imports are only supported for managed registries."
INVALID_SOURCE_IMAGE = "Source cannot be found. " \
                       "Please provide a valid image and source registry or a fully qualified source."


def acr_import(cmd,
               client,
               registry_name,
               source,
               source_registry=None,
               source_registry_username=None,
               source_registry_password=None,
               target_tags=None,
               resource_group_name=None,
               repository=None,
               force=False):

    _, resource_group_name = validate_managed_registry(
        cmd, registry_name, resource_group_name, IMPORT_NOT_SUPPORTED)

    if not source:
        raise CLIError(INVALID_SOURCE_IMAGE)
    source_image = source

    ImportImageParameters, ImportSource, ImportMode = cmd.get_models(
        'ImportImageParameters', 'ImportSource', 'ImportMode')

    if source_registry:
        if is_valid_resource_id(source_registry):
            source = ImportSource(resource_id=source_registry, source_image=source_image)
        else:
            registry = get_registry_from_name_or_login_server(cmd.cli_ctx, source_registry, source_registry)
            if registry:
                source = ImportSource(resource_id=registry.id, source_image=source_image)
            else:
                if source_registry_password:
                    ImportSourceCredentials = cmd.get_models('ImportSourceCredentials')
                    source = ImportSource(registry_uri=source_registry,
                                          source_image=source_image,
                                          credentials=ImportSourceCredentials(password=source_registry_password,
                                                                              username=source_registry_username))
                else:
                    raise CLIError(SOURCE_REGISTRY_NOT_FOUND)
    else:
        slash = source_image.find('/')
        if slash > 0:
            registry_uri = source_image[:slash]
            source_image = source_image[slash + 1:]
            if source_registry_password:
                ImportSourceCredentials = cmd.get_models('ImportSourceCredentials')
                source = ImportSource(registry_uri=registry_uri,
                                      source_image=source_image,
                                      credentials=ImportSourceCredentials(password=source_registry_password,
                                                                          username=source_registry_username))
            else:
                registry = get_registry_from_name_or_login_server(cmd.cli_ctx, registry_uri)
                if registry:
                    source = ImportSource(resource_id=registry.id, source_image=source_image)
                else:
                    source = ImportSource(registry_uri=registry_uri, source_image=source_image)
        else:
            raise CLIError(INVALID_SOURCE_IMAGE)

    if not target_tags and not repository:
        index = source_image.find("@")
        if index > 0:
            target_tags = [source_image[:index]]
        else:
            target_tags = [source_image]

    import_parameters = ImportImageParameters(source=source,
                                              target_tags=target_tags,
                                              untagged_target_repositories=repository,
                                              mode=ImportMode.force.value if force else ImportMode.no_force.value)
    return client.import_image(
        resource_group_name=resource_group_name,
        registry_name=registry_name,
        parameters=import_parameters)
