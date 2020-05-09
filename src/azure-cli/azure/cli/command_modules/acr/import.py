# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError
from knack.log import get_logger
from msrestazure.tools import is_valid_resource_id, parse_resource_id

from ._utils import (
    validate_managed_registry, get_registry_from_name_or_login_server, get_registry_by_name
)

from azure.cli.core.commands import LongRunningOperation

logger = get_logger(__name__)

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

    registry = None
    if source_registry:
        if is_valid_resource_id(source_registry):
            source = ImportSource(resource_id=source_registry, source_image=source_image)
        else:
            registry = get_registry_from_name_or_login_server(cmd.cli_ctx, source_registry, source_registry)
            if registry:
                # trim away redundant login server name, a common error
                prefix = registry.login_server + '/'
                if source_image.lower().startswith(prefix.lower()):
                    warning = ('The login server name of "%s" in the "--source" argument will be ignored as '
                               '"--registry" already supplies the same information')
                    logger.warning(warning, prefix[:-1])
                    source_image = source_image[len(prefix):]
                # For Azure container registry
                source = ImportSource(resource_id=registry.id, source_image=source_image)
            else:
                # For non-Azure container registry
                raise CLIError(SOURCE_REGISTRY_NOT_FOUND)

    else:
        registry_uri, source_image = _split_registry_and_image(source_image)
        if source_registry_password:
            ImportSourceCredentials = cmd.get_models('ImportSourceCredentials')
            source = ImportSource(registry_uri=registry_uri,
                                  source_image=source_image,
                                  credentials=ImportSourceCredentials(password=source_registry_password,
                                                                      username=source_registry_username))
        else:
            registry = get_registry_from_name_or_login_server(cmd.cli_ctx, registry_uri)
            if registry:
                # For Azure container registry
                source = ImportSource(resource_id=registry.id, source_image=source_image)
            else:
                # For non-Azure container registry
                source = ImportSource(registry_uri=registry_uri, source_image=source_image)

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
    result_poller = client.import_image(
        resource_group_name=resource_group_name,
        registry_name=registry_name,
        parameters=import_parameters)

    return _handle_result(cmd, result_poller, source_registry, source_image, registry)


def _handle_result(cmd, result_poller, source_registry, source_image, registry):
    from msrestazure.azure_exceptions import ClientException
    try:
        result = LongRunningOperation(cmd.cli_ctx, 'Importing image...')(result_poller)
    except CLIError as e:
        try:
            # if command fails, it might be because user specified registry twice in --source and --registry
            if source_registry:

                if not hasattr(registry, 'login_server'):
                    if is_valid_resource_id(source_registry):
                        registry, _ = get_registry_by_name(cmd.cli_ctx, parse_resource_id(source_registry)["name"])
                    else:
                        registry = get_registry_from_name_or_login_server(cmd.cli_ctx, source_registry, source_registry)

                if registry.login_server.lower() in source_image.lower():
                    logger.warning("Import from source failed.\n\tsource image: '%s'\n"
                                   "Attention: When source registry is specified with `--registry`, "
                                   "`--source` is considered to be a source image name. "
                                   "Do not prefix `--source` with the registry login server name.", "{}/{}"
                                   .format(registry.login_server, source_image))
        except (ClientException, CLIError) as unexpected_ex:  # raise exception
            logger.debug("Unexpected exception: %s", unexpected_ex)

        raise e  # regardless re-raise the CLIError as this is an error from the service

    return result


def _split_registry_and_image(source_image):
    slash = source_image.find('/')
    if slash <= 0:
        raise CLIError(SOURCE_NOT_FOUND)

    registry_uri = source_image[:slash]
    if '.' not in registry_uri:
        raise CLIError(LOGIN_SERVER_NOT_VALID)

    source_image = source_image[slash + 1:]
    return registry_uri, source_image
