# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import re
import os
from enum import Enum
from azure.cli.core.commands import LongRunningOperation

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse  # pylint: disable=import-error

from azure.cli.core.util import sdk_no_wait
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.core.commands.validators import get_default_location_from_resource_group
from knack.util import CLIError
from msrestazure.tools import is_valid_resource_id, resource_id, parse_resource_id

import copy
from msrest.exceptions import ClientException, ValidationError
from azure.mgmt.imagebuilder.models import ImageTemplate

from knack.log import get_logger
logger = get_logger(__name__)


class _SourceType(Enum):
    PLATFORM_IMAGE = "PlatformImage"
    ISO_URI = "ISO"

class _DestType(Enum):
    MANAGED_IMAGE = 1
    SHARED_IMAGE_GALLERY = 2

# region Client Factories

def image_builder_client_factory(cli_ctx, _):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.imagebuilder import ImageBuilderClient
    return get_mgmt_service_client(cli_ctx, ImageBuilderClient)

def cf_img_bldr_image_templates(cli_ctx, _):
    return image_builder_client_factory(cli_ctx, _).virtual_machine_image_template

# endregion

def _parse_script(script_str):
    script_name = script_str
    script = {"script": script_str, "name": script_name}
    if urlparse(script_str).scheme and "://" in script_str:
        logger.info("{} appears to be a url.".format(script_str))
        if "/" in script_str:
            _, script_name = script_str.rsplit(sep="/", maxsplit=1)
            script["name"] = script_name
        script["is_url"] = True
    else:
        logger.info("{} does not look like a url. Assuming it is a file.".format(script_str))
        script["is_url"] = False
        if not os.path.isfile(script_str):
            raise CLIError("Script file {} does not exist.".format(script_str))
        raise CLIError("Script file found, however, uploading to a storage account is not yet supported on the CLI.")
    return script

def _no_white_space_or_err(words):
    for char in words:
        if char.isspace():
            raise CLIError("Error: White space in {}".format(words))

def _parse_managed_image_destination(cmd, rg, destination):

    if any([not destination, "=" not in destination]):
        raise CLIError("Invalid Format: the given image destination {} must be a string that contains the '=' delimiter.".format(destination))

    rid, location = destination.rsplit(sep="=", maxsplit=1)
    if not rid or not location:
        raise CLIError("Invalid Format: destination {} should have format 'destination=location'.".format(destination))

    _no_white_space_or_err(rid)

    if not is_valid_resource_id(rid):
        rid = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=rg,
            namespace='Microsoft.Compute', type='images',
            name=rid
        )

    return rid, location


def _parse_shared_image_destination(cmd, rg, destination):

    if any([not destination, "=" not in destination]):
        raise CLIError("Invalid Format: the given image destination {} must be a string that contains the '=' delimiter.".format(destination))

    rid, location = destination.rsplit(sep="=", maxsplit=1)

    if not rid or not location:
        raise CLIError("Invalid Format: destination {} should have format 'destination=location'.".format(destination))

    _no_white_space_or_err(rid)

    if not is_valid_resource_id(rid):
        if "/" not in rid:
            raise CLIError("Invalid Format: {} must have a shared image gallery name and definition. They must be delimited by a '/'.".format(rid))

        sig_name, sig_def = rid.rsplit(sep="/", maxsplit=1)

        rid = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx), resource_group=rg,
            namespace='Microsoft.Compute',
            type='galleries', name=sig_name,
            child_type_1='images', child_name_1=sig_def
        )

    return (rid, location.split(","))

def _validate_location(location, location_names, location_display_names):

    if ' ' in location:
        # if display name is provided, attempt to convert to short form name
        location = next((l for l in location_display_names if l.lower() == location.lower()), location)

    if location.lower() not in [l.lower() for l in location_names]:
        raise CLIError("Location {} is not a valid subscription location. Use one from `az account list-locations`.".format(location))

    return location

