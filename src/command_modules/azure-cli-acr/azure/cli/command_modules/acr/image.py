from knack.util import CLIError
from azure.mgmt.containerregistry.v2018_02_01_preview.models import (
    ImportImageParameters,
    ImportSource,
    ImportMode
)

from azure.cli.core.commands import LongRunningOperation

from ._utils import (
    validate_managed_registry,
    get_resource_id_by_registry_name
)

IMPORT_NOT_SUPPORTED = "Image imports are only supported for managed registries."
INVALID_SOURCE_IMAGE = "Please specify source image in the form of 'regsitry.azurecr.io/repository[:tag]'."

def acr_image_import(cmd,
                     client,
                     registry_name,
                     source_image,
                     resource_id=None,
                     tags=None,
                     resource_group_name=None,
                     repository=None,
                     force=False):
    _, resource_group_name = validate_managed_registry(
        cmd.cli_ctx, registry_name, resource_group_name, IMPORT_NOT_SUPPORTED)

    dot = source_image.find('.')
    slash = source_image.find('/')

    if dot < 0 or slash < 0:
        #todo we might support import images from docker hub
        raise CLIError(INVALID_SOURCE_IMAGE)

    source_registry = source_image[:dot]
    if not source_registry:
        raise CLIError(INVALID_SOURCE_IMAGE)
    if not resource_id:
        resource_id = get_resource_id_by_registry_name(cmd.cli_ctx, source_registry)
    source_image = source_image[slash + 1 :]
    if not source_image:
        raise CLIError(INVALID_SOURCE_IMAGE)
    image_source = ImportSource(resource_id=resource_id, source_image=source_image)

    if tags is None and repository is None:
        tags = [source_image]

    import_parameters = ImportImageParameters(source=image_source,
                                              target_tags=tags,
                                              untagged_target_repositories=repository,
                                              mode=ImportMode.force.value if force else ImportMode.no_force.value)

    return LongRunningOperation(cmd.cli_ctx)(client.import_image(
        resource_group_name=resource_group_name,
        registry_name=registry_name,
        parameters=import_parameters))
