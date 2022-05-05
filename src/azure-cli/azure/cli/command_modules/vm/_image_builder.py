# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# TODO refactor out _image_builder commands.
# i.e something like image_builder/_client_factory image_builder/commands.py image_builder/_params.py
import os
import re
import json
import traceback
from enum import Enum

import requests

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse  # pylint: disable=import-error

from knack.util import CLIError
from knack.log import get_logger

from msrestazure.tools import is_valid_resource_id, resource_id, parse_resource_id

from azure.core.exceptions import HttpResponseError

from azure.cli.core.commands import cached_get, cached_put
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.core.commands.validators import get_default_location_from_resource_group, validate_tags
from azure.cli.core.azclierror import RequiredArgumentMissingError

from azure.cli.command_modules.vm._client_factory import _compute_client_factory
from azure.cli.command_modules.vm._validators import _get_resource_id

logger = get_logger(__name__)


class _SourceType(Enum):
    PLATFORM_IMAGE = "PlatformImage"
    ISO_URI = "ISO"
    MANAGED_IMAGE = "ManagedImage"
    SIG_VERSION = "SharedImageVersion"


class _DestType(Enum):
    MANAGED_IMAGE = 1
    SHARED_IMAGE_GALLERY = 2


class ScriptType(Enum):
    SHELL = "shell"
    POWERSHELL = "powershell"
    WINDOWS_RESTART = "windows-restart"
    WINDOWS_UPDATE = "windows-update"
    FILE = "file"


# region Client Factories

def image_builder_client_factory(cli_ctx, _):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.imagebuilder import ImageBuilderClient
    client = get_mgmt_service_client(cli_ctx, ImageBuilderClient)
    return client


def cf_img_bldr_image_templates(cli_ctx, _):
    return image_builder_client_factory(cli_ctx, _).virtual_machine_image_templates

# endregion


def _no_white_space_or_err(words):
    for char in words:
        if char.isspace():
            raise CLIError("Error: White space in {}".format(words))


def _require_defer(cmd):
    use_cache = cmd.cli_ctx.data.get('_cache', False)
    if not use_cache:
        raise CLIError("This command requires --defer")


def _parse_script(script_str):
    script_name = script_str
    script = {"script": script_str, "name": script_name, "type": None}
    if urlparse(script_str).scheme and "://" in script_str:
        _, script_name = script_str.rsplit("/", 1)
        script["name"] = script_name
        script["is_url"] = True
    else:
        raise CLIError("Expected a url, got: {}".format(script_str))

    if script_str.lower().endswith(".sh"):
        script["type"] = ScriptType.SHELL
    elif script_str.lower().endswith(".ps1"):
        script["type"] = ScriptType.POWERSHELL

    return script


def _parse_image_destination(cmd, rg, destination, is_shared_image):

    if any([not destination, "=" not in destination]):
        raise CLIError("Invalid Format: the given image destination {} must contain the '=' delimiter."
                       .format(destination))

    rid, location = destination.rsplit("=", 1)
    if not rid or not location:
        raise CLIError("Invalid Format: destination {} should have format 'destination=location'.".format(destination))

    _no_white_space_or_err(rid)

    result = None
    if is_shared_image:
        if not is_valid_resource_id(rid):
            if "/" not in rid:
                raise CLIError("Invalid Format: {} must have a shared image gallery name and definition. "
                               "They must be delimited by a '/'.".format(rid))

            sig_name, sig_def = rid.rsplit("/", 1)

            rid = resource_id(
                subscription=get_subscription_id(cmd.cli_ctx), resource_group=rg,
                namespace='Microsoft.Compute',
                type='galleries', name=sig_name,
                child_type_1='images', child_name_1=sig_def
            )

        result = rid, location.split(",")
    else:
        if not is_valid_resource_id(rid):
            rid = resource_id(
                subscription=get_subscription_id(cmd.cli_ctx),
                resource_group=rg,
                namespace='Microsoft.Compute', type='images',
                name=rid
            )

        result = rid, location

    return result


