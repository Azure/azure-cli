# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long, consider-using-f-string, logging-format-interpolation, inconsistent-return-statements, broad-except, bare-except, too-many-statements, too-many-locals, too-many-boolean-expressions, too-many-branches, too-many-nested-blocks, pointless-statement, expression-not-assigned, unbalanced-tuple-unpacking, unsupported-assignment-operation
# pylint: disable=unused-argument, no-else-raise
from copy import deepcopy
import json
import threading
import sys
import time
from urllib.parse import urlparse
import requests


from azure.cli.core.azclierror import (
    RequiredArgumentMissingError,
    ValidationError,
    ResourceNotFoundError,
    CLIError,
    CLIInternalError,
    InvalidArgumentValueError,
    ArgumentUsageError,
    MutuallyExclusiveArgumentError)
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.core.util import open_page_in_browser
from azure.mgmt.core.tools import parse_resource_id, is_valid_resource_id
from knack.log import get_logger
from knack.prompting import prompt_y_n, prompt as prompt_str

from msrest.exceptions import DeserializationError

from .containerapp_job_decorator import ContainerAppJobDecorator, ContainerAppJobCreateDecorator
from .containerapp_env_decorator import ContainerAppEnvDecorator, ContainerAppEnvCreateDecorator, ContainerAppEnvUpdateDecorator
from .containerapp_auth_decorator import ContainerAppAuthDecorator
from .containerapp_decorator import ContainerAppCreateDecorator, BaseContainerAppDecorator
from ._client_factory import handle_raw_exception, handle_non_resource_not_found_exception, \
    handle_non_404_status_code_exception
from ._clients import (
    ManagedEnvironmentClient,
    ContainerAppClient,
    GitHubActionClient,
    DaprComponentClient,
    StorageClient,
    AuthClient,
    WorkloadProfileClient,
    ContainerAppsJobClient,
    HttpRouteConfigClient,
    SubscriptionClient
)
from ._github_oauth import get_github_access_token
from ._models import (
    JobExecutionTemplate as JobExecutionTemplateModel,
    RegistryCredentials as RegistryCredentialsModel,
    ContainerResources as ContainerResourcesModel,
    Scale as ScaleModel,
    Container as ContainerModel,
    GitHubActionConfiguration,
    RegistryInfo as RegistryInfoModel,
    AzureCredentials as AzureCredentialsModel,
    SourceControl as SourceControlModel,
    ContainerAppCertificateEnvelope as ContainerAppCertificateEnvelopeModel,
    ContainerAppCustomDomain as ContainerAppCustomDomainModel,
    AzureFileProperties as AzureFilePropertiesModel,
    ScaleRule as ScaleRuleModel,
    Volume as VolumeModel,
    VolumeMount as VolumeMountModel)

from ._utils import (_validate_subscription_registered,
                     parse_secret_flags, store_as_secret_and_return_secret_ref, parse_env_var_flags,
                     _get_existing_secrets, _convert_object_from_snake_to_camel_case,
                     _object_to_dict, _add_or_update_secrets, _remove_additional_attributes, _remove_readonly_attributes,
                     _add_or_update_env_vars, _add_or_update_tags, _update_revision_weights, _append_label_weights,
                     _get_app_from_revision, raise_missing_token_suggestion, _remove_registry_secret, _remove_secret,
                     _ensure_identity_resource_id, _remove_dapr_readonly_attributes, _remove_env_vars, _validate_traffic_sum,
                     _update_revision_env_secretrefs, _get_acr_cred, safe_get, await_github_action, repo_url_to_name,
                     validate_container_app_name, _update_weights, register_provider_if_needed,
                     generate_randomized_cert_name, _get_name, load_cert_file, check_cert_name_availability,
                     validate_hostname, patch_new_custom_domain, get_custom_domains, _validate_revision_name, set_managed_identity,
                     is_registry_msi_system, clean_null_values, _populate_secret_values,
                     safe_set, parse_metadata_flags, parse_auth_flags, set_ip_restrictions, certificate_matches,
                     ensure_workload_profile_supported, _generate_secret_volume_name,
                     trigger_workflow, AppType,
                     format_location, certificate_location_matches, generate_randomized_managed_cert_name,
                     check_managed_cert_name_availability, prepare_managed_certificate_envelop)
from ._validators import validate_revision_suffix
from ._ssh_utils import (SSH_DEFAULT_ENCODING, WebSocketConnection, read_ssh, get_stdin_writer, SSH_CTRL_C_MSG,
                         SSH_BACKUP_ENCODING)
from ._constants import (MICROSOFT_SECRET_SETTING_NAME, FACEBOOK_SECRET_SETTING_NAME, GITHUB_SECRET_SETTING_NAME,
                         GOOGLE_SECRET_SETTING_NAME, TWITTER_SECRET_SETTING_NAME, APPLE_SECRET_SETTING_NAME, CONTAINER_APPS_RP,
                         NAME_INVALID, NAME_ALREADY_EXISTS, ACR_IMAGE_SUFFIX, HELLO_WORLD_IMAGE, LOG_TYPE_SYSTEM, LOG_TYPE_CONSOLE,
                         MANAGED_CERTIFICATE_RT, PRIVATE_CERTIFICATE_RT, PENDING_STATUS, SUCCEEDED_STATUS, CONTAINER_APPS_SDK_MODELS,
                         BLOB_STORAGE_TOKEN_STORE_SECRET_SETTING_NAME, DEFAULT_PORT)

from .containerapp_job_registry_decorator import ContainerAppJobRegistryDecorator, ContainerAppJobRegistrySetDecorator, \
    ContainerAppJobRegistryRemoveDecorator

logger = get_logger(__name__)


# These properties should be under the "properties" attribute. Move the properties under "properties" attribute
def process_loaded_yaml(yaml_containerapp):
    if not isinstance(yaml_containerapp, dict):  # pylint: disable=unidiomatic-typecheck
        raise ValidationError('Invalid YAML provided. Please see https://aka.ms/azure-container-apps-yaml for a valid containerapps YAML spec.')
    if not yaml_containerapp.get('properties'):
        yaml_containerapp['properties'] = {}

    if yaml_containerapp.get('identity') and yaml_containerapp['identity'].get('userAssignedIdentities'):
        for identity in yaml_containerapp['identity']['userAssignedIdentities']:
            # properties (principalId and clientId) are readonly and create (PUT) will throw error if they are provided
            # Update (PATCH) ignores them so it's okay to remove them as well
            yaml_containerapp['identity']['userAssignedIdentities'][identity] = {}

    nested_properties = ["provisioningState",
                         "managedEnvironmentId",
                         "environmentId",
                         "latestRevisionName",
                         "latestRevisionFqdn",
                         "customDomainVerificationId",
                         "configuration",
                         "template",
                         "outboundIPAddresses",
                         "workloadProfileName",
                         "latestReadyRevisionName",
                         "eventStreamEndpoint"]
    for nested_property in nested_properties:
        tmp = yaml_containerapp.get(nested_property)
        if nested_property in yaml_containerapp:
            yaml_containerapp['properties'][nested_property] = tmp
            del yaml_containerapp[nested_property]

    if "managedEnvironmentId" in yaml_containerapp['properties']:
        tmp = yaml_containerapp['properties']['managedEnvironmentId']
        if tmp:
            yaml_containerapp['properties']["environmentId"] = tmp
        del yaml_containerapp['properties']['managedEnvironmentId']

    return yaml_containerapp


def load_yaml_file(file_name):
    import yaml
    import errno

    try:
        with open(file_name) as stream:  # pylint: disable=unspecified-encoding
            return yaml.safe_load(stream.read().replace('\x00', ''))
    except OSError as ex:
        if getattr(ex, 'errno', 0) == errno.ENOENT:
            raise ValidationError('{} does not exist'.format(file_name)) from ex
        raise
    except (yaml.parser.ParserError, UnicodeDecodeError) as ex:
        raise ValidationError('Error parsing {} ({})'.format(file_name, str(ex))) from ex


def create_deserializer():
    from ._sdk_models import ContainerApp  # pylint: disable=unused-import
    from msrest import Deserializer
    import inspect

    sdkClasses = inspect.getmembers(sys.modules[CONTAINER_APPS_SDK_MODELS])
    deserializer = {}

    for sdkClass in sdkClasses:
        deserializer[sdkClass[0]] = sdkClass[1]

    return Deserializer(deserializer)


def update_containerapp_yaml(cmd, name, resource_group_name, file_name, from_revision=None, no_wait=False):
    yaml_containerapp = process_loaded_yaml(load_yaml_file(file_name))

    if not yaml_containerapp.get('name'):
        yaml_containerapp['name'] = name
    elif yaml_containerapp.get('name').lower() != name.lower():
        logger.warning('The app name provided in the --yaml file "{}" does not match the one provided in the --name flag "{}". The one provided in the --yaml file will be used.'.format(yaml_containerapp.get('name'), name))
    name = yaml_containerapp.get('name')

    if not yaml_containerapp.get('type'):
        yaml_containerapp['type'] = 'Microsoft.App/containerApps'
    elif yaml_containerapp.get('type').lower() != "microsoft.app/containerapps":
        raise ValidationError('Containerapp type must be \"Microsoft.App/ContainerApps\"')

    containerapp_def = None

    # Check if containerapp exists
    try:
        containerapp_def = ContainerAppClient.show(cmd=cmd, resource_group_name=resource_group_name, name=name)
    except Exception:
        pass

    if not containerapp_def:
        raise ValidationError("The containerapp '{}' does not exist".format(name))
    existed_environment_id = containerapp_def['properties']['environmentId']
    containerapp_def = None

    # Deserialize the yaml into a ContainerApp object. Need this since we're not using SDK
    try:
        deserializer = create_deserializer()
        containerapp_def = deserializer('ContainerApp', yaml_containerapp)
    except DeserializationError as ex:
        raise ValidationError('Invalid YAML provided. Please see https://aka.ms/azure-container-apps-yaml for a valid containerapps YAML spec.') from ex

    # Remove tags before converting from snake case to camel case, then re-add tags. We don't want to change the case of the tags. Need this since we're not using SDK
    tags = None
    if yaml_containerapp.get('tags'):
        tags = yaml_containerapp.get('tags')
        del yaml_containerapp['tags']

    containerapp_def = _convert_object_from_snake_to_camel_case(_object_to_dict(containerapp_def))
    containerapp_def['tags'] = tags

    # After deserializing, some properties may need to be moved under the "properties" attribute. Need this since we're not using SDK
    containerapp_def = process_loaded_yaml(containerapp_def)

    # Change which revision we update from
    if from_revision:
        r = ContainerAppClient.show_revision(cmd=cmd, resource_group_name=resource_group_name, container_app_name=name, name=from_revision)
        _update_revision_env_secretrefs(r["properties"]["template"]["containers"], name)
        containerapp_def["properties"]["template"] = r["properties"]["template"]

    # Remove "additionalProperties" and read-only attributes that are introduced in the deserialization. Need this since we're not using SDK
    _remove_additional_attributes(containerapp_def)
    _remove_readonly_attributes(containerapp_def)

    secret_values = list_secrets(cmd=cmd, name=name, resource_group_name=resource_group_name, show_values=True)
    _populate_secret_values(containerapp_def, secret_values)

    # Clean null values since this is an update
    containerapp_def = clean_null_values(containerapp_def)

    # Fix bug with revisionSuffix when containers are added
    if not safe_get(containerapp_def, "properties", "template", "revisionSuffix"):
        if "properties" not in containerapp_def:
            containerapp_def["properties"] = {}
        if "template" not in containerapp_def["properties"]:
            containerapp_def["properties"]["template"] = {}
        containerapp_def["properties"]["template"]["revisionSuffix"] = None

    # Remove the environmentId in the PATCH payload if it has not been changed
    if safe_get(containerapp_def, "properties", "environmentId") and safe_get(containerapp_def, "properties", "environmentId").lower() == existed_environment_id.lower():
        del containerapp_def["properties"]['environmentId']

    try:
        r = ContainerAppClient.update(
            cmd=cmd, resource_group_name=resource_group_name, name=name, container_app_envelope=containerapp_def, no_wait=no_wait)

        if not no_wait and "properties" in r and "provisioningState" in r["properties"] and r["properties"]["provisioningState"].lower() == "waiting":
            logger.warning('Containerapp creation in progress. Please monitor the creation using `az containerapp show -n {} -g {}`'.format(
                name, resource_group_name
            ))

        return r
    except Exception as e:
        handle_raw_exception(e)


def create_containerapp(cmd,
                        name,
                        resource_group_name,
                        yaml=None,
                        image=None,
                        container_name=None,
                        managed_env=None,
                        min_replicas=None,
                        max_replicas=None,
                        scale_rule_name=None,
                        scale_rule_type=None,
                        scale_rule_http_concurrency=None,
                        scale_rule_metadata=None,
                        scale_rule_auth=None,
                        target_port=None,
                        exposed_port=None,
                        transport="auto",
                        ingress=None,
                        allow_insecure=False,
                        revisions_mode="single",
                        secrets=None,
                        env_vars=None,
                        cpu=None,
                        memory=None,
                        registry_server=None,
                        registry_user=None,
                        registry_pass=None,
                        dapr_enabled=False,
                        dapr_app_port=None,
                        dapr_app_id=None,
                        dapr_app_protocol=None,
                        dapr_http_read_buffer_size=None,
                        dapr_http_max_request_size=None,
                        dapr_log_level=None,
                        dapr_enable_api_logging=False,
                        revision_suffix=None,
                        startup_command=None,
                        args=None,
                        tags=None,
                        no_wait=False,
                        system_assigned=False,
                        disable_warnings=False,
                        user_assigned=None,
                        registry_identity=None,
                        workload_profile_name=None,
                        termination_grace_period=None,
                        secret_volume_mount=None):
    raw_parameters = locals()

    containerapp_create_decorator = ContainerAppCreateDecorator(
        cmd=cmd,
        client=ContainerAppClient,
        raw_parameters=raw_parameters,
        models=CONTAINER_APPS_SDK_MODELS
    )
    containerapp_create_decorator.register_provider(CONTAINER_APPS_RP)
    containerapp_create_decorator.validate_arguments()

    containerapp_create_decorator.construct_payload()
    r = containerapp_create_decorator.create()
    containerapp_create_decorator.construct_for_post_process(r)
    r = containerapp_create_decorator.post_process(r)
    return r


def update_containerapp_logic(cmd,
                              name,
                              resource_group_name,
                              yaml=None,
                              image=None,
                              container_name=None,
                              min_replicas=None,
                              max_replicas=None,
                              scale_rule_name=None,
                              scale_rule_type="http",
                              scale_rule_http_concurrency=None,
                              scale_rule_metadata=None,
                              scale_rule_auth=None,
                              set_env_vars=None,
                              remove_env_vars=None,
                              replace_env_vars=None,
                              remove_all_env_vars=False,
                              cpu=None,
                              memory=None,
                              revision_suffix=None,
                              startup_command=None,
                              args=None,
                              tags=None,
                              no_wait=False,
                              from_revision=None,
                              ingress=None,
                              target_port=None,
                              workload_profile_name=None,
                              termination_grace_period=None,
                              registry_server=None,
                              registry_user=None,
                              registry_pass=None,
                              secret_volume_mount=None):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)
    validate_revision_suffix(revision_suffix)

    # Validate that max_replicas is set to 0-1000
    if max_replicas is not None:
        if max_replicas < 1 or max_replicas > 1000:
            raise ArgumentUsageError('--max-replicas must be in the range [1,1000]')

    if yaml:
        if image or min_replicas or max_replicas or\
            set_env_vars or remove_env_vars or replace_env_vars or remove_all_env_vars or cpu or memory or\
                startup_command or args or tags:
            logger.warning('Additional flags were passed along with --yaml. These flags will be ignored, and the configuration defined in the yaml will be used instead')
        return update_containerapp_yaml(cmd=cmd, name=name, resource_group_name=resource_group_name, file_name=yaml, no_wait=no_wait, from_revision=from_revision)

    containerapp_def = None
    try:
        containerapp_def = ContainerAppClient.show(cmd=cmd, resource_group_name=resource_group_name, name=name)
    except Exception as e:
        handle_non_404_status_code_exception(e)

    if not containerapp_def:
        raise ResourceNotFoundError("The containerapp '{}' does not exist".format(name))

    new_containerapp = {}
    new_containerapp["properties"] = {}
    if from_revision:
        try:
            r = ContainerAppClient.show_revision(cmd=cmd, resource_group_name=resource_group_name, container_app_name=name, name=from_revision)
        except CLIError as e:
            # Error handle the case where revision not found?
            handle_raw_exception(e)

        _update_revision_env_secretrefs(r["properties"]["template"]["containers"], name)
        new_containerapp["properties"]["template"] = r["properties"]["template"]

    # Doing this while API has bug. If env var is an empty string, API doesn't return "value" even though the "value" should be an empty string
    for container in safe_get(containerapp_def, "properties", "template", "containers", default=[]):
        if "env" in container:
            for e in container["env"]:
                if "value" not in e:
                    e["value"] = ""

    update_map = {}
    update_map['scale'] = min_replicas is not None or max_replicas is not None or scale_rule_name
    update_map['container'] = image or container_name or set_env_vars is not None or remove_env_vars is not None or replace_env_vars is not None or remove_all_env_vars or cpu or memory or startup_command is not None or args is not None or secret_volume_mount is not None
    update_map['ingress'] = ingress or target_port
    update_map['registry'] = registry_server or registry_user or registry_pass

    if tags:
        _add_or_update_tags(new_containerapp, tags)

    if revision_suffix is not None:
        new_containerapp["properties"]["template"] = {} if "template" not in new_containerapp["properties"] else new_containerapp["properties"]["template"]
        new_containerapp["properties"]["template"]["revisionSuffix"] = revision_suffix

    if termination_grace_period is not None:
        safe_set(new_containerapp, "properties", "template", "terminationGracePeriodSeconds", value=termination_grace_period)

    if workload_profile_name:
        new_containerapp["properties"]["workloadProfileName"] = workload_profile_name

        parsed_managed_env = parse_resource_id(containerapp_def["properties"]["managedEnvironmentId"])
        managed_env_name = parsed_managed_env['name']
        managed_env_rg = parsed_managed_env['resource_group']
        managed_env_info = None
        try:
            managed_env_info = ManagedEnvironmentClient.show(cmd=cmd, resource_group_name=managed_env_rg, name=managed_env_name)
        except:
            pass

        if not managed_env_info:
            raise ValidationError("Error parsing the managed environment '{}' from the specified containerapp".format(managed_env_name))

        ensure_workload_profile_supported(cmd, managed_env_name, managed_env_rg, workload_profile_name, managed_env_info)

    # Containers
    if update_map["container"]:
        new_containerapp["properties"]["template"] = {} if "template" not in new_containerapp["properties"] else new_containerapp["properties"]["template"]
        new_containerapp["properties"]["template"]["containers"] = containerapp_def["properties"]["template"]["containers"]
        if not container_name:
            if len(new_containerapp["properties"]["template"]["containers"]) == 1:
                container_name = new_containerapp["properties"]["template"]["containers"][0]["name"]
            else:
                raise ValidationError("Usage error: --container-name is required when adding or updating a container")

        # Check if updating existing container
        updating_existing_container = False
        for c in new_containerapp["properties"]["template"]["containers"]:
            if c["name"].lower() == container_name.lower():
                updating_existing_container = True

                if image is not None:
                    c["image"] = image

                if set_env_vars is not None:
                    if "env" not in c or not c["env"]:
                        c["env"] = []
                    # env vars
                    _add_or_update_env_vars(c["env"], parse_env_var_flags(set_env_vars))

                if replace_env_vars is not None:
                    # Remove other existing env_vars, then add them
                    c["env"] = []
                    _add_or_update_env_vars(c["env"], parse_env_var_flags(replace_env_vars))

                if remove_env_vars is not None:
                    if "env" not in c or not c["env"]:
                        c["env"] = []
                    # env vars
                    _remove_env_vars(c["env"], remove_env_vars)

                if remove_all_env_vars:
                    c["env"] = []

                if startup_command is not None:
                    if isinstance(startup_command, list) and not startup_command:
                        c["command"] = None
                    else:
                        c["command"] = startup_command
                if args is not None:
                    if isinstance(args, list) and not args:
                        c["args"] = None
                    else:
                        c["args"] = args
                if cpu is not None or memory is not None:
                    if "resources" in c and c["resources"]:
                        if cpu is not None:
                            c["resources"]["cpu"] = cpu
                        if memory is not None:
                            c["resources"]["memory"] = memory
                    else:
                        c["resources"] = {
                            "cpu": cpu,
                            "memory": memory
                        }
                if secret_volume_mount is not None:
                    new_containerapp["properties"]["template"]["volumes"] = containerapp_def["properties"]["template"]["volumes"]
                    if "volumeMounts" not in c or not c["volumeMounts"]:
                        # if no volume mount exists, create a new volume and then mount
                        volume_def = VolumeModel
                        volume_mount_def = VolumeMountModel
                        volume_def["name"] = _generate_secret_volume_name()
                        volume_def["storageType"] = "Secret"

                        volume_mount_def["volumeName"] = volume_def["name"]
                        volume_mount_def["mountPath"] = secret_volume_mount

                        if "volumes" not in new_containerapp["properties"]["template"] or new_containerapp["properties"]["template"]["volumes"] is None:
                            new_containerapp["properties"]["template"]["volumes"] = [volume_def]
                        else:
                            new_containerapp["properties"]["template"]["volumes"].append(volume_def)
                        c["volumeMounts"] = [volume_mount_def]
                    else:
                        if len(c["volumeMounts"]) > 1:
                            raise ValidationError("Usage error: --secret-volume-mount can only be used with a container that has a single volume mount, to define multiple volumes and mounts please use --yaml")
                        else:
                            # check that the only volume is of type secret
                            volume_name = c["volumeMounts"][0]["volumeName"]
                            for v in new_containerapp["properties"]["template"]["volumes"]:
                                if v["name"].lower() == volume_name.lower():
                                    if v["storageType"] != "Secret":
                                        raise ValidationError("Usage error: --secret-volume-mount can only be used to update volume mounts with volumes of type secret. To update other types of volumes please use --yaml")
                                    break
                            c["volumeMounts"][0]["mountPath"] = secret_volume_mount

        # If not updating existing container, add as new container
        if not updating_existing_container:
            if image is None:
                raise ValidationError("Usage error: --image is required when adding a new container")

            resources_def = None
            if cpu is not None or memory is not None:
                resources_def = ContainerResourcesModel
                resources_def["cpu"] = cpu
                resources_def["memory"] = memory

            container_def = ContainerModel
            container_def["name"] = container_name
            container_def["image"] = image
            container_def["env"] = []

            if set_env_vars is not None:
                # env vars
                _add_or_update_env_vars(container_def["env"], parse_env_var_flags(set_env_vars))

            if replace_env_vars is not None:
                # env vars
                _add_or_update_env_vars(container_def["env"], parse_env_var_flags(replace_env_vars))

            if remove_env_vars is not None:
                # env vars
                _remove_env_vars(container_def["env"], remove_env_vars)

            if remove_all_env_vars:
                container_def["env"] = []

            if startup_command is not None:
                if isinstance(startup_command, list) and not startup_command:
                    container_def["command"] = None
                else:
                    container_def["command"] = startup_command
            if args is not None:
                if isinstance(args, list) and not args:
                    container_def["args"] = None
                else:
                    container_def["args"] = args
            if resources_def is not None:
                container_def["resources"] = resources_def
            if secret_volume_mount is not None:
                new_containerapp["properties"]["template"]["volumes"] = containerapp_def["properties"]["template"]["volumes"]
                # generate a new volume name
                volume_def = VolumeModel
                volume_mount_def = VolumeMountModel
                volume_def["name"] = _generate_secret_volume_name()
                volume_def["storageType"] = "Secret"

                # mount the volume to the container
                volume_mount_def["volumeName"] = volume_def["name"]
                volume_mount_def["mountPath"] = secret_volume_mount
                container_def["volumeMounts"] = [volume_mount_def]
                if "volumes" not in new_containerapp["properties"]["template"]:
                    new_containerapp["properties"]["template"]["volumes"] = [volume_def]
                else:
                    new_containerapp["properties"]["template"]["volumes"].append(volume_def)

            new_containerapp["properties"]["template"]["containers"].append(container_def)
    # Scale
    if update_map["scale"]:
        new_containerapp["properties"]["template"] = {} if "template" not in new_containerapp["properties"] else new_containerapp["properties"]["template"]
        if "scale" not in new_containerapp["properties"]["template"]:
            new_containerapp["properties"]["template"]["scale"] = {}
        if min_replicas is not None:
            new_containerapp["properties"]["template"]["scale"]["minReplicas"] = min_replicas
        if max_replicas is not None:
            new_containerapp["properties"]["template"]["scale"]["maxReplicas"] = max_replicas

    scale_def = None
    if min_replicas is not None or max_replicas is not None:
        scale_def = ScaleModel
        scale_def["minReplicas"] = min_replicas
        scale_def["maxReplicas"] = max_replicas
    # so we don't overwrite rules
    if safe_get(new_containerapp, "properties", "template", "scale", "rules"):
        new_containerapp["properties"]["template"]["scale"].pop("rules")
    if scale_rule_name:
        if not scale_rule_type:
            scale_rule_type = "http"
        scale_rule_type = scale_rule_type.lower()
        scale_rule_def = ScaleRuleModel
        curr_metadata = {}
        if scale_rule_http_concurrency:
            if scale_rule_type == 'http':
                curr_metadata["concurrentRequests"] = str(scale_rule_http_concurrency)
            elif scale_rule_type == 'tcp':
                curr_metadata["concurrentConnections"] = str(scale_rule_http_concurrency)
        metadata_def = parse_metadata_flags(scale_rule_metadata, curr_metadata)
        auth_def = parse_auth_flags(scale_rule_auth)
        if scale_rule_type == "http":
            scale_rule_def["name"] = scale_rule_name
            scale_rule_def["custom"] = None
            scale_rule_def["tcp"] = None
            scale_rule_def["http"] = {}
            scale_rule_def["http"]["metadata"] = metadata_def
            scale_rule_def["http"]["auth"] = auth_def
        elif scale_rule_type == "tcp":
            scale_rule_def["name"] = scale_rule_name
            scale_rule_def["custom"] = None
            scale_rule_def["http"] = None
            scale_rule_def["tcp"] = {}
            scale_rule_def["tcp"]["metadata"] = metadata_def
            scale_rule_def["tcp"]["auth"] = auth_def
        else:
            scale_rule_def["name"] = scale_rule_name
            scale_rule_def["http"] = None
            scale_rule_def["tcp"] = None
            scale_rule_def["custom"] = {}
            scale_rule_def["custom"]["type"] = scale_rule_type
            scale_rule_def["custom"]["metadata"] = metadata_def
            scale_rule_def["custom"]["auth"] = auth_def
        if not scale_def:
            scale_def = ScaleModel
        scale_def["rules"] = [scale_rule_def]
        new_containerapp["properties"]["template"]["scale"]["rules"] = scale_def["rules"]
    # Ingress
    if update_map["ingress"]:
        new_containerapp["properties"]["configuration"] = {} if "configuration" not in new_containerapp["properties"] else new_containerapp["properties"]["configuration"]
        if target_port is not None or ingress is not None:
            new_containerapp["properties"]["configuration"]["ingress"] = {}
            if ingress:
                new_containerapp["properties"]["configuration"]["ingress"]["external"] = ingress.lower() == "external"
            if target_port:
                new_containerapp["properties"]["configuration"]["ingress"]["targetPort"] = target_port

    # Registry
    if update_map["registry"]:
        new_containerapp["properties"]["configuration"] = {} if "configuration" not in new_containerapp["properties"] else new_containerapp["properties"]["configuration"]
        if "registries" in containerapp_def["properties"]["configuration"]:
            new_containerapp["properties"]["configuration"]["registries"] = containerapp_def["properties"]["configuration"]["registries"]
        if "registries" not in containerapp_def["properties"]["configuration"] or containerapp_def["properties"]["configuration"]["registries"] is None:
            new_containerapp["properties"]["configuration"]["registries"] = []

        registries_def = new_containerapp["properties"]["configuration"]["registries"]

        _get_existing_secrets(cmd, resource_group_name, name, containerapp_def)
        if "secrets" in containerapp_def["properties"]["configuration"] and containerapp_def["properties"]["configuration"]["secrets"]:
            new_containerapp["properties"]["configuration"]["secrets"] = containerapp_def["properties"]["configuration"]["secrets"]
        else:
            new_containerapp["properties"]["configuration"]["secrets"] = []

        if registry_server:
            if not registry_pass or not registry_user:
                if ACR_IMAGE_SUFFIX not in registry_server:
                    raise RequiredArgumentMissingError('Registry url is required if using Azure Container Registry, otherwise Registry username and password are required if using Dockerhub')
                logger.warning('No credential was provided to access Azure Container Registry. Trying to look up...')
                parsed = urlparse(registry_server)
                registry_name = (parsed.netloc if parsed.scheme else parsed.path).split('.')[0]
                registry_user, registry_pass, _ = _get_acr_cred(cmd.cli_ctx, registry_name)
            # Check if updating existing registry
            updating_existing_registry = False
            for r in registries_def:
                if r['server'].lower() == registry_server.lower():
                    updating_existing_registry = True
                    if registry_user:
                        r["username"] = registry_user
                    if registry_pass:
                        r["passwordSecretRef"] = store_as_secret_and_return_secret_ref(
                            new_containerapp["properties"]["configuration"]["secrets"],
                            r["username"],
                            r["server"],
                            registry_pass,
                            update_existing_secret=True,
                            disable_warnings=True)

            # If not updating existing registry, add as new registry
            if not updating_existing_registry:
                registry = RegistryCredentialsModel
                registry["server"] = registry_server
                registry["username"] = registry_user
                registry["passwordSecretRef"] = store_as_secret_and_return_secret_ref(
                    new_containerapp["properties"]["configuration"]["secrets"],
                    registry_user,
                    registry_server,
                    registry_pass,
                    update_existing_secret=True,
                    disable_warnings=True)

                registries_def.append(registry)

    if not revision_suffix:
        new_containerapp["properties"]["template"] = {} if "template" not in new_containerapp["properties"] else new_containerapp["properties"]["template"]
        new_containerapp["properties"]["template"]["revisionSuffix"] = None

    try:
        r = ContainerAppClient.update(
            cmd=cmd, resource_group_name=resource_group_name, name=name, container_app_envelope=new_containerapp, no_wait=no_wait)

        if not no_wait and "properties" in r and "provisioningState" in r["properties"] and r["properties"]["provisioningState"].lower() == "waiting":
            logger.warning('Containerapp update in progress. Please monitor the update using `az containerapp show -n {} -g {}`'.format(name, resource_group_name))

        return r
    except Exception as e:
        handle_raw_exception(e)