def process_image_template_create_namespace(cmd, namespace):
    from azure.cli.core.commands.parameters import get_subscription_locations

    source = None
    scripts = []

    # default location to RG location.
    if not namespace.location:
        get_default_location_from_resource_group(cmd, namespace)

    # Validate and parse scripts
    for ns_script in namespace.scripts:
        scripts.append(_parse_script(ns_script))


    # Validate and parse destination and locations

    destinations = []
    subscription_locations = get_subscription_locations(cmd.cli_ctx)
    location_names = [l.name for l in subscription_locations]
    location_display_names = [l.display_name for l in subscription_locations]

    if namespace.managed_image_destinations:
        for dest in namespace.managed_image_destinations:
            id, location = _parse_managed_image_destination(cmd, namespace.resource_group_name, dest)
            location = _validate_location(location, location_names, location_display_names)
            destinations.append((_DestType.MANAGED_IMAGE, id, location))

    if namespace.shared_image_destinations:
        for dest in namespace.shared_image_destinations:
            id, locations = _parse_shared_image_destination(cmd, namespace.resource_group_name, dest)
            locations = [_validate_location(l, location_names, location_display_names) for l in locations]
            destinations.append((_DestType.SHARED_IMAGE_GALLERY, id, locations))

    # Validate and parse source image
    # 1 - check if source is a URN. A urn e.g "Canonical:UbuntuServer:18.04-LTS:latest"
    urn_match = re.match('([^:]*):([^:]*):([^:]*):([^:]*)', namespace.source)
    if urn_match: # if platform image urn
        source = {
            'publisher': urn_match.group(1),
            'offer': urn_match.group(2),
            'sku': urn_match.group(3),
            'version': urn_match.group(4),
            'type': _SourceType.PLATFORM_IMAGE
        }

    # 2 - check if source is a Redhat iso uri. If so a checksum must be provided.
    elif urlparse(namespace.source).scheme and "://" in namespace.source and ".iso" in namespace.source.lower():
        if not namespace.checksum:
            raise CLIError("Must provide a checksum for source uri.", )
        source = {
            'source_uri': namespace.source,
            'sha256_checksum': namespace.checksum,
            'type': _SourceType.ISO_URI
        }
    # 3 - check if source is a urn alias from the vmImageAliasDoc endpoint. See "az cloud show"
    else:
        from azure.cli.command_modules.vm._actions import load_images_from_aliases_doc
        images = load_images_from_aliases_doc(cmd.cli_ctx)
        matched = next((x for x in images if x['urnAlias'].lower() == namespace.source.lower()), None)
        if matched:
            source = {
                'publisher': matched['publisher'],
                'offer': matched['offer'],
                'sku': matched['sku'],
                'version': matched['version'],
                'type': _SourceType.PLATFORM_IMAGE
            }

    if not source:
        err = 'Invalid image "{}". Use a valid image URN, ISO URI, or pick a platform image alias from {}.\n' \
              'See vm create -h for more information on specifying an image.'
        raise CLIError(err.format(namespace.source, ", ".join([x['urnAlias'] for x in images])))


    namespace.source_dict = source
    namespace.scripts_list = scripts
    namespace.destinations_lists = destinations