def _validate_location(location, location_names, location_display_names):

    if ' ' in location:
        # if display name is provided, attempt to convert to short form name
        location = next((name for name in location_display_names if name.lower() == location.lower()), location)

    if location.lower() not in [location_name.lower() for location_name in location_names]:
        raise CLIError("Location {} is not a valid subscription location. "
                       "Use one from `az account list-locations`.".format(location))

    return location


def process_image_template_create_namespace(cmd, namespace):  # pylint: disable=too-many-locals, too-many-branches, too-many-statements
    if namespace.image_template is not None:
        return

    from azure.cli.core.commands.parameters import get_subscription_locations

    source = None
    scripts = []

    # default location to RG location.
    if not namespace.location:
        get_default_location_from_resource_group(cmd, namespace)

    # validate tags.
    validate_tags(namespace)

    # Validate and parse scripts
    if namespace.scripts:
        for ns_script in namespace.scripts:
            scripts.append(_parse_script(ns_script))

    # Validate and parse destination and locations
    destinations = []
    subscription_locations = get_subscription_locations(cmd.cli_ctx)
    location_names = [location.name for location in subscription_locations]
    location_display_names = [location.display_name for location in subscription_locations]

    if namespace.managed_image_destinations:
        for dest in namespace.managed_image_destinations:
            rid, location = _parse_image_destination(cmd, namespace.resource_group_name, dest, is_shared_image=False)
            location = _validate_location(location, location_names, location_display_names)
            destinations.append((_DestType.MANAGED_IMAGE, rid, location))

    if namespace.shared_image_destinations:
        for dest in namespace.shared_image_destinations:
            rid, locations = _parse_image_destination(cmd, namespace.resource_group_name, dest, is_shared_image=True)
            locations = [_validate_location(location, location_names, location_display_names) for location in locations]
            destinations.append((_DestType.SHARED_IMAGE_GALLERY, rid, locations))

    # Validate and parse source image
    # 1 - check if source is a URN. A urn e.g "Canonical:UbuntuServer:18.04-LTS:latest"
    urn_match = re.match('([^:]*):([^:]*):([^:]*):([^:]*)', namespace.source)
    if urn_match:  # if platform image urn
        source = {
            'publisher': urn_match.group(1),
            'offer': urn_match.group(2),
            'sku': urn_match.group(3),
            'version': urn_match.group(4),
            'type': _SourceType.PLATFORM_IMAGE
        }

        likely_linux = bool("windows" not in source["offer"].lower() and "windows" not in source["sku"].lower())

        logger.info("%s looks like a platform image URN", namespace.source)

    # 2 - check if a fully-qualified ID (assumes it is an image ID)
    elif is_valid_resource_id(namespace.source):

        parsed = parse_resource_id(namespace.source)
        image_type = parsed.get('type')
        image_resource_type = parsed.get('type')

        if not image_type:
            pass

        elif image_type.lower() == 'images':
            source = {
                'image_id': namespace.source,
                'type': _SourceType.MANAGED_IMAGE
            }
            logger.info("%s looks like a managed image id.", namespace.source)

        elif image_type == "galleries" and image_resource_type:
            source = {
                'image_version_id': namespace.source,
                'type': _SourceType.SIG_VERSION
            }
            logger.info("%s looks like a shared image version id.", namespace.source)

    # 3 - check if source is a Redhat iso uri. If so a checksum must be provided.
    elif urlparse(namespace.source).scheme and "://" in namespace.source and ".iso" in namespace.source.lower():
        if not namespace.checksum:
            raise CLIError("Must provide a checksum for source uri: {}".format(namespace.source))
        source = {
            'source_uri': namespace.source,
            'sha256_checksum': namespace.checksum,
            'type': _SourceType.ISO_URI
        }
        likely_linux = True

        logger.info("%s looks like a RedHat iso uri.", namespace.source)

    # 4 - check if source is a urn alias from the vmImageAliasDoc endpoint. See "az cloud show"
    if not source:
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

        if "windows" not in source["offer"].lower() and "windows" not in source["sku"].lower():
            likely_linux = True

        logger.info("%s looks like a platform image alias.", namespace.source)

    # 5 - check if source is an existing managed disk image resource
    if not source:
        compute_client = _compute_client_factory(cmd.cli_ctx)
        try:
            image_name = namespace.source
            compute_client.images.get(namespace.resource_group_name, namespace.source)
            namespace.source = _get_resource_id(cmd.cli_ctx, namespace.source, namespace.resource_group_name,
                                                'images', 'Microsoft.Compute')
            source = {
                'image_id': namespace.source,
                'type': _SourceType.MANAGED_IMAGE
            }

            logger.info("%s, looks like a managed image name. Using resource ID: %s", image_name, namespace.source)  # pylint: disable=line-too-long
        except HttpResponseError:
            pass

    if not source:
        err = 'Invalid image "{}". Use a valid image URN, managed image name or ID, ISO URI, ' \
              'or pick a platform image alias from {}.\nSee vm create -h for more information on specifying an image.'\
            .format(namespace.source, ", ".join([x['urnAlias'] for x in images]))
        raise CLIError(err)

    for script in scripts:
        if script["type"] is None:
            try:
                script["type"] = ScriptType.SHELL if likely_linux else ScriptType.POWERSHELL
                logger.info("For script %s, likely linux is %s.", script["script"], likely_linux)
            except NameError:
                raise CLIError("Unable to infer the type of script {}.".format(script["script"]))

    namespace.source_dict = source
    namespace.scripts_list = scripts
    namespace.destinations_lists = destinations