def update_containerapp(cmd,
                        name,
                        resource_group_name,
                        yaml=None,
                        image=None,
                        container_name=None,
                        min_replicas=None,
                        max_replicas=None,
                        scale_rule_name=None,
                        scale_rule_type=None,
                        scale_rule_http_concurrency=None,
                        scale_rule_metadata=None,
                        scale_rule_auth=None,
                        set_env_vars=None,
                        remove_env_vars=None,
                        replace_env_vars=None,
                        remove_all_env_vars=False,
                        cpu=None,
                        memory=None,
                        revision_suffix=None,
                        startup_command=None,
                        args=None,
                        tags=None,
                        workload_profile_name=None,
                        termination_grace_period=None,
                        no_wait=False,
                        secret_volume_mount=None):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)

    return update_containerapp_logic(cmd=cmd,
                                     name=name,
                                     resource_group_name=resource_group_name,
                                     yaml=yaml,
                                     image=image,
                                     container_name=container_name,
                                     min_replicas=min_replicas,
                                     max_replicas=max_replicas,
                                     scale_rule_name=scale_rule_name,
                                     scale_rule_type=scale_rule_type,
                                     scale_rule_http_concurrency=scale_rule_http_concurrency,
                                     scale_rule_metadata=scale_rule_metadata,
                                     scale_rule_auth=scale_rule_auth,
                                     set_env_vars=set_env_vars,
                                     remove_env_vars=remove_env_vars,
                                     replace_env_vars=replace_env_vars,
                                     remove_all_env_vars=remove_all_env_vars,
                                     cpu=cpu,
                                     memory=memory,
                                     revision_suffix=revision_suffix,
                                     startup_command=startup_command,
                                     args=args,
                                     tags=tags,
                                     workload_profile_name=workload_profile_name,
                                     termination_grace_period=termination_grace_period,
                                     no_wait=no_wait,
                                     secret_volume_mount=secret_volume_mount)


def show_containerapp(cmd, name, resource_group_name, show_secrets=False):
    raw_parameters = locals()
    containerapp_base_decorator = BaseContainerAppDecorator(
        cmd=cmd,
        client=ContainerAppClient,
        raw_parameters=raw_parameters,
        models=CONTAINER_APPS_SDK_MODELS
    )
    containerapp_base_decorator.validate_subscription_registered(CONTAINER_APPS_RP)

    return containerapp_base_decorator.show()


def list_containerapp(cmd, resource_group_name=None, managed_env=None):
    raw_parameters = locals()
    containerapp_list_decorator = BaseContainerAppDecorator(
        cmd=cmd,
        client=ContainerAppClient,
        raw_parameters=raw_parameters,
        models=CONTAINER_APPS_SDK_MODELS
    )
    containerapp_list_decorator.validate_subscription_registered(CONTAINER_APPS_RP)

    return containerapp_list_decorator.list()


def show_custom_domain_verification_id(cmd):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)
    try:
        r = SubscriptionClient.show_custom_domain_verification_id(cmd)
        return r
    except CLIError as e:
        handle_raw_exception(e)


def list_usages(cmd, location):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)
    try:
        r = SubscriptionClient.list_usages(cmd, location)
        return r
    except CLIError as e:
        handle_raw_exception(e)


def list_environment_usages(cmd, resource_group_name, name):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)
    try:
        r = ManagedEnvironmentClient.list_usages(cmd, resource_group_name, name)
        return r
    except CLIError as e:
        handle_raw_exception(e)


def delete_containerapp(cmd, name, resource_group_name, no_wait=False):
    raw_parameters = locals()
    containerapp_base_decorator = BaseContainerAppDecorator(
        cmd=cmd,
        client=ContainerAppClient,
        raw_parameters=raw_parameters,
        models=CONTAINER_APPS_SDK_MODELS
    )
    containerapp_base_decorator.validate_subscription_registered(CONTAINER_APPS_RP)

    return containerapp_base_decorator.delete()


def create_managed_environment(cmd,
                               name,
                               resource_group_name,
                               logs_destination="log-analytics",
                               storage_account=None,
                               logs_customer_id=None,
                               logs_key=None,
                               location=None,
                               instrumentation_key=None,
                               dapr_connection_string=None,
                               infrastructure_subnet_resource_id=None,
                               infrastructure_resource_group=None,
                               docker_bridge_cidr=None,
                               platform_reserved_cidr=None,
                               platform_reserved_dns_ip=None,
                               internal_only=False,
                               tags=None,
                               disable_warnings=False,
                               zone_redundant=False,
                               hostname=None,
                               certificate_file=None,
                               certificate_password=None,
                               enable_workload_profiles=True,
                               mtls_enabled=None,
                               p2p_encryption_enabled=None,
                               no_wait=False):
    raw_parameters = locals()
    containerapp_env_create_decorator = ContainerAppEnvCreateDecorator(
        cmd=cmd,
        client=ManagedEnvironmentClient,
        raw_parameters=raw_parameters,
        models=CONTAINER_APPS_SDK_MODELS
    )
    containerapp_env_create_decorator.validate_arguments()
    containerapp_env_create_decorator.register_provider(CONTAINER_APPS_RP)

    containerapp_env_create_decorator.construct_payload()
    r = containerapp_env_create_decorator.create()
    r = containerapp_env_create_decorator.post_process(r)

    return r


def update_managed_environment(cmd,
                               name,
                               resource_group_name,
                               logs_destination=None,
                               storage_account=None,
                               logs_customer_id=None,
                               logs_key=None,
                               hostname=None,
                               certificate_file=None,
                               certificate_password=None,
                               tags=None,
                               workload_profile_type=None,
                               workload_profile_name=None,
                               min_nodes=None,
                               max_nodes=None,
                               mtls_enabled=None,
                               p2p_encryption_enabled=None,
                               dapr_connection_string=None,
                               no_wait=False):
    raw_parameters = locals()
    containerapp_env_update_decorator = ContainerAppEnvUpdateDecorator(
        cmd=cmd,
        client=ManagedEnvironmentClient,
        raw_parameters=raw_parameters,
        models=CONTAINER_APPS_SDK_MODELS
    )
    containerapp_env_update_decorator.validate_arguments()
    containerapp_env_update_decorator.construct_payload()
    r = containerapp_env_update_decorator.update()
    r = containerapp_env_update_decorator.post_process(r)

    return r


def show_managed_environment(cmd, name, resource_group_name):
    raw_parameters = locals()
    containerapp_env_decorator = ContainerAppEnvDecorator(
        cmd=cmd,
        client=ManagedEnvironmentClient,
        raw_parameters=raw_parameters,
        models=CONTAINER_APPS_SDK_MODELS
    )
    containerapp_env_decorator.validate_subscription_registered(CONTAINER_APPS_RP)

    return containerapp_env_decorator.show()


def list_managed_environments(cmd, resource_group_name=None):
    raw_parameters = locals()
    containerapp_env_decorator = ContainerAppEnvDecorator(
        cmd=cmd,
        client=ManagedEnvironmentClient,
        raw_parameters=raw_parameters,
        models=CONTAINER_APPS_SDK_MODELS
    )
    containerapp_env_decorator.validate_subscription_registered(CONTAINER_APPS_RP)

    return containerapp_env_decorator.list()


def delete_managed_environment(cmd, name, resource_group_name, no_wait=False):
    raw_parameters = locals()
    containerapp_env_decorator = ContainerAppEnvDecorator(
        cmd=cmd,
        client=ManagedEnvironmentClient,
        raw_parameters=raw_parameters,
        models=CONTAINER_APPS_SDK_MODELS
    )
    containerapp_env_decorator.validate_subscription_registered(CONTAINER_APPS_RP)

    return containerapp_env_decorator.delete()


def create_containerappsjob(cmd,
                            name,
                            resource_group_name,
                            yaml=None,
                            image=None,
                            container_name=None,
                            managed_env=None,
                            trigger_type=None,
                            replica_timeout=None,
                            replica_retry_limit=None,
                            replica_completion_count=None,
                            parallelism=None,
                            cron_expression=None,
                            secrets=None,
                            env_vars=None,
                            cpu=None,
                            memory=None,
                            registry_server=None,
                            registry_user=None,
                            registry_pass=None,
                            startup_command=None,
                            args=None,
                            scale_rule_metadata=None,
                            scale_rule_name=None,
                            scale_rule_type=None,
                            scale_rule_auth=None,
                            polling_interval=None,
                            min_executions=None,
                            max_executions=None,
                            tags=None,
                            no_wait=False,
                            system_assigned=False,
                            disable_warnings=False,
                            user_assigned=None,
                            registry_identity=None,
                            workload_profile_name=None):
    raw_parameters = locals()
    containerapp_job_create_decorator = ContainerAppJobCreateDecorator(
        cmd=cmd,
        client=ContainerAppsJobClient,
        raw_parameters=raw_parameters,
        models=CONTAINER_APPS_SDK_MODELS
    )
    containerapp_job_create_decorator.register_provider(CONTAINER_APPS_RP)
    containerapp_job_create_decorator.validate_arguments()

    containerapp_job_create_decorator.construct_payload()
    r = containerapp_job_create_decorator.create()
    containerapp_job_create_decorator.construct_for_post_process(r)
    r = containerapp_job_create_decorator.post_process(r)

    return r


def show_containerappsjob(cmd, name, resource_group_name):
    raw_parameters = locals()
    containerapp_job_decorator = ContainerAppJobDecorator(
        cmd=cmd,
        client=ContainerAppsJobClient,
        raw_parameters=raw_parameters,
        models=CONTAINER_APPS_SDK_MODELS
    )
    containerapp_job_decorator.validate_subscription_registered(CONTAINER_APPS_RP)

    return containerapp_job_decorator.show()


def list_containerappsjob(cmd, resource_group_name=None):
    raw_parameters = locals()
    containerapp_job_decorator = ContainerAppJobDecorator(
        cmd=cmd,
        client=ContainerAppsJobClient,
        raw_parameters=raw_parameters,
        models=CONTAINER_APPS_SDK_MODELS
    )
    containerapp_job_decorator.validate_subscription_registered(CONTAINER_APPS_RP)

    return containerapp_job_decorator.list()


def delete_containerappsjob(cmd, name, resource_group_name, no_wait=False):
    raw_parameters = locals()
    containerapp_job_decorator = ContainerAppJobDecorator(
        cmd=cmd,
        client=ContainerAppsJobClient,
        raw_parameters=raw_parameters,
        models=CONTAINER_APPS_SDK_MODELS
    )
    containerapp_job_decorator.validate_subscription_registered(CONTAINER_APPS_RP)

    return containerapp_job_decorator.delete()


def update_containerappsjob(cmd,
                            name,
                            resource_group_name,
                            yaml=None,
                            image=None,
                            container_name=None,
                            replica_timeout=None,
                            replica_retry_limit=None,
                            replica_completion_count=None,
                            parallelism=None,
                            cron_expression=None,
                            set_env_vars=None,
                            remove_env_vars=None,
                            replace_env_vars=None,
                            remove_all_env_vars=False,
                            cpu=None,
                            memory=None,
                            startup_command=None,
                            args=None,
                            scale_rule_metadata=None,
                            scale_rule_name=None,
                            scale_rule_type=None,
                            scale_rule_auth=None,
                            polling_interval=None,
                            min_executions=None,
                            max_executions=None,
                            tags=None,
                            workload_profile_name=None,
                            no_wait=False):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)

    return update_containerappsjob_logic(cmd=cmd,
                                         name=name,
                                         resource_group_name=resource_group_name,
                                         yaml=yaml,
                                         image=image,
                                         container_name=container_name,
                                         replica_timeout=replica_timeout,
                                         replica_retry_limit=replica_retry_limit,
                                         replica_completion_count=replica_completion_count,
                                         parallelism=parallelism,
                                         cron_expression=cron_expression,
                                         set_env_vars=set_env_vars,
                                         remove_env_vars=remove_env_vars,
                                         replace_env_vars=replace_env_vars,
                                         remove_all_env_vars=remove_all_env_vars,
                                         cpu=cpu,
                                         memory=memory,
                                         startup_command=startup_command,
                                         args=args,
                                         tags=tags,
                                         workload_profile_name=workload_profile_name,
                                         scale_rule_metadata=scale_rule_metadata,
                                         scale_rule_name=scale_rule_name,
                                         scale_rule_type=scale_rule_type,
                                         scale_rule_auth=scale_rule_auth,
                                         polling_interval=polling_interval,
                                         min_executions=min_executions,
                                         max_executions=max_executions,
                                         no_wait=no_wait)


def update_containerappsjob_logic(cmd,
                                  name,
                                  resource_group_name,
                                  yaml=None,
                                  image=None,
                                  container_name=None,
                                  replica_timeout=None,
                                  replica_retry_limit=None,
                                  replica_completion_count=None,
                                  parallelism=None,
                                  cron_expression=None,
                                  set_env_vars=None,
                                  remove_env_vars=None,
                                  replace_env_vars=None,
                                  remove_all_env_vars=False,
                                  cpu=None,
                                  memory=None,
                                  startup_command=None,
                                  args=None,
                                  tags=None,
                                  workload_profile_name=None,
                                  scale_rule_metadata=None,
                                  scale_rule_name=None,
                                  scale_rule_type=None,
                                  scale_rule_auth=None,
                                  polling_interval=None,
                                  min_executions=None,
                                  max_executions=None,
                                  no_wait=False,
                                  registry_server=None,
                                  registry_user=None,
                                  registry_pass=None):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)

    if yaml:
        if image or replica_timeout or replica_retry_limit or\
           set_env_vars or remove_env_vars or replace_env_vars or remove_all_env_vars or cpu or memory or\
           startup_command or args or tags:
            logger.warning('Additional flags were passed along with --yaml. These flags will be ignored, and the configuration defined in the yaml will be used instead')
        return update_containerappjob_yaml(cmd=cmd, name=name, resource_group_name=resource_group_name, file_name=yaml, no_wait=no_wait)

    containerappsjob_def = None
    try:
        containerappsjob_def = ContainerAppsJobClient.show(cmd=cmd, resource_group_name=resource_group_name, name=name)
    except:
        pass

    if not containerappsjob_def:
        raise ResourceNotFoundError("The containerapps job '{}' does not exist".format(name))

    new_containerappsjob = {}
    new_containerappsjob["properties"] = {}

    # Doing this while API has bug. If env var is an empty string, API doesn't return "value" even though the "value" should be an empty string
    if "properties" in containerappsjob_def and "template" in containerappsjob_def["properties"] and "containers" in containerappsjob_def["properties"]["template"]:
        for container in containerappsjob_def["properties"]["template"]["containers"]:
            if "env" in container:
                for e in container["env"]:
                    if "value" not in e:
                        e["value"] = ""

    update_map = {}
    update_map['replicaConfigurations'] = replica_timeout or replica_retry_limit
    update_map['triggerConfigurations'] = replica_completion_count or parallelism or cron_expression or scale_rule_name or scale_rule_type or scale_rule_auth or polling_interval or min_executions is not None or max_executions is not None
    update_map['container'] = image or container_name or set_env_vars is not None or remove_env_vars is not None or replace_env_vars is not None or remove_all_env_vars or cpu or memory or startup_command is not None or args is not None
    update_map['registry'] = registry_server or registry_user or registry_pass

    if tags:
        _add_or_update_tags(new_containerappsjob, tags)

    if workload_profile_name:
        new_containerappsjob["properties"]["workloadProfileName"] = workload_profile_name

        parsed_managed_env = parse_resource_id(containerappsjob_def["properties"]["environmentId"])
        managed_env_name = parsed_managed_env['name']
        managed_env_rg = parsed_managed_env['resource_group']
        managed_env_info = None
        try:
            managed_env_info = ManagedEnvironmentClient.show(cmd=cmd, resource_group_name=managed_env_rg, name=managed_env_name)
        except:
            pass

        if not managed_env_info:
            raise ValidationError("Error parsing the managed environment '{}' from the specified containerappjob".format(managed_env_name))

        ensure_workload_profile_supported(cmd, managed_env_name, managed_env_rg, workload_profile_name, managed_env_info)

    # replicaConfiguration
    if update_map["replicaConfigurations"]:
        new_containerappsjob["properties"]["configuration"] = {} if "configuration" not in new_containerappsjob["properties"] else new_containerappsjob["properties"]["configuration"]
        if replica_timeout is not None or replica_retry_limit is not None:
            if replica_timeout:
                new_containerappsjob["properties"]["configuration"]["replicaTimeout"] = replica_timeout
            if replica_retry_limit:
                new_containerappsjob["properties"]["configuration"]["replicaRetryLimit"] = replica_retry_limit

    # triggerConfiguration
    if update_map["triggerConfigurations"]:
        new_containerappsjob["properties"]["configuration"] = {} if "configuration" not in new_containerappsjob["properties"] else new_containerappsjob["properties"]["configuration"]
        if containerappsjob_def["properties"]["configuration"]["triggerType"] == "Manual":
            manualTriggerConfig_def = None
            manualTriggerConfig_def = containerappsjob_def["properties"]["configuration"]["manualTriggerConfig"]
            if replica_completion_count is not None or parallelism is not None:
                if replica_completion_count:
                    manualTriggerConfig_def["replicaCompletionCount"] = replica_completion_count
                if parallelism:
                    manualTriggerConfig_def["parallelism"] = parallelism
            new_containerappsjob["properties"]["configuration"]["manualTriggerConfig"] = manualTriggerConfig_def
        if containerappsjob_def["properties"]["configuration"]["triggerType"] == "Schedule":
            scheduleTriggerConfig_def = None
            scheduleTriggerConfig_def = containerappsjob_def["properties"]["configuration"]["scheduleTriggerConfig"]
            if replica_completion_count is not None or parallelism is not None or cron_expression is not None:
                if replica_completion_count:
                    scheduleTriggerConfig_def["replicaCompletionCount"] = replica_completion_count
                if parallelism:
                    scheduleTriggerConfig_def["parallelism"] = parallelism
                if cron_expression:
                    scheduleTriggerConfig_def["cronExpression"] = cron_expression
            new_containerappsjob["properties"]["configuration"]["scheduleTriggerConfig"] = scheduleTriggerConfig_def
        if containerappsjob_def["properties"]["configuration"]["triggerType"] == "Event":
            eventTriggerConfig_def = None
            eventTriggerConfig_def = containerappsjob_def["properties"]["configuration"]["eventTriggerConfig"]
            if replica_completion_count is not None or parallelism is not None or min_executions is not None or max_executions is not None or polling_interval is not None or scale_rule_name is not None:
                if replica_completion_count:
                    eventTriggerConfig_def["replicaCompletionCount"] = replica_completion_count
                if parallelism:
                    eventTriggerConfig_def["parallelism"] = parallelism
                # Scale
                if "scale" in eventTriggerConfig_def["scale"]:
                    eventTriggerConfig_def["scale"] = {}
                if min_executions is not None:
                    eventTriggerConfig_def["scale"]["minExecutions"] = min_executions
                if max_executions is not None:
                    eventTriggerConfig_def["scale"]["maxExecutions"] = max_executions
                if polling_interval is not None:
                    eventTriggerConfig_def["scale"]["pollingInterval"] = polling_interval
                # ScaleRule
                if scale_rule_name:
                    scale_rule_type = scale_rule_type.lower()
                    scale_rule_def = ScaleRuleModel
                    curr_metadata = {}
                    metadata_def = parse_metadata_flags(scale_rule_metadata, curr_metadata)
                    auth_def = parse_auth_flags(scale_rule_auth)
                    scale_rule_def["name"] = scale_rule_name
                    scale_rule_def["type"] = scale_rule_type
                    scale_rule_def["metadata"] = metadata_def
                    scale_rule_def["auth"] = auth_def
                    if safe_get(eventTriggerConfig_def, "scale", "rules") is None:
                        eventTriggerConfig_def["scale"]["rules"] = []
                    existing_rules = eventTriggerConfig_def["scale"]["rules"]
                    updated_rule = False
                    for rule in existing_rules:
                        if rule["name"] == scale_rule_name:
                            rule.update(scale_rule_def)
                            updated_rule = True
                            break
                    if not updated_rule:
                        existing_rules.append(scale_rule_def)

            new_containerappsjob["properties"]["configuration"]["eventTriggerConfig"] = eventTriggerConfig_def

    # Containers
    if update_map["container"]:
        new_containerappsjob["properties"]["template"] = {} if "template" not in new_containerappsjob["properties"] else new_containerappsjob["properties"]["template"]
        new_containerappsjob["properties"]["template"]["containers"] = containerappsjob_def["properties"]["template"]["containers"]
        if not container_name:
            if len(new_containerappsjob["properties"]["template"]["containers"]) == 1:
                container_name = new_containerappsjob["properties"]["template"]["containers"][0]["name"]
            else:
                raise ValidationError("Usage error: --container-name is required when adding or updating a container")

        # Check if updating existing container
        updating_existing_container = False
        for c in new_containerappsjob["properties"]["template"]["containers"]:
            if c["name"].lower() == container_name.lower():
                updating_existing_container = True

                if image is not None:
                    c["image"] = image

                if set_env_vars is not None:
                    if "env" not in c or not c["env"]:
                        c["env"] = []
                    # env vars
                    _add_or_update_env_vars(c["env"], parse_env_var_flags(set_env_vars))

                if replace_env_vars is not None:
                    # Remove other existing env_vars, then add them
                    c["env"] = []
                    _add_or_update_env_vars(c["env"], parse_env_var_flags(replace_env_vars))

                if remove_env_vars is not None:
                    if "env" not in c or not c["env"]:
                        c["env"] = []
                    # env vars
                    _remove_env_vars(c["env"], remove_env_vars)

                if remove_all_env_vars:
                    c["env"] = []

                if startup_command is not None:
                    if isinstance(startup_command, list) and not startup_command:
                        c["command"] = None
                    else:
                        c["command"] = startup_command
                if args is not None:
                    if isinstance(args, list) and not args:
                        c["args"] = None
                    else:
                        c["args"] = args
                if cpu is not None or memory is not None:
                    if "resources" in c and c["resources"]:
                        if cpu is not None:
                            c["resources"]["cpu"] = cpu
                        if memory is not None:
                            c["resources"]["memory"] = memory
                    else:
                        c["resources"] = {
                            "cpu": cpu,
                            "memory": memory
                        }

        # If not updating existing container, add as new container
        if not updating_existing_container:
            if image is None:
                raise ValidationError("Usage error: --image is required when adding a new container")

            resources_def = None
            if cpu is not None or memory is not None:
                resources_def = ContainerResourcesModel
                resources_def["cpu"] = cpu
                resources_def["memory"] = memory

            container_def = ContainerModel
            container_def["name"] = container_name
            container_def["image"] = image
            container_def["env"] = []

            if set_env_vars is not None:
                # env vars
                _add_or_update_env_vars(container_def["env"], parse_env_var_flags(set_env_vars))

            if replace_env_vars is not None:
                # env vars
                _add_or_update_env_vars(container_def["env"], parse_env_var_flags(replace_env_vars))

            if remove_env_vars is not None:
                # env vars
                _remove_env_vars(container_def["env"], remove_env_vars)

            if remove_all_env_vars:
                container_def["env"] = []

            if startup_command is not None:
                if isinstance(startup_command, list) and not startup_command:
                    container_def["command"] = None
                else:
                    container_def["command"] = startup_command
            if args is not None:
                if isinstance(args, list) and not args:
                    container_def["args"] = None
                else:
                    container_def["args"] = args
            if resources_def is not None:
                container_def["resources"] = resources_def

            new_containerappsjob["properties"]["template"]["containers"].append(container_def)

        new_containerappsjob["properties"]["configuration"] = {} if "configuration" not in new_containerappsjob["properties"] else new_containerappsjob["properties"]["configuration"]

    # Registry
    if update_map["registry"]:
        new_containerappsjob["properties"]["configuration"] = {} if "configuration" not in new_containerappsjob["properties"] else new_containerappsjob["properties"]["configuration"]
        if "registries" in containerappsjob_def["properties"]["configuration"]:
            new_containerappsjob["properties"]["configuration"]["registries"] = containerappsjob_def["properties"]["configuration"]["registries"]
        if "registries" not in containerappsjob_def["properties"]["configuration"] or containerappsjob_def["properties"]["configuration"]["registries"] is None:
            new_containerappsjob["properties"]["configuration"]["registries"] = []

        registries_def = new_containerappsjob["properties"]["configuration"]["registries"]

        _get_existing_secrets(cmd, resource_group_name, name, containerappsjob_def, AppType.ContainerAppJob)
        if "secrets" in containerappsjob_def["properties"]["configuration"] and containerappsjob_def["properties"]["configuration"]["secrets"]:
            new_containerappsjob["properties"]["configuration"]["secrets"] = containerappsjob_def["properties"]["configuration"]["secrets"]
        else:
            new_containerappsjob["properties"]["configuration"]["secrets"] = []

        if registry_server:
            if not registry_pass or not registry_user:
                if ACR_IMAGE_SUFFIX not in registry_server:
                    raise RequiredArgumentMissingError('Registry url is required if using Azure Container Registry, otherwise Registry username and password are required if using Dockerhub')
                logger.warning('No credential was provided to access Azure Container Registry. Trying to look up...')
                parsed = urlparse(registry_server)
                registry_name = (parsed.netloc if parsed.scheme else parsed.path).split('.')[0]
                registry_user, registry_pass, _ = _get_acr_cred(cmd.cli_ctx, registry_name)
            # Check if updating existing registry
            updating_existing_registry = False
            for r in registries_def:
                if r['server'].lower() == registry_server.lower():
                    updating_existing_registry = True
                    if registry_user:
                        r["username"] = registry_user
                    if registry_pass:
                        r["passwordSecretRef"] = store_as_secret_and_return_secret_ref(
                            new_containerappsjob["properties"]["configuration"]["secrets"],
                            r["username"],
                            r["server"],
                            registry_pass,
                            update_existing_secret=True,
                            disable_warnings=True)

            # If not updating existing registry, add as new registry
            if not updating_existing_registry:
                registry = RegistryCredentialsModel
                registry["server"] = registry_server
                registry["username"] = registry_user
                registry["passwordSecretRef"] = store_as_secret_and_return_secret_ref(
                    new_containerappsjob["properties"]["configuration"]["secrets"],
                    registry_user,
                    registry_server,
                    registry_pass,
                    update_existing_secret=True,
                    disable_warnings=True)

                registries_def.append(registry)

    try:
        r = ContainerAppsJobClient.update(
            cmd=cmd, resource_group_name=resource_group_name, name=name, containerapp_job_envelope=new_containerappsjob, no_wait=no_wait)

        if "properties" in r and "provisioningState" in r["properties"] and r["properties"]["provisioningState"].lower() == "waiting" and not no_wait:
            logger.warning('Containerapps job update in progress. Please monitor the update using `az containerapp job show -n {} -g {}`'.format(name, resource_group_name))

        return r
    except Exception as e:
        handle_raw_exception(e)


