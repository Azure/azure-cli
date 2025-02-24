# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long, consider-using-f-string, no-else-return, duplicate-string-formatting-argument, expression-not-assigned, too-many-locals, logging-fstring-interpolation, broad-except, pointless-statement, bare-except, too-many-public-methods, logging-format-interpolation, too-many-boolean-expressions, too-many-branches, useless-parent-delegation
from copy import deepcopy
from typing import Dict, Any

from azure.cli.core.commands import AzCliCommand

import time

from azure.cli.core.azclierror import (
    RequiredArgumentMissingError,
    ValidationError)
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.mgmt.core.tools import parse_resource_id, is_valid_resource_id

from knack.log import get_logger
from knack.util import CLIError

from msrest.exceptions import DeserializationError

from .base_resource import BaseResource
from ._clients import ManagedEnvironmentClient
from ._client_factory import handle_raw_exception, handle_non_404_status_code_exception

from ._models import (
    Ingress as IngressModel,
    Configuration as ConfigurationModel,
    Template as TemplateModel,
    RegistryCredentials as RegistryCredentialsModel,
    ContainerApp as ContainerAppModel,
    Dapr as DaprModel,
    ContainerResources as ContainerResourcesModel,
    Scale as ScaleModel,
    Container as ContainerModel,
    ManagedServiceIdentity as ManagedServiceIdentityModel,
    ScaleRule as ScaleRuleModel,
    Volume as VolumeModel,
    VolumeMount as VolumeMountModel)

from ._decorator_utils import (create_deserializer,
                               process_loaded_yaml,
                               load_yaml_file)
from ._utils import (_ensure_location_allowed,
                     parse_secret_flags, store_as_secret_and_return_secret_ref, parse_env_var_flags,
                     _convert_object_from_snake_to_camel_case,
                     _object_to_dict, _remove_additional_attributes,
                     _remove_readonly_attributes,
                     _infer_acr_credentials,
                     _ensure_identity_resource_id,
                     validate_container_app_name,
                     set_managed_identity,
                     create_acrpull_role_assignment, is_registry_msi_system,
                     safe_set, parse_metadata_flags, parse_auth_flags,
                     get_default_workload_profile_name_from_env,
                     ensure_workload_profile_supported, _generate_secret_volume_name,
                     AppType,
                     safe_get)
from ._validators import validate_create, validate_revision_suffix

from ._constants import (CONTAINER_APPS_RP,
                         HELLO_WORLD_IMAGE)

logger = get_logger(__name__)


