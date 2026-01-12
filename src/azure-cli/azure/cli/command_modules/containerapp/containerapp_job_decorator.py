# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long
# pylint: disable=ungrouped-imports
# pylint: disable=unused-argument, unused-variable
# pylint: disable=broad-exception-caught
# pylint: disable=logging-format-interpolation
# pylint: disable=too-many-statements, too-many-locals, too-many-branches, too-many-public-methods, too-many-boolean-expressions, expression-not-assigned
from typing import Dict, Any

from azure.cli.core.commands import AzCliCommand

import time

from azure.cli.core.azclierror import (
    RequiredArgumentMissingError,
    ValidationError)
from azure.cli.core.commands.client_factory import get_subscription_id

from knack.log import get_logger

from azure.mgmt.core.tools import parse_resource_id, is_valid_resource_id
from msrest.exceptions import DeserializationError

from ._decorator_utils import process_loaded_yaml, load_yaml_file, create_deserializer
from ._constants import HELLO_WORLD_IMAGE, CONTAINER_APPS_RP
from ._validators import validate_create
from .base_resource import BaseResource
from ._clients import ManagedEnvironmentClient
from ._client_factory import handle_raw_exception

from ._models import (
    JobConfiguration as JobConfigurationModel,
    ManualTriggerConfig as ManualTriggerModel,
    ScheduleTriggerConfig as ScheduleTriggerModel,
    EventTriggerConfig as EventTriggerModel,
    JobTemplate as JobTemplateModel,
    RegistryCredentials as RegistryCredentialsModel,
    ContainerAppsJob as ContainerAppsJobModel,
    ContainerResources as ContainerResourcesModel,
    JobScale as JobScaleModel,
    Container as ContainerModel,
    ManagedServiceIdentity as ManagedServiceIdentityModel,
    ScaleRule as ScaleRuleModel)

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
                     ensure_workload_profile_supported,
                     AppType,
                     safe_get)

logger = get_logger(__name__)


class ContainerAppJobDecorator(BaseResource):

    def get_environment_client(self):
        return ManagedEnvironmentClient

    def get_argument_yaml(self):
        return self.get_param("yaml")

    def get_argument_image(self):
        return self.get_param("image")

    def get_argument_container_name(self):
        return self.get_param("container_name")

    def set_argument_image(self, image):
        self.set_param("image", image)

    def get_argument_managed_env(self):
        return self.get_param("managed_env")

    def get_argument_trigger_type(self):
        return self.get_param("trigger_type")

    def get_argument_replica_timeout(self):
        return self.get_param("replica_timeout")

    def get_argument_replica_retry_limit(self):
        return self.get_param("replica_retry_limit")

    def get_argument_replica_completion_count(self):
        return self.get_param("replica_completion_count")

    def get_argument_parallelism(self):
        return self.get_param("parallelism")

    def get_argument_cron_expression(self):
        return self.get_param("cron_expression")

    def get_argument_cpu(self):
        return self.get_param("cpu")

    def get_argument_memory(self):
        return self.get_param("memory")

    def get_argument_secrets(self):
        return self.get_param("secrets")

    def get_argument_env_vars(self):
        return self.get_param("env_vars")

    def get_argument_startup_command(self):
        return self.get_param("startup_command")

    def get_argument_args(self):
        return self.get_param("args")

    def get_argument_scale_rule_metadata(self):
        return self.get_param("scale_rule_metadata")

    def get_argument_scale_rule_name(self):
        return self.get_param("scale_rule_name")

    def get_argument_scale_rule_type(self):
        return self.get_param("scale_rule_type")

    def get_argument_scale_rule_auth(self):
        return self.get_param("scale_rule_auth")

    def get_argument_polling_interval(self):
        return self.get_param("polling_interval")

    def get_argument_min_executions(self):
        return self.get_param("min_executions")

    def get_argument_max_executions(self):
        return self.get_param("max_executions")

    def get_argument_disable_warnings(self):
        return self.get_param("disable_warnings")

    def get_argument_registry_pass(self):
        return self.get_param("registry_pass")

    def set_argument_registry_pass(self, registry_pass):
        self.set_param("registry_pass", registry_pass)

    def get_argument_registry_server(self):
        return self.get_param("registry_server")

    def get_argument_registry_user(self):
        return self.get_param("registry_user")

    def set_argument_registry_user(self, registry_user):
        self.set_param("registry_user", registry_user)

    def get_argument_tags(self):
        return self.get_param("tags")

    def get_argument_system_assigned(self):
        return self.get_param("system_assigned")

    def get_argument_user_assigned(self):
        return self.get_param("user_assigned")

    def get_argument_registry_identity(self):
        return self.get_param("registry_identity")

    def get_argument_workload_profile_name(self):
        return self.get_param("workload_profile_name")

    def set_augument_workload_profile_name(self, workload_profile_name):
        self.set_param("workload_profile_name", workload_profile_name)