def update_containerappjob_yaml(cmd, name, resource_group_name, file_name, from_revision=None, no_wait=False):
    yaml_containerappsjob = process_loaded_yaml(load_yaml_file(file_name))
    # check if the type is dict
    if not isinstance(yaml_containerappsjob, dict):
        raise ValidationError('Invalid YAML provided. Please see https://aka.ms/azure-container-apps-job-yaml for a valid YAML spec.')

    if not yaml_containerappsjob.get('name'):
        yaml_containerappsjob['name'] = name
    elif yaml_containerappsjob.get('name').lower() != name.lower():
        logger.warning('The job name provided in the --yaml file "{}" does not match the one provided in the --name flag "{}". The one provided in the --yaml file will be used.'.format(yaml_containerappsjob.get('name'), name))
    name = yaml_containerappsjob.get('name')

    if not yaml_containerappsjob.get('type'):
        yaml_containerappsjob['type'] = 'Microsoft.App/jobs'
    elif yaml_containerappsjob.get('type').lower() != "microsoft.app/jobs":
        raise ValidationError('Container App Job type must be \"Microsoft.App/jobs\"')

    containerappsjob_def = None

    # Check if containerapp job exists
    try:
        containerappsjob_def = ContainerAppsJobClient.show(cmd=cmd, resource_group_name=resource_group_name, name=name)
    except Exception:
        pass

    if not containerappsjob_def:
        raise ResourceNotFoundError("The containerapp job '{}' does not exist".format(name))
    existed_environment_id = containerappsjob_def['properties']['environmentId']
    containerappsjob_def = None

    # Deserialize the yaml into a ContainerApp job object. Need this since we're not using SDK
    try:
        deserializer = create_deserializer()
        containerappsjob_def = deserializer('ContainerAppsJob', yaml_containerappsjob)
    except DeserializationError as ex:
        raise ValidationError('Invalid YAML provided. Please see https://aka.ms/azure-container-apps-job-yaml for a valid YAML spec.') from ex

    # Remove tags before converting from snake case to camel case, then re-add tags. We don't want to change the case of the tags. Need this since we're not using SDK
    tags = None
    if yaml_containerappsjob.get('tags'):
        tags = yaml_containerappsjob.get('tags')
        del yaml_containerappsjob['tags']

    containerappsjob_def = _convert_object_from_snake_to_camel_case(_object_to_dict(containerappsjob_def))
    containerappsjob_def['tags'] = tags

    # After deserializing, some properties may need to be moved under the "properties" attribute. Need this since we're not using SDK
    containerappsjob_def = process_loaded_yaml(containerappsjob_def)

    # Remove "additionalProperties" and read-only attributes that are introduced in the deserialization. Need this since we're not using SDK
    _remove_additional_attributes(containerappsjob_def)
    _remove_readonly_attributes(containerappsjob_def)

    secret_values = list_secrets_job(cmd=cmd, name=name, resource_group_name=resource_group_name, show_values=True)
    _populate_secret_values(containerappsjob_def, secret_values)

    # Clean null values since this is an update
    containerappsjob_def = clean_null_values(containerappsjob_def)

    # If job to be updated is of triggerType 'event' then update scale
    if safe_get(containerappsjob_def, "properties", "configuration", "triggerType") and containerappsjob_def["properties"]["configuration"]["triggerType"].lower() == "event":
        if safe_get(yaml_containerappsjob, "properties", "configuration", "eventTriggerConfig", "scale"):
            print("scale is present")
            containerappsjob_def["properties"]["configuration"]["eventTriggerConfig"]["scale"] = yaml_containerappsjob["properties"]["configuration"]["eventTriggerConfig"]["scale"]

    # Remove the environmentId in the PATCH payload if it has not been changed
    if safe_get(containerappsjob_def, "properties", "environmentId") and safe_get(containerappsjob_def, "properties", "environmentId").lower() == existed_environment_id.lower():
        del containerappsjob_def["properties"]['environmentId']

    try:
        r = ContainerAppsJobClient.update(
            cmd=cmd, resource_group_name=resource_group_name, name=name, containerapp_job_envelope=containerappsjob_def, no_wait=no_wait)

        if not no_wait and "properties" in r and "provisioningState" in r["properties"] and r["properties"]["provisioningState"].lower() == "waiting":
            logger.warning('Containerapp job creation in progress. Please monitor the creation using `az containerapp job show -n {} -g {}`'.format(
                name, resource_group_name
            ))

        return r
    except Exception as e:
        handle_raw_exception(e)


def start_containerappsjob(cmd,
                           resource_group_name,
                           name,
                           image=None,
                           container_name=None,
                           env_vars=None,
                           startup_command=None,
                           args=None,
                           cpu=None,
                           memory=None,
                           registry_identity=None,
                           yaml=None):

    if yaml:
        if image or container_name or env_vars or\
            startup_command or args or cpu or memory or\
                startup_command or args:
            logger.warning('Additional flags were passed along with --yaml. These flags will be ignored, and the configuration defined in the yaml will be used instead')
        return start_containerappjob_execution_yaml(cmd=cmd, name=name, resource_group_name=resource_group_name, file_name=yaml)

    template_def = None

    if image is not None:
        template_def = JobExecutionTemplateModel
        container_def = ContainerModel
        resources_def = None
        if cpu is not None or memory is not None:
            resources_def = ContainerResourcesModel
            resources_def["cpu"] = cpu
            resources_def["memory"] = memory

        container_def["name"] = container_name if container_name else name
        container_def["image"] = image if not is_registry_msi_system(registry_identity) else HELLO_WORLD_IMAGE
        if env_vars is not None:
            container_def["env"] = parse_env_var_flags(env_vars)
        if startup_command is not None:
            container_def["command"] = startup_command
        if args is not None:
            container_def["args"] = args
        if resources_def is not None:
            container_def["resources"] = resources_def

        template_def["containers"] = [container_def]

    try:
        return ContainerAppsJobClient.start_job(cmd=cmd, resource_group_name=resource_group_name, name=name, containerapp_job_start_envelope=template_def)
    except CLIError as e:
        handle_raw_exception(e)


def start_containerappjob_execution_yaml(cmd, name, resource_group_name, file_name, no_wait=False):
    yaml_containerappjob_execution = load_yaml_file(file_name)
    # check if the type is dict
    if not isinstance(yaml_containerappjob_execution, dict):
        raise InvalidArgumentValueError('Invalid YAML provided. Please see https://aka.ms/azure-container-apps-yaml for a valid containerapp job execution YAML.')

    containerappjob_def = None

    # Check if containerapp exists
    try:
        containerappjob_def = ContainerAppsJobClient.show(cmd=cmd, resource_group_name=resource_group_name, name=name)
    except Exception:
        pass

    if not containerappjob_def:
        raise ResourceNotFoundError("The containerapp job '{}' does not exist".format(name))

    containerappjobexec_def = None

    # Deserialize the yaml into a ContainerApp job execution object. Need this since we're not using SDK
    try:
        deserializer = create_deserializer()
        containerappjobexec_def = deserializer('JobExecutionTemplate', yaml_containerappjob_execution)
    except DeserializationError as ex:
        raise InvalidArgumentValueError('Invalid YAML provided. Please see https://aka.ms/azure-container-apps-yaml for a valid containerapp job execution YAML.') from ex

    containerappjobexec_def = _convert_object_from_snake_to_camel_case(_object_to_dict(containerappjobexec_def))

    # Remove "additionalProperties" attributes that are introduced in the deserialization.
    _remove_additional_attributes(containerappjobexec_def)

    # Clean null values since this is an update
    containerappjobexec_def = clean_null_values(containerappjobexec_def)

    try:
        return ContainerAppsJobClient.start_job(cmd=cmd, resource_group_name=resource_group_name, name=name, containerapp_job_start_envelope=containerappjobexec_def)
    except CLIError as e:
        handle_raw_exception(e)


def stop_containerappsjob(cmd, resource_group_name, name, job_execution_name=None, execution_name_list=None):
    try:
        # todo: remove execution_name_list in future and allow calling with or without job_execution_name
        if execution_name_list is not None:
            return "--execution-name-list is deprecated. Please use --job-execution-name instead."

        r = ContainerAppsJobClient.stop_job(cmd=cmd, resource_group_name=resource_group_name, name=name, job_execution_name=job_execution_name)

        # if stop is called for a single job execution, return generic response else return the response
        if job_execution_name:
            return "Job Execution: " + job_execution_name + ", stopped successfully."

        # else return the response
        return r
    except CLIError as e:
        handle_raw_exception(e)


def listexecution_containerappsjob(cmd, resource_group_name, name):
    try:
        executions = ContainerAppsJobClient.get_executions(cmd=cmd, resource_group_name=resource_group_name, name=name)
        return executions['value']
    except CLIError as e:
        handle_raw_exception(e)


def getSingleExecution_containerappsjob(cmd, resource_group_name, name, job_execution_name):
    try:
        execution = ContainerAppsJobClient.get_single_execution(cmd=cmd, resource_group_name=resource_group_name, name=name, job_execution_name=job_execution_name)
        return execution
    except CLIError as e:
        handle_raw_exception(e)


def assign_managed_identity(cmd, name, resource_group_name, system_assigned=False, user_assigned=None, no_wait=False):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)
    containerapp_def = None

    # Get containerapp properties of CA we are updating
    try:
        containerapp_def = ContainerAppClient.show(cmd=cmd, resource_group_name=resource_group_name, name=name)
    except:
        pass

    if not containerapp_def:
        raise ResourceNotFoundError("The containerapp '{}' does not exist".format(name))

    _get_existing_secrets(cmd, resource_group_name, name, containerapp_def)
    set_managed_identity(cmd, resource_group_name, containerapp_def, system_assigned, user_assigned)

    try:
        r = ContainerAppClient.create_or_update(
            cmd=cmd, resource_group_name=resource_group_name, name=name, container_app_envelope=containerapp_def, no_wait=no_wait)
        # If identity is not returned, do nothing
        return r["identity"]

    except Exception as e:
        handle_raw_exception(e)


def remove_managed_identity(cmd, name, resource_group_name, system_assigned=False, user_assigned=None, no_wait=False):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)

    remove_system_identity = system_assigned
    remove_user_identities = user_assigned

    if user_assigned:
        remove_id_size = len(remove_user_identities)

        # Remove duplicate identities that are passed and notify
        remove_user_identities = list(set(remove_user_identities))
        if remove_id_size != len(remove_user_identities):
            logger.warning("At least one identity was passed twice.")

    containerapp_def = None
    # Get containerapp properties of CA we are updating
    try:
        containerapp_def = ContainerAppClient.show(cmd=cmd, resource_group_name=resource_group_name, name=name)
    except:
        pass

    if not containerapp_def:
        raise ResourceNotFoundError("The containerapp '{}' does not exist".format(name))

    _get_existing_secrets(cmd, resource_group_name, name, containerapp_def)

    # If identity not returned
    try:
        containerapp_def["identity"]
        containerapp_def["identity"]["type"]
    except:
        containerapp_def["identity"] = {}
        containerapp_def["identity"]["type"] = "None"

    if containerapp_def["identity"]["type"] == "None":
        raise InvalidArgumentValueError("The containerapp {} has no system or user assigned identities.".format(name))

    if remove_system_identity:
        if containerapp_def["identity"]["type"] == "UserAssigned":
            raise InvalidArgumentValueError("The containerapp {} has no system assigned identities.".format(name))
        containerapp_def["identity"]["type"] = ("None" if containerapp_def["identity"]["type"] == "SystemAssigned" else "UserAssigned")

    if isinstance(user_assigned, list) and not user_assigned:
        containerapp_def["identity"]["userAssignedIdentities"] = {}
        remove_user_identities = []

        if containerapp_def["identity"]["userAssignedIdentities"] == {}:
            containerapp_def["identity"]["userAssignedIdentities"] = None
            containerapp_def["identity"]["type"] = ("None" if containerapp_def["identity"]["type"] == "UserAssigned" else "SystemAssigned")

    if remove_user_identities:
        subscription_id = get_subscription_id(cmd.cli_ctx)
        try:
            containerapp_def["identity"]["userAssignedIdentities"]
        except:
            containerapp_def["identity"]["userAssignedIdentities"] = {}
        for remove_id in remove_user_identities:
            given_id = remove_id
            remove_id = _ensure_identity_resource_id(subscription_id, resource_group_name, remove_id)
            wasRemoved = False

            for old_user_identity in containerapp_def["identity"]["userAssignedIdentities"]:
                if old_user_identity.lower() == remove_id.lower():
                    containerapp_def["identity"]["userAssignedIdentities"].pop(old_user_identity)
                    wasRemoved = True
                    break

            if not wasRemoved:
                raise InvalidArgumentValueError("The containerapp does not have specified user identity '{}' assigned, so it cannot be removed.".format(given_id))

        if containerapp_def["identity"]["userAssignedIdentities"] == {}:
            containerapp_def["identity"]["userAssignedIdentities"] = None
            containerapp_def["identity"]["type"] = ("None" if containerapp_def["identity"]["type"] == "UserAssigned" else "SystemAssigned")

    try:
        r = ContainerAppClient.create_or_update(cmd=cmd, resource_group_name=resource_group_name, name=name, container_app_envelope=containerapp_def, no_wait=no_wait)
        return r["identity"]
    except Exception as e:
        handle_raw_exception(e)


def show_managed_identity(cmd, name, resource_group_name):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)

    try:
        r = ContainerAppClient.show(cmd=cmd, resource_group_name=resource_group_name, name=name)
    except CLIError as e:
        handle_raw_exception(e)

    try:
        return r["identity"]
    except:
        r["identity"] = {}
        r["identity"]["type"] = "None"
        return r["identity"]


def assign_managed_identity_job(cmd, name, resource_group_name, system_assigned=False, user_assigned=None, no_wait=False):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)
    containerappjob_def = None

    # Get containerapp job properties of CA we are updating
    try:
        containerappjob_def = ContainerAppsJobClient.show(cmd=cmd, resource_group_name=resource_group_name, name=name)
    except:
        pass

    if not containerappjob_def:
        raise ResourceNotFoundError("The containerapp job '{}' does not exist".format(name))

    _get_existing_secrets(cmd, resource_group_name, name, containerappjob_def, AppType.ContainerAppJob)
    set_managed_identity(cmd, resource_group_name, containerappjob_def, system_assigned, user_assigned)

    try:
        r = ContainerAppsJobClient.create_or_update(
            cmd=cmd, resource_group_name=resource_group_name, name=name, containerapp_job_envelope=containerappjob_def, no_wait=no_wait)
        # If identity is not returned, do nothing
        return r["identity"]

    except Exception as e:
        handle_raw_exception(e)


def remove_managed_identity_job(cmd, name, resource_group_name, system_assigned=False, user_assigned=None, no_wait=False):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)

    remove_system_identity = system_assigned
    remove_user_identities = user_assigned

    if user_assigned:
        remove_id_size = len(remove_user_identities)

        # Remove duplicate identities that are passed and notify
        remove_user_identities = list(set(remove_user_identities))
        if remove_id_size != len(remove_user_identities):
            logger.warning("At least one identity was passed twice.")

    containerappjob_def = None
    # Get containerapp job properties of CA we are updating
    try:
        containerappjob_def = ContainerAppsJobClient.show(cmd=cmd, resource_group_name=resource_group_name, name=name)
    except:
        pass

    if not containerappjob_def:
        raise ResourceNotFoundError("The containerapp job '{}' does not exist".format(name))

    _get_existing_secrets(cmd, resource_group_name, name, containerappjob_def, AppType.ContainerAppJob)

    # If identity not returned
    try:
        containerappjob_def["identity"]
        containerappjob_def["identity"]["type"]
    except:
        containerappjob_def["identity"] = {}
        containerappjob_def["identity"]["type"] = "None"

    if containerappjob_def["identity"]["type"] == "None":
        raise InvalidArgumentValueError("The containerapp job {} has no system or user assigned identities.".format(name))

    if remove_system_identity:
        if containerappjob_def["identity"]["type"] == "UserAssigned":
            raise InvalidArgumentValueError("The containerapp job {} has no system assigned identities.".format(name))
        containerappjob_def["identity"]["type"] = ("None" if containerappjob_def["identity"]["type"] == "SystemAssigned" else "UserAssigned")

    if isinstance(user_assigned, list) and not user_assigned:
        containerappjob_def["identity"]["userAssignedIdentities"] = {}
        remove_user_identities = []

        if containerappjob_def["identity"]["userAssignedIdentities"] == {}:
            containerappjob_def["identity"]["userAssignedIdentities"] = None
            containerappjob_def["identity"]["type"] = ("None" if containerappjob_def["identity"]["type"] == "UserAssigned" else "SystemAssigned")

    if remove_user_identities:
        subscription_id = get_subscription_id(cmd.cli_ctx)
        try:
            containerappjob_def["identity"]["userAssignedIdentities"]
        except:
            containerappjob_def["identity"]["userAssignedIdentities"] = {}
        for remove_id in remove_user_identities:
            given_id = remove_id
            remove_id = _ensure_identity_resource_id(subscription_id, resource_group_name, remove_id)
            wasRemoved = False

            for old_user_identity in containerappjob_def["identity"]["userAssignedIdentities"]:
                if old_user_identity.lower() == remove_id.lower():
                    containerappjob_def["identity"]["userAssignedIdentities"].pop(old_user_identity)
                    wasRemoved = True
                    break

            if not wasRemoved:
                raise InvalidArgumentValueError("The containerapp job does not have specified user identity '{}' assigned, so it cannot be removed.".format(given_id))

        if containerappjob_def["identity"]["userAssignedIdentities"] == {}:
            containerappjob_def["identity"]["userAssignedIdentities"] = None
            containerappjob_def["identity"]["type"] = ("None" if containerappjob_def["identity"]["type"] == "UserAssigned" else "SystemAssigned")

    try:
        r = ContainerAppsJobClient.create_or_update(cmd=cmd, resource_group_name=resource_group_name, name=name, containerapp_job_envelope=containerappjob_def, no_wait=no_wait)
        return r["identity"]
    except Exception as e:
        handle_raw_exception(e)


def show_managed_identity_job(cmd, name, resource_group_name):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)

    try:
        r = ContainerAppsJobClient.show(cmd=cmd, resource_group_name=resource_group_name, name=name)
    except CLIError as e:
        handle_raw_exception(e)

    try:
        return r["identity"]
    except:
        r["identity"] = {}
        r["identity"]["type"] = "None"
        return r["identity"]


def _validate_github(repo, branch, token):
    from github import Github, GithubException
    from github.GithubException import BadCredentialsException

    if repo:
        g = Github(token)
        github_repo = None
        try:
            github_repo = g.get_repo(repo)
            if not branch:
                branch = github_repo.default_branch
            if not github_repo.permissions.push or not github_repo.permissions.maintain:
                raise ValidationError("The token does not have appropriate access rights to repository {}.".format(repo))
            try:
                github_repo.get_branch(branch=branch)
            except GithubException as e:
                error_msg = "Encountered GitHub error when accessing {} branch in {} repo.".format(branch, repo)
                if e.data and e.data['message']:
                    error_msg += " Error: {}".format(e.data['message'])
                raise CLIInternalError(error_msg) from e
            logger.warning('Verified GitHub repo and branch')
        except BadCredentialsException as e:
            raise ValidationError("Could not authenticate to the repository. Please create a Personal Access Token "
                                  "and use the --token argument. Run 'az webapp deployment github-actions add --help' "
                                  "for more information.") from e
        except GithubException as e:
            error_msg = "Encountered GitHub error when accessing {} repo".format(repo)
            if e.data and e.data['message']:
                error_msg += " Error: {}".format(e.data['message'])
            raise CLIInternalError(error_msg) from e
    return branch


def create_or_update_github_action(cmd,
                                   name,
                                   resource_group_name,
                                   repo_url,
                                   registry_url=None,
                                   registry_username=None,
                                   registry_password=None,
                                   branch=None,
                                   token=None,
                                   login_with_github=False,
                                   image=None,
                                   context_path=None,
                                   service_principal_client_id=None,
                                   service_principal_client_secret=None,
                                   service_principal_tenant_id=None,
                                   trigger_existing_workflow=False,
                                   no_wait=False):
    if not token and not login_with_github:
        raise_missing_token_suggestion()
    elif not token:
        scopes = ["admin:repo_hook", "repo", "workflow"]
        token = get_github_access_token(cmd, scopes)
    elif token and login_with_github:
        logger.warning("Both token and --login-with-github flag are provided. Will use provided token")

    repo = repo_url_to_name(repo_url)
    repo_url = f"https://github.com/{repo}"  # allow specifying repo as <user>/<repo> without the full github url

    branch = _validate_github(repo, branch, token)

    source_control_info = None

    try:
        source_control_info = GitHubActionClient.show(cmd=cmd, resource_group_name=resource_group_name, name=name)

    except Exception as ex:
        if not service_principal_client_id or not service_principal_client_secret or not service_principal_tenant_id:
            raise RequiredArgumentMissingError('Service principal client ID, secret and tenant ID are required to add github actions for the first time. Please create one using the command \"az ad sp create-for-rbac --name {{name}} --role contributor --scopes /subscriptions/{{subscription}}/resourceGroups/{{resourceGroup}} --sdk-auth\"') from ex
        source_control_info = SourceControlModel

    # Need to trigger the workflow manually if it already exists (performing an update)
    try:
        workflow_name = GitHubActionClient.get_workflow_name(cmd=cmd, repo=repo, branch_name=branch, container_app_name=name, token=token)
        if workflow_name is not None:
            if trigger_existing_workflow:
                trigger_workflow(token, repo, workflow_name, branch)
            return source_control_info
    except:  # pylint: disable=bare-except
        pass

    source_control_info["properties"]["repoUrl"] = repo_url
    source_control_info["properties"]["branch"] = branch

    azure_credentials = None

    if service_principal_client_id or service_principal_client_secret or service_principal_tenant_id:
        azure_credentials = AzureCredentialsModel
        azure_credentials["clientId"] = service_principal_client_id
        azure_credentials["clientSecret"] = service_principal_client_secret
        azure_credentials["tenantId"] = service_principal_tenant_id
        azure_credentials["subscriptionId"] = get_subscription_id(cmd.cli_ctx)

    # Registry
    if registry_username is None or registry_password is None:
        # If registry is Azure Container Registry, we can try inferring credentials
        if not registry_url or ACR_IMAGE_SUFFIX not in registry_url:
            raise RequiredArgumentMissingError('Registry url is required if using Azure Container Registry, otherwise Registry username and password are required if using Dockerhub')
        logger.warning('No credential was provided to access Azure Container Registry. Trying to look up...')
        parsed = urlparse(registry_url)
        registry_name = (parsed.netloc if parsed.scheme else parsed.path).split('.')[0]

        try:
            registry_username, registry_password, _ = _get_acr_cred(cmd.cli_ctx, registry_name)
        except Exception as ex:
            raise RequiredArgumentMissingError('Failed to retrieve credentials for container registry. Please provide the registry username and password') from ex

    registry_info = RegistryInfoModel
    registry_info["registryUrl"] = registry_url
    registry_info["registryUserName"] = registry_username
    registry_info["registryPassword"] = registry_password

    github_action_configuration = GitHubActionConfiguration
    github_action_configuration["registryInfo"] = registry_info
    github_action_configuration["azureCredentials"] = azure_credentials
    github_action_configuration["contextPath"] = context_path
    github_action_configuration["image"] = image

    source_control_info["properties"]["githubActionConfiguration"] = github_action_configuration

    headers = ["x-ms-github-auxiliary={}".format(token)]

    try:
        logger.warning("Creating Github action...")
        r = GitHubActionClient.create_or_update(cmd=cmd, resource_group_name=resource_group_name, name=name, github_action_envelope=source_control_info, headers=headers, no_wait=no_wait)
        if not no_wait:
            WORKFLOW_POLL_RETRY = 3
            WORKFLOW_POLL_SLEEP = 10

            # Poll for the workflow file just created (may take up to 30s)
            for _ in range(0, WORKFLOW_POLL_RETRY):
                time.sleep(WORKFLOW_POLL_SLEEP)
                workflow_name = GitHubActionClient.get_workflow_name(cmd=cmd, repo=repo, branch_name=branch, container_app_name=name, token=token)
                if workflow_name is not None:
                    await_github_action(token, repo, workflow_name)
                    return r

            raise ValidationError(
                "Failed to find workflow file for Container App '{}' in .github/workflow folder for repo '{}'. ".format(name, repo) +
                "If this file was removed, please use the 'az containerapp github-action delete' command to disconnect the removed workflow file connection.")
        return r
    except Exception as e:
        handle_raw_exception(e)