# first argument is `cmd`, but it is unused. Feel free to substitute it in.
def process_img_tmpl_customizer_add_namespace(cmd, namespace):  # pylint:disable=unused-argument

    if namespace.customizer_type.lower() in [ScriptType.SHELL.value.lower(), ScriptType.POWERSHELL.value.lower()]:  # pylint:disable=no-member, line-too-long
        if not (namespace.script_url or namespace.inline_script):
            raise CLIError("A script must be provided if the customizer type is one of: {} {}"
                           .format(ScriptType.SHELL.value, ScriptType.POWERSHELL.value))

        if namespace.script_url and namespace.inline_script:
            raise CLIError("Cannot supply both script url and inline script.")

    elif namespace.customizer_type.lower() == ScriptType.WINDOWS_RESTART.value.lower():  # pylint:disable=no-member
        if namespace.script_url or namespace.inline_script:
            logger.warning("Ignoring the supplied script as scripts are not used for Windows Restart.")


def process_img_tmpl_output_add_namespace(cmd, namespace):
    from azure.cli.core.commands.parameters import get_subscription_locations

    outputs = [output for output in [namespace.managed_image, namespace.gallery_image_definition, namespace.is_vhd] if output]  # pylint:disable=line-too-long

    if len(outputs) != 1:
        err = "Supplied outputs: {}".format(outputs)
        logger.debug(err)
        raise CLIError("Usage error: must supply exactly one destination type to add. Supplied {}".format(len(outputs)))

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
                raise CLIError("Usage error: gallery image definition is a name and not an ID.")

            namespace.gallery_image_definition = resource_id(
                subscription=get_subscription_id(cmd.cli_ctx), resource_group=namespace.resource_group_name,
                namespace='Microsoft.Compute',
                type='galleries', name=namespace.gallery_name,
                child_type_1='images', child_name_1=namespace.gallery_image_definition
            )

    if namespace.is_vhd and not namespace.output_name:
        raise CLIError("Usage error: If --is-vhd is used, a run output name must be provided via --output-name.")

    subscription_locations = get_subscription_locations(cmd.cli_ctx)
    location_names = [location.name for location in subscription_locations]
    location_display_names = [location.display_name for location in subscription_locations]

    if namespace.managed_image_location:
        namespace.managed_image_location = _validate_location(namespace.managed_image_location,
                                                              location_names, location_display_names)

    if namespace.gallery_replication_regions:
        processed_regions = []
        for loc in namespace.gallery_replication_regions:
            processed_regions.append(_validate_location(loc, location_names, location_display_names))
        namespace.gallery_replication_regions = processed_regions

    # get default location from resource group
    if not any([namespace.managed_image_location, namespace.gallery_replication_regions]) and hasattr(namespace, 'location'):  # pylint: disable=line-too-long
        # store location in namespace.location for use in custom method.
        get_default_location_from_resource_group(cmd, namespace)

    # validate tags.
    validate_tags(namespace)