class BaseContainerAppDecorator(BaseResource):
    def __init__(self, cmd: AzCliCommand, client: Any, raw_parameters: Dict, models: str):
        super().__init__(cmd, client, raw_parameters, models)

    def list(self):
        containerapps = super().list()
        managed_env = self.get_argument_managed_env()
        if managed_env:
            env_name = parse_resource_id(managed_env)["name"].lower()
            if "resource_group" in parse_resource_id(managed_env):
                self.get_environment_client().show(self.cmd, parse_resource_id(managed_env)["resource_group"],
                                                   parse_resource_id(managed_env)["name"])
                containerapps = [c for c in containerapps if
                                 c["properties"]["environmentId"].lower() == managed_env.lower()]
            else:
                containerapps = [c for c in containerapps if
                                 parse_resource_id(c["properties"]["environmentId"])["name"].lower() == env_name]

        return containerapps

    def show(self):
        try:
            r = super().show()
            if self.get_param("show_secrets"):
                self.set_up_get_existing_secrets(r)
            return r
        except CLIError as e:
            handle_raw_exception(e)

    def get_environment_client(self):
        return ManagedEnvironmentClient

    def set_up_get_existing_secrets(self, containerapp_def):
        if "secrets" not in containerapp_def["properties"]["configuration"]:
            containerapp_def["properties"]["configuration"]["secrets"] = []
        else:
            secrets = None
            try:
                secrets = self.client.list_secrets(cmd=self.cmd, resource_group_name=self.get_argument_resource_group_name(), name=self.get_argument_name())
            except Exception as e:  # pylint: disable=broad-except
                handle_raw_exception(e)

            containerapp_def["properties"]["configuration"]["secrets"] = secrets["value"]
            safe_set(containerapp_def, "properties", "configuration", "secrets", value=secrets["value"])

    def get_param(self, key) -> Any:
        return self.raw_param.get(key)

    def set_param(self, key, value):
        self.raw_param[key] = value

    def get_argument_name(self):
        return self.get_param("name")

    def get_argument_resource_group_name(self):
        return self.get_param("resource_group_name")

    def get_argument_no_wait(self):
        return self.get_param("no_wait")

    def get_argument_yaml(self):
        return self.get_param("yaml")

    def get_argument_image(self):
        return self.get_param("image")

    def set_argument_image(self, image):
        self.set_param("image", image)

    def get_argument_container_name(self):
        return self.get_param("container_name")

    def get_argument_managed_env(self):
        return self.get_param("managed_env")

    def set_argument_managed_env(self, managed_env):
        self.set_param("managed_env", managed_env)

    def get_argument_min_replicas(self):
        return self.get_param("min_replicas")

    def get_argument_max_replicas(self):
        return self.get_param("max_replicas")

    def get_argument_scale_rule_name(self):
        return self.get_param("scale_rule_name")

    def get_argument_scale_rule_type(self):
        return self.get_param("scale_rule_type")

    def set_argument_scale_rule_type(self, scale_rule_type):
        self.set_param("scale_rule_type", scale_rule_type)

    def get_argument_scale_rule_http_concurrency(self):
        return self.get_param("scale_rule_http_concurrency")

    def get_argument_scale_rule_metadata(self):
        return self.get_param("scale_rule_metadata")

    def get_argument_scale_rule_auth(self):
        return self.get_param("scale_rule_auth")

    def get_argument_target_port(self):
        return self.get_param("target_port")

    def get_argument_exposed_port(self):
        return self.get_param("exposed_port")

    def get_argument_transport(self):
        return self.get_param("transport")

    def get_argument_ingress(self):
        return self.get_param("ingress")

    def get_argument_allow_insecure(self):
        return self.get_param("allow_insecure")

    def get_argument_revisions_mode(self):
        return self.get_param("revisions_mode")

    def get_argument_secrets(self):
        return self.get_param("secrets")

    def get_argument_env_vars(self):
        return self.get_param("env_vars")

    def get_argument_cpu(self):
        return self.get_param("cpu")

    def get_argument_memory(self):
        return self.get_param("memory")

    def get_argument_registry_server(self):
        return self.get_param("registry_server")

    def get_argument_registry_user(self):
        return self.get_param("registry_user")

    def set_argument_registry_user(self, registry_user):
        self.set_param("registry_user", registry_user)

    def get_argument_registry_pass(self):
        return self.get_param("registry_pass")

    def set_argument_registry_pass(self, registry_pass):
        self.set_param("registry_pass", registry_pass)

    def get_argument_dapr_enabled(self):
        return self.get_param("dapr_enabled")

    def get_argument_dapr_app_port(self):
        return self.get_param("dapr_app_port")

    def get_argument_dapr_app_id(self):
        return self.get_param("dapr_app_id")

    def get_argument_dapr_app_protocol(self):
        return self.get_param("dapr_app_protocol")

    def get_argument_dapr_http_read_buffer_size(self):
        return self.get_param("dapr_http_read_buffer_size")

    def get_argument_dapr_http_max_request_size(self):
        return self.get_param("dapr_http_max_request_size")

    def get_argument_dapr_log_level(self):
        return self.get_param("dapr_log_level")

    def get_argument_dapr_enable_api_logging(self):
        return self.get_param("dapr_enable_api_logging")

    def get_argument_revision_suffix(self):
        return self.get_param("revision_suffix")

    def get_argument_startup_command(self):
        return self.get_param("startup_command")

    def get_argument_args(self):
        return self.get_param("args")

    def get_argument_tags(self):
        return self.get_param("tags")

    def get_argument_system_assigned(self):
        return self.get_param("system_assigned")

    def get_argument_disable_warnings(self):
        return self.get_param("disable_warnings")

    def get_argument_user_assigned(self):
        return self.get_param("user_assigned")

    def get_argument_registry_identity(self):
        return self.get_param("registry_identity")

    def get_argument_workload_profile_name(self):
        return self.get_param("workload_profile_name")

    def set_argument_workload_profile_name(self, workload_profile_name):
        self.set_param("workload_profile_name", workload_profile_name)

    def get_argument_secret_volume_mount(self):
        return self.get_param("secret_volume_mount")

    def get_argument_termination_grace_period(self):
        return self.get_param("termination_grace_period")