def show_github_action(cmd, name, resource_group_name):
    try:
        return GitHubActionClient.show(cmd=cmd, resource_group_name=resource_group_name, name=name)
    except Exception as e:
        handle_raw_exception(e)


def delete_github_action(cmd, name, resource_group_name, token=None, login_with_github=False):
    # Check if there is an existing source control to delete
    try:
        github_action_config = GitHubActionClient.show(cmd=cmd, resource_group_name=resource_group_name, name=name)
    except Exception as e:
        handle_raw_exception(e)

    repo_url = github_action_config["properties"]["repoUrl"]

    if not token and not login_with_github:
        raise_missing_token_suggestion()
    elif not token:
        scopes = ["admin:repo_hook", "repo", "workflow"]
        token = get_github_access_token(cmd, scopes)
    elif token and login_with_github:
        logger.warning("Both token and --login-with-github flag are provided. Will use provided token")

    # Check if PAT can access repo
    try:
        # Verify github repo
        from github import Github, GithubException
        from github.GithubException import BadCredentialsException

        repo = None
        repo = repo_url.split('/')
        if len(repo) >= 2:
            repo = '/'.join(repo[-2:])

        if repo:
            g = Github(token)
            github_repo = None
            try:
                github_repo = g.get_repo(repo)
                if not github_repo.permissions.push or not github_repo.permissions.maintain:
                    raise ValidationError("The token does not have appropriate access rights to repository {}.".format(repo))
            except BadCredentialsException as e:
                raise CLIInternalError("Could not authenticate to the repository. Please create a Personal Access "
                                       "Token and use the --token argument. Run 'az webapp deployment github-actions "
                                       "add --help' for more information.") from e
            except GithubException as e:
                error_msg = "Encountered GitHub error when accessing {} repo".format(repo)
                if e.data and e.data['message']:
                    error_msg += " Error: {}".format(e.data['message'])
                raise CLIInternalError(error_msg) from e
    except CLIError as clierror:
        raise clierror
    except Exception:
        # If exception due to github package missing, etc just continue without validating the repo and rely on api validation
        pass

    headers = ["x-ms-github-auxiliary={}".format(token)]

    try:
        return GitHubActionClient.delete(cmd=cmd, resource_group_name=resource_group_name, name=name, headers=headers)
    except Exception as e:
        handle_raw_exception(e)


def list_revisions(cmd, name, resource_group_name, all=False):  # pylint: disable=redefined-builtin
    try:
        revision_list = ContainerAppClient.list_revisions(cmd=cmd, resource_group_name=resource_group_name, name=name)
        if all:
            return revision_list
        return [r for r in revision_list if r["properties"]["active"]]
    except CLIError as e:
        handle_raw_exception(e)


def show_revision(cmd, resource_group_name, revision_name, name=None):
    if not name:
        name = _get_app_from_revision(revision_name)

    try:
        return ContainerAppClient.show_revision(cmd=cmd, resource_group_name=resource_group_name, container_app_name=name, name=revision_name)
    except CLIError as e:
        handle_raw_exception(e)


def restart_revision(cmd, resource_group_name, revision_name, name=None):
    if not name:
        name = _get_app_from_revision(revision_name)

    try:
        return ContainerAppClient.restart_revision(cmd=cmd, resource_group_name=resource_group_name, container_app_name=name, name=revision_name)
    except CLIError as e:
        handle_raw_exception(e)


def activate_revision(cmd, resource_group_name, revision_name, name=None):
    if not name:
        name = _get_app_from_revision(revision_name)

    try:
        return ContainerAppClient.activate_revision(cmd=cmd, resource_group_name=resource_group_name, container_app_name=name, name=revision_name)
    except CLIError as e:
        handle_raw_exception(e)


def deactivate_revision(cmd, resource_group_name, revision_name, name=None):
    if not name:
        name = _get_app_from_revision(revision_name)

    try:
        return ContainerAppClient.deactivate_revision(cmd=cmd, resource_group_name=resource_group_name, container_app_name=name, name=revision_name)
    except CLIError as e:
        handle_raw_exception(e)


def copy_revision(cmd,
                  resource_group_name,
                  from_revision=None,
                  # label=None,
                  name=None,
                  yaml=None,
                  image=None,
                  container_name=None,
                  min_replicas=None,
                  max_replicas=None,
                  scale_rule_name=None,
                  scale_rule_type=None,
                  scale_rule_http_concurrency=None,
                  scale_rule_metadata=None,
                  scale_rule_auth=None,
                  set_env_vars=None,
                  replace_env_vars=None,
                  remove_env_vars=None,
                  remove_all_env_vars=False,
                  cpu=None,
                  memory=None,
                  revision_suffix=None,
                  startup_command=None,
                  args=None,
                  tags=None,
                  workload_profile_name=None,
                  no_wait=False):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)

    if not name and not from_revision:
        raise RequiredArgumentMissingError('Usage error: --name is required if not using --from-revision.')

    if not name:
        name = _get_app_from_revision(from_revision)

    return update_containerapp_logic(cmd=cmd,
                                     name=name,
                                     resource_group_name=resource_group_name,
                                     yaml=yaml,
                                     image=image,
                                     container_name=container_name,
                                     min_replicas=min_replicas,
                                     max_replicas=max_replicas,
                                     scale_rule_name=scale_rule_name,
                                     scale_rule_type=scale_rule_type,
                                     scale_rule_http_concurrency=scale_rule_http_concurrency,
                                     scale_rule_metadata=scale_rule_metadata,
                                     scale_rule_auth=scale_rule_auth,
                                     set_env_vars=set_env_vars,
                                     remove_env_vars=remove_env_vars,
                                     replace_env_vars=replace_env_vars,
                                     remove_all_env_vars=remove_all_env_vars,
                                     cpu=cpu,
                                     memory=memory,
                                     revision_suffix=revision_suffix,
                                     startup_command=startup_command,
                                     args=args,
                                     tags=tags,
                                     no_wait=no_wait,
                                     workload_profile_name=workload_profile_name,
                                     from_revision=from_revision)


def set_revision_mode(cmd, resource_group_name, name, mode, no_wait=False):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)

    containerapp_def = None
    try:
        containerapp_def = ContainerAppClient.show(cmd=cmd, resource_group_name=resource_group_name, name=name)
    except:
        pass

    if not containerapp_def:
        raise ResourceNotFoundError("The containerapp '{}' does not exist".format(name))

    containerapp_def["properties"]["configuration"]["activeRevisionsMode"] = mode.lower()

    _get_existing_secrets(cmd, resource_group_name, name, containerapp_def)

    try:
        r = ContainerAppClient.create_or_update(
            cmd=cmd, resource_group_name=resource_group_name, name=name, container_app_envelope=containerapp_def, no_wait=no_wait)
        return r["properties"]["configuration"]["activeRevisionsMode"]
    except Exception as e:
        handle_raw_exception(e)


def add_revision_label(cmd, resource_group_name, revision, label, name=None, no_wait=False, yes=False):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)

    if not name:
        name = _get_app_from_revision(revision)

    containerapp_def = None
    try:
        containerapp_def = ContainerAppClient.show(cmd=cmd, resource_group_name=resource_group_name, name=name)
    except:
        pass

    if not containerapp_def:
        raise ResourceNotFoundError(f"The containerapp '{name}' does not exist in group '{resource_group_name}'")

    if "ingress" not in containerapp_def['properties']['configuration'] or "traffic" not in containerapp_def['properties']['configuration']['ingress']:
        raise ValidationError("Ingress and traffic weights are required to add labels.")

    traffic_weight = containerapp_def['properties']['configuration']['ingress']['traffic'] if 'traffic' in containerapp_def['properties']['configuration']['ingress'] else {}

    _validate_revision_name(cmd, revision, resource_group_name, name)

    label_added = False
    for weight in traffic_weight:
        if "label" in weight and weight["label"].lower() == label.lower():
            r_name = "latest" if "latestRevision" in weight and weight["latestRevision"] else weight["revisionName"]
            if not yes and r_name.lower() != revision.lower():
                msg = f"A weight with the label '{label}' already exists. Remove existing label '{label}' from '{r_name}' and add to '{revision}'?"
                if not prompt_y_n(msg, default="n"):
                    raise ArgumentUsageError(f"Usage Error: cannot specify existing label without agreeing to remove existing label '{label}' from '{r_name}' and add to '{revision}'.")
            weight["label"] = None

        if "latestRevision" in weight:
            if revision.lower() == "latest" and weight["latestRevision"]:
                label_added = True
                weight["label"] = label
        else:
            if revision.lower() == weight["revisionName"].lower():
                label_added = True
                weight["label"] = label

    if not label_added:
        containerapp_def["properties"]["configuration"]["ingress"]["traffic"].append({
            "revisionName": revision if revision.lower() != "latest" else None,
            "weight": 0,
            "latestRevision": revision.lower() == "latest",
            "label": label
        })

    containerapp_patch_def = {}
    containerapp_patch_def['properties'] = {}
    containerapp_patch_def['properties']['configuration'] = {}
    containerapp_patch_def['properties']['configuration']['ingress'] = {}

    containerapp_patch_def['properties']['configuration']['ingress']['traffic'] = traffic_weight

    try:
        r = ContainerAppClient.update(
            cmd=cmd, resource_group_name=resource_group_name, name=name, container_app_envelope=containerapp_patch_def, no_wait=no_wait)
        return r['properties']['configuration']['ingress']['traffic']
    except Exception as e:
        handle_raw_exception(e)


def swap_revision_label(cmd, name, resource_group_name, source_label, target_label, no_wait=False):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)

    if source_label == target_label:
        raise ArgumentUsageError("Label names to be swapped must be different.")

    containerapp_def = None
    try:
        containerapp_def = ContainerAppClient.show(cmd=cmd, resource_group_name=resource_group_name, name=name)
    except:
        pass

    if not containerapp_def:
        raise ResourceNotFoundError(f"The containerapp '{name}' does not exist in group '{resource_group_name}'")

    if "ingress" not in containerapp_def['properties']['configuration'] or "traffic" not in containerapp_def['properties']['configuration']['ingress']:
        raise ValidationError("Ingress and traffic weights are required to swap labels.")

    traffic_weight = containerapp_def['properties']['configuration']['ingress']['traffic'] if 'traffic' in containerapp_def['properties']['configuration']['ingress'] else {}

    source_label_found = False
    target_label_found = False
    for weight in traffic_weight:
        if "label" in weight:
            if weight["label"].lower() == source_label.lower():
                if not source_label_found:
                    source_label_found = True
                    weight["label"] = target_label
            elif weight["label"].lower() == target_label.lower():
                if not target_label_found:
                    target_label_found = True
                    weight["label"] = source_label
    if not source_label_found and not target_label_found:
        raise ArgumentUsageError(f"Could not find label '{source_label}' nor label '{target_label}' in traffic.")
    if not source_label_found:
        raise ArgumentUsageError(f"Could not find label '{source_label}' in traffic.")
    if not target_label_found:
        raise ArgumentUsageError(f"Could not find label '{target_label}' in traffic.")

    containerapp_patch_def = {}
    containerapp_patch_def['properties'] = {}
    containerapp_patch_def['properties']['configuration'] = {}
    containerapp_patch_def['properties']['configuration']['ingress'] = {}

    containerapp_patch_def['properties']['configuration']['ingress']['traffic'] = traffic_weight

    try:
        r = ContainerAppClient.update(
            cmd=cmd, resource_group_name=resource_group_name, name=name, container_app_envelope=containerapp_patch_def, no_wait=no_wait)
        return r['properties']['configuration']['ingress']['traffic']
    except Exception as e:
        handle_raw_exception(e)


def remove_revision_label(cmd, resource_group_name, name, label, no_wait=False):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)

    containerapp_def = None
    try:
        containerapp_def = ContainerAppClient.show(cmd=cmd, resource_group_name=resource_group_name, name=name)
    except:
        pass

    if not containerapp_def:
        raise ResourceNotFoundError(f"The containerapp '{name}' does not exist in group '{resource_group_name}'")

    if "ingress" not in containerapp_def['properties']['configuration'] or "traffic" not in containerapp_def['properties']['configuration']['ingress']:
        raise ValidationError("Ingress and traffic weights are required to remove labels.")

    traffic_weight = containerapp_def['properties']['configuration']['ingress']['traffic']

    label_removed = False
    for weight in traffic_weight:
        if "label" in weight and weight["label"].lower() == label.lower():
            label_removed = True
            weight["label"] = None
            break
    if not label_removed:
        raise ValidationError("Please specify a label name with an associated traffic weight.")

    containerapp_patch_def = {}
    containerapp_patch_def['properties'] = {}
    containerapp_patch_def['properties']['configuration'] = {}
    containerapp_patch_def['properties']['configuration']['ingress'] = {}

    containerapp_patch_def['properties']['configuration']['ingress']['traffic'] = traffic_weight

    try:
        r = ContainerAppClient.update(
            cmd=cmd, resource_group_name=resource_group_name, name=name, container_app_envelope=containerapp_patch_def, no_wait=no_wait)
        return r['properties']['configuration']['ingress']['traffic']
    except Exception as e:
        handle_raw_exception(e)


def show_ingress(cmd, name, resource_group_name):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)

    containerapp_def = None
    try:
        containerapp_def = ContainerAppClient.show(cmd=cmd, resource_group_name=resource_group_name, name=name)
    except:
        pass

    if not containerapp_def:
        raise ResourceNotFoundError("The containerapp '{}' does not exist".format(name))

    try:
        return containerapp_def["properties"]["configuration"]["ingress"]
    except Exception as e:
        raise ValidationError("The containerapp '{}' does not have ingress enabled.".format(name)) from e


def enable_ingress(cmd, name, resource_group_name, type, target_port=None, transport="auto", exposed_port=None, allow_insecure=False, disable_warnings=False, no_wait=False):  # pylint: disable=redefined-builtin
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)

    containerapp_def = None
    try:
        containerapp_def = ContainerAppClient.show(cmd=cmd, resource_group_name=resource_group_name, name=name)
    except:
        pass

    if not containerapp_def:
        raise ResourceNotFoundError("The containerapp '{}' does not exist".format(name))

    new_containerapp_def = {}

    external_ingress = None
    if type is not None:
        if type.lower() == "internal":
            external_ingress = False
        elif type.lower() == "external":
            external_ingress = True

    if type is not None:
        ingress_def = {}
        ingress_def["external"] = external_ingress
        ingress_def["transport"] = transport
        ingress_def["allowInsecure"] = allow_insecure
        ingress_def["exposedPort"] = exposed_port if transport == "tcp" else None

        if target_port is not None:
            ingress_def["targetPort"] = target_port
        else:
            ingress_def["targetPort"] = DEFAULT_PORT

        safe_set(new_containerapp_def, "properties", "configuration", "ingress", value=ingress_def)

    try:
        r = ContainerAppClient.update(
            cmd=cmd, resource_group_name=resource_group_name, name=name, container_app_envelope=new_containerapp_def, no_wait=no_wait)
        not disable_warnings and logger.warning("\nIngress enabled. Access your app at https://{}/\n".format(r["properties"]["configuration"]["ingress"]["fqdn"]))
        return r["properties"]["configuration"]["ingress"]
    except Exception as e:
        handle_raw_exception(e)


def disable_ingress(cmd, name, resource_group_name, no_wait=False):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)

    containerapp_def = None
    try:
        containerapp_def = ContainerAppClient.show(cmd=cmd, resource_group_name=resource_group_name, name=name)
    except:
        pass

    if not containerapp_def:
        raise ResourceNotFoundError("The containerapp '{}' does not exist".format(name))

    containerapp_def["properties"]["configuration"]["ingress"] = None

    _get_existing_secrets(cmd, resource_group_name, name, containerapp_def)

    try:
        ContainerAppClient.create_or_update(cmd=cmd, resource_group_name=resource_group_name, name=name, container_app_envelope=containerapp_def, no_wait=no_wait)
        logger.warning("Ingress has been disabled successfully.")
        return
    except Exception as e:
        handle_raw_exception(e)


# pylint: disable=redefined-builtin
def update_ingress(cmd, name, resource_group_name, type=None, target_port=None, transport=None, exposed_port=None, allow_insecure=False, disable_warnings=False, no_wait=False):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)

    containerapp_def = None
    try:
        containerapp_def = ContainerAppClient.show(cmd=cmd, resource_group_name=resource_group_name, name=name)
    except:
        pass

    if not containerapp_def:
        raise ResourceNotFoundError("The containerapp '{}' does not exist".format(name))

    if containerapp_def["properties"]["configuration"]["ingress"] is None:
        raise ValidationError("The containerapp '{}' does not have ingress enabled. Try running `az containerapp ingress -h` for more info.".format(name))

    external_ingress = None
    if type is not None:
        if type.lower() == "internal":
            external_ingress = False
        elif type.lower() == "external":
            external_ingress = True

    containerapp_patch_def = {}
    containerapp_patch_def['properties'] = {}
    containerapp_patch_def['properties']['configuration'] = {}
    containerapp_patch_def['properties']['configuration']['ingress'] = {}

    ingress_def = {}
    if external_ingress is not None:
        ingress_def["external"] = external_ingress
    if target_port is not None:
        ingress_def["targetPort"] = target_port
    if transport is not None:
        ingress_def["transport"] = transport
    if allow_insecure is not None:
        ingress_def["allowInsecure"] = allow_insecure

    if "transport" in ingress_def and ingress_def["transport"] == "tcp":
        # Client certificate mode can only be set for http transport.
        ingress_def["clientCertificateMode"] = None
        if exposed_port is not None:
            ingress_def["exposedPort"] = exposed_port
    else:
        ingress_def["exposedPort"] = None

    containerapp_patch_def["properties"]["configuration"]["ingress"] = ingress_def

    try:
        r = ContainerAppClient.update(
            cmd=cmd, resource_group_name=resource_group_name, name=name, container_app_envelope=containerapp_patch_def, no_wait=no_wait)
        not disable_warnings and logger.warning("\nIngress Updated. Access your app at https://{}/\n".format(r["properties"]["configuration"]["ingress"]["fqdn"]))
        return r["properties"]["configuration"]["ingress"]
    except Exception as e:
        handle_raw_exception(e)


def set_ingress_traffic(cmd, name, resource_group_name, label_weights=None, revision_weights=None, no_wait=False):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)
    if not label_weights and not revision_weights:
        raise ValidationError("Must specify either --label-weight or --revision-weight.")

    containerapp_def = None
    try:
        containerapp_def = ContainerAppClient.show(cmd=cmd, resource_group_name=resource_group_name, name=name)
    except:
        pass

    if not containerapp_def:
        raise ResourceNotFoundError(f"The containerapp '{name}' does not exist in group '{resource_group_name}'")

    if containerapp_def["properties"]["configuration"]["activeRevisionsMode"].lower() == "single":
        raise ValidationError(f"Containerapp '{name}' is configured for single revision. Set revision mode to multiple in order to set ingress traffic. Try `az containerapp revision set-mode -h` for more details.")

    try:
        containerapp_def["properties"]["configuration"]["ingress"]
        containerapp_def["properties"]["configuration"]["ingress"]["traffic"]
    except Exception as e:
        raise ValidationError("Ingress must be enabled to set ingress traffic. Try running `az containerapp ingress -h` for more info.") from e

    if not revision_weights:
        revision_weights = []

    # convert label weights to appropriate revision name
    _append_label_weights(containerapp_def, label_weights, revision_weights)

    # validate sum is less than 100
    _validate_traffic_sum(revision_weights)

    # update revision weights to containerapp, get the old weight sum
    old_weight_sum = _update_revision_weights(containerapp_def, revision_weights)

    # validate revision names
    for revision in revision_weights:
        _validate_revision_name(cmd, revision.split('=')[0], resource_group_name, name)

    _update_weights(containerapp_def, revision_weights, old_weight_sum)

    containerapp_patch_def = {}
    containerapp_patch_def['properties'] = {}
    containerapp_patch_def['properties']['configuration'] = {}
    containerapp_patch_def['properties']['configuration']['ingress'] = {}
    containerapp_patch_def['properties']['configuration']['ingress']['traffic'] = containerapp_def["properties"]["configuration"]["ingress"]["traffic"]

    try:
        r = ContainerAppClient.update(
            cmd=cmd, resource_group_name=resource_group_name, name=name, container_app_envelope=containerapp_patch_def, no_wait=no_wait)
        return r['properties']['configuration']['ingress']['traffic']
    except Exception as e:
        handle_raw_exception(e)


def show_ingress_traffic(cmd, name, resource_group_name):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)

    containerapp_def = None
    try:
        containerapp_def = ContainerAppClient.show(cmd=cmd, resource_group_name=resource_group_name, name=name)
    except:
        pass

    if not containerapp_def:
        raise ResourceNotFoundError("The containerapp '{}' does not exist".format(name))

    try:
        return containerapp_def["properties"]["configuration"]["ingress"]["traffic"]
    except Exception as e:
        raise ValidationError("Ingress must be enabled to show ingress traffic. Try running `az containerapp ingress -h` for more info.") from e


def set_ip_restriction(cmd, name, resource_group_name, rule_name, ip_address, action, description=None, no_wait=False):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)

    containerapp_def = None
    try:
        containerapp_def = ContainerAppClient.show(cmd=cmd, resource_group_name=resource_group_name, name=name)
    except:
        pass

    if not containerapp_def:
        raise ResourceNotFoundError(f"The containerapp '{name}' does not exist in group '{resource_group_name}'")

    ip_restrictions = safe_get(containerapp_def, "properties", "configuration", "ingress", "ipSecurityRestrictions", default=[])

    ip_security_restrictions = set_ip_restrictions(ip_restrictions, rule_name, ip_address, description, action)
    containerapp_patch = {}
    safe_set(containerapp_patch, "properties", "configuration", "ingress", "ipSecurityRestrictions", value=ip_security_restrictions)
    try:
        r = ContainerAppClient.update(
            cmd=cmd, resource_group_name=resource_group_name, name=name, container_app_envelope=containerapp_patch, no_wait=no_wait)
        return r['properties']['configuration']['ingress']['ipSecurityRestrictions']
    except Exception as e:
        handle_raw_exception(e)


def remove_ip_restriction(cmd, name, resource_group_name, rule_name, no_wait=False):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)

    containerapp_def = None
    try:
        containerapp_def = ContainerAppClient.show(cmd=cmd, resource_group_name=resource_group_name, name=name)
    except:
        pass

    if not containerapp_def:
        raise ResourceNotFoundError("The containerapp '{}' does not exist".format(name))

    ip_restrictions = safe_get(containerapp_def, "properties", "configuration", "ingress", "ipSecurityRestrictions", default=[])

    restriction_removed = False
    for index, value in enumerate(ip_restrictions):
        if value["name"].lower() == rule_name.lower():
            ip_restrictions.pop(index)
            restriction_removed = True
            break

    if not restriction_removed:
        raise ValidationError(f"Ip restriction name '{rule_name}' does not exist.")

    containerapp_patch = {}
    safe_set(containerapp_patch, "properties", "configuration", "ingress", "ipSecurityRestrictions", value=ip_restrictions)
    try:
        r = ContainerAppClient.update(
            cmd=cmd, resource_group_name=resource_group_name, name=name, container_app_envelope=containerapp_patch, no_wait=no_wait)
        ip_restrictions = safe_get(r, "properties", "configuration", "ingress", "ipSecurityRestrictions", default=[])
        return ip_restrictions
    except Exception as e:
        handle_raw_exception(e)


def show_ip_restrictions(cmd, name, resource_group_name):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)

    containerapp_def = None
    try:
        containerapp_def = ContainerAppClient.show(cmd=cmd, resource_group_name=resource_group_name, name=name)
    except:
        pass

    if not containerapp_def:
        raise ResourceNotFoundError("The containerapp '{}' does not exist".format(name))

    try:
        try:
            containerapp_def['properties']['configuration']['ingress']
        except Exception as e:
            raise ValidationError("Ingress must be enabled to list ip restrictions. Try running `az containerapp ingress -h` for more info.") from e
        return safe_get(containerapp_def, "properties", "configuration", "ingress", "ipSecurityRestrictions", default=[])
    except:
        return []