def process_img_tmpl_output_add_namespace(cmd, namespace):
    from azure.cli.core.commands.parameters import get_subscription_locations
    from azure.cli.core.commands.validators import get_default_location_from_resource_group

    outputs = [namespace.managed_image, namespace.gallery_image_definition]
    if not any(outputs) or all(outputs):
        raise CLIError("Usage error: must supply only one managed image or shared image destination.")

    if namespace.managed_image:
        if not is_valid_resource_id(namespace.managed_image):
            namespace.managed_image = resource_id(
                subscription=get_subscription_id(cmd.cli_ctx),
                resource_group=namespace.resource_group_name,
                namespace='Microsoft.Compute', type='images',
                name=namespace.managed_image
            )

    if namespace.gallery_image_definition:
        if not is_valid_resource_id(namespace.gallery_image_definition):
            if not namespace.gallery_name:
                raise CLIError("Usage error: gallery image definition is a name and not an ID..")

            namespace.gallery_image_definition = resource_id(
                subscription=get_subscription_id(cmd.cli_ctx), resource_group=namespace.resource_group_name,
                namespace='Microsoft.Compute',
                type='galleries', name=namespace.gallery_name,
                child_type_1='images', child_name_1=namespace.gallery_image_definition
            )

    subscription_locations = get_subscription_locations(cmd.cli_ctx)
    location_names = [l.name for l in subscription_locations]
    location_display_names = [l.display_name for l in subscription_locations]

    if namespace.managed_image_location:
        namespace.managed_image_location = _validate_location(namespace.managed_image_location, location_names, location_display_names)

    if namespace.gallery_replication_regions:
        processed_regions = []
        for loc in namespace.gallery_replication_regions:
            processed_regions.append(_validate_location(loc, location_names, location_display_names))
        namespace.gallery_replication_regions = processed_regions


    if not any([namespace.managed_image_location, namespace.gallery_replication_regions]) and hasattr(namespace, 'location'):
        get_default_location_from_resource_group(cmd, namespace) # store location in namespace.location for use in custom method.


# region Custom Commands

def create_image_template(client, resource_group_name, image_template_name, source, scripts,
                          checksum=None, location=None, no_wait=False,
                          managed_image_destinations=None, shared_image_destinations=None,
                          source_dict=None, scripts_list=None, destinations_lists=None):
    from azure.mgmt.imagebuilder.models import ImageTemplate, ImageTemplatePlatformImageSource, ImageTemplateIsoSource,\
        ImageTemplateShellCustomizer, ImageTemplateManagedImageDistributor, ImageTemplateSharedImageDistributor

    template_source, template_scripts, template_destinations = None, [], []

    # create image template source settings
    if source_dict['type'] == _SourceType.PLATFORM_IMAGE:
        template_source = ImageTemplatePlatformImageSource(**source_dict)
    elif source_dict['type'] == _SourceType.ISO_URI:
        template_source = ImageTemplateIsoSource(**source_dict)

    # create image template customizer settings
    for script in scripts_list:
        script.pop("is_url")
        template_scripts.append(ImageTemplateShellCustomizer(**script))

    # create image template distribution / destination settings
    for dest_type, id, loc_info in destinations_lists:
        parsed = parse_resource_id(id)
        if dest_type == _DestType.MANAGED_IMAGE:
            template_destinations.append(ImageTemplateManagedImageDistributor(image_id=id, location=loc_info, run_output_name=parsed['name']))
        elif dest_type == _DestType.SHARED_IMAGE_GALLERY:
            template_destinations.append(ImageTemplateSharedImageDistributor(gallery_image_id=id, replication_regions=loc_info, run_output_name=parsed['child_name_1']))  # pylint: disable=line-too-long
        else:
            logger.info("No applicable destination found for destination {}".format(tuple([dest_type, id, loc_info])))

    image_template = ImageTemplate(source=template_source, customize=template_scripts, distribute=template_destinations, location=location)
    return sdk_no_wait(no_wait, client.virtual_machine_image_template.create_or_update, image_template, resource_group_name, image_template_name)


def list_image_templates(client, resource_group_name=None):
    if resource_group_name:
        return client.virtual_machine_image_template.list_by_resource_group(resource_group_name)
    return client.virtual_machine_image_template.list()


def build_image_template(client, resource_group_name, image_template_name, no_wait=False):
    # bug we need to specify utf8 in headers. Todo: remove when bug fixed.
    header = {'Content-Type' : 'application/json'}
    return sdk_no_wait(no_wait, client.virtual_machine_image_template.run, resource_group_name, image_template_name, custom_headers=header)