class ContainerAppJobCreateDecorator(ContainerAppJobDecorator):
    def __init__(self, cmd: AzCliCommand, client: Any, raw_parameters: Dict, models: str):
        super().__init__(cmd, client, raw_parameters, models)
        self.containerappjob_def = ContainerAppsJobModel

    def validate_arguments(self):
        validate_container_app_name(self.get_argument_name(), AppType.ContainerAppJob.name)
        validate_create(self.get_argument_registry_identity(), self.get_argument_registry_pass(), self.get_argument_registry_user(), self.get_argument_registry_server(), self.get_argument_no_wait())
        if self.get_argument_yaml() is None:
            if self.get_argument_replica_timeout() is None:
                raise RequiredArgumentMissingError('Usage error: --replica-timeout is required')

            if self.get_argument_replica_retry_limit() is None:
                raise RequiredArgumentMissingError('Usage error: --replica-retry-limit is required')

            if self.get_argument_managed_env() is None:
                raise RequiredArgumentMissingError('Usage error: --environment is required if not using --yaml')

    def create(self):
        try:
            r = self.client.create_or_update(
                cmd=self.cmd, resource_group_name=self.get_argument_resource_group_name(), name=self.get_argument_name(),
                containerapp_job_envelope=self.containerappjob_def, no_wait=self.get_argument_no_wait())
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
            containers_def = safe_get(self.containerappjob_def, "properties", "template", "containers")
            containers_def[0]["image"] = self.get_argument_image()

            registries_def = RegistryCredentialsModel
            registries_def["server"] = self.get_argument_registry_server()
            registries_def["identity"] = self.get_argument_registry_identity()
            safe_set(self.containerappjob_def, "properties", "configuration", "registries", value=[registries_def])

    def post_process(self, r):
        if is_registry_msi_system(self.get_argument_registry_identity()):
            r = self.create()

        if "properties" in r and "provisioningState" in r["properties"] and r["properties"]["provisioningState"].lower() == "waiting" and not self.get_argument_no_wait():
            if not self.get_argument_disable_warnings():
                logger.warning('Containerapp job creation in progress. Please monitor the creation using `az containerapp job show -n {} -g {}`'.format(self.get_argument_name(), self.get_argument_resource_group_name()))
        return r

    def construct_payload(self):
        if self.get_argument_registry_identity() and not is_registry_msi_system(self.get_argument_registry_identity()):
            logger.info("Creating an acrpull role assignment for the registry identity")
            create_acrpull_role_assignment(self.cmd, self.get_argument_registry_server(), self.get_argument_registry_identity(), skip_error=True)

        if self.get_argument_yaml():
            return self.set_up_create_containerapp_job_yaml(name=self.get_argument_name(), file_name=self.get_argument_yaml())

        if not self.get_argument_image():
            self.set_argument_image(HELLO_WORLD_IMAGE)

        # Validate managed environment
        parsed_managed_env = parse_resource_id(self.get_argument_managed_env())
        managed_env_name = parsed_managed_env['name']
        managed_env_rg = parsed_managed_env['resource_group']
        managed_env_info = None

        try:
            managed_env_info = self.get_environment_client().show(cmd=self.cmd, resource_group_name=managed_env_rg, name=managed_env_name)
        except:  # pylint: disable=bare-except
            pass

        if not managed_env_info:
            raise ValidationError(
                "The environment '{}' does not exist. Specify a valid environment".format(self.get_argument_managed_env()))

        location = managed_env_info["location"]
        _ensure_location_allowed(self.cmd, location, CONTAINER_APPS_RP, "jobs")

        if not self.get_argument_workload_profile_name() and "workloadProfiles" in managed_env_info:
            workload_profile_name = get_default_workload_profile_name_from_env(self.cmd, managed_env_info, managed_env_rg)
            self.set_augument_workload_profile_name(workload_profile_name)

        manualTriggerConfig_def = None
        if self.get_argument_trigger_type() is not None and self.get_argument_trigger_type().lower() == "manual":
            manualTriggerConfig_def = ManualTriggerModel
            manualTriggerConfig_def[
                "replicaCompletionCount"] = 0 if self.get_argument_replica_completion_count() is None else self.get_argument_replica_completion_count()
            manualTriggerConfig_def["parallelism"] = 0 if self.get_argument_parallelism() is None else self.get_argument_parallelism()

        scheduleTriggerConfig_def = None
        if self.get_argument_trigger_type() is not None and self.get_argument_trigger_type().lower() == "schedule":
            scheduleTriggerConfig_def = ScheduleTriggerModel
            scheduleTriggerConfig_def[
                "replicaCompletionCount"] = 0 if self.get_argument_replica_completion_count() is None else self.get_argument_replica_completion_count()
            scheduleTriggerConfig_def["parallelism"] = 0 if self.get_argument_parallelism() is None else self.get_argument_parallelism()
            scheduleTriggerConfig_def["cronExpression"] = self.get_argument_cron_expression()

        eventTriggerConfig_def = None
        if self.get_argument_trigger_type() is not None and self.get_argument_trigger_type().lower() == "event":
            scale_def = None
            if self.get_argument_min_executions() is not None or self.get_argument_max_executions() is not None or self.get_argument_polling_interval() is not None:
                scale_def = JobScaleModel
                scale_def["pollingInterval"] = self.get_argument_polling_interval()
                scale_def["minExecutions"] = self.get_argument_min_executions()
                scale_def["maxExecutions"] = self.get_argument_max_executions()

            if self.get_argument_scale_rule_name():
                scale_rule_type = self.get_argument_scale_rule_type().lower()
                scale_rule_def = ScaleRuleModel
                curr_metadata = {}
                metadata_def = parse_metadata_flags(self.get_argument_scale_rule_metadata(), curr_metadata)
                auth_def = parse_auth_flags(self.get_argument_scale_rule_auth())
                scale_rule_def["name"] = self.get_argument_scale_rule_name()
                scale_rule_def["type"] = scale_rule_type
                scale_rule_def["metadata"] = metadata_def
                scale_rule_def["auth"] = auth_def

                if not scale_def:
                    scale_def = JobScaleModel
                scale_def["rules"] = [scale_rule_def]

            eventTriggerConfig_def = EventTriggerModel
            eventTriggerConfig_def["replicaCompletionCount"] = self.get_argument_replica_completion_count()
            eventTriggerConfig_def["parallelism"] = self.get_argument_parallelism()
            eventTriggerConfig_def["scale"] = scale_def

        secrets_def = None
        if self.get_argument_secrets() is not None:
            secrets_def = parse_secret_flags(self.get_argument_secrets())

        registries_def = None
        if self.get_argument_registry_server() is not None and not is_registry_msi_system(self.get_argument_registry_identity()):
            registries_def = RegistryCredentialsModel
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

        config_def = JobConfigurationModel
        config_def["secrets"] = secrets_def
        config_def["triggerType"] = self.get_argument_trigger_type()
        config_def["replicaTimeout"] = self.get_argument_replica_timeout()
        config_def["replicaRetryLimit"] = self.get_argument_replica_retry_limit()
        config_def["manualTriggerConfig"] = manualTriggerConfig_def
        config_def["scheduleTriggerConfig"] = scheduleTriggerConfig_def
        config_def["eventTriggerConfig"] = eventTriggerConfig_def
        config_def["registries"] = [registries_def] if registries_def is not None else None

        # Identity actions
        identity_def = ManagedServiceIdentityModel
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

        resources_def = None
        if self.get_argument_cpu() is not None or self.get_argument_memory() is not None:
            resources_def = ContainerResourcesModel
            resources_def["cpu"] = self.get_argument_cpu()
            resources_def["memory"] = self.get_argument_memory()

        container_def = ContainerModel
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

        template_def = JobTemplateModel
        template_def["containers"] = [container_def]

        self.containerappjob_def["location"] = location
        self.containerappjob_def["identity"] = identity_def
        self.containerappjob_def["properties"]["environmentId"] = self.get_argument_managed_env()
        self.containerappjob_def["properties"]["configuration"] = config_def
        self.containerappjob_def["properties"]["template"] = template_def
        self.containerappjob_def["tags"] = self.get_argument_tags()

        if self.get_argument_workload_profile_name():
            self.containerappjob_def["properties"]["workloadProfileName"] = self.get_argument_workload_profile_name()
            ensure_workload_profile_supported(self.cmd, managed_env_name, managed_env_rg, self.get_argument_workload_profile_name(),
                                              managed_env_info)

        if self.get_argument_registry_identity():
            if is_registry_msi_system(self.get_argument_registry_identity()):
                set_managed_identity(self.cmd, self.get_argument_resource_group_name(), self.containerappjob_def, system_assigned=True)
            else:
                set_managed_identity(self.cmd, self.get_argument_resource_group_name(), self.containerappjob_def, user_assigned=[self.get_argument_registry_identity()])

    def set_up_create_containerapp_job_yaml(self, name, file_name):
        if self.get_argument_image() or self.get_argument_trigger_type() or self.get_argument_replica_timeout() or self.get_argument_replica_retry_limit() or \
                self.get_argument_replica_completion_count() or self.get_argument_parallelism() or self.get_argument_cron_expression() or self.get_argument_cpu() or self.get_argument_memory() or self.get_argument_registry_server() or \
                self.get_argument_registry_user() or self.get_argument_registry_pass() or self.get_argument_secrets() or self.get_argument_env_vars() or \
                self.get_argument_startup_command() or self.get_argument_args() or self.get_argument_tags():
            not self.get_argument_disable_warnings() and logger.warning(
                'Additional flags were passed along with --yaml. These flags will be ignored, and the configuration defined in the yaml will be used instead')

        yaml_containerappsjob = process_loaded_yaml(load_yaml_file(file_name))

        if not yaml_containerappsjob.get('name'):
            yaml_containerappsjob['name'] = name
        elif yaml_containerappsjob.get('name').lower() != name.lower():
            logger.warning(
                'The job name provided in the --yaml file "{}" does not match the one provided in the --name flag "{}". The one provided in the --yaml file will be used.'.format(
                    yaml_containerappsjob.get('name'), name))
        name = yaml_containerappsjob.get('name')

        if not yaml_containerappsjob.get('type'):
            yaml_containerappsjob['type'] = 'Microsoft.App/jobs'
        elif yaml_containerappsjob.get('type').lower() != "microsoft.app/jobs":
            raise ValidationError('Containerapp job type must be \"Microsoft.App/jobs\"')

        # Deserialize the yaml into a ContainerAppsJob object. Need this since we're not using SDK
        try:
            deserializer = create_deserializer(self.models)

            self.containerappjob_def = deserializer('ContainerAppsJob', yaml_containerappsjob)
        except DeserializationError as ex:
            raise ValidationError(
                'Invalid YAML provided. Please see https://aka.ms/azure-container-apps-yaml for a valid containerapps YAML spec.') from ex

        # Remove tags before converting from snake case to camel case, then re-add tags. We don't want to change the case of the tags. Need this since we're not using SDK
        tags = None
        if yaml_containerappsjob.get('tags'):
            tags = yaml_containerappsjob.get('tags')
            del yaml_containerappsjob['tags']

        self.containerappjob_def = _convert_object_from_snake_to_camel_case(_object_to_dict(self.containerappjob_def))
        self.containerappjob_def['tags'] = tags

        # After deserializing, some properties may need to be moved under the "properties" attribute. Need this since we're not using SDK
        self.containerappjob_def = process_loaded_yaml(self.containerappjob_def)

        # Remove "additionalProperties" and read-only attributes that are introduced in the deserialization. Need this since we're not using SDK
        _remove_additional_attributes(self.containerappjob_def)
        _remove_readonly_attributes(self.containerappjob_def)

        # Remove extra workloadProfileName introduced in deserialization
        if "workloadProfileName" in self.containerappjob_def:
            del self.containerappjob_def["workloadProfileName"]

        # Validate managed environment
        env_id = self.containerappjob_def["properties"]['environmentId']
        env_info = None
        if self.get_argument_managed_env():
            if not self.get_argument_disable_warnings() and env_id is not None and env_id != self.get_argument_managed_env():
                logger.warning('The environmentId was passed along with --yaml. The value entered with --environment will be ignored, and the configuration defined in the yaml will be used instead')
            if env_id is None:
                env_id = self.get_argument_managed_env()
                safe_set(self.containerappjob_def, "properties", "environmentId", value=env_id)

        if not self.containerappjob_def["properties"].get('environmentId'):
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
        except:  # pylint: disable=bare-except
            pass

        if not env_info:
            raise ValidationError("The environment '{}' in resource group '{}' was not found".format(env_name, env_rg))

        # Validate location
        if not self.containerappjob_def.get('location'):
            self.containerappjob_def['location'] = env_info['location']