def set_ingress_sticky_session(cmd, name, resource_group_name, affinity, no_wait=False):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)

    containerapp_def = None
    try:
        containerapp_def = ContainerAppClient.show(cmd=cmd, resource_group_name=resource_group_name, name=name)
    except:
        pass

    if not containerapp_def:
        raise ResourceNotFoundError(f"The containerapp '{name}' does not exist in group '{resource_group_name}'")

    containerapp_patch = {}
    safe_set(containerapp_patch, "properties", "configuration", "ingress", "stickySessions", "affinity", value=affinity)
    try:
        r = ContainerAppClient.update(
            cmd=cmd, resource_group_name=resource_group_name, name=name, container_app_envelope=containerapp_patch, no_wait=no_wait)
        return r['properties']['configuration']['ingress']
    except Exception as e:
        handle_raw_exception(e)


def show_ingress_sticky_session(cmd, name, resource_group_name):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)

    containerapp_def = None
    try:
        containerapp_def = ContainerAppClient.show(cmd=cmd, resource_group_name=resource_group_name, name=name)
    except:
        pass

    if not containerapp_def:
        raise ResourceNotFoundError("The containerapp '{}' does not exist".format(name))

    try:
        return containerapp_def["properties"]["configuration"]["ingress"]
    except Exception as e:
        raise ValidationError("Ingress must be enabled to enable sticky sessions. Try running `az containerapp ingress -h` for more info.") from e


def enable_cors_policy(cmd, name, resource_group_name, allowed_origins, allowed_methods=None, allowed_headers=None, expose_headers=None, allow_credentials=None, max_age=None, no_wait=False):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)

    if not allowed_origins:
        raise ValidationError("Allowed origins must be specified.")

    containerapp_def = None
    try:
        containerapp_def = ContainerAppClient.show(cmd=cmd, resource_group_name=resource_group_name, name=name)
    except:
        pass

    if not containerapp_def:
        raise ResourceNotFoundError(f"The containerapp '{name}' does not exist in group '{resource_group_name}'")

    reset_max_age = False
    if max_age == "":
        reset_max_age = True

    containerapp_patch = {}
    if allowed_origins is not None:
        safe_set(containerapp_patch, "properties", "configuration", "ingress", "corsPolicy", "allowedOrigins", value=allowed_origins)
    if allowed_methods is not None:
        safe_set(containerapp_patch, "properties", "configuration", "ingress", "corsPolicy", "allowedMethods", value=allowed_methods)
    if allowed_headers is not None:
        safe_set(containerapp_patch, "properties", "configuration", "ingress", "corsPolicy", "allowedHeaders", value=allowed_headers)
    if expose_headers is not None:
        safe_set(containerapp_patch, "properties", "configuration", "ingress", "corsPolicy", "exposeHeaders", value=expose_headers)
    if allow_credentials is not None:
        safe_set(containerapp_patch, "properties", "configuration", "ingress", "corsPolicy", "allowCredentials", value=allow_credentials)
    if max_age is not None:
        if reset_max_age:
            safe_set(containerapp_patch, "properties", "configuration", "ingress", "corsPolicy", "maxAge", value=None)
        else:
            safe_set(containerapp_patch, "properties", "configuration", "ingress", "corsPolicy", "maxAge", value=max_age)

    try:
        r = ContainerAppClient.update(
            cmd=cmd, resource_group_name=resource_group_name, name=name, container_app_envelope=containerapp_patch, no_wait=no_wait)
        return safe_get(r, "properties", "configuration", "ingress", "corsPolicy", default={})
    except Exception as e:
        handle_raw_exception(e)


def disable_cors_policy(cmd, name, resource_group_name, no_wait=False):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)

    containerapp_def = None
    try:
        containerapp_def = ContainerAppClient.show(cmd=cmd, resource_group_name=resource_group_name, name=name)
    except:
        pass

    if not containerapp_def:
        raise ResourceNotFoundError(f"The containerapp '{name}' does not exist in group '{resource_group_name}'")

    containerapp_patch = {}
    safe_set(containerapp_patch, "properties", "configuration", "ingress", "corsPolicy", value=None)
    try:
        r = ContainerAppClient.update(
            cmd=cmd, resource_group_name=resource_group_name, name=name, container_app_envelope=containerapp_patch, no_wait=no_wait)
        return safe_get(r, "properties", "configuration", "ingress", default={})
    except Exception as e:
        handle_raw_exception(e)


def update_cors_policy(cmd, name, resource_group_name, allowed_origins=None, allowed_methods=None, allowed_headers=None, expose_headers=None, allow_credentials=None, max_age=None, no_wait=False):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)

    containerapp_def = None
    try:
        containerapp_def = ContainerAppClient.show(cmd=cmd, resource_group_name=resource_group_name, name=name)
    except:
        pass

    if not containerapp_def:
        raise ResourceNotFoundError(f"The containerapp '{name}' does not exist in group '{resource_group_name}'")

    if allowed_origins is not None and len(allowed_origins) == 0:
        raise RequiredArgumentMissingError("allowed-origins must be specified if provided.")

    reset_max_age = False
    if max_age == "":
        reset_max_age = True

    containerapp_patch = {}
    if allowed_origins is not None:
        safe_set(containerapp_patch, "properties", "configuration", "ingress", "corsPolicy", "allowedOrigins", value=allowed_origins)
    if allowed_methods is not None:
        safe_set(containerapp_patch, "properties", "configuration", "ingress", "corsPolicy", "allowedMethods", value=allowed_methods)
    if allowed_headers is not None:
        safe_set(containerapp_patch, "properties", "configuration", "ingress", "corsPolicy", "allowedHeaders", value=allowed_headers)
    if expose_headers is not None:
        safe_set(containerapp_patch, "properties", "configuration", "ingress", "corsPolicy", "exposeHeaders", value=expose_headers)
    if allow_credentials is not None:
        safe_set(containerapp_patch, "properties", "configuration", "ingress", "corsPolicy", "allowCredentials", value=allow_credentials)
    if max_age is not None:
        if reset_max_age:
            safe_set(containerapp_patch, "properties", "configuration", "ingress", "corsPolicy", "maxAge", value=None)
        else:
            safe_set(containerapp_patch, "properties", "configuration", "ingress", "corsPolicy", "maxAge", value=max_age)

    try:
        r = ContainerAppClient.update(
            cmd=cmd, resource_group_name=resource_group_name, name=name, container_app_envelope=containerapp_patch, no_wait=no_wait)
        return safe_get(r, "properties", "configuration", "ingress", "corsPolicy", default={})
    except Exception as e:
        handle_raw_exception(e)


def show_cors_policy(cmd, name, resource_group_name):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)

    containerapp_def = None
    try:
        containerapp_def = ContainerAppClient.show(cmd=cmd, resource_group_name=resource_group_name, name=name)
    except:
        pass

    if not containerapp_def:
        raise ResourceNotFoundError(f"The containerapp '{name}' does not exist in group '{resource_group_name}'")

    try:
        return safe_get(containerapp_def, "properties", "configuration", "ingress", "corsPolicy", default={})
    except Exception as e:
        raise ValidationError("CORS must be enabled to enable CORS policy. Try running `az containerapp ingress cors enable -h` for more info.") from e


def show_registry(cmd, name, resource_group_name, server):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)

    containerapp_def = None
    try:
        containerapp_def = ContainerAppClient.show(cmd=cmd, resource_group_name=resource_group_name, name=name)
    except:
        pass

    if not containerapp_def:
        raise ResourceNotFoundError("The containerapp '{}' does not exist".format(name))

    try:
        containerapp_def["properties"]["configuration"]["registries"]
    except Exception as e:
        raise ValidationError("The containerapp {} has no assigned registries.".format(name)) from e

    registries_def = containerapp_def["properties"]["configuration"]["registries"]

    if registries_def is not None:
        for r in registries_def:
            if r['server'].lower() == server.lower():
                return r
    raise InvalidArgumentValueError("The containerapp {} does not have specified registry assigned.".format(name))


def list_registry(cmd, name, resource_group_name):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)

    containerapp_def = None
    try:
        containerapp_def = ContainerAppClient.show(cmd=cmd, resource_group_name=resource_group_name, name=name)
    except:
        pass

    if not containerapp_def:
        raise ResourceNotFoundError("The containerapp '{}' does not exist".format(name))

    try:
        return containerapp_def["properties"]["configuration"]["registries"]
    except Exception as e:
        raise ValidationError("The containerapp {} has no assigned registries.".format(name)) from e


def set_registry(cmd, name, resource_group_name, server, username=None, password=None, disable_warnings=False, identity=None, no_wait=False):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)
    if (username or password) and identity:
        raise MutuallyExclusiveArgumentError("Use either identity or username/password.")

    containerapp_def = None
    try:
        containerapp_def = ContainerAppClient.show(cmd=cmd, resource_group_name=resource_group_name, name=name)
    except:
        pass

    if not containerapp_def:
        raise ResourceNotFoundError("The containerapp '{}' does not exist".format(name))

    _get_existing_secrets(cmd, resource_group_name, name, containerapp_def)

    registry = None

    registries_def = safe_get(containerapp_def, "properties", "configuration", "registries", default=[])
    containerapp_def["properties"]["configuration"]["registries"] = registries_def

    if (not username or not password) and not identity:
        # If registry is Azure Container Registry, we can try inferring credentials
        if ACR_IMAGE_SUFFIX not in server:
            raise RequiredArgumentMissingError('Registry username and password are required if you are not using Azure Container Registry.')
        not disable_warnings and logger.warning('No credential was provided to access Azure Container Registry. Trying to look up...')
        parsed = urlparse(server)
        registry_name = (parsed.netloc if parsed.scheme else parsed.path).split('.')[0]

        try:
            username, password, _ = _get_acr_cred(cmd.cli_ctx, registry_name)
        except Exception as ex:
            raise RequiredArgumentMissingError('Failed to retrieve credentials for container registry. Please provide the registry username and password') from ex

    # Check if updating existing registry
    updating_existing_registry = False
    for r in registries_def:
        if r['server'].lower() == server.lower():
            not disable_warnings and logger.warning("Updating existing registry.")
            updating_existing_registry = True
            if username:
                r["username"] = username
                r["identity"] = None
            if password:
                r["passwordSecretRef"] = store_as_secret_and_return_secret_ref(
                    containerapp_def["properties"]["configuration"]["secrets"],
                    r["username"],
                    r["server"],
                    password,
                    update_existing_secret=True)
                r["identity"] = None
            if identity:
                r["identity"] = identity
                r["username"] = None
                r["passwordSecretRef"] = None

    # If not updating existing registry, add as new registry
    if not updating_existing_registry:
        registry = RegistryCredentialsModel
        registry["server"] = server
        if not identity:
            registry["username"] = username
            registry["passwordSecretRef"] = store_as_secret_and_return_secret_ref(
                containerapp_def["properties"]["configuration"]["secrets"],
                username,
                server,
                password,
                update_existing_secret=True)
        else:
            registry["identity"] = identity

        registries_def.append(registry)

    if identity:
        system_assigned_identity = identity.lower() == "system"
        user_assigned = None if system_assigned_identity else [identity]
        set_managed_identity(cmd, resource_group_name, containerapp_def, system_assigned_identity, user_assigned)

    try:
        r = ContainerAppClient.create_or_update(
            cmd=cmd, resource_group_name=resource_group_name, name=name, container_app_envelope=containerapp_def, no_wait=no_wait)

        return r["properties"]["configuration"]["registries"]
    except Exception as e:
        handle_raw_exception(e)


def remove_registry(cmd, name, resource_group_name, server, no_wait=False):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)

    containerapp_def = None
    try:
        containerapp_def = ContainerAppClient.show(cmd=cmd, resource_group_name=resource_group_name, name=name)
    except:
        pass

    if not containerapp_def:
        raise ResourceNotFoundError("The containerapp '{}' does not exist".format(name))

    _get_existing_secrets(cmd, resource_group_name, name, containerapp_def)

    registries_def = None

    try:
        containerapp_def["properties"]["configuration"]["registries"]
    except Exception as e:
        raise ValidationError("The containerapp {} has no assigned registries.".format(name)) from e

    registries_def = containerapp_def["properties"]["configuration"]["registries"]

    wasRemoved = False
    for i, value in enumerate(registries_def):
        r = value
        if r['server'].lower() == server.lower():
            registries_def.pop(i)
            _remove_registry_secret(containerapp_def=containerapp_def, server=server, username=r["username"])
            wasRemoved = True
            break

    if not wasRemoved:
        raise ValidationError("Containerapp does not have registry server {} assigned.".format(server))

    if len(containerapp_def["properties"]["configuration"]["registries"]) == 0:
        containerapp_def["properties"]["configuration"].pop("registries")

    try:
        r = ContainerAppClient.create_or_update(
            cmd=cmd, resource_group_name=resource_group_name, name=name, container_app_envelope=containerapp_def, no_wait=no_wait)
        logger.warning("Registry successfully removed.")
        return r["properties"]["configuration"]["registries"]
    # No registries to return, so return nothing
    except Exception:
        pass


def list_secrets(cmd, name, resource_group_name, show_values=False):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)

    containerapp_def = None
    try:
        r = containerapp_def = ContainerAppClient.show(cmd=cmd, resource_group_name=resource_group_name, name=name)
    except:
        pass

    if not containerapp_def:
        raise ResourceNotFoundError("The containerapp '{}' does not exist".format(name))

    if not show_values:
        try:
            return r["properties"]["configuration"]["secrets"]
        except:
            return []
    try:
        return ContainerAppClient.list_secrets(cmd=cmd, resource_group_name=resource_group_name, name=name)["value"]
    except Exception:
        return []
        # raise ValidationError("The containerapp {} has no assigned secrets.".format(name)) from e


def show_secret(cmd, name, resource_group_name, secret_name):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)

    containerapp_def = None
    try:
        containerapp_def = ContainerAppClient.show(cmd=cmd, resource_group_name=resource_group_name, name=name)
    except:
        pass

    if not containerapp_def:
        raise ResourceNotFoundError("The containerapp '{}' does not exist".format(name))

    r = ContainerAppClient.list_secrets(cmd=cmd, resource_group_name=resource_group_name, name=name)
    for secret in r["value"]:
        if secret["name"].lower() == secret_name.lower():
            return secret
    raise ValidationError("The containerapp {} does not have a secret assigned with name {}.".format(name, secret_name))


def remove_secrets(cmd, name, resource_group_name, secret_names, no_wait=False):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)

    containerapp_def = None
    try:
        containerapp_def = ContainerAppClient.show(cmd=cmd, resource_group_name=resource_group_name, name=name)
    except:
        pass

    if not containerapp_def:
        raise ResourceNotFoundError("The containerapp '{}' does not exist".format(name))

    _get_existing_secrets(cmd, resource_group_name, name, containerapp_def)

    for secret_name in secret_names:
        wasRemoved = False
        for secret in containerapp_def["properties"]["configuration"]["secrets"]:
            if secret["name"].lower() == secret_name.lower():
                _remove_secret(containerapp_def, secret_name=secret["name"])
                wasRemoved = True
                break
        if not wasRemoved:
            raise ValidationError("The containerapp {} does not have a secret assigned with name {}.".format(name, secret_name))
    try:
        r = ContainerAppClient.create_or_update(
            cmd=cmd, resource_group_name=resource_group_name, name=name, container_app_envelope=containerapp_def, no_wait=no_wait)
        logger.warning("Secret(s) successfully removed.")
        try:
            return r["properties"]["configuration"]["secrets"]
        # No secrets to return
        except:
            pass
    except Exception as e:
        handle_raw_exception(e)


def set_secrets(cmd, name, resource_group_name, secrets,
                # yaml=None,
                disable_max_length=False,
                no_wait=False):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)

    # if not yaml and not secrets:
    #     raise RequiredArgumentMissingError('Usage error: --secrets is required if not using --yaml')

    # if not secrets:
    #     secrets = []

    # if yaml:
    #     yaml_secrets = load_yaml_file(yaml).split(' ')
    #     try:
    #         parse_secret_flags(yaml_secrets)
    #     except:
    #         raise ValidationError("YAML secrets must be a list of secrets in key=value format, delimited by new line.")
    #     for secret in yaml_secrets:
    #         secrets.append(secret.strip())

    containerapp_def = None
    try:
        containerapp_def = ContainerAppClient.show(cmd=cmd, resource_group_name=resource_group_name, name=name)
    except:
        pass

    if not containerapp_def:
        raise ResourceNotFoundError("The containerapp '{}' does not exist".format(name))

    _get_existing_secrets(cmd, resource_group_name, name, containerapp_def)
    _add_or_update_secrets(containerapp_def, parse_secret_flags(secrets))

    try:
        r = ContainerAppClient.create_or_update(
            cmd=cmd, resource_group_name=resource_group_name, name=name, container_app_envelope=containerapp_def, no_wait=no_wait)
        logger.warning("Containerapp '{}' must be restarted in order for secret changes to take effect.".format(name))
        return r["properties"]["configuration"]["secrets"]
    except Exception as e:
        handle_raw_exception(e)


def list_secrets_job(cmd, name, resource_group_name, show_values=False):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)

    containerappjob_def = None
    try:
        r = containerappjob_def = ContainerAppsJobClient.show(cmd=cmd, resource_group_name=resource_group_name, name=name)
    except:
        pass

    if not containerappjob_def:
        raise ResourceNotFoundError("The containerapp job '{}' does not exist".format(name))

    if not show_values:
        try:
            return r["properties"]["configuration"]["secrets"]
        except:
            return []
    try:
        return ContainerAppsJobClient.list_secrets(cmd=cmd, resource_group_name=resource_group_name, name=name)["value"]
    except Exception:
        return []
        # raise ValidationError("The containerapp job {} has no assigned secrets.".format(name)) from e


def show_secret_job(cmd, name, resource_group_name, secret_name):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)

    containerappjob_def = None
    try:
        containerappjob_def = ContainerAppsJobClient.show(cmd=cmd, resource_group_name=resource_group_name, name=name)
    except:
        pass

    if not containerappjob_def:
        raise ResourceNotFoundError("The containerapp job '{}' does not exist".format(name))

    r = ContainerAppsJobClient.list_secrets(cmd=cmd, resource_group_name=resource_group_name, name=name)
    for secret in r["value"]:
        if secret["name"].lower() == secret_name.lower():
            return secret
    raise ValidationError("The containerapp job {} does not have a secret assigned with name {}.".format(name, secret_name))


def remove_secrets_job(cmd, name, resource_group_name, secret_names, no_wait=False):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)

    containerappjob_def = None
    try:
        containerappjob_def = ContainerAppsJobClient.show(cmd=cmd, resource_group_name=resource_group_name, name=name)
    except:
        pass

    if not containerappjob_def:
        raise ResourceNotFoundError("The containerapp job '{}' does not exist".format(name))

    _get_existing_secrets(cmd, resource_group_name, name, containerappjob_def, AppType.ContainerAppJob)

    for secret_name in secret_names:
        wasRemoved = False
        for secret in containerappjob_def["properties"]["configuration"]["secrets"]:
            if secret["name"].lower() == secret_name.lower():
                _remove_secret(containerappjob_def, secret_name=secret["name"])
                wasRemoved = True
                break
        if not wasRemoved:
            raise ValidationError("The containerapp job {} does not have a secret assigned with name {}.".format(name, secret_name))
    try:
        r = ContainerAppsJobClient.create_or_update(
            cmd=cmd, resource_group_name=resource_group_name, name=name, containerapp_job_envelope=containerappjob_def, no_wait=no_wait)
        logger.warning("Secret(s) successfully removed.")
        try:
            return r["properties"]["configuration"]["secrets"]
        # No secrets to return
        except:
            pass
    except Exception as e:
        handle_raw_exception(e)


def set_secrets_job(cmd, name, resource_group_name, secrets,
                    # yaml=None,
                    disable_max_length=False,
                    no_wait=False):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)

    containerappjob_def = None
    try:
        containerappjob_def = ContainerAppsJobClient.show(cmd=cmd, resource_group_name=resource_group_name, name=name)
    except:
        pass

    if not containerappjob_def:
        raise ResourceNotFoundError("The containerapp job '{}' does not exist".format(name))

    _get_existing_secrets(cmd, resource_group_name, name, containerappjob_def, AppType.ContainerAppJob)
    _add_or_update_secrets(containerappjob_def, parse_secret_flags(secrets))

    try:
        r = ContainerAppsJobClient.create_or_update(
            cmd=cmd, resource_group_name=resource_group_name, name=name, containerapp_job_envelope=containerappjob_def, no_wait=no_wait)
        logger.warning("Containerapp job '{}' executions triggered now will have the added/updated secret.".format(name))
        return r["properties"]["configuration"]["secrets"]
    except Exception as e:
        handle_raw_exception(e)


def show_registry_job(cmd, name, resource_group_name, server):
    raw_parameters = locals()

    containerapp_job_registry_decorator = ContainerAppJobRegistryDecorator(
        cmd=cmd,
        client=ContainerAppsJobClient,
        raw_parameters=raw_parameters,
        models=CONTAINER_APPS_SDK_MODELS
    )
    containerapp_job_registry_decorator.validate_subscription_registered(CONTAINER_APPS_RP)
    containerapp_job_registry_decorator.validate_arguments()

    r = containerapp_job_registry_decorator.show()
    return r


def list_registry_job(cmd, name, resource_group_name):
    raw_parameters = locals()

    containerapp_job_registry_decorator = ContainerAppJobRegistryDecorator(
        cmd=cmd,
        client=ContainerAppsJobClient,
        raw_parameters=raw_parameters,
        models=CONTAINER_APPS_SDK_MODELS
    )
    containerapp_job_registry_decorator.validate_subscription_registered(CONTAINER_APPS_RP)
    containerapp_job_registry_decorator.validate_arguments()

    r = containerapp_job_registry_decorator.list()
    return r


def set_registry_job(cmd, name, resource_group_name, server, username=None, password=None, disable_warnings=False, identity=None, no_wait=False):
    raw_parameters = locals()

    containerapp_job_registry_set_decorator = ContainerAppJobRegistrySetDecorator(
        cmd=cmd,
        client=ContainerAppsJobClient,
        raw_parameters=raw_parameters,
        models=CONTAINER_APPS_SDK_MODELS
    )
    containerapp_job_registry_set_decorator.validate_subscription_registered(CONTAINER_APPS_RP)
    containerapp_job_registry_set_decorator.validate_arguments()
    containerapp_job_registry_set_decorator.construct_payload()
    r = containerapp_job_registry_set_decorator.set()
    return r


def remove_registry_job(cmd, name, resource_group_name, server, no_wait=False):
    raw_parameters = locals()

    containerapp_job_registry_remove_decorator = ContainerAppJobRegistryRemoveDecorator(
        cmd=cmd,
        client=ContainerAppsJobClient,
        raw_parameters=raw_parameters,
        models=CONTAINER_APPS_SDK_MODELS
    )
    containerapp_job_registry_remove_decorator.validate_subscription_registered(CONTAINER_APPS_RP)
    containerapp_job_registry_remove_decorator.validate_arguments()
    containerapp_job_registry_remove_decorator.construct_payload()
    r = containerapp_job_registry_remove_decorator.remove()
    return r


def enable_dapr(cmd, name, resource_group_name,
                dapr_app_id=None,
                dapr_app_port=None,
                dapr_app_protocol=None,
                dapr_http_read_buffer_size=None,
                dapr_http_max_request_size=None,
                dapr_log_level=None,
                dapr_enable_api_logging=False,
                no_wait=False):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)

    containerapp_def = None
    try:
        containerapp_def = ContainerAppClient.show(cmd=cmd, resource_group_name=resource_group_name, name=name)
    except:
        pass

    if not containerapp_def:
        raise ResourceNotFoundError("The containerapp '{}' does not exist".format(name))

    _get_existing_secrets(cmd, resource_group_name, name, containerapp_def)

    if 'configuration' not in containerapp_def['properties']:
        containerapp_def['properties']['configuration'] = {}

    if not safe_get(containerapp_def['properties']['configuration'], 'dapr'):
        containerapp_def['properties']['configuration']['dapr'] = {}

    if dapr_app_id:
        containerapp_def['properties']['configuration']['dapr']['appId'] = dapr_app_id

    if dapr_app_port:
        containerapp_def['properties']['configuration']['dapr']['appPort'] = dapr_app_port

    if dapr_app_protocol:
        containerapp_def['properties']['configuration']['dapr']['appProtocol'] = dapr_app_protocol

    if dapr_http_read_buffer_size:
        containerapp_def['properties']['configuration']['dapr']['httpReadBufferSize'] = dapr_http_read_buffer_size

    if dapr_http_max_request_size:
        containerapp_def['properties']['configuration']['dapr']['httpMaxRequestSize'] = dapr_http_max_request_size

    if dapr_log_level:
        containerapp_def['properties']['configuration']['dapr']['logLevel'] = dapr_log_level

    if dapr_enable_api_logging:
        containerapp_def['properties']['configuration']['dapr']['enableApiLogging'] = dapr_enable_api_logging

    containerapp_def['properties']['configuration']['dapr']['enabled'] = True

    try:
        r = ContainerAppClient.create_or_update(
            cmd=cmd, resource_group_name=resource_group_name, name=name, container_app_envelope=containerapp_def, no_wait=no_wait)
        return r["properties"]['configuration']['dapr']
    except Exception as e:
        handle_raw_exception(e)


def disable_dapr(cmd, name, resource_group_name, no_wait=False):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)

    containerapp_def = None
    try:
        containerapp_def = ContainerAppClient.show(cmd=cmd, resource_group_name=resource_group_name, name=name)
    except:
        pass

    if not containerapp_def:
        raise ResourceNotFoundError("The containerapp '{}' does not exist".format(name))

    _get_existing_secrets(cmd, resource_group_name, name, containerapp_def)

    if 'configuration' not in containerapp_def['properties']:
        containerapp_def['properties']['configuration'] = {}

    if 'dapr' not in containerapp_def['properties']['configuration']:
        containerapp_def['properties']['configuration']['dapr'] = {}

    containerapp_def['properties']['configuration']['dapr']['enabled'] = False

    try:
        r = ContainerAppClient.create_or_update(
            cmd=cmd, resource_group_name=resource_group_name, name=name, container_app_envelope=containerapp_def, no_wait=no_wait)
        return r["properties"]['configuration']['dapr']
    except Exception as e:
        handle_raw_exception(e)


def list_dapr_components(cmd, resource_group_name, environment_name):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)

    return DaprComponentClient.list(cmd, resource_group_name, environment_name)


def show_dapr_component(cmd, resource_group_name, dapr_component_name, environment_name):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)

    return DaprComponentClient.show(cmd, resource_group_name, environment_name, name=dapr_component_name)