def show_build_output(client, resource_group_name, image_template_name, output_name=None):
    if output_name:
        return client.virtual_machine_image_template.get_run_output(resource_group_name, image_template_name, output_name)
    return client.virtual_machine_image_template.get_run_outputs(resource_group_name, image_template_name)

# TODO: add when new whl file generated. support tags for create and here.
def add_template_output(cmd, client, resource_group_name, image_template_name, gallery_name=None, location=None,
                        gallery_image_definition=None, gallery_replication_regions=None,
                        managed_image=None, managed_image_location=None, output_name=None):
    from azure.mgmt.imagebuilder.models import ImageTemplateManagedImageDistributor, ImageTemplateSharedImageDistributor
    existing_image_template = client.virtual_machine_image_template.get(resource_group_name, image_template_name)
    old_template_copy = copy.deepcopy(existing_image_template)

    if managed_image:
        parsed = parse_resource_id(managed_image)
        distributor = ImageTemplateManagedImageDistributor(run_output_name=output_name or parsed['name'],
                                                               image_id=managed_image, location=managed_image_location or location)
    elif gallery_image_definition:
        parsed = parse_resource_id(gallery_image_definition)
        distributor = ImageTemplateSharedImageDistributor(run_output_name=output_name or parsed['child_name_1'],
                                                               gallery_image_id=gallery_image_definition, replication_regions=gallery_replication_regions or [location])

    if existing_image_template.distribute is None:
        existing_image_template.distribute = []
    else:
        for existing_distributor in existing_image_template.distribute:
            if existing_distributor.run_output_name.lower() == distributor.run_output_name.lower():
                raise CLIError("Output with output name {} already exists in image template {}.".format(distributor.run_output_name.lower(), image_template_name))

    existing_image_template.distribute.append(distributor)
    # Work around of not having update method. delete then create.
    return _update_image_template(cmd, client, resource_group_name, image_template_name, existing_image_template, old_template_copy)

def remove_template_output(cmd, client, resource_group_name, image_template_name, output_name):
    existing_image_template = client.virtual_machine_image_template.get(resource_group_name, image_template_name)
    old_template_copy = copy.deepcopy(existing_image_template)

    if not existing_image_template.distribute:
        raise CLIError("No outputs to remove.")

    new_distribute = []
    for existing_distributor in existing_image_template.distribute:
        if existing_distributor.run_output_name.lower() == output_name.lower():
            continue
        new_distribute.append(new_distribute)

    if len(new_distribute) == len(existing_image_template.distribute):
        raise CLIError("Output with output name {} not in image template distribute list.".format(output_name))

    existing_image_template.distribute = new_distribute

    return _update_image_template(cmd, client, resource_group_name, image_template_name, existing_image_template, old_template_copy)


def clear_template_output(cmd, client, resource_group_name, image_template_name):
    existing_image_template = client.virtual_machine_image_template.get(resource_group_name, image_template_name)

    old_template_copy = copy.deepcopy(existing_image_template)

    if not existing_image_template.distribute:
        raise CLIError("No outputs to remove.")

    existing_image_template.distribute = []

    return _update_image_template(cmd, client, resource_group_name, image_template_name, existing_image_template, old_template_copy)



def _update_image_template(cmd, client, resource_group_name, image_template_name, new_template, old_template):
    LongRunningOperation(cmd.cli_ctx)(client.virtual_machine_image_template.delete(resource_group_name, image_template_name))
    try:
        return LongRunningOperation(cmd.cli_ctx)(client.virtual_machine_image_template.create_or_update(new_template, resource_group_name, image_template_name))
    except (ClientException) as e:
        logger.warning("Failed to create updated template.\nError: %s.\nRe-creating old template", e)
        old_template.distribute = old_template.distribute or []
        old_template.customize = old_template.customize or []
        return LongRunningOperation(cmd.cli_ctx)(client.virtual_machine_image_template.create_or_update(old_template, resource_group_name, image_template_name))

# endregion