# region Custom Commands

def create_image_template(  # pylint: disable=too-many-locals, too-many-branches, too-many-statements, unused-argument
        cmd, client, resource_group_name, image_template_name, location=None,
        source_dict=None, scripts_list=None, destinations_lists=None, build_timeout=None, tags=None,
        source=None, scripts=None, checksum=None, managed_image_destinations=None,
        shared_image_destinations=None, no_wait=False, image_template=None, identity=None,
        vm_size=None, os_disk_size=None, vnet=None, subnet=None, proxy_vm_size=None, build_vm_identities=None):
    from azure.mgmt.imagebuilder.models import (ImageTemplate, ImageTemplateSharedImageVersionSource,
                                                ImageTemplatePlatformImageSource, ImageTemplateManagedImageSource,
                                                ImageTemplateShellCustomizer, ImageTemplatePowerShellCustomizer,
                                                ImageTemplateManagedImageDistributor,
                                                ImageTemplateSharedImageDistributor, ImageTemplateIdentity,
                                                ComponentsVrq145SchemasImagetemplateidentityPropertiesUserassignedidentitiesAdditionalproperties,  # pylint: disable=line-too-long
                                                ImageTemplateVmProfile, VirtualNetworkConfig)

    if image_template is not None:
        logger.warning('You are using --image-template. All other parameters will be ignored.')
        if os.path.exists(image_template):
            # Local file
            with open(image_template) as f:
                content = f.read()
        else:
            # It should be an URL
            msg = '\nusage error: --image-template is not a correct local path or URL'
            try:
                r = requests.get(image_template)
            except Exception:
                raise CLIError(traceback.format_exc() + msg)
            if r.status_code != 200:
                raise CLIError(traceback.format_exc() + msg)
            content = r.content

        try:
            obj = json.loads(content)
        except json.JSONDecodeError:
            raise CLIError(traceback.format_exc() +
                           '\nusage error: Content of --image-template is not a valid JSON string')
        content = {}
        if 'properties' in obj:
            content = obj['properties']
        if 'location' in obj:
            content['location'] = obj['location']
        if 'tags' in obj:
            content['tags'] = obj['tags']
        if 'identity' in obj:
            content['identity'] = obj['identity']
        return client.virtual_machine_image_templates.begin_create_or_update(
            parameters=content, resource_group_name=resource_group_name, image_template_name=image_template_name)

    template_source, template_scripts, template_destinations = None, [], []

    # create image template source settings
    if source_dict['type'] == _SourceType.PLATFORM_IMAGE:
        template_source = ImageTemplatePlatformImageSource(**source_dict)
    elif source_dict['type'] == _SourceType.ISO_URI:
        # It was supported before but is removed in the current service version.
        raise CLIError('usage error: Source type ISO URI is not supported.')
    elif source_dict['type'] == _SourceType.MANAGED_IMAGE:
        template_source = ImageTemplateManagedImageSource(**source_dict)
    elif source_dict['type'] == _SourceType.SIG_VERSION:
        template_source = ImageTemplateSharedImageVersionSource(**source_dict)

    # create image template customizer settings
    # Script structure can be found in _parse_script's function definition
    for script in scripts_list:
        script.pop("is_url")
        script["script_uri"] = script.pop("script")

        if script["type"] == ScriptType.SHELL:
            template_scripts.append(ImageTemplateShellCustomizer(**script))
        elif script["type"] == ScriptType.POWERSHELL:
            template_scripts.append(ImageTemplatePowerShellCustomizer(**script))
        else:  # Should never happen
            logger.debug("Script %s has type %s", script["script"], script["type"])
            raise CLIError("Script {} has an invalid type.".format(script["script"]))

    # create image template distribution / destination settings
    for dest_type, rid, loc_info in destinations_lists:
        parsed = parse_resource_id(rid)
        if dest_type == _DestType.MANAGED_IMAGE:
            template_destinations.append(ImageTemplateManagedImageDistributor(
                image_id=rid, location=loc_info, run_output_name=parsed['name']))
        elif dest_type == _DestType.SHARED_IMAGE_GALLERY:
            template_destinations.append(ImageTemplateSharedImageDistributor(
                gallery_image_id=rid, replication_regions=loc_info, run_output_name=parsed['child_name_1']))
        else:
            logger.info("No applicable destination found for destination %s", str(tuple([dest_type, rid, loc_info])))

    # Identity
    identity_body = None
    if identity is not None:
        subscription_id = get_subscription_id(cmd.cli_ctx)
        user_assigned_identities = {}
        for ide in identity:
            if not is_valid_resource_id(ide):
                ide = resource_id(subscription=subscription_id, resource_group=resource_group_name,
                                  namespace='Microsoft.ManagedIdentity', type='userAssignedIdentities', name=ide)
            user_assigned_identities[ide] = ComponentsVrq145SchemasImagetemplateidentityPropertiesUserassignedidentitiesAdditionalproperties()  # pylint: disable=line-too-long
        identity_body = ImageTemplateIdentity(type='UserAssigned', user_assigned_identities=user_assigned_identities)

    # VM profile
    vnet_config = None
    if vnet or subnet:
        if not is_valid_resource_id(subnet):
            subscription_id = get_subscription_id(cmd.cli_ctx)
            subnet = resource_id(subscription=subscription_id, resource_group=resource_group_name,
                                 namespace='Microsoft.Network', type='virtualNetworks', name=vnet,
                                 child_type_1='subnets', child_name_1=subnet)
        vnet_config = VirtualNetworkConfig(subnet_id=subnet)
    if proxy_vm_size is not None:
        if subnet is not None:
            vnet_config = VirtualNetworkConfig(subnet_id=subnet, proxy_vm_size=proxy_vm_size)
        else:
            raise RequiredArgumentMissingError('Usage error: --proxy-vm-size is only configurable when --subnet is specified.')
    vm_profile = ImageTemplateVmProfile(vm_size=vm_size, os_disk_size_gb=os_disk_size, user_assigned_identities=build_vm_identities, vnet_config=vnet_config)  # pylint: disable=line-too-long

    image_template = ImageTemplate(source=template_source, customize=template_scripts, distribute=template_destinations,
                                   location=location, build_timeout_in_minutes=build_timeout, tags=(tags or {}),
                                   identity=identity_body, vm_profile=vm_profile)

    return cached_put(cmd, client.virtual_machine_image_templates.begin_create_or_update, parameters=image_template,
                      resource_group_name=resource_group_name, image_template_name=image_template_name)