def create_or_update_dapr_component(cmd, resource_group_name, environment_name, dapr_component_name, yaml):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)

    yaml_dapr_component = load_yaml_file(yaml)
    # check if the type is dict
    if not isinstance(yaml_dapr_component, dict):
        raise ValidationError('Invalid YAML provided. Please see https://learn.microsoft.com/en-us/azure/container-apps/dapr-overview?tabs=bicep1%2Cyaml#component-schema for a valid Dapr Component YAML spec.')

    # Deserialize the yaml into a DaprComponent object. Need this since we're not using SDK
    daprcomponent_def = None
    try:
        deserializer = create_deserializer()

        daprcomponent_def = deserializer('DaprComponent', yaml_dapr_component)
    except DeserializationError as ex:
        raise ValidationError('Invalid YAML provided. Please see https://aka.ms/azure-container-apps-yaml for a valid containerapps YAML spec.') from ex

    daprcomponent_def = _convert_object_from_snake_to_camel_case(_object_to_dict(daprcomponent_def))

    # Remove "additionalProperties" and read-only attributes that are introduced in the deserialization. Need this since we're not using SDK
    _remove_additional_attributes(daprcomponent_def)
    _remove_dapr_readonly_attributes(daprcomponent_def)

    if not daprcomponent_def["ignoreErrors"]:
        daprcomponent_def["ignoreErrors"] = False

    dapr_component_envelope = {}

    dapr_component_envelope["properties"] = daprcomponent_def

    try:
        r = DaprComponentClient.create_or_update(cmd, resource_group_name=resource_group_name, environment_name=environment_name, dapr_component_envelope=dapr_component_envelope, name=dapr_component_name)
        return r
    except Exception as e:
        handle_raw_exception(e)


def remove_dapr_component(cmd, resource_group_name, dapr_component_name, environment_name):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)

    try:
        DaprComponentClient.show(cmd, resource_group_name, environment_name, name=dapr_component_name)
    except Exception as e:
        raise ResourceNotFoundError("Dapr component not found.") from e

    try:
        r = DaprComponentClient.delete(cmd, resource_group_name, environment_name, name=dapr_component_name)
        logger.warning("Dapr componenet successfully deleted.")
        return r
    except Exception as e:
        handle_raw_exception(e)


def list_replicas(cmd, resource_group_name, name, revision=None):
    app = ContainerAppClient.show(cmd, resource_group_name, name)
    if not revision:
        revision = app["properties"]["latestRevisionName"]
    return ContainerAppClient.list_replicas(cmd=cmd,
                                            resource_group_name=resource_group_name,
                                            container_app_name=name,
                                            revision_name=revision)


def get_replica(cmd, resource_group_name, name, replica, revision=None):
    app = ContainerAppClient.show(cmd, resource_group_name, name)
    if not revision:
        revision = app["properties"]["latestRevisionName"]
    return ContainerAppClient.get_replica(cmd=cmd,
                                          resource_group_name=resource_group_name,
                                          container_app_name=name,
                                          revision_name=revision,
                                          replica_name=replica)


def containerapp_ssh(cmd, resource_group_name, name, container=None, revision=None, replica=None, startup_command="sh"):
    if isinstance(startup_command, list):
        startup_command = startup_command[0]  # CLI seems a little buggy when calling a param "--command"

    conn = WebSocketConnection(cmd=cmd, resource_group_name=resource_group_name, name=name, revision=revision,
                               replica=replica, container=container, startup_command=startup_command)

    encodings = [SSH_DEFAULT_ENCODING, SSH_BACKUP_ENCODING]
    reader = threading.Thread(target=read_ssh, args=(conn, encodings))
    reader.daemon = True
    reader.start()

    writer = get_stdin_writer(conn)
    writer.daemon = True
    writer.start()

    logger.warning("Use ctrl + D to exit.")
    while conn.is_connected:
        if not reader.is_alive() or not writer.is_alive():
            logger.warning("Reader or Writer for WebSocket is not alive. Closing the connection.")
            conn.disconnect()

        try:
            time.sleep(0.1)
        except KeyboardInterrupt:
            if conn.is_connected:
                logger.info("Caught KeyboardInterrupt. Sending ctrl+c to server")
                conn.send(SSH_CTRL_C_MSG)


def stream_containerapp_logs(cmd, resource_group_name, name, container=None, revision=None, replica=None, follow=False,
                             tail=None, output_format=None, kind=None):
    if tail:
        if tail < 0 or tail > 300:
            raise ValidationError("--tail must be between 0 and 300.")
    if kind == LOG_TYPE_SYSTEM:
        if container or replica or revision:
            raise MutuallyExclusiveArgumentError("--type: --container, --replica, and --revision not supported for system logs")
        if output_format and output_format != "json":
            raise MutuallyExclusiveArgumentError("--type: only json logs supported for system logs")

    sub = get_subscription_id(cmd.cli_ctx)
    token_response = ContainerAppClient.get_auth_token(cmd, resource_group_name, name)
    token = token_response["properties"]["token"]

    base_url = ContainerAppClient.show(cmd, resource_group_name, name)["properties"]["eventStreamEndpoint"]
    base_url = base_url[:base_url.index("/subscriptions/")]

    if kind == LOG_TYPE_CONSOLE:
        url = (f"{base_url}/subscriptions/{sub}/resourceGroups/{resource_group_name}/containerApps/{name}"
               f"/revisions/{revision}/replicas/{replica}/containers/{container}/logstream")
    else:
        url = f"{base_url}/subscriptions/{sub}/resourceGroups/{resource_group_name}/containerApps/{name}/eventstream"

    logger.info("connecting to : %s", url)
    request_params = {"follow": str(follow).lower(),
                      "output": output_format,
                      "tailLines": tail}
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url,
                        timeout=None,
                        stream=True,
                        params=request_params,
                        headers=headers)

    if not resp.ok:
        raise ValidationError(f"Got bad status from the logstream API: {resp.status_code}")

    for line in resp.iter_lines():
        if line:
            logger.info("received raw log line: %s", line)
            if output_format == "json":
                print(json.dumps(json.loads(line)))
            else:
                print(line.decode("utf-8"))


def stream_environment_logs(cmd, resource_group_name, name, follow=False, tail=None):
    if tail:
        if tail < 0 or tail > 300:
            raise ValidationError("--tail must be between 0 and 300.")

    env = show_managed_environment(cmd, name, resource_group_name)
    url = safe_get(env, "properties", "eventStreamEndpoint")

    if url is None:
        sub = get_subscription_id(cmd.cli_ctx)
        base_url = f"https://{format_location(env['location'])}.azurecontainerapps.dev"
        url = (f"{base_url}/subscriptions/{sub}/resourceGroups/{resource_group_name}/managedEnvironments/{name}"
               f"/eventstream")

    token_response = ManagedEnvironmentClient.get_auth_token(cmd, resource_group_name, name)
    token = token_response["properties"]["token"]

    logger.info("connecting to : %s", url)
    request_params = {"follow": str(follow).lower(),
                      "tailLines": tail}
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url,
                        timeout=None,
                        stream=True,
                        params=request_params,
                        headers=headers)

    if not resp.ok:
        raise ValidationError(f"Got bad status from the logstream API: {resp.status_code}")

    for line in resp.iter_lines():
        if line:
            logger.info("received raw log line: %s", line)
            # these .replaces are needed to display color/quotations properly
            # for some reason the API returns garbled unicode special characters (may need to add more in the future)
            print(line.decode("utf-8").replace("\\u0022", "\u0022").replace("\\u001B", "\u001B").replace("\\u002B", "\u002B").replace("\\u0027", "\u0027"))


def open_containerapp_in_browser(cmd, name, resource_group_name):
    app = ContainerAppClient.show(cmd, resource_group_name, name)
    url = safe_get(app, "properties", "configuration", "ingress", "fqdn")
    if not url:
        raise ValidationError("Could not open in browser: no public URL for this app")
    if not url.startswith("http"):
        url = f"http://{url}"
    open_page_in_browser(url)


def containerapp_up(cmd,
                    name,
                    resource_group_name=None,
                    managed_env=None,
                    location=None,
                    registry_server=None,
                    image=None,
                    source=None,
                    ingress=None,
                    target_port=None,
                    registry_user=None,
                    registry_pass=None,
                    env_vars=None,
                    logs_customer_id=None,
                    logs_key=None,
                    repo=None,
                    token=None,
                    branch=None,
                    browse=False,
                    context_path=None,
                    workload_profile_name=None,
                    service_principal_client_id=None,
                    service_principal_client_secret=None,
                    service_principal_tenant_id=None):
    from ._up_utils import (_validate_up_args, _reformat_image, _get_dockerfile_content, _get_ingress_and_target_port,
                            ResourceGroup, ContainerAppEnvironment, ContainerApp, _get_registry_from_app,
                            _get_registry_details, _create_github_action, _set_up_defaults, up_output,
                            check_env_name_on_rg, get_token, _has_dockerfile)
    from ._github_oauth import cache_github_token
    HELLOWORLD = "mcr.microsoft.com/k8se/quickstart"
    dockerfile = "Dockerfile"  # for now the dockerfile name must be "Dockerfile" (until GH actions API is updated)

    register_provider_if_needed(cmd, CONTAINER_APPS_RP)
    _validate_up_args(cmd, source, image, repo, registry_server)
    validate_container_app_name(name, AppType.ContainerApp.name)
    check_env_name_on_rg(cmd, managed_env, resource_group_name, location)

    image = _reformat_image(source, repo, image)
    token = get_token(cmd, repo, token)

    if image and HELLOWORLD in image.lower():
        ingress = "external" if not ingress else ingress
        target_port = 80 if not target_port else target_port

    if source and not _has_dockerfile(source, dockerfile):
        pass
    else:
        dockerfile_content = _get_dockerfile_content(repo, branch, token, source, context_path, dockerfile)
        ingress, target_port = _get_ingress_and_target_port(ingress, target_port, dockerfile_content)

    resource_group = ResourceGroup(cmd, name=resource_group_name, location=location)
    env = ContainerAppEnvironment(cmd, managed_env, resource_group, location=location, logs_key=logs_key, logs_customer_id=logs_customer_id)
    app = ContainerApp(cmd, name, resource_group, None, image, env, target_port, registry_server, registry_user, registry_pass, env_vars, workload_profile_name, ingress)

    # Check and see if registry username and passwords are specified. If so, set is_registry_server_params_set to True to use those creds.
    is_registry_server_params_set = bool(registry_server and registry_user and registry_pass)
    _set_up_defaults(cmd, name, resource_group_name, logs_customer_id, location, resource_group, env, app, is_registry_server_params_set)

    if app.check_exists():
        if app.get()["properties"]["provisioningState"] == "InProgress":
            raise ValidationError("Containerapp has an existing provisioning in progress. Please wait until provisioning has completed and rerun the command.")

    resource_group.create_if_needed()
    env.create_if_needed(name)

    if source or repo:
        if not registry_server:
            _get_registry_from_app(app, source)  # if the app exists, get the registry
        _get_registry_details(cmd, app, source)  # fetch ACR creds from arguments registry arguments

    app.create_acr_if_needed()

    if source:
        app.run_acr_build(dockerfile, source, quiet=False, build_from_source=not _has_dockerfile(source, dockerfile))

    app.create(no_registry=bool(repo))
    if repo:
        _create_github_action(app, env, service_principal_client_id, service_principal_client_secret,
                              service_principal_tenant_id, branch, token, repo, context_path)
        cache_github_token(cmd, token, repo)

    if browse:
        open_containerapp_in_browser(cmd, app.name, app.resource_group.name)

    up_output(app, no_dockerfile=(source and not _has_dockerfile(source, dockerfile)))


def containerapp_up_logic(cmd, resource_group_name, name, managed_env, image, env_vars, ingress, target_port, registry_server, registry_user, workload_profile_name, registry_pass):
    containerapp_def = None
    try:
        containerapp_def = ContainerAppClient.show(cmd=cmd, resource_group_name=resource_group_name, name=name)
    except:
        pass

    if containerapp_def:
        return update_containerapp_logic(cmd=cmd, name=name, resource_group_name=resource_group_name, image=image, replace_env_vars=env_vars, ingress=ingress, target_port=target_port,
                                         registry_server=registry_server, registry_user=registry_user, registry_pass=registry_pass, workload_profile_name=workload_profile_name, container_name=name)
    return create_containerapp(cmd=cmd, name=name, resource_group_name=resource_group_name, managed_env=managed_env, image=image, env_vars=env_vars, ingress=ingress, target_port=target_port, registry_server=registry_server, registry_user=registry_user, registry_pass=registry_pass, workload_profile_name=workload_profile_name)


def create_managed_certificate(cmd, name, resource_group_name, hostname, validation_method, certificate_name=None):
    if certificate_name and not check_managed_cert_name_availability(cmd, resource_group_name, name, certificate_name):
        raise ValidationError(f"Certificate name '{certificate_name}' is not available.")
    cert_name = certificate_name
    while not cert_name:
        cert_name = generate_randomized_managed_cert_name(hostname, resource_group_name)
        if not check_managed_cert_name_availability(cmd, resource_group_name, name, certificate_name):
            cert_name = None
    certificate_envelop = prepare_managed_certificate_envelop(cmd, name, resource_group_name, hostname, validation_method.upper())
    try:
        r = ManagedEnvironmentClient.create_or_update_managed_certificate(cmd, resource_group_name, name, cert_name, certificate_envelop, True, validation_method.upper() == 'TXT')
        return r
    except Exception as e:
        handle_raw_exception(e)


def list_certificates(cmd, name, resource_group_name, location=None, certificate=None, thumbprint=None, managed_certificates_only=False, private_key_certificates_only=False):

    return list_certificates_logic(cmd, name, resource_group_name, location, certificate, thumbprint, managed_certificates_only=managed_certificates_only, private_key_certificates_only=private_key_certificates_only)


def list_certificates_logic(cmd, name, resource_group_name, location=None, certificate=None, thumbprint=None, managed_certificates_only=False, private_key_certificates_only=False):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)
    if managed_certificates_only and private_key_certificates_only:
        raise MutuallyExclusiveArgumentError("Use either '--managed-certificates-only' or '--private-key-certificates-only'.")
    if managed_certificates_only and thumbprint:
        raise MutuallyExclusiveArgumentError("'--thumbprint' not supported for managed certificates.")

    if certificate and is_valid_resource_id(certificate):
        certificate_name = parse_resource_id(certificate)["resource_name"]
        certificate_type = parse_resource_id(certificate)["resource_type"]
    else:
        certificate_name = certificate
        certificate_type = PRIVATE_CERTIFICATE_RT if private_key_certificates_only or thumbprint else (MANAGED_CERTIFICATE_RT if managed_certificates_only else None)

    if certificate_type == MANAGED_CERTIFICATE_RT:
        return get_managed_certificates(cmd, name, resource_group_name, certificate_name, location)
    if certificate_type == PRIVATE_CERTIFICATE_RT:
        return get_private_certificates(cmd, name, resource_group_name, certificate_name, thumbprint, location)
    managed_certs = get_managed_certificates(cmd, name, resource_group_name, certificate_name, location)
    private_certs = get_private_certificates(cmd, name, resource_group_name, certificate_name, thumbprint, location)
    return managed_certs + private_certs


def get_private_certificates(cmd, name, resource_group_name, certificate_name=None, thumbprint=None, location=None):
    if certificate_name:
        try:
            r = ManagedEnvironmentClient.show_certificate(cmd, resource_group_name, name, certificate_name)
            return [r] if certificate_matches(r, location, thumbprint) else []
        except Exception as e:
            handle_non_resource_not_found_exception(e)
            return []
    else:
        try:
            r = ManagedEnvironmentClient.list_certificates(cmd, resource_group_name, name)
            return list(filter(lambda c: certificate_matches(c, location, thumbprint), r))
        except Exception as e:
            handle_raw_exception(e)


def get_managed_certificates(cmd, name, resource_group_name, certificate_name=None, location=None):
    if certificate_name:
        try:
            r = ManagedEnvironmentClient.show_managed_certificate(cmd, resource_group_name, name, certificate_name)
            return [r] if certificate_location_matches(r, location) else []
        except Exception as e:
            handle_non_resource_not_found_exception(e)
            return []
    else:
        try:
            r = ManagedEnvironmentClient.list_managed_certificates(cmd, resource_group_name, name)
            return list(filter(lambda c: certificate_location_matches(c, location), r))
        except Exception as e:
            handle_raw_exception(e)


def upload_certificate(cmd, name, resource_group_name, certificate_file, certificate_name=None, certificate_password=None, location=None, prompt=False):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)

    blob, thumbprint = load_cert_file(certificate_file, certificate_password)

    cert_name = None
    if certificate_name:
        name_availability = check_cert_name_availability(cmd, resource_group_name, name, certificate_name)
        if not name_availability["nameAvailable"]:
            if name_availability["reason"] == NAME_ALREADY_EXISTS:
                msg = '{}. If continue with this name, it will be overwritten by the new certificate file.\nOverwrite?'
                overwrite = True
                if prompt:
                    overwrite = prompt_y_n(msg.format(name_availability["message"]))
                else:
                    logger.warning('{}. It will be overwritten by the new certificate file.'.format(name_availability["message"]))
                if overwrite:
                    cert_name = certificate_name
            else:
                raise ValidationError(name_availability["message"])
        else:
            cert_name = certificate_name

    while not cert_name:
        random_name = generate_randomized_cert_name(thumbprint, name, resource_group_name)
        check_result = check_cert_name_availability(cmd, resource_group_name, name, random_name)
        if check_result["nameAvailable"]:
            cert_name = random_name
        elif not check_result["nameAvailable"] and (check_result["reason"] == NAME_INVALID):
            raise ValidationError(check_result["message"])

    certificate = ContainerAppCertificateEnvelopeModel
    certificate["properties"]["password"] = certificate_password
    certificate["properties"]["value"] = blob
    certificate["location"] = location
    if not certificate["location"]:
        try:
            managed_env = ManagedEnvironmentClient.show(cmd, resource_group_name, name)
            certificate["location"] = managed_env["location"]
        except Exception as e:
            handle_raw_exception(e)

    try:
        r = ManagedEnvironmentClient.create_or_update_certificate(cmd, resource_group_name, name, cert_name, certificate)
        return r
    except Exception as e:
        handle_raw_exception(e)


def delete_certificate(cmd, resource_group_name, name, location=None, certificate=None, thumbprint=None):

    delete_certificate_logic(cmd=cmd, resource_group_name=resource_group_name, name=name, cert_name=certificate, location=location, certificate=certificate, thumbprint=thumbprint)


# this function will be used in extension
def delete_certificate_logic(cmd, resource_group_name, name, cert_name, location=None, certificate=None, thumbprint=None, cert_type=None):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)
    if not certificate and not thumbprint:
        raise RequiredArgumentMissingError('Please specify at least one of parameters: --certificate and --thumbprint')

    cert_name = certificate
    if certificate and is_valid_resource_id(certificate):
        cert_type = parse_resource_id(certificate)["resource_type"]
        cert_name = parse_resource_id(certificate)["resource_name"]
    if thumbprint:
        cert_type = PRIVATE_CERTIFICATE_RT

    if cert_type == PRIVATE_CERTIFICATE_RT:
        certs = list_certificates(cmd, name, resource_group_name, location, certificate, thumbprint)
        if len(certs) == 0:
            msg = "'{}'".format(cert_name) if cert_name else "with thumbprint '{}'".format(thumbprint)
            raise ResourceNotFoundError(f"The certificate {msg} does not exist in Container app environment '{name}'.")
        for cert in certs:
            try:
                ManagedEnvironmentClient.delete_certificate(cmd, resource_group_name, name, cert["name"])
                logger.warning('Successfully deleted certificate: %s', cert["name"])
            except Exception as e:
                handle_raw_exception(e)
    elif cert_type == MANAGED_CERTIFICATE_RT:
        try:
            ManagedEnvironmentClient.delete_managed_certificate(cmd, resource_group_name, name, cert_name)
            logger.warning('Successfully deleted certificate: {}'.format(cert_name))
        except Exception as e:
            handle_raw_exception(e)
    else:
        managed_certs = list(filter(lambda c: c["name"] == cert_name, get_managed_certificates(cmd, name, resource_group_name, None, location)))
        private_certs = list(filter(lambda c: c["name"] == cert_name, get_private_certificates(cmd, name, resource_group_name, None, None, location)))
        if len(managed_certs) == 0 and len(private_certs) == 0:
            raise ResourceNotFoundError(f"The certificate '{cert_name}' does not exist in Container app environment '{name}'.")
        if len(managed_certs) > 0 and len(private_certs) > 0:
            raise RequiredArgumentMissingError(f"Found more than one certificates with name '{cert_name}':\n'{managed_certs[0]['id']}',\n'{private_certs[0]['id']}'.\nPlease specify the certificate id using --certificate.")
        if private_certs:
            try:
                ManagedEnvironmentClient.delete_certificate(cmd, resource_group_name, name, cert_name)
                logger.warning('Successfully deleted certificate: %s', cert_name)
            except Exception as e:
                handle_raw_exception(e)

        if managed_certs:
            try:
                ManagedEnvironmentClient.delete_managed_certificate(cmd, resource_group_name, name, cert_name)
                logger.warning('Successfully deleted certificate: %s', cert_name)
            except Exception as e:
                handle_raw_exception(e)


def upload_ssl(cmd, resource_group_name, name, environment, certificate_file, hostname, certificate_password=None, certificate_name=None, location=None):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)

    passed, message = validate_hostname(cmd, resource_group_name, name, hostname)
    if not passed:
        raise ValidationError(message or 'Please configure the DNS records before adding the hostname.')

    custom_domains = get_custom_domains(cmd, resource_group_name, name, location, environment)
    new_custom_domains = list(filter(lambda c: c["name"] != hostname, custom_domains))

    env_name = _get_name(environment)
    logger.warning('Uploading certificate to %s.', env_name)
    if is_valid_resource_id(environment):
        cert = upload_certificate(cmd, env_name, parse_resource_id(environment)["resource_group"], certificate_file, certificate_name, certificate_password, location)
    else:
        cert = upload_certificate(cmd, env_name, resource_group_name, certificate_file, certificate_name, certificate_password, location)
    cert_id = cert["id"]

    new_domain = deepcopy(ContainerAppCustomDomainModel)
    new_domain["name"] = hostname
    new_domain["certificateId"] = cert_id
    new_custom_domains.append(new_domain)
    logger.warning('Adding hostname %s and binding to %s.', hostname, name)
    return patch_new_custom_domain(cmd, resource_group_name, name, new_custom_domains)


def bind_hostname(cmd, resource_group_name, name, hostname, thumbprint=None, certificate=None, location=None, environment=None, validation_method=None):

    return bind_hostname_logic(cmd, resource_group_name, name, hostname, thumbprint, certificate, location, environment, validation_method)


def bind_hostname_logic(cmd, resource_group_name, name, hostname, thumbprint=None, certificate=None, location=None, environment=None, validation_method=None):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)

    if not environment and not certificate:
        raise RequiredArgumentMissingError('Please specify at least one of parameters: --certificate and --environment')
    if certificate and not is_valid_resource_id(certificate) and not environment:
        raise RequiredArgumentMissingError('Please specify the parameter: --environment')

    standardized_hostname = hostname.lower()
    passed, message = validate_hostname(cmd, resource_group_name, name, standardized_hostname)
    if not passed:
        raise ValidationError(message or 'Please configure the DNS records before adding the hostname.')

    env_name = _get_name(environment) if environment else None
    env_rg = resource_group_name
    if is_valid_resource_id(environment):
        env_dict = parse_resource_id(environment)
        env_name = env_dict.get('name')
        env_rg = env_dict.get('resource_group')

    if certificate:
        if is_valid_resource_id(certificate):
            cert_id = certificate
        else:
            certs = list_certificates(cmd, env_name, env_rg, location, certificate, thumbprint)
            if len(certs) == 0:
                msg = "'{}' with thumbprint '{}'".format(certificate, thumbprint) if thumbprint else "'{}'".format(certificate)
                raise ResourceNotFoundError(f"The certificate {msg} does not exist in Container app environment '{env_name}'.")
            cert_id = certs[0]["id"]
    elif thumbprint:
        certs = list_certificates(cmd, env_name, env_rg, location, certificate, thumbprint)
        if len(certs) == 0:
            raise ResourceNotFoundError(f"The certificate with thumbprint '{thumbprint}' does not exist in Container app environment '{env_name}'.")
        cert_id = certs[0]["id"]
    else:  # look for or create a managed certificate if no certificate info provided
        managed_certs = get_managed_certificates(cmd, env_name, env_rg, None, None)
        managed_cert = [cert for cert in managed_certs if cert["properties"]["subjectName"].lower() == standardized_hostname]
        if len(managed_cert) > 0 and managed_cert[0]["properties"]["provisioningState"] in [SUCCEEDED_STATUS, PENDING_STATUS]:
            cert_id = managed_cert[0]["id"]
            cert_name = managed_cert[0]["name"]
        else:
            cert_name = None
            while not cert_name:
                random_name = generate_randomized_managed_cert_name(standardized_hostname, env_name)
                available = check_managed_cert_name_availability(cmd, env_rg, env_name, cert_name)
                if available:
                    cert_name = random_name
            logger.warning("Creating managed certificate '%s' for %s.\nIt may take up to 20 minutes to create and issue a managed certificate.", cert_name, standardized_hostname)

            if validation_method is None:
                raise RequiredArgumentMissingError('Please specify the parameter: --validation-method')
            validation = validation_method.upper()
            while validation not in ["TXT", "CNAME", "HTTP"]:
                validation = prompt_str('\nPlease choose one of the following domain validation methods: TXT, CNAME, HTTP\nYour answer: ').upper()

            certificate_envelop = prepare_managed_certificate_envelop(cmd, env_name, env_rg, standardized_hostname, validation, location)
            try:
                managed_cert = ManagedEnvironmentClient.create_or_update_managed_certificate(cmd, env_rg, env_name, cert_name, certificate_envelop, False, validation == 'TXT')
            except Exception as e:
                handle_raw_exception(e)
            cert_id = managed_cert["id"]

        logger.warning("\nBinding managed certificate '%s' to %s\n", cert_name, standardized_hostname)

    custom_domains = get_custom_domains(cmd, resource_group_name, name, location, environment)
    new_custom_domains = list(filter(lambda c: safe_get(c, "name", default=[]) != standardized_hostname, custom_domains))
    new_domain = deepcopy(ContainerAppCustomDomainModel)
    new_domain["name"] = standardized_hostname
    new_domain["certificateId"] = cert_id
    new_custom_domains.append(new_domain)

    return patch_new_custom_domain(cmd, resource_group_name, name, new_custom_domains)


