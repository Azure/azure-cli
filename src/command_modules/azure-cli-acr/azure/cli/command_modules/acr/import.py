from knack.util import CLIError
from azure.mgmt.containerregistry.v2018_02_01_preview.models import (
    ImportImageParameters,
    ImportSource,
    ImportMode
)
from ._utils import (
    validate_managed_registry,
    get_registry_by_login_server
)

IMPORT_NOT_SUPPORTED = "Image imports are only supported for managed registries."
INVALID_SOURCE_IMAGE = "Please specify source image in the form of 'registry.azurecr.io/repository[:tag]'."
SOURCE_REGISTRY_NOT_FOUND = "Source registry cannot be found in the current subscription. " \
                            "Please specify the full resource ID for it: "
NO_TTY_ERROR = "Unable to prompt for resource ID as no tty available."
REGISTRY_MISMATCH = "Registry mismatch. Please check either source-image or resource ID " \
                    "to make sure that they are referring to the same registry and try again."


def acr_import(cmd,
               client,
               registry_name,
               source,
               resource_id=None,
               target_tags=None,
               resource_group_name=None,
               repository=None,
               force=False):
    _, resource_group_name = validate_managed_registry(
        cmd.cli_ctx, registry_name, resource_group_name, IMPORT_NOT_SUPPORTED)

    slash = source.find('/')

    if slash < 0:
        raise CLIError(INVALID_SOURCE_IMAGE)

    source_registry_login_server = source[:slash]
    if not source_registry_login_server:
        raise CLIError(INVALID_SOURCE_IMAGE)

    registry_from_login_server = get_registry_by_login_server(cmd.cli_ctx, source_registry_login_server)

    if registry_from_login_server:
        if resource_id and registry_from_login_server.id != resource_id:
            raise CLIError(REGISTRY_MISMATCH)
        else:
            resource_id = registry_from_login_server.id
    elif not resource_id:
        from knack.prompting import prompt, NoTTYException
        try:
            resource_id = prompt(SOURCE_REGISTRY_NOT_FOUND)
        except NoTTYException:
            raise CLIError(NO_TTY_ERROR)

    source_image = source[slash + 1:]
    if not source_image:
        raise CLIError(INVALID_SOURCE_IMAGE)

    image_source = ImportSource(resource_id=resource_id, source_image=source_image)

    if target_tags is None and repository is None:
        target_tags = [source_image]

    import_parameters = ImportImageParameters(source=image_source,
                                              target_tags=target_tags,
                                              untagged_target_repositories=repository,
                                              mode=ImportMode.force.value if force else ImportMode.no_force.value)

    return client.import_image(
        resource_group_name=resource_group_name,
        registry_name=registry_name,
        parameters=import_parameters)