def list_image_templates(client, resource_group_name=None):
    if resource_group_name:
        return client.virtual_machine_image_templates.list_by_resource_group(resource_group_name)
    return client.virtual_machine_image_templates.list()


def show_build_output(client, resource_group_name, image_template_name, output_name=None):
    if output_name:
        return client.virtual_machine_image_templates.get_run_output(resource_group_name, image_template_name, output_name)  # pylint: disable=line-too-long
    return client.virtual_machine_image_templates.list_run_outputs(resource_group_name, image_template_name)


def add_template_output(cmd, client, resource_group_name, image_template_name, gallery_name=None, location=None,  # pylint: disable=line-too-long, unused-argument
                        output_name=None, is_vhd=None, tags=None,
                        gallery_image_definition=None, gallery_replication_regions=None,
                        managed_image=None, managed_image_location=None):  # pylint: disable=line-too-long, unused-argument

    _require_defer(cmd)

    from azure.mgmt.imagebuilder.models import (ImageTemplateManagedImageDistributor, ImageTemplateVhdDistributor,
                                                ImageTemplateSharedImageDistributor)
    existing_image_template = cached_get(cmd, client.virtual_machine_image_templates.get,
                                         resource_group_name=resource_group_name,
                                         image_template_name=image_template_name)

    distributor = None

    if managed_image:
        parsed = parse_resource_id(managed_image)
        distributor = ImageTemplateManagedImageDistributor(
            run_output_name=output_name or parsed['name'],
            image_id=managed_image, location=managed_image_location or location)
    elif gallery_image_definition:
        parsed = parse_resource_id(gallery_image_definition)
        distributor = ImageTemplateSharedImageDistributor(
            run_output_name=output_name or parsed['child_name_1'], gallery_image_id=gallery_image_definition,
            replication_regions=gallery_replication_regions or [location])
    elif is_vhd:
        distributor = ImageTemplateVhdDistributor(run_output_name=output_name)

    if distributor:
        distributor.artifact_tags = tags or {}

    if existing_image_template.distribute is None:
        existing_image_template.distribute = []
    else:
        for existing_distributor in existing_image_template.distribute:
            if existing_distributor.run_output_name == distributor.run_output_name:
                raise CLIError("Output with output name {} already exists in image template {}."
                               .format(distributor.run_output_name.lower(), image_template_name))

    existing_image_template.distribute.append(distributor)

    return cached_put(cmd, client.virtual_machine_image_templates.begin_create_or_update, parameters=existing_image_template,  # pylint: disable=line-too-long
                      resource_group_name=resource_group_name, image_template_name=image_template_name)