def add_hostname(cmd, resource_group_name, name, hostname, location=None):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)
    standardized_hostname = hostname.lower()
    custom_domains = get_custom_domains(cmd, resource_group_name, name, location, None)
    existing_hostname = list(filter(lambda c: safe_get(c, "name", default=[]) == standardized_hostname, custom_domains))
    if len(existing_hostname) > 0:
        raise InvalidArgumentValueError("'{standardized_hostname}' already exists in container app '{name}'.")
    new_domain = deepcopy(ContainerAppCustomDomainModel)
    new_domain["name"] = standardized_hostname
    new_domain["bindingType"] = "Disabled"
    custom_domains.append(new_domain)
    return patch_new_custom_domain(cmd, resource_group_name, name, custom_domains)


def list_hostname(cmd, resource_group_name, name, location=None):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)

    custom_domains = get_custom_domains(cmd, resource_group_name, name, location)
    return custom_domains


def delete_hostname(cmd, resource_group_name, name, hostname, location=None):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)

    custom_domains = get_custom_domains(cmd, resource_group_name, name, location)
    new_custom_domains = list(filter(lambda c: c["name"] != hostname, custom_domains))
    if len(new_custom_domains) == len(custom_domains):
        raise ResourceNotFoundError("The hostname '{}' in Container app '{}' was not found.".format(hostname, name))

    r = patch_new_custom_domain(cmd, resource_group_name, name, new_custom_domains)
    logger.warning('Successfully deleted custom domain: {}'.format(hostname))
    return r


def show_storage(cmd, name, storage_name, resource_group_name):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)

    try:
        return StorageClient.show(cmd, resource_group_name, name, storage_name)
    except CLIError as e:
        handle_raw_exception(e)


def list_storage(cmd, name, resource_group_name):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)

    try:
        return StorageClient.list(cmd, resource_group_name, name)
    except CLIError as e:
        handle_raw_exception(e)


def create_or_update_storage(cmd, storage_name, resource_group_name, name, azure_file_account_name, azure_file_share_name, azure_file_account_key, access_mode, no_wait=False):  # pylint: disable=redefined-builtin
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)

    if len(azure_file_share_name) < 3:
        raise ValidationError("File share name must be longer than 2 characters.")

    if len(azure_file_account_name) < 3:
        raise ValidationError("Account name must be longer than 2 characters.")

    r = None

    try:
        r = StorageClient.show(cmd, resource_group_name, name, storage_name)
    except:
        pass

    if r:
        logger.warning("Only AzureFile account keys can be updated. In order to change the AzureFile share name or account name, please delete this storage and create a new one.")

    storage_def = AzureFilePropertiesModel
    storage_def["accountKey"] = azure_file_account_key
    storage_def["accountName"] = azure_file_account_name
    storage_def["shareName"] = azure_file_share_name
    storage_def["accessMode"] = access_mode
    storage_envelope = {}
    storage_envelope["properties"] = {}
    storage_envelope["properties"]["azureFile"] = storage_def

    try:
        return StorageClient.create_or_update(cmd, resource_group_name, name, storage_name, storage_envelope)
    except CLIError as e:
        handle_raw_exception(e)


def remove_storage(cmd, storage_name, name, resource_group_name):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)

    try:
        return StorageClient.delete(cmd, resource_group_name, name, storage_name)
    except CLIError as e:
        handle_raw_exception(e)


# TODO: Refactor provider code to make it cleaner
def update_aad_settings(cmd, resource_group_name, name,
                        client_id=None, client_secret_setting_name=None,
                        issuer=None, allowed_token_audiences=None, client_secret=None,
                        client_secret_certificate_thumbprint=None,
                        client_secret_certificate_san=None,
                        client_secret_certificate_issuer=None,
                        yes=False, tenant_id=None):
    try:
        show_ingress(cmd, name, resource_group_name)
    except Exception as e:
        raise ValidationError("Authentication requires ingress to be enabled for your containerapp.") from e

    if client_secret is not None and client_secret_setting_name is not None:
        raise ArgumentUsageError('Usage Error: --client-secret and --client-secret-setting-name cannot both be '
                                 'configured to non empty strings')

    if client_secret_setting_name is not None and client_secret_certificate_thumbprint is not None:
        raise ArgumentUsageError('Usage Error: --client-secret-setting-name and --thumbprint cannot both be '
                                 'configured to non empty strings')

    if client_secret is not None and client_secret_certificate_thumbprint is not None:
        raise ArgumentUsageError('Usage Error: --client-secret and --thumbprint cannot both be '
                                 'configured to non empty strings')

    if client_secret is not None and client_secret_certificate_san is not None:
        raise ArgumentUsageError('Usage Error: --client-secret and --san cannot both be '
                                 'configured to non empty strings')

    if client_secret_setting_name is not None and client_secret_certificate_san is not None:
        raise ArgumentUsageError('Usage Error: --client-secret-setting-name and --san cannot both be '
                                 'configured to non empty strings')

    if client_secret_certificate_thumbprint is not None and client_secret_certificate_san is not None:
        raise ArgumentUsageError('Usage Error: --thumbprint and --san cannot both be '
                                 'configured to non empty strings')

    if ((client_secret_certificate_san is not None and client_secret_certificate_issuer is None) or
            (client_secret_certificate_san is None and client_secret_certificate_issuer is not None)):
        raise ArgumentUsageError('Usage Error: --san and --certificate-issuer must both be '
                                 'configured to non empty strings')

    if issuer is not None and (tenant_id is not None):
        raise ArgumentUsageError('Usage Error: --issuer and --tenant-id cannot be configured '
                                 'to non empty strings at the same time.')

    is_new_aad_app = False
    existing_auth = {}
    try:
        existing_auth = AuthClient.get(cmd=cmd, resource_group_name=resource_group_name, container_app_name=name, auth_config_name="current")["properties"]
    except:
        existing_auth = {}
        existing_auth["platform"] = {}
        existing_auth["platform"]["enabled"] = True
        existing_auth["globalValidation"] = {}
        existing_auth["login"] = {}

    registration = {}
    validation = {}
    if "identityProviders" not in existing_auth:
        existing_auth["identityProviders"] = {}
    if "azureActiveDirectory" not in existing_auth["identityProviders"]:
        existing_auth["identityProviders"]["azureActiveDirectory"] = {}
        is_new_aad_app = True

    if is_new_aad_app and issuer is None and tenant_id is None:
        raise ArgumentUsageError('Usage Error: Either --issuer or --tenant-id must be specified when configuring the '
                                 'Microsoft auth registration.')

    if client_secret is not None and not yes:
        msg = 'Configuring --client-secret will add a secret to the containerapp. Are you sure you want to continue?'
        if not prompt_y_n(msg, default="n"):
            raise ArgumentUsageError('Usage Error: --client-secret cannot be used without agreeing to add secret '
                                     'to the containerapp.')

    openid_issuer = issuer
    if openid_issuer is None:
        # cmd.cli_ctx.cloud resolves to whichever cloud the customer is currently logged into
        authority = cmd.cli_ctx.cloud.endpoints.active_directory

        if tenant_id is not None:
            openid_issuer = authority + "/" + tenant_id + "/v2.0"

    registration = {}
    validation = {}
    if "identityProviders" not in existing_auth:
        existing_auth["identityProviders"] = {}
    if "azureActiveDirectory" not in existing_auth["identityProviders"]:
        existing_auth["identityProviders"]["azureActiveDirectory"] = {}
    if (client_id is not None or client_secret is not None or
            client_secret_setting_name is not None or openid_issuer is not None or
            client_secret_certificate_thumbprint is not None or
            client_secret_certificate_san is not None or
            client_secret_certificate_issuer is not None):
        if "registration" not in existing_auth["identityProviders"]["azureActiveDirectory"]:
            existing_auth["identityProviders"]["azureActiveDirectory"]["registration"] = {}
        registration = existing_auth["identityProviders"]["azureActiveDirectory"]["registration"]
    if allowed_token_audiences is not None:
        if "validation" not in existing_auth["identityProviders"]["azureActiveDirectory"]:
            existing_auth["identityProviders"]["azureActiveDirectory"]["validation"] = {}
        validation = existing_auth["identityProviders"]["azureActiveDirectory"]["validation"]

    if client_id is not None:
        registration["clientId"] = client_id
    if client_secret_setting_name is not None:
        registration["clientSecretSettingName"] = client_secret_setting_name
    if client_secret is not None:
        registration["clientSecretSettingName"] = MICROSOFT_SECRET_SETTING_NAME
        set_secrets(cmd, name, resource_group_name, secrets=[f"{MICROSOFT_SECRET_SETTING_NAME}={client_secret}"], no_wait=False, disable_max_length=True)
    if client_secret_setting_name is not None or client_secret is not None:
        fields = ["clientSecretCertificateThumbprint", "clientSecretCertificateSubjectAlternativeName", "clientSecretCertificateIssuer"]
        for field in [f for f in fields if registration.get(f)]:
            registration[field] = None
    if client_secret_certificate_thumbprint is not None:
        registration["clientSecretCertificateThumbprint"] = client_secret_certificate_thumbprint
        fields = ["clientSecretSettingName", "clientSecretCertificateSubjectAlternativeName", "clientSecretCertificateIssuer"]
        for field in [f for f in fields if registration.get(f)]:
            registration[field] = None
    if client_secret_certificate_san is not None:
        registration["clientSecretCertificateSubjectAlternativeName"] = client_secret_certificate_san
    if client_secret_certificate_issuer is not None:
        registration["clientSecretCertificateIssuer"] = client_secret_certificate_issuer
    if client_secret_certificate_san is not None and client_secret_certificate_issuer is not None:
        if "clientSecretSettingName" in registration:
            registration["clientSecretSettingName"] = None
        if "clientSecretCertificateThumbprint" in registration:
            registration["clientSecretCertificateThumbprint"] = None
    if openid_issuer is not None:
        registration["openIdIssuer"] = openid_issuer
    if allowed_token_audiences is not None:
        validation["allowedAudiences"] = allowed_token_audiences.split(",")
        existing_auth["identityProviders"]["azureActiveDirectory"]["validation"] = validation
    if (client_id is not None or client_secret is not None or
            client_secret_setting_name is not None or issuer is not None or
            client_secret_certificate_thumbprint is not None or
            client_secret_certificate_san is not None or
            client_secret_certificate_issuer is not None):
        existing_auth["identityProviders"]["azureActiveDirectory"]["registration"] = registration

    try:
        updated_auth_settings = AuthClient.create_or_update(cmd=cmd, resource_group_name=resource_group_name, container_app_name=name, auth_config_name="current", auth_config_envelope=existing_auth)["properties"]
        return updated_auth_settings["identityProviders"]["azureActiveDirectory"]
    except Exception as e:
        handle_raw_exception(e)


def get_aad_settings(cmd, resource_group_name, name):
    auth_settings = {}
    try:
        auth_settings = AuthClient.get(cmd=cmd, resource_group_name=resource_group_name, container_app_name=name, auth_config_name="current")["properties"]
    except:
        pass
    if "identityProviders" not in auth_settings:
        return {}
    if "azureActiveDirectory" not in auth_settings["identityProviders"]:
        return {}
    return auth_settings["identityProviders"]["azureActiveDirectory"]


def get_facebook_settings(cmd, resource_group_name, name):
    auth_settings = {}
    try:
        auth_settings = AuthClient.get(cmd=cmd, resource_group_name=resource_group_name, container_app_name=name, auth_config_name="current")["properties"]
    except:
        pass
    if "identityProviders" not in auth_settings:
        return {}
    if "facebook" not in auth_settings["identityProviders"]:
        return {}
    return auth_settings["identityProviders"]["facebook"]


def update_facebook_settings(cmd, resource_group_name, name,
                             app_id=None, app_secret_setting_name=None,
                             graph_api_version=None, scopes=None, app_secret=None, yes=False):
    try:
        show_ingress(cmd, name, resource_group_name)
    except Exception as e:
        raise ValidationError("Authentication requires ingress to be enabled for your containerapp.") from e

    if app_secret is not None and app_secret_setting_name is not None:
        raise ArgumentUsageError('Usage Error: --app-secret and --app-secret-setting-name cannot both be configured '
                                 'to non empty strings')

    if app_secret is not None and not yes:
        msg = 'Configuring --client-secret will add a secret to the containerapp. Are you sure you want to continue?'
        if not prompt_y_n(msg, default="n"):
            raise ArgumentUsageError('Usage Error: --client-secret cannot be used without agreeing to add secret '
                                     'to the containerapp.')

    existing_auth = {}
    try:
        existing_auth = AuthClient.get(cmd=cmd, resource_group_name=resource_group_name, container_app_name=name, auth_config_name="current")["properties"]
    except:
        existing_auth = {}
        existing_auth["platform"] = {}
        existing_auth["platform"]["enabled"] = True
        existing_auth["globalValidation"] = {}
        existing_auth["login"] = {}

    registration = {}
    if "identityProviders" not in existing_auth:
        existing_auth["identityProviders"] = {}
    if "facebook" not in existing_auth["identityProviders"]:
        existing_auth["identityProviders"]["facebook"] = {}
    if app_id is not None or app_secret is not None or app_secret_setting_name is not None:
        if "registration" not in existing_auth["identityProviders"]["facebook"]:
            existing_auth["identityProviders"]["facebook"]["registration"] = {}
        registration = existing_auth["identityProviders"]["facebook"]["registration"]
    if scopes is not None:
        if "login" not in existing_auth["identityProviders"]["facebook"]:
            existing_auth["identityProviders"]["facebook"]["login"] = {}

    if app_id is not None:
        registration["appId"] = app_id
    if app_secret_setting_name is not None:
        registration["appSecretSettingName"] = app_secret_setting_name
    if app_secret is not None:
        registration["appSecretSettingName"] = FACEBOOK_SECRET_SETTING_NAME
        set_secrets(cmd, name, resource_group_name, secrets=[f"{FACEBOOK_SECRET_SETTING_NAME}={app_secret}"], no_wait=False, disable_max_length=True)
    if graph_api_version is not None:
        existing_auth["identityProviders"]["facebook"]["graphApiVersion"] = graph_api_version
    if scopes is not None:
        existing_auth["identityProviders"]["facebook"]["login"]["scopes"] = scopes.split(",")
    if app_id is not None or app_secret is not None or app_secret_setting_name is not None:
        existing_auth["identityProviders"]["facebook"]["registration"] = registration

    try:
        updated_auth_settings = AuthClient.create_or_update(cmd=cmd, resource_group_name=resource_group_name, container_app_name=name, auth_config_name="current", auth_config_envelope=existing_auth)["properties"]
        return updated_auth_settings["identityProviders"]["facebook"]
    except Exception as e:
        handle_raw_exception(e)


def get_github_settings(cmd, resource_group_name, name):
    auth_settings = {}
    try:
        auth_settings = AuthClient.get(cmd=cmd, resource_group_name=resource_group_name, container_app_name=name, auth_config_name="current")["properties"]
    except:
        pass
    if "identityProviders" not in auth_settings:
        return {}
    if "gitHub" not in auth_settings["identityProviders"]:
        return {}
    return auth_settings["identityProviders"]["gitHub"]


def update_github_settings(cmd, resource_group_name, name,
                           client_id=None, client_secret_setting_name=None,
                           scopes=None, client_secret=None, yes=False):
    try:
        show_ingress(cmd, name, resource_group_name)
    except Exception as e:
        raise ValidationError("Authentication requires ingress to be enabled for your containerapp.") from e

    if client_secret is not None and client_secret_setting_name is not None:
        raise ArgumentUsageError('Usage Error: --client-secret and --client-secret-setting-name cannot '
                                 'both be configured to non empty strings')

    if client_secret is not None and not yes:
        msg = 'Configuring --client-secret will add a secret to the containerapp. Are you sure you want to continue?'
        if not prompt_y_n(msg, default="n"):
            raise ArgumentUsageError('Usage Error: --client-secret cannot be used without agreeing to add secret '
                                     'to the containerapp.')

    existing_auth = {}
    try:
        existing_auth = AuthClient.get(cmd=cmd, resource_group_name=resource_group_name, container_app_name=name, auth_config_name="current")["properties"]
    except:
        existing_auth = {}
        existing_auth["platform"] = {}
        existing_auth["platform"]["enabled"] = True
        existing_auth["globalValidation"] = {}
        existing_auth["login"] = {}

    registration = {}
    if "identityProviders" not in existing_auth:
        existing_auth["identityProviders"] = {}
    if "gitHub" not in existing_auth["identityProviders"]:
        existing_auth["identityProviders"]["gitHub"] = {}
    if client_id is not None or client_secret is not None or client_secret_setting_name is not None:
        if "registration" not in existing_auth["identityProviders"]["gitHub"]:
            existing_auth["identityProviders"]["gitHub"]["registration"] = {}
        registration = existing_auth["identityProviders"]["gitHub"]["registration"]
    if scopes is not None:
        if "login" not in existing_auth["identityProviders"]["gitHub"]:
            existing_auth["identityProviders"]["gitHub"]["login"] = {}

    if client_id is not None:
        registration["clientId"] = client_id
    if client_secret_setting_name is not None:
        registration["clientSecretSettingName"] = client_secret_setting_name
    if client_secret is not None:
        registration["clientSecretSettingName"] = GITHUB_SECRET_SETTING_NAME
        set_secrets(cmd, name, resource_group_name, secrets=[f"{GITHUB_SECRET_SETTING_NAME}={client_secret}"], no_wait=False, disable_max_length=True)
    if scopes is not None:
        existing_auth["identityProviders"]["gitHub"]["login"]["scopes"] = scopes.split(",")
    if client_id is not None or client_secret is not None or client_secret_setting_name is not None:
        existing_auth["identityProviders"]["gitHub"]["registration"] = registration

    try:
        updated_auth_settings = AuthClient.create_or_update(cmd=cmd, resource_group_name=resource_group_name, container_app_name=name, auth_config_name="current", auth_config_envelope=existing_auth)["properties"]
        return updated_auth_settings["identityProviders"]["gitHub"]
    except Exception as e:
        handle_raw_exception(e)


def get_google_settings(cmd, resource_group_name, name):
    auth_settings = {}
    try:
        auth_settings = AuthClient.get(cmd=cmd, resource_group_name=resource_group_name, container_app_name=name, auth_config_name="current")["properties"]
    except:
        pass
    if "identityProviders" not in auth_settings:
        return {}
    if "google" not in auth_settings["identityProviders"]:
        return {}
    return auth_settings["identityProviders"]["google"]


def update_google_settings(cmd, resource_group_name, name,
                           client_id=None, client_secret_setting_name=None,
                           scopes=None, allowed_token_audiences=None, client_secret=None, yes=False):
    try:
        show_ingress(cmd, name, resource_group_name)
    except Exception as e:
        raise ValidationError("Authentication requires ingress to be enabled for your containerapp.") from e

    if client_secret is not None and client_secret_setting_name is not None:
        raise ArgumentUsageError('Usage Error: --client-secret and --client-secret-setting-name cannot '
                                 'both be configured to non empty strings')

    if client_secret is not None and not yes:
        msg = 'Configuring --client-secret will add a secret to the containerapp. Are you sure you want to continue?'
        if not prompt_y_n(msg, default="n"):
            raise ArgumentUsageError('Usage Error: --client-secret cannot be used without agreeing to add secret '
                                     'to the containerapp.')

    existing_auth = {}
    try:
        existing_auth = AuthClient.get(cmd=cmd, resource_group_name=resource_group_name, container_app_name=name, auth_config_name="current")["properties"]
    except:
        existing_auth = {}
        existing_auth["platform"] = {}
        existing_auth["platform"]["enabled"] = True
        existing_auth["globalValidation"] = {}
        existing_auth["login"] = {}

    registration = {}
    validation = {}
    if "identityProviders" not in existing_auth:
        existing_auth["identityProviders"] = {}
    if "google" not in existing_auth["identityProviders"]:
        existing_auth["identityProviders"]["google"] = {}
    if client_id is not None or client_secret is not None or client_secret_setting_name is not None:
        if "registration" not in existing_auth["identityProviders"]["google"]:
            existing_auth["identityProviders"]["google"]["registration"] = {}
        registration = existing_auth["identityProviders"]["google"]["registration"]
    if scopes is not None:
        if "login" not in existing_auth["identityProviders"]["google"]:
            existing_auth["identityProviders"]["google"]["login"] = {}
    if allowed_token_audiences is not None:
        if "validation" not in existing_auth["identityProviders"]["google"]:
            existing_auth["identityProviders"]["google"]["validation"] = {}

    if client_id is not None:
        registration["clientId"] = client_id
    if client_secret_setting_name is not None:
        registration["clientSecretSettingName"] = client_secret_setting_name
    if client_secret is not None:
        registration["clientSecretSettingName"] = GOOGLE_SECRET_SETTING_NAME
        set_secrets(cmd, name, resource_group_name, secrets=[f"{GOOGLE_SECRET_SETTING_NAME}={client_secret}"], no_wait=False, disable_max_length=True)
    if scopes is not None:
        existing_auth["identityProviders"]["google"]["login"]["scopes"] = scopes.split(",")
    if allowed_token_audiences is not None:
        validation["allowedAudiences"] = allowed_token_audiences.split(",")
        existing_auth["identityProviders"]["google"]["validation"] = validation
    if client_id is not None or client_secret is not None or client_secret_setting_name is not None:
        existing_auth["identityProviders"]["google"]["registration"] = registration

    try:
        updated_auth_settings = AuthClient.create_or_update(cmd=cmd, resource_group_name=resource_group_name, container_app_name=name, auth_config_name="current", auth_config_envelope=existing_auth)["properties"]
        return updated_auth_settings["identityProviders"]["google"]
    except Exception as e:
        handle_raw_exception(e)


def get_twitter_settings(cmd, resource_group_name, name):
    auth_settings = {}
    try:
        auth_settings = AuthClient.get(cmd=cmd, resource_group_name=resource_group_name, container_app_name=name, auth_config_name="current")["properties"]
    except:
        pass
    if "identityProviders" not in auth_settings:
        return {}
    if "twitter" not in auth_settings["identityProviders"]:
        return {}
    return auth_settings["identityProviders"]["twitter"]


def update_twitter_settings(cmd, resource_group_name, name,
                            consumer_key=None, consumer_secret_setting_name=None,
                            consumer_secret=None, yes=False):
    try:
        show_ingress(cmd, name, resource_group_name)
    except Exception as e:
        raise ValidationError("Authentication requires ingress to be enabled for your containerapp.") from e

    if consumer_secret is not None and consumer_secret_setting_name is not None:
        raise ArgumentUsageError('Usage Error: --consumer-secret and --consumer-secret-setting-name cannot '
                                 'both be configured to non empty strings')

    if consumer_secret is not None and not yes:
        msg = 'Configuring --client-secret will add a secret to the containerapp. Are you sure you want to continue?'
        if not prompt_y_n(msg, default="n"):
            raise ArgumentUsageError('Usage Error: --client-secret cannot be used without agreeing to add secret '
                                     'to the containerapp.')

    existing_auth = {}
    try:
        existing_auth = AuthClient.get(cmd=cmd, resource_group_name=resource_group_name, container_app_name=name, auth_config_name="current")["properties"]
    except:
        existing_auth = {}
        existing_auth["platform"] = {}
        existing_auth["platform"]["enabled"] = True
        existing_auth["globalValidation"] = {}
        existing_auth["login"] = {}

    registration = {}
    if "identityProviders" not in existing_auth:
        existing_auth["identityProviders"] = {}
    if "twitter" not in existing_auth["identityProviders"]:
        existing_auth["identityProviders"]["twitter"] = {}
    if consumer_key is not None or consumer_secret is not None or consumer_secret_setting_name is not None:
        if "registration" not in existing_auth["identityProviders"]["twitter"]:
            existing_auth["identityProviders"]["twitter"]["registration"] = {}
        registration = existing_auth["identityProviders"]["twitter"]["registration"]

    if consumer_key is not None:
        registration["consumerKey"] = consumer_key
    if consumer_secret_setting_name is not None:
        registration["consumerSecretSettingName"] = consumer_secret_setting_name
    if consumer_secret is not None:
        registration["consumerSecretSettingName"] = TWITTER_SECRET_SETTING_NAME
        set_secrets(cmd, name, resource_group_name, secrets=[f"{TWITTER_SECRET_SETTING_NAME}={consumer_secret}"], no_wait=False, disable_max_length=True)
    if consumer_key is not None or consumer_secret is not None or consumer_secret_setting_name is not None:
        existing_auth["identityProviders"]["twitter"]["registration"] = registration
    try:
        updated_auth_settings = AuthClient.create_or_update(cmd=cmd, resource_group_name=resource_group_name, container_app_name=name, auth_config_name="current", auth_config_envelope=existing_auth)["properties"]
        return updated_auth_settings["identityProviders"]["twitter"]
    except Exception as e:
        handle_raw_exception(e)


def get_apple_settings(cmd, resource_group_name, name):
    auth_settings = {}
    try:
        auth_settings = AuthClient.get(cmd=cmd, resource_group_name=resource_group_name, container_app_name=name, auth_config_name="current")["properties"]
    except:
        pass
    if "identityProviders" not in auth_settings:
        return {}
    if "apple" not in auth_settings["identityProviders"]:
        return {}
    return auth_settings["identityProviders"]["apple"]


def update_apple_settings(cmd, resource_group_name, name,
                          client_id=None, client_secret_setting_name=None,
                          scopes=None, client_secret=None, yes=False):
    try:
        show_ingress(cmd, name, resource_group_name)
    except Exception as e:
        raise ValidationError("Authentication requires ingress to be enabled for your containerapp.") from e

    if client_secret is not None and client_secret_setting_name is not None:
        raise ArgumentUsageError('Usage Error: --client-secret and --client-secret-setting-name '
                                 'cannot both be configured to non empty strings')

    if client_secret is not None and not yes:
        msg = 'Configuring --client-secret will add a secret to the containerapp. Are you sure you want to continue?'
        if not prompt_y_n(msg, default="n"):
            raise ArgumentUsageError('Usage Error: --client-secret cannot be used without agreeing to add secret '
                                     'to the containerapp.')

    existing_auth = {}
    try:
        existing_auth = AuthClient.get(cmd=cmd, resource_group_name=resource_group_name, container_app_name=name, auth_config_name="current")["properties"]
    except:
        existing_auth = {}
        existing_auth["platform"] = {}
        existing_auth["platform"]["enabled"] = True
        existing_auth["globalValidation"] = {}
        existing_auth["login"] = {}

    registration = {}
    if "identityProviders" not in existing_auth:
        existing_auth["identityProviders"] = {}
    if "apple" not in existing_auth["identityProviders"]:
        existing_auth["identityProviders"]["apple"] = {}
    if client_id is not None or client_secret is not None or client_secret_setting_name is not None:
        if "registration" not in existing_auth["identityProviders"]["apple"]:
            existing_auth["identityProviders"]["apple"]["registration"] = {}
        registration = existing_auth["identityProviders"]["apple"]["registration"]
    if scopes is not None:
        if "login" not in existing_auth["identityProviders"]["apple"]:
            existing_auth["identityProviders"]["apple"]["login"] = {}

    if client_id is not None:
        registration["clientId"] = client_id
    if client_secret_setting_name is not None:
        registration["clientSecretSettingName"] = client_secret_setting_name
    if client_secret is not None:
        registration["clientSecretSettingName"] = APPLE_SECRET_SETTING_NAME
        set_secrets(cmd, name, resource_group_name, secrets=[f"{APPLE_SECRET_SETTING_NAME}={client_secret}"], no_wait=False, disable_max_length=True)
    if scopes is not None:
        existing_auth["identityProviders"]["apple"]["login"]["scopes"] = scopes.split(",")
    if client_id is not None or client_secret is not None or client_secret_setting_name is not None:
        existing_auth["identityProviders"]["apple"]["registration"] = registration

    try:
        updated_auth_settings = AuthClient.create_or_update(cmd=cmd, resource_group_name=resource_group_name, container_app_name=name, auth_config_name="current", auth_config_envelope=existing_auth)["properties"]
        return updated_auth_settings["identityProviders"]["apple"]
    except Exception as e:
        handle_raw_exception(e)


