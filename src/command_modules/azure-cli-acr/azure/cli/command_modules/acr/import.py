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

SOURCE_REGISTRY_MISSING = "Please specify the source container registry name, login server or resource ID: "
IMPORT_NOT_SUPPORTED = "Imports are only supported for managed registries."
INVALID_SOURCE_IMAGE = "Please specify source image in the format '[registry.azurecr.io/]repository[:tag]' or " \
                       "'[registry.azurecr.io/]repository@digest'"
NO_TTY_ERROR = "Please specify source registry ID by passing parameters to import command directly."
REGISTRY_MISMATCH = "Registry mismatch. Please check either source-image or resource ID " \
                    "to make sure that they are referring to the same registry and try again."


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

    slash = source.find('/')

    ImportImageParameters, ImportSource, ImportMode = cmd.get_models(
        'ImportImageParameters', 'ImportSource', 'ImportMode')
    if slash < 0:
        if not source_registry:
            from knack.prompting import prompt, NoTTYException
            try:
                source_registry = prompt(SOURCE_REGISTRY_MISSING)
            except NoTTYException:
                raise CLIError(NO_TTY_ERROR)
        if not is_valid_resource_id(source_registry):
            registry = get_registry_from_name_or_login_server(cmd.cli_ctx, source_registry, source_registry)
            if registry:
                source_registry = registry.id
        source = ImportSource(resource_id=source_registry, source_image=source_image)
    else:
        source_registry_login_server = source_image[:slash]
        source_image = source_image[slash + 1:]
        if not source_image or not source_registry_login_server:
            raise CLIError(INVALID_SOURCE_IMAGE)
        registry = get_registry_from_name_or_login_server(cmd.cli_ctx, source_registry_login_server)
        if registry:
            if source_registry and \
               source_registry.lower() != registry.id.lower() and \
               source_registry.lower() != registry.name.lower() and \
               source_registry.lower() != registry.login_server.lower():
                raise CLIError(REGISTRY_MISMATCH)
            source = ImportSource(resource_id=registry.id,
                                  source_image=source_image)
        else:
            if source_registry_password:
                ImportSourceCredentials = cmd.get_models('ImportSourceCredentials')
                if source_registry_username:
                    source = ImportSource(registry_uri=source_registry_login_server,
                                          source_image=source_image,
                                          credentials=ImportSourceCredentials(password=source_registry_password,
                                                                              username=source_registry_username))
                else:
                    source = ImportSource(registry_uri=source_registry_login_server,
                                          source_image=source_image,
                                          credentials=ImportSourceCredentials(password=source_registry_password))
            else:
                source = ImportSource(registry_uri=source_registry_login_server, source_image=source_image)

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