class ContainerAppCreateDecorator(BaseContainerAppDecorator):
    def __init__(
        self, cmd: AzCliCommand, client: Any, raw_parameters: Dict, models: str
    ):
        super().__init__(cmd, client, raw_parameters, models)
        self.containerapp_def = deepcopy(ContainerAppModel)

    def validate_arguments(self):
        validate_container_app_name(self.get_argument_name(), AppType.ContainerApp.name)
        validate_create(self.get_argument_registry_identity(), self.get_argument_registry_pass(), self.get_argument_registry_user(), self.get_argument_registry_server(), self.get_argument_no_wait())
        validate_revision_suffix(self.get_argument_revision_suffix())

    def construct_payload(self):
        if self.get_argument_registry_identity() and not is_registry_msi_system(self.get_argument_registry_identity()):
            logger.info("Creating an acrpull role assignment for the registry identity")
            create_acrpull_role_assignment(self.cmd, self.get_argument_registry_server(), self.get_argument_registry_identity(), skip_error=True)

        if self.get_argument_yaml():
            return self.set_up_create_containerapp_yaml(name=self.get_argument_name(), file_name=self.get_argument_yaml())

        if not self.get_argument_image():
            self.set_argument_image(HELLO_WORLD_IMAGE)

        if self.get_argument_managed_env() is None:
            raise RequiredArgumentMissingError('Usage error: --environment is required if not using --yaml')

        # Validate managed environment
        parsed_managed_env = parse_resource_id(self.get_argument_managed_env())
        managed_env_name = parsed_managed_env['name']
        managed_env_rg = parsed_managed_env['resource_group']
        managed_env_info = None

        try:
            managed_env_info = self.get_environment_client().show(cmd=self.cmd, resource_group_name=managed_env_rg, name=managed_env_name)
        except Exception as e:
            handle_non_404_status_code_exception(e)

        if not managed_env_info:
            raise ValidationError("The environment '{}' does not exist. Specify a valid environment".format(self.get_argument_managed_env()))

        while not self.get_argument_no_wait() and safe_get(managed_env_info, "properties", "provisioningState", default="").lower() in ["inprogress", "updating"]:
            logger.info("Waiting for environment provisioning to finish before creating container app")
            time.sleep(5)
            managed_env_info = self.get_environment_client().show(cmd=self.cmd, resource_group_name=managed_env_rg, name=managed_env_name)

        location = managed_env_info["location"]
        _ensure_location_allowed(self.cmd, location, CONTAINER_APPS_RP, "containerApps")

        if not self.get_argument_workload_profile_name() and "workloadProfiles" in managed_env_info:
            workload_profile_name = get_default_workload_profile_name_from_env(self.cmd, managed_env_info, managed_env_rg)
            self.set_argument_workload_profile_name(workload_profile_name)

        external_ingress = None
        if self.get_argument_ingress() is not None:
            if self.get_argument_ingress().lower() == "internal":
                external_ingress = False
            elif self.get_argument_ingress().lower() == "external":
                external_ingress = True

        ingress_def = None
        if self.get_argument_ingress() is not None:
            ingress_def = deepcopy(IngressModel)
            ingress_def["external"] = external_ingress
            ingress_def["transport"] = self.get_argument_transport()
            ingress_def["exposedPort"] = self.get_argument_exposed_port() if self.get_argument_transport() == "tcp" else None
            ingress_def["allowInsecure"] = self.get_argument_allow_insecure()

            if self.get_argument_target_port() is not None:
                ingress_def["targetPort"] = self.get_argument_target_port()

        secrets_def = None
        if self.get_argument_secrets() is not None:
            secrets_def = parse_secret_flags(self.get_argument_secrets())

        registries_def = None
        if self.get_argument_registry_server() is not None and not is_registry_msi_system(self.get_argument_registry_identity()):
            registries_def = deepcopy(RegistryCredentialsModel)
            registries_def["server"] = self.get_argument_registry_server()

            # Infer credentials if not supplied and its azurecr
            if (self.get_argument_registry_user() is None or self.get_argument_registry_pass() is None) and self.get_argument_registry_identity() is None:
                registry_user, registry_pass = _infer_acr_credentials(self.cmd, self.get_argument_registry_server(), self.get_argument_disable_warnings())
                self.set_argument_registry_user(registry_user)
                self.set_argument_registry_pass(registry_pass)

            if not self.get_argument_registry_identity():
                registries_def["username"] = self.get_argument_registry_user()

                if secrets_def is None:
                    secrets_def = []
                registries_def["passwordSecretRef"] = store_as_secret_and_return_secret_ref(secrets_def, self.get_argument_registry_user(),
                                                                                            self.get_argument_registry_server(),
                                                                                            self.get_argument_registry_pass(),
                                                                                            disable_warnings=self.get_argument_disable_warnings())
            else:
                registries_def["identity"] = self.get_argument_registry_identity()

        dapr_def = None
        if self.get_argument_dapr_enabled():
            dapr_def = deepcopy(DaprModel)
            dapr_def["enabled"] = True
            dapr_def["appId"] = self.get_argument_dapr_app_id()
            dapr_def["appPort"] = self.get_argument_dapr_app_port()
            dapr_def["appProtocol"] = self.get_argument_dapr_app_protocol()
            dapr_def["httpReadBufferSize"] = self.get_argument_dapr_http_read_buffer_size()
            dapr_def["httpMaxRequestSize"] = self.get_argument_dapr_http_max_request_size()
            dapr_def["logLevel"] = self.get_argument_dapr_log_level()
            dapr_def["enableApiLogging"] = self.get_argument_dapr_enable_api_logging()

        config_def = deepcopy(ConfigurationModel)
        config_def["secrets"] = secrets_def
        config_def["activeRevisionsMode"] = self.get_argument_revisions_mode()
        config_def["ingress"] = ingress_def
        config_def["registries"] = [registries_def] if registries_def is not None else None
        config_def["dapr"] = dapr_def

        # Identity actions
        identity_def = deepcopy(ManagedServiceIdentityModel)
        identity_def["type"] = "None"

        assign_system_identity = self.get_argument_system_assigned()
        if self.get_argument_user_assigned():
            assign_user_identities = [x.lower() for x in self.get_argument_user_assigned()]
        else:
            assign_user_identities = []

        if assign_system_identity and assign_user_identities:
            identity_def["type"] = "SystemAssigned, UserAssigned"
        elif assign_system_identity:
            identity_def["type"] = "SystemAssigned"
        elif assign_user_identities:
            identity_def["type"] = "UserAssigned"

        if assign_user_identities:
            identity_def["userAssignedIdentities"] = {}
            subscription_id = get_subscription_id(self.cmd.cli_ctx)

            for r in assign_user_identities:
                r = _ensure_identity_resource_id(subscription_id, self.get_argument_resource_group_name(), r)
                identity_def["userAssignedIdentities"][r] = {}  # pylint: disable=unsupported-assignment-operation

        scale_def = self.set_up_scale_rule()

        resources_def = None
        if self.get_argument_cpu() is not None or self.get_argument_memory() is not None:
            resources_def = deepcopy(ContainerResourcesModel)
            resources_def["cpu"] = self.get_argument_cpu()
            resources_def["memory"] = self.get_argument_memory()

        container_def = deepcopy(ContainerModel)
        container_def["name"] = self.get_argument_container_name() if self.get_argument_container_name() else self.get_argument_name()
        container_def["image"] = self.get_argument_image() if not is_registry_msi_system(self.get_argument_registry_identity()) else HELLO_WORLD_IMAGE
        if self.get_argument_env_vars() is not None:
            container_def["env"] = parse_env_var_flags(self.get_argument_env_vars())
        if self.get_argument_startup_command() is not None:
            container_def["command"] = self.get_argument_startup_command()
        if self.get_argument_args() is not None:
            container_def["args"] = self.get_argument_args()
        if resources_def is not None:
            container_def["resources"] = resources_def

        template_def = deepcopy(TemplateModel)

        template_def["containers"] = [container_def]
        template_def["scale"] = scale_def

        if self.get_argument_secret_volume_mount() is not None:
            volume_def = deepcopy(VolumeModel)
            volume_mount_def = deepcopy(VolumeMountModel)
            # generate a volume name
            volume_def["name"] = _generate_secret_volume_name()
            volume_def["storageType"] = "Secret"

            # mount the volume to the container
            volume_mount_def["volumeName"] = volume_def["name"]
            volume_mount_def["mountPath"] = self.get_argument_secret_volume_mount()
            container_def["volumeMounts"] = [volume_mount_def]
            template_def["volumes"] = [volume_def]

        if self.get_argument_revision_suffix() is not None and not is_registry_msi_system(self.get_argument_registry_identity()):
            template_def["revisionSuffix"] = self.get_argument_revision_suffix()

        if self.get_argument_termination_grace_period() is not None:
            template_def["terminationGracePeriodSeconds"] = self.get_argument_termination_grace_period()

        self.containerapp_def["location"] = location
        self.containerapp_def["identity"] = identity_def
        self.containerapp_def["properties"]["environmentId"] = self.get_argument_managed_env()
        self.containerapp_def["properties"]["configuration"] = config_def
        self.containerapp_def["properties"]["template"] = template_def
        self.containerapp_def["tags"] = self.get_argument_tags()

        if self.get_argument_workload_profile_name():
            self.containerapp_def["properties"]["workloadProfileName"] = self.get_argument_workload_profile_name()
            ensure_workload_profile_supported(self.cmd, managed_env_name, managed_env_rg, self.get_argument_workload_profile_name(),
                                              managed_env_info)

        if self.get_argument_registry_identity():
            if is_registry_msi_system(self.get_argument_registry_identity()):
                set_managed_identity(self.cmd, self.get_argument_resource_group_name(), self.containerapp_def, system_assigned=True)
            else:
                set_managed_identity(self.cmd, self.get_argument_resource_group_name(), self.containerapp_def, user_assigned=[self.get_argument_registry_identity()])

    def create(self):
        try:
            r = self.client.create_or_update(
                cmd=self.cmd, resource_group_name=self.get_argument_resource_group_name(), name=self.get_argument_name(), container_app_envelope=self.containerapp_def,
                no_wait=self.get_argument_no_wait())

            return r
        except Exception as e:
            handle_raw_exception(e)

    def construct_for_post_process(self, r):
        if is_registry_msi_system(self.get_argument_registry_identity()):
            while r["properties"]["provisioningState"] == "InProgress":
                r = self.client.show(self.cmd, self.get_argument_resource_group_name(), self.get_argument_name())
                time.sleep(10)
            logger.info("Creating an acrpull role assignment for the system identity")
            system_sp = r["identity"]["principalId"]
            create_acrpull_role_assignment(self.cmd, self.get_argument_registry_server(), registry_identity=None, service_principal=system_sp)
            containers_def = safe_get(self.containerapp_def, "properties", "template", "containers")
            containers_def[0]["image"] = self.get_argument_image()

            safe_set(self.containerapp_def, "properties", "template", "revisionSuffix", value=self.get_argument_revision_suffix())

            registries_def = deepcopy(RegistryCredentialsModel)
            registries_def["server"] = self.get_argument_registry_server()
            registries_def["identity"] = self.get_argument_registry_identity()
            safe_set(self.containerapp_def, "properties", "configuration", "registries", value=[registries_def])

    def post_process(self, r):
        if is_registry_msi_system(self.get_argument_registry_identity()):
            r = self.create()

        if "properties" in r and "provisioningState" in r["properties"] and r["properties"]["provisioningState"].lower() == "waiting" and not self.get_argument_no_wait():
            not self.get_argument_disable_warnings() and logger.warning('Containerapp creation in progress. Please monitor the creation using `az containerapp show -n {} -g {}`'.format(self.get_argument_name(), self.get_argument_resource_group_name()))

        if "configuration" in r["properties"] and "ingress" in r["properties"]["configuration"] and r["properties"]["configuration"]["ingress"] and "fqdn" in r["properties"]["configuration"]["ingress"]:
            not self.get_argument_disable_warnings() and logger.warning("\nContainer app created. Access your app at https://{}/\n".format(r["properties"]["configuration"]["ingress"]["fqdn"]))
        else:
            target_port = self.get_argument_target_port() or "<port>"
            not self.get_argument_disable_warnings() and logger.warning("\nContainer app created. To access it over HTTPS, enable ingress: "
                                                                        "az containerapp ingress enable -n %s -g %s --type external --target-port %s"
                                                                        " --transport auto\n", self.get_argument_name(), self.get_argument_resource_group_name(), target_port)

        return r

    def set_up_create_containerapp_yaml(self, name, file_name):
        if self.get_argument_image() or self.get_argument_min_replicas() or self.get_argument_max_replicas() or self.get_argument_target_port() or self.get_argument_ingress() or \
                self.get_argument_revisions_mode() or self.get_argument_secrets() or self.get_argument_env_vars() or self.get_argument_cpu() or self.get_argument_memory() or self.get_argument_registry_server() or \
                self.get_argument_registry_user() or self.get_argument_registry_pass() or self.get_argument_dapr_enabled() or self.get_argument_dapr_app_port() or self.get_argument_dapr_app_id() or \
                self.get_argument_startup_command() or self.get_argument_args() or self.get_argument_tags():
            not self.get_argument_disable_warnings() and logger.warning(
                'Additional flags were passed along with --yaml. These flags will be ignored, and the configuration defined in the yaml will be used instead')

        yaml_containerapp = process_loaded_yaml(load_yaml_file(file_name))

        if not yaml_containerapp.get('name'):
            yaml_containerapp['name'] = name
        elif yaml_containerapp.get('name').lower() != name.lower():
            logger.warning(
                'The app name provided in the --yaml file "{}" does not match the one provided in the --name flag "{}". The one provided in the --yaml file will be used.'.format(
                    yaml_containerapp.get('name'), name))
        name = yaml_containerapp.get('name')

        if not yaml_containerapp.get('type'):
            yaml_containerapp['type'] = 'Microsoft.App/containerApps'
        elif yaml_containerapp.get('type').lower() != "microsoft.app/containerapps":
            raise ValidationError('Containerapp type must be \"Microsoft.App/ContainerApps\"')

        # Deserialize the yaml into a ContainerApp object. Need this since we're not using SDK
        try:
            deserializer = create_deserializer(self.models)

            self.containerapp_def = deserializer('ContainerApp', yaml_containerapp)
        except DeserializationError as ex:
            raise ValidationError(
                'Invalid YAML provided. Please see https://aka.ms/azure-container-apps-yaml for a valid containerapps YAML spec.') from ex

        # Remove tags before converting from snake case to camel case, then re-add tags. We don't want to change the case of the tags. Need this since we're not using SDK
        tags = None
        if yaml_containerapp.get('tags'):
            tags = yaml_containerapp.get('tags')
            del yaml_containerapp['tags']

        self.containerapp_def = _convert_object_from_snake_to_camel_case(_object_to_dict(self.containerapp_def))
        self.containerapp_def['tags'] = tags

        # After deserializing, some properties may need to be moved under the "properties" attribute. Need this since we're not using SDK
        self.containerapp_def = process_loaded_yaml(self.containerapp_def)

        # Remove "additionalProperties" and read-only attributes that are introduced in the deserialization. Need this since we're not using SDK
        _remove_additional_attributes(self.containerapp_def)
        _remove_readonly_attributes(self.containerapp_def)

        # Remove extra workloadProfileName introduced in deserialization
        if "workloadProfileName" in self.containerapp_def:
            del self.containerapp_def["workloadProfileName"]

        # Validate managed environment
        env_id = self.containerapp_def["properties"]['environmentId']
        env_info = None
        if self.get_argument_managed_env():
            if not self.get_argument_disable_warnings() and env_id is not None and env_id != self.get_argument_managed_env():
                logger.warning('The environmentId was passed along with --yaml. The value entered with --environment will be ignored, and the configuration defined in the yaml will be used instead')
            if env_id is None:
                env_id = self.get_argument_managed_env()
                safe_set(self.containerapp_def, "properties", "environmentId", value=env_id)

        if not self.containerapp_def["properties"].get('environmentId'):
            raise RequiredArgumentMissingError(
                'environmentId is required. This can be retrieved using the `az containerapp env show -g MyResourceGroup -n MyContainerappEnvironment --query id` command. Please see https://aka.ms/azure-container-apps-yaml for a valid containerapps YAML spec.')

        if is_valid_resource_id(env_id):
            parsed_managed_env = parse_resource_id(env_id)
            env_name = parsed_managed_env['name']
            env_rg = parsed_managed_env['resource_group']
        else:
            raise ValidationError('Invalid environmentId specified. Environment not found')

        try:
            env_info = self.get_environment_client().show(cmd=self.cmd, resource_group_name=env_rg, name=env_name)
        except Exception as e:
            handle_non_404_status_code_exception(e)

        if not env_info:
            raise ValidationError("The environment '{}' in resource group '{}' was not found".format(env_name, env_rg))

        # Validate location
        if not self.containerapp_def.get('location'):
            self.containerapp_def['location'] = env_info['location']

    # pylint: disable=unsupported-assignment-operation
    def set_up_scale_rule(self):
        scale_def = None
        if self.get_argument_min_replicas() is not None or self.get_argument_max_replicas() is not None:
            scale_def = deepcopy(ScaleModel)
            scale_def["minReplicas"] = self.get_argument_min_replicas()
            scale_def["maxReplicas"] = self.get_argument_max_replicas()

        scale_rule_type = self.get_argument_scale_rule_type()
        scale_rule_name = self.get_argument_scale_rule_name()
        scale_rule_auth = self.get_argument_scale_rule_auth()
        scale_rule_metadata = self.get_argument_scale_rule_metadata()
        scale_rule_http_concurrency = self.get_argument_scale_rule_http_concurrency()
        if self.get_argument_scale_rule_name():
            if not scale_rule_type:
                scale_rule_type = "http"
            scale_rule_type = scale_rule_type.lower()
            scale_rule_def = deepcopy(ScaleRuleModel)
            curr_metadata = {}
            if self.get_argument_scale_rule_http_concurrency():
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
                scale_def = deepcopy(ScaleModel)
            scale_def["rules"] = [scale_rule_def]

        return scale_def