def get_openid_connect_provider_settings(cmd, resource_group_name, name, provider_name):
    auth_settings = {}
    try:
        auth_settings = AuthClient.get(cmd=cmd, resource_group_name=resource_group_name, container_app_name=name, auth_config_name="current")["properties"]
    except:
        pass
    if "identityProviders" not in auth_settings:
        raise ArgumentUsageError('Usage Error: The following custom OpenID Connect provider '
                                 'has not been configured: ' + provider_name)
    if "customOpenIdConnectProviders" not in auth_settings["identityProviders"]:
        raise ArgumentUsageError('Usage Error: The following custom OpenID Connect provider '
                                 'has not been configured: ' + provider_name)
    if provider_name not in auth_settings["identityProviders"]["customOpenIdConnectProviders"]:
        raise ArgumentUsageError('Usage Error: The following custom OpenID Connect provider '
                                 'has not been configured: ' + provider_name)
    return auth_settings["identityProviders"]["customOpenIdConnectProviders"][provider_name]


def add_openid_connect_provider_settings(cmd, resource_group_name, name, provider_name,
                                         client_id=None, client_secret_setting_name=None,
                                         openid_configuration=None, scopes=None,
                                         client_secret=None, yes=False):
    from ._utils import get_oidc_client_setting_app_setting_name
    try:
        show_ingress(cmd, name, resource_group_name)
    except Exception as e:
        raise ValidationError("Authentication requires ingress to be enabled for your containerapp.") from e

    if client_secret is not None and not yes:
        msg = 'Configuring --client-secret will add a secret to the containerapp. Are you sure you want to continue?'
        if not prompt_y_n(msg, default="n"):
            raise ArgumentUsageError('Usage Error: --client-secret cannot be used without agreeing to add secret '
                                     'to the containerapp.')

    auth_settings = {}
    try:
        auth_settings = AuthClient.get(cmd=cmd, resource_group_name=resource_group_name, container_app_name=name, auth_config_name="current")["properties"]
    except:
        auth_settings = {}
        auth_settings["platform"] = {}
        auth_settings["platform"]["enabled"] = True
        auth_settings["globalValidation"] = {}
        auth_settings["login"] = {}

    if "identityProviders" not in auth_settings:
        auth_settings["identityProviders"] = {}
    if "customOpenIdConnectProviders" not in auth_settings["identityProviders"]:
        auth_settings["identityProviders"]["customOpenIdConnectProviders"] = {}
    if provider_name in auth_settings["identityProviders"]["customOpenIdConnectProviders"]:
        raise ArgumentUsageError('Usage Error: The following custom OpenID Connect provider has already been '
                                 'configured: ' + provider_name + '. Please use `az containerapp auth oidc update` to '
                                 'update the provider.')

    final_client_secret_setting_name = client_secret_setting_name
    if client_secret is not None:
        final_client_secret_setting_name = get_oidc_client_setting_app_setting_name(provider_name)
        set_secrets(cmd, name, resource_group_name, secrets=[f"{final_client_secret_setting_name}={client_secret}"], no_wait=True, disable_max_length=True)

    auth_settings["identityProviders"]["customOpenIdConnectProviders"][provider_name] = {
        "registration": {
            "clientId": client_id,
            "clientCredential": {
                "clientSecretSettingName": final_client_secret_setting_name
            },
            "openIdConnectConfiguration": {
                "wellKnownOpenIdConfiguration": openid_configuration
            }
        }
    }
    login = {}
    if scopes is not None:
        login["scopes"] = scopes.split(',')
    else:
        login["scopes"] = ["openid"]

    auth_settings["identityProviders"]["customOpenIdConnectProviders"][provider_name]["login"] = login

    try:
        updated_auth_settings = AuthClient.create_or_update(cmd=cmd, resource_group_name=resource_group_name, container_app_name=name, auth_config_name="current", auth_config_envelope=auth_settings)["properties"]
        return updated_auth_settings["identityProviders"]["customOpenIdConnectProviders"][provider_name]
    except Exception as e:
        handle_raw_exception(e)


def update_openid_connect_provider_settings(cmd, resource_group_name, name, provider_name,
                                            client_id=None, client_secret_setting_name=None,
                                            openid_configuration=None, scopes=None,
                                            client_secret=None, yes=False):
    from ._utils import get_oidc_client_setting_app_setting_name
    try:
        show_ingress(cmd, name, resource_group_name)
    except Exception as e:
        raise ValidationError("Authentication requires ingress to be enabled for your containerapp.") from e

    if client_secret is not None and not yes:
        msg = 'Configuring --client-secret will add a secret to the containerapp. Are you sure you want to continue?'
        if not prompt_y_n(msg, default="n"):
            raise ArgumentUsageError('Usage Error: --client-secret cannot be used without agreeing to add secret '
                                     'to the containerapp.')

    auth_settings = {}
    try:
        auth_settings = AuthClient.get(cmd=cmd, resource_group_name=resource_group_name, container_app_name=name, auth_config_name="current")["properties"]
    except:
        auth_settings = {}
        auth_settings["platform"] = {}
        auth_settings["platform"]["enabled"] = True
        auth_settings["globalValidation"] = {}
        auth_settings["login"] = {}

    if "identityProviders" not in auth_settings:
        raise ArgumentUsageError('Usage Error: The following custom OpenID Connect provider '
                                 'has not been configured: ' + provider_name)
    if "customOpenIdConnectProviders" not in auth_settings["identityProviders"]:
        raise ArgumentUsageError('Usage Error: The following custom OpenID Connect provider '
                                 'has not been configured: ' + provider_name)
    if provider_name not in auth_settings["identityProviders"]["customOpenIdConnectProviders"]:
        raise ArgumentUsageError('Usage Error: The following custom OpenID Connect provider '
                                 'has not been configured: ' + provider_name)

    custom_open_id_connect_providers = auth_settings["identityProviders"]["customOpenIdConnectProviders"]
    registration = {}
    if client_id is not None or client_secret_setting_name is not None or openid_configuration is not None:
        if "registration" not in custom_open_id_connect_providers[provider_name]:
            custom_open_id_connect_providers[provider_name]["registration"] = {}
        registration = custom_open_id_connect_providers[provider_name]["registration"]

    if client_secret_setting_name is not None or client_secret is not None:
        if "clientCredential" not in custom_open_id_connect_providers[provider_name]["registration"]:
            custom_open_id_connect_providers[provider_name]["registration"]["clientCredential"] = {}

    if openid_configuration is not None:
        if "openIdConnectConfiguration" not in custom_open_id_connect_providers[provider_name]["registration"]:
            custom_open_id_connect_providers[provider_name]["registration"]["openIdConnectConfiguration"] = {}

    if scopes is not None:
        if "login" not in auth_settings["identityProviders"]["customOpenIdConnectProviders"][provider_name]:
            custom_open_id_connect_providers[provider_name]["login"] = {}

    if client_id is not None:
        registration["clientId"] = client_id
    if client_secret_setting_name is not None:
        registration["clientCredential"]["clientSecretSettingName"] = client_secret_setting_name
    if client_secret is not None:
        final_client_secret_setting_name = get_oidc_client_setting_app_setting_name(provider_name)
        registration["clientSecretSettingName"] = final_client_secret_setting_name
        set_secrets(cmd, name, resource_group_name, secrets=[f"{final_client_secret_setting_name}={client_secret}"], no_wait=False, disable_max_length=True)
    if openid_configuration is not None:
        registration["openIdConnectConfiguration"]["wellKnownOpenIdConfiguration"] = openid_configuration
    if scopes is not None:
        custom_open_id_connect_providers[provider_name]["login"]["scopes"] = scopes.split(",")
    if client_id is not None or client_secret_setting_name is not None or openid_configuration is not None:
        custom_open_id_connect_providers[provider_name]["registration"] = registration
    auth_settings["identityProviders"]["customOpenIdConnectProviders"] = custom_open_id_connect_providers

    try:
        updated_auth_settings = AuthClient.create_or_update(cmd=cmd, resource_group_name=resource_group_name, container_app_name=name, auth_config_name="current", auth_config_envelope=auth_settings)["properties"]
        return updated_auth_settings["identityProviders"]["customOpenIdConnectProviders"][provider_name]
    except Exception as e:
        handle_raw_exception(e)


def remove_openid_connect_provider_settings(cmd, resource_group_name, name, provider_name):
    auth_settings = {}
    try:
        auth_settings = AuthClient.get(cmd=cmd, resource_group_name=resource_group_name, container_app_name=name, auth_config_name="current")["properties"]
    except:
        pass
    if "identityProviders" not in auth_settings:
        raise ArgumentUsageError('Usage Error: The following custom OpenID Connect provider '
                                 'has not been configured: ' + provider_name)
    if "customOpenIdConnectProviders" not in auth_settings["identityProviders"]:
        raise ArgumentUsageError('Usage Error: The following custom OpenID Connect provider '
                                 'has not been configured: ' + provider_name)
    if provider_name not in auth_settings["identityProviders"]["customOpenIdConnectProviders"]:
        raise ArgumentUsageError('Usage Error: The following custom OpenID Connect provider '
                                 'has not been configured: ' + provider_name)
    auth_settings["identityProviders"]["customOpenIdConnectProviders"].pop(provider_name, None)
    try:
        AuthClient.create_or_update(cmd=cmd, resource_group_name=resource_group_name, container_app_name=name, auth_config_name="current", auth_config_envelope=auth_settings)
        return {}
    except Exception as e:
        handle_raw_exception(e)


def update_auth_config(cmd, resource_group_name, name, set_string=None, enabled=None,
                       runtime_version=None, config_file_path=None, unauthenticated_client_action=None,
                       redirect_provider=None, require_https=None,
                       proxy_convention=None, proxy_custom_host_header=None,
                       proxy_custom_proto_header=None, excluded_paths=None,
                       token_store=None, sas_url_secret=None, sas_url_secret_name=None,
                       yes=False):
    raw_parameters = locals()
    containerapp_auth_decorator = ContainerAppAuthDecorator(
        cmd=cmd,
        client=AuthClient,
        raw_parameters=raw_parameters,
        models=CONTAINER_APPS_SDK_MODELS
    )

    containerapp_auth_decorator.construct_payload()
    # Set secretes will add a secret to the containerapp
    if containerapp_auth_decorator.get_argument_token_store() and containerapp_auth_decorator.get_argument_sas_url_secret() is not None:
        if not containerapp_auth_decorator.get_argument_yes():
            msg = 'Configuring --sas-url-secret will add a secret to the containerapp. Are you sure you want to continue?'
            if not prompt_y_n(msg, default="n"):
                raise ArgumentUsageError(
                    'Usage Error: --sas-url-secret cannot be used without agreeing to add secret to the containerapp.')
        set_secrets(cmd, name, resource_group_name, secrets=[f"{BLOB_STORAGE_TOKEN_STORE_SECRET_SETTING_NAME}={containerapp_auth_decorator.get_argument_sas_url_secret()}"], no_wait=False, disable_max_length=True)
    return containerapp_auth_decorator.create_or_update()


def show_auth_config(cmd, resource_group_name, name):
    raw_parameters = locals()
    containerapp_auth_decorator = ContainerAppAuthDecorator(
        cmd=cmd,
        client=AuthClient,
        raw_parameters=raw_parameters,
        models=CONTAINER_APPS_SDK_MODELS
    )

    return containerapp_auth_decorator.show()


# Compose
def create_containerapps_from_compose(cmd,  # pylint: disable=R0914
                                      resource_group_name,
                                      managed_env,
                                      compose_file_path='./docker-compose.yml',
                                      registry_server=None,
                                      registry_user=None,
                                      registry_pass=None,
                                      transport_mapping=None,
                                      location=None,
                                      tags=None):
    from pycomposefile import ComposeFile

    from ._compose_utils import (create_containerapps_compose_environment,
                                 build_containerapp_from_compose_service,
                                 check_supported_platform,
                                 warn_about_unsupported_elements,
                                 resolve_ingress_and_target_port,
                                 resolve_registry_from_cli_args,
                                 resolve_transport_from_cli_args,
                                 resolve_service_startup_command,
                                 validate_memory_and_cpu_setting,
                                 resolve_cpu_configuration_from_service,
                                 resolve_memory_configuration_from_service,
                                 resolve_replicas_from_service,
                                 resolve_environment_from_service,
                                 resolve_secret_from_service)

    # Validate managed environment
    parsed_managed_env = parse_resource_id(managed_env)
    managed_env_name = parsed_managed_env['name']

    env_rg = parsed_managed_env.get('resource_group', resource_group_name)

    try:
        managed_environment = show_managed_environment(cmd=cmd,
                                                       name=managed_env_name,
                                                       resource_group_name=env_rg)
    except CLIInternalError:  # pylint: disable=W0702
        logger.info(  # pylint: disable=W1203
            f"Creating the Container Apps managed environment {managed_env_name} under {env_rg} in {location}.")
        managed_environment = create_containerapps_compose_environment(cmd,
                                                                       managed_env_name,
                                                                       env_rg,
                                                                       tags=tags,
                                                                       location=location)

    compose_yaml = load_yaml_file(compose_file_path)
    parsed_compose_file = ComposeFile(compose_yaml)
    logger.info(parsed_compose_file)
    containerapps_from_compose = []
    # Using the key to iterate to get the service name
    # pylint: disable=C0201,C0206
    for service_name in parsed_compose_file.ordered_services.keys():
        service = parsed_compose_file.services[service_name]
        if not check_supported_platform(service.platform):
            message = "Unsupported platform found. "
            message += "Azure Container Apps only supports linux/amd64 container images."
            raise InvalidArgumentValueError(message)
        image = service.image
        warn_about_unsupported_elements(service)
        logger.info(  # pylint: disable=W1203
            f"Creating the Container Apps instance for {service_name} under {resource_group_name} in {location}.")
        ingress_type, target_port = resolve_ingress_and_target_port(service)
        registry, registry_username, registry_password = resolve_registry_from_cli_args(registry_server, registry_user, registry_pass)  # pylint: disable=C0301
        transport_setting = resolve_transport_from_cli_args(service_name, transport_mapping)
        startup_command, startup_args = resolve_service_startup_command(service)
        cpu, memory = validate_memory_and_cpu_setting(
            resolve_cpu_configuration_from_service(service),
            resolve_memory_configuration_from_service(service),
            managed_environment
        )
        replicas = resolve_replicas_from_service(service)
        environment = resolve_environment_from_service(service)
        secret_vars, secret_env_ref = resolve_secret_from_service(service, parsed_compose_file.secrets)
        if environment is not None and secret_env_ref is not None:
            environment.extend(secret_env_ref)
        elif secret_env_ref is not None:
            environment = secret_env_ref
        if service.build is not None:
            logger.warning("Build configuration defined for this service.")
            logger.warning("The build will be performed by Azure Container Registry.")
            context = service.build.context
            dockerfile = "Dockerfile"
            if service.build.dockerfile is not None:
                dockerfile = service.build.dockerfile
            image, registry, registry_username, registry_password = build_containerapp_from_compose_service(
                cmd,
                service_name,
                context,
                dockerfile,
                resource_group_name,
                managed_env,
                location,
                image,
                target_port,
                ingress_type,
                registry,
                registry_username,
                registry_password,
                environment)
        containerapps_from_compose.append(
            create_containerapp(cmd,
                                service_name,
                                resource_group_name,
                                image=image,
                                container_name=service.container_name,
                                managed_env=managed_environment["id"],
                                ingress=ingress_type,
                                target_port=target_port,
                                registry_server=registry,
                                registry_user=registry_username,
                                registry_pass=registry_password,
                                transport=transport_setting,
                                startup_command=startup_command,
                                args=startup_args,
                                cpu=cpu,
                                memory=memory,
                                env_vars=environment,
                                secrets=secret_vars,
                                min_replicas=replicas,
                                max_replicas=replicas, )
        )
    return containerapps_from_compose


def list_supported_workload_profiles(cmd, location):
    return WorkloadProfileClient.list_supported(cmd, location)


def list_workload_profiles(cmd, resource_group_name, env_name):
    return WorkloadProfileClient.list(cmd, resource_group_name, env_name)


def show_workload_profile(cmd, resource_group_name, env_name, workload_profile_name):
    workload_profiles = WorkloadProfileClient.list(cmd, resource_group_name, env_name)
    profile = [p for p in workload_profiles if p["name"].lower() == workload_profile_name.lower()]
    if not profile:
        raise ValidationError(f"No such workload profile found on the environment. The workload profile(s) on the environment are: {','.join([p['name'] for p in workload_profiles])}")
    return profile[0]


def set_workload_profile(cmd, resource_group_name, env_name, workload_profile_name, workload_profile_type=None, min_nodes=None, max_nodes=None):
    return update_managed_environment(cmd, env_name, resource_group_name, workload_profile_type=workload_profile_type, workload_profile_name=workload_profile_name, min_nodes=min_nodes, max_nodes=max_nodes)


def add_workload_profile(cmd, resource_group_name, env_name, workload_profile_name, workload_profile_type=None, min_nodes=None, max_nodes=None):
    r = None
    try:
        r = ManagedEnvironmentClient.show(cmd=cmd, resource_group_name=resource_group_name, name=env_name)
    except CLIError as e:
        handle_raw_exception(e)

    if r and safe_get(r, "properties", "workloadProfiles") is None:
        raise ValidationError("Cannot add workload profile because the environment doesn't enable workload profile.\n"
                              "If you want to use Consumption and Dedicated environment, please create a new one with 'az containerapp env create'.")

    workload_profiles = r["properties"]["workloadProfiles"]

    workload_profiles_lower = [p["name"].lower() for p in workload_profiles]

    if workload_profile_name.lower() in workload_profiles_lower:
        raise ValidationError(f"Cannot add workload profile with name {workload_profile_name} because it already exists in this environment")

    return update_managed_environment(cmd, env_name, resource_group_name, workload_profile_type=workload_profile_type, workload_profile_name=workload_profile_name, min_nodes=min_nodes, max_nodes=max_nodes)


def update_workload_profile(cmd, resource_group_name, env_name, workload_profile_name, min_nodes=None, max_nodes=None):
    r = None
    try:
        r = ManagedEnvironmentClient.show(cmd=cmd, resource_group_name=resource_group_name, name=env_name)
    except CLIError as e:
        handle_raw_exception(e)

    if r and safe_get(r, "properties", "workloadProfiles") is None:
        raise ValidationError("Cannot update workload profile because the environment doesn't enable workload profile.\n"
                              "If you want to use Consumption and Dedicated environment, please create a new one with 'az containerapp env create'.")

    workload_profiles = r["properties"]["workloadProfiles"]

    workload_profiles_lower = [p["name"].lower() for p in workload_profiles]

    if workload_profile_name.lower() not in workload_profiles_lower:
        raise ValidationError(f"Workload profile with name {workload_profile_name} does not exist in this environment. The workload profiles available in this environment are {','.join([p['name'] for p in workload_profiles])}")

    return update_managed_environment(cmd, env_name, resource_group_name, workload_profile_name=workload_profile_name, min_nodes=min_nodes, max_nodes=max_nodes)


def delete_workload_profile(cmd, resource_group_name, env_name, workload_profile_name):
    try:
        r = ManagedEnvironmentClient.show(cmd=cmd, resource_group_name=resource_group_name, name=env_name)
    except CLIError as e:
        handle_raw_exception(e)

    if "workloadProfiles" not in r["properties"] or not r["properties"]["workloadProfiles"]:
        raise ValidationError("This environment does not allow for workload profiles. Can create a compatible environment with 'az containerapp env create --enable-workload-profiles'")

    if workload_profile_name.lower() == "consumption":
        raise ValidationError("Cannot delete the 'Consumption' workload profile")

    workload_profiles = [p for p in r["properties"]["workloadProfiles"] if p["name"].lower() != workload_profile_name.lower()]

    managed_env_def = {}
    safe_set(managed_env_def, "properties", "workloadProfiles", value=workload_profiles)
    try:
        r = ManagedEnvironmentClient.update(
            cmd=cmd, resource_group_name=resource_group_name, name=env_name, managed_environment_envelope=managed_env_def)

        return r
    except Exception as e:
        handle_raw_exception(e)


def create_http_route_config(cmd, resource_group_name, name, http_route_config_name, yaml):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)
    yaml_http_route_config = load_yaml_file(yaml)
    # check if the type is dict
    if not isinstance(yaml_http_route_config, dict):
        raise ValidationError('Invalid YAML provided. Please see https://aka.ms/azure-container-apps-yaml for a valid YAML spec.')

    http_route_config_envelope = {"properties": yaml_http_route_config}

    try:
        return HttpRouteConfigClient.create(cmd, resource_group_name, name, http_route_config_name, http_route_config_envelope)
    except Exception as e:
        handle_raw_exception(e)


def update_http_route_config(cmd, resource_group_name, name, http_route_config_name, yaml):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)
    yaml_http_route_config = load_yaml_file(yaml)
    # check if the type is dict
    if not isinstance(yaml_http_route_config, dict):
        raise ValidationError('Invalid YAML provided. Please see https://aka.ms/azure-container-apps-yaml for a valid YAML spec.')

    http_route_config_envelope = {"properties": yaml_http_route_config}

    try:
        return HttpRouteConfigClient.update(cmd, resource_group_name, name, http_route_config_name, http_route_config_envelope)
    except Exception as e:
        handle_raw_exception(e)


def list_http_route_configs(cmd, resource_group_name, name):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)
    try:
        return HttpRouteConfigClient.list(cmd, resource_group_name, name)
    except Exception as e:
        handle_raw_exception(e)


def show_http_route_config(cmd, resource_group_name, name, http_route_config_name):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)
    try:
        return HttpRouteConfigClient.show(cmd, resource_group_name, name, http_route_config_name)
    except Exception as e:
        handle_raw_exception(e)


def delete_http_route_config(cmd, resource_group_name, name, http_route_config_name):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)
    try:
        return HttpRouteConfigClient.delete(cmd, resource_group_name, name, http_route_config_name)
    except Exception as e:
        handle_raw_exception(e)


def show_environment_premium_ingress(cmd, name, resource_group_name):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)

    try:
        env = ManagedEnvironmentClient.show(cmd, resource_group_name, name)
        ingress_config = safe_get(env, "properties", "ingressConfiguration")
        if not ingress_config:
            return {"message": "No premium ingress configuration found for this environment, using default values."}

        return ingress_config
    except Exception as e:
        handle_raw_exception(e)


def add_environment_premium_ingress(cmd, name, resource_group_name, workload_profile_name, termination_grace_period=None, request_idle_timeout=None, header_count_limit=None, no_wait=False):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)

    try:
        ManagedEnvironmentClient.show(cmd, resource_group_name, name)
        env_patch = {}
        ingress_config = {}
        safe_set(env_patch, "properties", "ingressConfiguration", value=ingress_config)

        # Required
        ingress_config["workloadProfileName"] = workload_profile_name
        # Optional, remove if None
        ingress_config["terminationGracePeriodSeconds"] = termination_grace_period
        ingress_config["requestIdleTimeout"] = request_idle_timeout
        ingress_config["headerCountLimit"] = header_count_limit

        result = ManagedEnvironmentClient.update(
            cmd=cmd,
            resource_group_name=resource_group_name,
            name=name,
            managed_environment_envelope=env_patch,
            no_wait=no_wait
        )

        return safe_get(result, "properties", "ingressConfiguration")

    except Exception as e:
        handle_raw_exception(e)


def update_environment_premium_ingress(cmd, name, resource_group_name, workload_profile_name=None, termination_grace_period=None, request_idle_timeout=None, header_count_limit=None, no_wait=False):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)

    try:
        ManagedEnvironmentClient.show(cmd, resource_group_name, name)
        env_patch = {}
        ingress_config = {}

        if workload_profile_name is not None:
            ingress_config["workloadProfileName"] = workload_profile_name
        if termination_grace_period is not None:
            ingress_config["terminationGracePeriodSeconds"] = termination_grace_period
        if request_idle_timeout is not None:
            ingress_config["requestIdleTimeout"] = request_idle_timeout
        if header_count_limit is not None:
            ingress_config["headerCountLimit"] = header_count_limit

        # Only add ingressConfiguration to the patch if any values were specified
        if ingress_config:
            safe_set(env_patch, "properties", "ingressConfiguration", value=ingress_config)
        else:
            return {"message": "No changes specified for premium ingress configuration"}

        # Update the environment with the patched ingress configuration
        result = ManagedEnvironmentClient.update(
            cmd=cmd,
            resource_group_name=resource_group_name,
            name=name,
            managed_environment_envelope=env_patch,
            no_wait=no_wait
        )

        return safe_get(result, "properties", "ingressConfiguration")

    except Exception as e:
        handle_raw_exception(e)


def remove_environment_premium_ingress(cmd, name, resource_group_name, no_wait=False):
    _validate_subscription_registered(cmd, CONTAINER_APPS_RP)

    try:
        ManagedEnvironmentClient.show(cmd, resource_group_name, name)
        env_patch = {}
        # Remove the whole section to restore defaults
        safe_set(env_patch, "properties", "ingressConfiguration", value=None)

        ManagedEnvironmentClient.update(
            cmd=cmd,
            resource_group_name=resource_group_name,
            name=name,
            managed_environment_envelope=env_patch,
            no_wait=no_wait
        )

    except Exception as e:
        handle_raw_exception(e)