def remove_template_output(cmd, client, resource_group_name, image_template_name, output_name):
    _require_defer(cmd)

    existing_image_template = cached_get(cmd, client.virtual_machine_image_templates.get,
                                         resource_group_name=resource_group_name,
                                         image_template_name=image_template_name)
    if not existing_image_template.distribute:
        raise CLIError("No outputs to remove.")

    new_distribute = []
    for existing_distributor in existing_image_template.distribute:
        if existing_distributor.run_output_name.lower() == output_name.lower():
            continue
        new_distribute.append(existing_distributor)

    if len(new_distribute) == len(existing_image_template.distribute):
        raise CLIError("Output with output name {} not in image template distribute list.".format(output_name))

    existing_image_template.distribute = new_distribute

    return cached_put(cmd, client.virtual_machine_image_templates.begin_create_or_update, parameters=existing_image_template,  # pylint: disable=line-too-long
                      resource_group_name=resource_group_name, image_template_name=image_template_name)


def clear_template_output(cmd, client, resource_group_name, image_template_name):
    _require_defer(cmd)

    existing_image_template = cached_get(cmd, client.virtual_machine_image_templates.get,
                                         resource_group_name=resource_group_name,
                                         image_template_name=image_template_name)
    if not existing_image_template.distribute:
        raise CLIError("No outputs to remove.")

    existing_image_template.distribute = []

    return cached_put(cmd, client.virtual_machine_image_templates.begin_create_or_update, parameters=existing_image_template,  # pylint: disable=line-too-long
                      resource_group_name=resource_group_name, image_template_name=image_template_name)


