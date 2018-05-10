from azure.cli.core.commands import LongRunningOperation
from azure.mgmt.containerregistry.v2018_02_01_preview.models import (
    ImportImageParameters,
    ImportSource
)
from ._utils import validate_managed_registry
from ._client_factory import cf_acr_registries

IMPORT_NOT_SUPPORTED = "Image imports are only supported for managed registries."


def acr_image_import(cmd,
                     registry_name,
                     resource_id,
                     source_image,
                     target_tags,
                     untagged_target_repositories=None,
                     resource_group_name=None,
                     mode="NoForce"):
    _, resource_group_name = validate_managed_registry(
        cmd.cli_ctx, registry_name, resource_group_name, IMPORT_NOT_SUPPORTED)

    client_registries = cf_acr_registries(cmd.cli_ctx)

    image_source = ImportSource(
        resource_id=resource_id, source_image=source_image)

    import_parameters = ImportImageParameters(source=image_source,
                                              target_tags=target_tags,
                                              untagged_target_repositories=untagged_target_repositories,
                                              mode=mode)

    image_imported = LongRunningOperation(cmd.cli_ctx)(client_registries.import_image(
        resource_group_name=resource_group_name,
        registry_name=registry_name,
        parameters=import_parameters))

    return image_imported
