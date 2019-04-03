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

SOURCE_REGISTRY_NOT_FOUND = "The source container registry can not be found in the current subscription. " \
                            "Please provide a valid address and/or credentials."
IMPORT_NOT_SUPPORTED = "Imports are only supported for managed registries."
SOURCE_NOT_FOUND = "Source cannot be found. " \
                   "Please provide a valid image and source registry or a fully qualified source."
LOGIN_SERVER_NOT_VALID = "Login server of the registry is not valid " \
                         "because it is not a fully qualified domain name."
CREDENTIALS_INVALID = "Authentication failed. Please provide password."


def acr_import(cmd,
               client,
               registry_name,
               source_image,
               source_registry=None,
               source_registry_username=None,
               source_registry_password=None,
               target_tags=None,
               resource_group_name=None,
               repository=None,
               force=False):

    if source_registry_username and not source_registry_password:
        raise CLIError(CREDENTIALS_INVALID)

    _, resource_group_name = validate_managed_registry(
        cmd, registry_name, resource_group_name, IMPORT_NOT_SUPPORTED)

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
                raise CLIError(SOURCE_REGISTRY_NOT_FOUND)
    else:
        slash = source_image.find('/')
        if slash > 0:
            registry_uri = source_image[:slash]
            dot = registry_uri.find('.')
            if dot > 0:
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
                raise CLIError(LOGIN_SERVER_NOT_VALID)
        else:
            raise CLIError(SOURCE_NOT_FOUND)

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