def add_template_customizer(cmd, client, resource_group_name, image_template_name, customizer_name, customizer_type,
                            script_url=None, inline_script=None, valid_exit_codes=None,
                            restart_command=None, restart_check_command=None, restart_timeout=None,
                            file_source=None, dest_path=None, search_criteria=None, filters=None, update_limit=None):
    _require_defer(cmd)

    from azure.mgmt.imagebuilder.models import (ImageTemplateShellCustomizer, ImageTemplatePowerShellCustomizer,
                                                ImageTemplateRestartCustomizer, ImageTemplateFileCustomizer,
                                                ImageTemplateWindowsUpdateCustomizer)

    existing_image_template = cached_get(cmd, client.virtual_machine_image_templates.get,
                                         resource_group_name=resource_group_name,
                                         image_template_name=image_template_name)

    if existing_image_template.customize is None:
        existing_image_template.customize = []
    else:
        for existing_customizer in existing_image_template.customize:
            if existing_customizer.name == customizer_name:
                raise CLIError("Output with output name {} already exists in image template {}."
                               .format(customizer_name, image_template_name))

    new_customizer = None

    if customizer_type.lower() == ScriptType.SHELL.value.lower():  # pylint:disable=no-member
        new_customizer = ImageTemplateShellCustomizer(name=customizer_name, script_uri=script_url, inline=inline_script)
    elif customizer_type.lower() == ScriptType.POWERSHELL.value.lower():  # pylint:disable=no-member
        new_customizer = ImageTemplatePowerShellCustomizer(name=customizer_name, script_uri=script_url,
                                                           inline=inline_script, valid_exit_codes=valid_exit_codes)
    elif customizer_type.lower() == ScriptType.WINDOWS_RESTART.value.lower():  # pylint:disable=no-member
        new_customizer = ImageTemplateRestartCustomizer(name=customizer_name, restart_command=restart_command,
                                                        restart_check_command=restart_check_command,
                                                        restart_timeout=restart_timeout)
    elif customizer_type.lower() == ScriptType.FILE.value.lower():  # pylint:disable=no-member
        new_customizer = ImageTemplateFileCustomizer(name=customizer_name, source_uri=file_source,
                                                     destination=dest_path)
    elif customizer_type.lower() == ScriptType.WINDOWS_UPDATE.value.lower():
        new_customizer = ImageTemplateWindowsUpdateCustomizer(name=customizer_name, search_criteria=search_criteria,
                                                              filters=filters, update_limit=update_limit)

    if not new_customizer:
        raise CLIError("Cannot determine customizer from type {}.".format(customizer_type))

    existing_image_template.customize.append(new_customizer)

    return cached_put(cmd, client.virtual_machine_image_templates.begin_create_or_update, parameters=existing_image_template,  # pylint: disable=line-too-long
                      resource_group_name=resource_group_name, image_template_name=image_template_name)


def remove_template_customizer(cmd, client, resource_group_name, image_template_name, customizer_name):
    existing_image_template = cached_get(cmd, client.virtual_machine_image_templates.get,
                                         resource_group_name=resource_group_name,
                                         image_template_name=image_template_name)
    _require_defer(cmd)

    if not existing_image_template.customize:
        raise CLIError("No customizers to remove.")

    new_customize = []
    for existing_customizer in existing_image_template.customize:
        if existing_customizer.name == customizer_name:
            continue
        new_customize.append(existing_customizer)

    if len(new_customize) == len(existing_image_template.customize):
        raise CLIError("Customizer with name {} not in image template customizer list.".format(customizer_name))

    existing_image_template.customize = new_customize

    return cached_put(cmd, client.virtual_machine_image_templates.begin_create_or_update, parameters=existing_image_template,  # pylint: disable=line-too-long
                      resource_group_name=resource_group_name, image_template_name=image_template_name)


def clear_template_customizer(cmd, client, resource_group_name, image_template_name):
    _require_defer(cmd)

    existing_image_template = cached_get(cmd, client.virtual_machine_image_templates.get,
                                         resource_group_name=resource_group_name,
                                         image_template_name=image_template_name)

    if not existing_image_template.customize:
        raise CLIError("No customizers to remove.")

    existing_image_template.customize = []

    return cached_put(cmd, client.virtual_machine_image_templates.begin_create_or_update, parameters=existing_image_template,  # pylint: disable=line-too-long
                      resource_group_name=resource_group_name, image_template_name=image_template_name)

# endregion
