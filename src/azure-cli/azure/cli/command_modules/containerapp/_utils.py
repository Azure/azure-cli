# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long, consider-using-f-string, no-else-return, duplicate-string-formatting-argument, expression-not-assigned, too-many-locals, logging-fstring-interpolation, broad-except, pointless-statement, bare-except, unused-variable, redefined-outer-name, reimported, unused-import, consider-using-generator, broad-exception-raised

import time
import json
import platform
import subprocess
import stat
import io
import os
import tarfile
import zipfile
import hashlib
import re
import requests
import packaging.version as SemVer
from enum import Enum

from urllib.parse import urlparse
from urllib.request import urlopen
from datetime import datetime
from dateutil.relativedelta import relativedelta
from azure.cli.core.azclierror import (ValidationError, RequiredArgumentMissingError, CLIInternalError,
                                       ResourceNotFoundError, FileOperationError, CLIError, UnauthorizedError,
                                       InvalidArgumentValueError)
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.command_modules.appservice.utils import _normalize_location
from .aaz.latest.network.vnet import Show as VNetShow
from azure.cli.command_modules.role.custom import create_role_assignment
from azure.cli.command_modules.acr.custom import acr_show
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core._profile import Profile
from azure.cli.core.profiles import ResourceType
from azure.mgmt.containerregistry import ContainerRegistryManagementClient
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.servicelinker import ServiceLinkerManagementClient
from azure.mgmt.core.tools import parse_resource_id, is_valid_resource_id, resource_id

from knack.log import get_logger

from ._clients import ContainerAppClient, ManagedEnvironmentClient, WorkloadProfileClient, ContainerAppsJobClient
from ._client_factory import handle_raw_exception, providers_client_factory, cf_resource_groups, log_analytics_client_factory, log_analytics_shared_key_client_factory
from ._constants import (MAXIMUM_CONTAINER_APP_NAME_LENGTH, SHORT_POLLING_INTERVAL_SECS, LONG_POLLING_INTERVAL_SECS,
                         LOG_ANALYTICS_RP, CONTAINER_APPS_RP, CHECK_CERTIFICATE_NAME_AVAILABILITY_TYPE, ACR_IMAGE_SUFFIX,
                         LOGS_STRING, PENDING_STATUS, SUCCEEDED_STATUS, UPDATING_STATUS, DEV_SERVICE_LIST)
from ._models import (ContainerAppCustomDomainEnvelope as ContainerAppCustomDomainEnvelopeModel,
                      ManagedCertificateEnvelop as ManagedCertificateEnvelopModel)
from ._models import OryxMarinerRunImgTagProperty


class AppType(Enum):
    ContainerApp = 1
    ContainerAppJob = 2


logger = get_logger(__name__)


def register_provider_if_needed(cmd, rp_name):
    if not _is_resource_provider_registered(cmd, rp_name):
        _register_resource_provider(cmd, rp_name)


def validate_container_app_name(name, appType):
    name_regex = re.compile(r'^(?=.{1,32}$)[a-z]((?!.*--)[-a-z0-9]*[a-z0-9])?$', re.IGNORECASE)
    match = name_regex.match(name)

    if not match:
        raise ValidationError(f"Invalid {appType} name {name}. A name must consist of lower case alphanumeric characters or '-', start with a letter, end with an alphanumeric character, cannot have '--', and must be less than {MAXIMUM_CONTAINER_APP_NAME_LENGTH} characters.")


def retry_until_success(operation, err_txt, retry_limit, *args, **kwargs):
    while True:
        try:
            return operation(*args, **kwargs)
        except Exception as e:
            retry_limit -= 1
            if retry_limit <= 0:
                raise CLIInternalError(err_txt) from e
            time.sleep(5)
            logger.info(f"Encountered error: {e}. Retrying...")


def get_vnet_location(cmd, subnet_resource_id):
    parsed_rid = parse_resource_id(subnet_resource_id)
    vnet = VNetShow(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": parsed_rid.get("resource_group"),
        "name": parsed_rid.get("name")
    })
    location = vnet['location']
    return _normalize_location(cmd, location)


def _create_application(client, display_name):
    from azure.cli.command_modules.role.custom import GraphError
    body = {"displayName": display_name, "keyCredentials": []}

    try:
        result = client.application_create(body)
    except GraphError as ex:
        if 'insufficient privileges' in str(ex).lower():
            link = 'https://learn.microsoft.com/azure/azure-resource-manager/resource-group-create-service-principal-portal'  # pylint: disable=line-too-long
            raise ValidationError("Directory permission is needed for the current user to register the application. "
                                  "For how to configure, please refer '{}'. Original error: {}".format(link, ex)) from ex
        raise
    return result


def _create_service_principal(client, app_id):
    return client.service_principal_create({"appId": app_id, "accountEnabled": True})


def _create_role_assignment(cli_ctx, role, assignee, scope=None):
    import uuid
    from azure.cli.core.profiles import get_sdk, supported_api_version

    auth_client = get_mgmt_service_client(cli_ctx, ResourceType.MGMT_AUTHORIZATION)
    assignments_client = auth_client.role_assignments
    definitions_client = auth_client.role_definitions

    assignment_name = uuid.uuid4()
    role_defs = list(definitions_client.list(scope, "roleName eq '{}'".format(role)))
    role_id = role_defs[0].id

    api_version = supported_api_version(cli_ctx, resource_type=ResourceType.MGMT_AUTHORIZATION, max_api='2015-07-01')
    RoleAssignmentCreateParameters = get_sdk(cli_ctx, ResourceType.MGMT_AUTHORIZATION,
                                             'RoleAssignmentProperties' if api_version else 'RoleAssignmentCreateParameters',
                                             mod='models', operation_group='role_assignments')
    parameters = RoleAssignmentCreateParameters(role_definition_id=role_id, principal_id=assignee)
    parameters.principal_type = "ServicePrincipal"
    return assignments_client.create(scope, assignment_name, parameters)


def create_service_principal_for_github_action(cmd, scopes=None, role="contributor"):
    from azure.cli.command_modules.role import graph_client_factory

    SP_CREATION_ERR_TXT = "Failed to create service principal."
    RETRY_LIMIT = 36

    client = graph_client_factory(cmd.cli_ctx)
    now = datetime.utcnow()
    app_display_name = 'azure-cli-' + now.strftime('%Y-%m-%d-%H-%M-%S')
    app = retry_until_success(_create_application, SP_CREATION_ERR_TXT, RETRY_LIMIT, client, display_name=app_display_name)
    sp = retry_until_success(_create_service_principal, SP_CREATION_ERR_TXT, RETRY_LIMIT, client, app_id=app["appId"])
    for scope in scopes:
        retry_until_success(_create_role_assignment, SP_CREATION_ERR_TXT, RETRY_LIMIT, cmd.cli_ctx, role=role, assignee=sp["id"], scope=scope)
    service_principal = retry_until_success(client.service_principal_get, SP_CREATION_ERR_TXT, RETRY_LIMIT, sp["id"])

    body = {
        "passwordCredential": {
            "displayName": None,
            "startDateTime": now.strftime('%Y-%m-%dT%H:%M:%SZ'),
            "endDateTime": (now + relativedelta(years=1)).strftime('%Y-%m-%dT%H:%M:%SZ'),
        }
    }
    add_password_result = retry_until_success(client.service_principal_add_password, SP_CREATION_ERR_TXT, RETRY_LIMIT, service_principal["id"], body)

    return {
        'appId': service_principal['appId'],
        'password': add_password_result['secretText'],
        'tenant': client.tenant
    }


def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        pass
    return False


def get_github_repo(token, repo):
    from github import Github

    g = Github(token)
    return g.get_repo(repo)


def get_workflow(github_repo, workflow_name):  # pylint: disable=inconsistent-return-statements
    workflows = list(github_repo.get_workflows())
    workflows.sort(key=lambda r: r.created_at, reverse=True)  # sort by latest first
    workflow = [wf for wf in workflows if wf.path == f".github/workflows/{workflow_name}.yml"]

    if not workflow:
        raise CLIInternalError("Could not find workflow on github repo.")
    return workflow[0]


def trigger_workflow(token, repo, workflow_name, branch):
    wf = get_workflow(get_github_repo(token, repo), workflow_name)
    logger.warning(f"Triggering Github Action: {wf.path}")
    wf.create_dispatch(branch)


# pylint:disable=unused-argument
def await_github_action(token, repo, workflow_name, timeout_secs=1200):
    from ._clients import PollingAnimation

    start = datetime.utcnow()
    animation = PollingAnimation()
    animation.tick()

    github_repo = get_github_repo(token, repo)

    workflow = None
    while workflow is None:
        animation.tick()
        time.sleep(SHORT_POLLING_INTERVAL_SECS)
        try:
            workflow = get_workflow(github_repo, workflow_name)
        except CLIInternalError:
            pass
        animation.flush()

        if (datetime.utcnow() - start).seconds >= timeout_secs:
            raise CLIInternalError("Timed out while waiting for the Github action to start.")

    runs = workflow.get_runs()
    while runs is None or not [r for r in runs if r.status in ('queued', 'in_progress')]:
        time.sleep(SHORT_POLLING_INTERVAL_SECS)
        runs = workflow.get_runs()
        if (datetime.utcnow() - start).seconds >= timeout_secs:
            raise CLIInternalError("Timed out while waiting for the Github action to be started.")
    runs = [r for r in runs if r.status in ('queued', 'in_progress')]
    runs.sort(key=lambda r: r.created_at, reverse=True)
    run = runs[0]  # run with the latest created_at date that's either in progress or queued
    logger.warning(f"Github action run: https://github.com/{repo}/actions/runs/{run.id}")
    logger.warning("Waiting for deployment to complete...")
    run_id = run.id
    status = run.status
    while status in ('queued', 'in_progress'):
        time.sleep(LONG_POLLING_INTERVAL_SECS)
        animation.tick()
        status = github_repo.get_workflow_run(run_id).status
        animation.flush()
        if (datetime.utcnow() - start).seconds >= timeout_secs:
            raise CLIInternalError("Timed out while waiting for the Github action to complete.")

    animation.flush()  # needed to clear the animation from the terminal
    run = github_repo.get_workflow_run(run_id)
    if run.status != "completed" or run.conclusion != "success":
        raise ValidationError("Github action build or deployment failed. "
                              f"Please see https://github.com/{repo}/actions/runs/{run.id} for more details")


def repo_url_to_name(repo_url):
    repo = None
    repo = [s for s in repo_url.split('/') if s]
    if len(repo) >= 2:
        repo = '/'.join(repo[-2:])
    return repo


def _get_location_from_resource_group(cli_ctx, resource_group_name):
    client = cf_resource_groups(cli_ctx)
    group = client.get(resource_group_name)
    return group.location


def _register_resource_provider(cmd, resource_provider):
    from azure.mgmt.resource.resources.models import ProviderRegistrationRequest, ProviderConsentDefinition

    logger.warning(f"Registering resource provider {resource_provider} ...")
    properties = ProviderRegistrationRequest(third_party_provider_consent=ProviderConsentDefinition(consent_to_authorization=True))

    client = providers_client_factory(cmd.cli_ctx)
    try:
        client.register(resource_provider, properties=properties)
        # wait for registration to finish
        timeout_secs = 120
        registration = _is_resource_provider_registered(cmd, resource_provider)
        start = datetime.utcnow()
        while not registration:
            registration = _is_resource_provider_registered(cmd, resource_provider)
            time.sleep(SHORT_POLLING_INTERVAL_SECS)
            if (datetime.utcnow() - start).seconds >= timeout_secs:
                raise CLIInternalError(f"Timed out while waiting for the {resource_provider} resource provider to be registered.")

    except Exception as e:
        msg = ("This operation requires requires registering the resource provider {0}. "
               "We were unable to perform that registration on your behalf: "
               "Server responded with error message -- {1} . "
               "Please check with your admin on permissions, "
               "or try running registration manually with: az provider register --wait --namespace {0}")
        raise ValidationError(resource_provider, msg.format(e.args)) from e


def _is_resource_provider_registered(cmd, resource_provider, subscription_id=None):
    registered = None
    if not subscription_id:
        subscription_id = get_subscription_id(cmd.cli_ctx)
    try:
        providers_client = providers_client_factory(cmd.cli_ctx, subscription_id)
        registration_state = getattr(providers_client.get(resource_provider), 'registration_state', "NotRegistered")

        registered = (registration_state and registration_state.lower() == 'registered')
    except Exception:  # pylint: disable=broad-except
        pass
    return registered


def _validate_subscription_registered(cmd, resource_provider, subscription_id=None):
    if not subscription_id:
        subscription_id = get_subscription_id(cmd.cli_ctx)
    registered = _is_resource_provider_registered(cmd, resource_provider, subscription_id)
    if registered is False:
        raise ValidationError(f'Subscription {subscription_id} is not registered for the {resource_provider} '
                              f'resource provider. Please run "az provider register -n {resource_provider} --wait" '
                              'to register your subscription.')


def _ensure_location_allowed(cmd, location, resource_provider, resource_type):
    providers_client = None
    try:
        providers_client = providers_client_factory(cmd.cli_ctx, get_subscription_id(cmd.cli_ctx))
    except Exception as ex:
        handle_raw_exception(ex)

    if providers_client is not None:
        try:
            resource_types = getattr(providers_client.get(resource_provider), 'resource_types', [])
        except Exception as ex:
            handle_raw_exception(ex)

        res_locations = []
        for res in resource_types:
            if res and getattr(res, 'resource_type', "") == resource_type:
                res_locations = getattr(res, 'locations', [])

        res_locations = [format_location(res_loc) for res_loc in res_locations if res_loc.strip()]

        location_formatted = format_location(location)
        if location_formatted not in res_locations:
            raise ValidationError(f"Location '{location}' is not currently supported. To get list of supported locations, run `az provider show -n {resource_provider} --query \"resourceTypes[?resourceType=='{resource_type}'].locations\"`")


def parse_env_var_flags(env_list, is_update_containerapp=False):
    env_pairs = {}

    for pair in env_list:
        key_val = pair.split('=', 1)
        if len(key_val) != 2:
            if is_update_containerapp:
                raise ValidationError("Environment variables must be in the format \"<key>=<value> <key>=secretref:<value> ...\".")
            raise ValidationError("Environment variables must be in the format \"<key>=<value> <key>=secretref:<value> ...\".")
        if key_val[0] in env_pairs:
            raise ValidationError("Duplicate environment variable {env} found, environment variable names must be unique.".format(env=key_val[0]))
        value = key_val[1].split('secretref:')
        env_pairs[key_val[0]] = value

    env_var_def = []
    for key, value in env_pairs.items():
        if len(value) == 2:
            env_var_def.append({
                "name": key,
                "secretRef": value[1]
            })
        else:
            env_var_def.append({
                "name": key,
                "value": value[0]
            })

    return env_var_def


def parse_secret_flags(secret_list):
    secret_entries = []
    secret_var_def = []

    for secret in secret_list:
        key_val = secret.split('=', 1)
        if len(key_val) != 2:
            raise ValidationError("Secrets must be in format \"<key>=<value> <key>=<value> ...\" or \"<key>=<keyvaultref:keyvaulturl,identityref:indentityId> ...\".")
        if key_val[0] in secret_entries:
            raise ValidationError("Duplicate secret \"{secret}\" found, secret names must be unique.".format(secret=key_val[0]))
        secret_entries.append(key_val[0])

        name = key_val[0]
        value = key_val[1]
        kv_url = ""
        identity_Id = ""

        kv_identity = value.split(',', 2)
        if len(kv_identity) == 1:
            if kv_identity[0].startswith('keyvaultref:'):
                raise ValidationError("Identityref is missing. Secrets must be in format \"<key>=<value> <key>=<value> ...\" or \"<key>=<keyvaultref:keyvaulturl,identityref:indentityId> ...\".")
            if kv_identity[0].startswith('identityref:'):
                raise ValidationError("Keyvaultref is missing. Secrets must be in format \"<key>=<value> <key>=<value> ...\" or \"<key>=<keyvaultref:keyvaulturl,identityref:indentityId> ...\".")

        if len(kv_identity) == 2:
            kv = kv_identity[0]
            identity = kv_identity[1]
            if kv.startswith('keyvaultref:') and identity.startswith('identityref:'):
                kv_url = kv.split('keyvaultref:', 1)[1]
                identity_Id = identity.split('identityref:', 1)[1]
                value = ""

        secret_var_def.append({
            "name": name,
            "value": value,
            "keyVaultUrl": kv_url,
            "identity": identity_Id
        })

    return secret_var_def


def get_linker_client(cmd):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(cmd.cli_ctx, ServiceLinkerManagementClient)


def validate_binding_name(binding_name):
    pattern = r'^(?=.{1,60}$)[a-zA-Z0-9._]+$'
    return bool(re.match(pattern, binding_name))


def check_unique_bindings(cmd, service_connectors_def_list, service_bindings_def_list, resource_group_name, name):
    linker_client = get_linker_client(cmd)
    containerapp_def = None

    try:
        containerapp_def = ContainerAppClient.show(cmd=cmd, resource_group_name=resource_group_name, name=name)
    except:  # pylint: disable=bare-except
        pass
    all_bindings = []

    if containerapp_def:
        managed_bindings = linker_client.linker.list(resource_uri=containerapp_def["id"])
        service_binds = containerapp_def["properties"].get("template", {}).get("serviceBinds", [])

        if managed_bindings:
            all_bindings.extend([item.name for item in managed_bindings])
        if service_binds:
            all_bindings.extend([item["name"] for item in service_binds])

    service_binding_names = [service_bind["name"] for service_bind in service_bindings_def_list]
    linker_names = [connector["linker_name"] for connector in service_connectors_def_list]

    all_bindings_set = set(all_bindings)
    service_binding_names_set = set(service_binding_names)
    linker_names_set = set(linker_names)

    if len(all_bindings_set | service_binding_names_set | linker_names_set) != len(all_bindings_set) + len(
            service_binding_names_set) + len(linker_names_set):
        # There are duplicate elements across the lists
        return False
    elif len(all_bindings_set) + len(service_binding_names_set) + len(linker_names_set) != len(all_bindings) + len(
            service_binding_names) + len(linker_names):
        # There are duplicate elements within one or more of the lists
        return False
    else:
        # There are no duplicate elements among the lists or within any of the lists
        return True


def parse_metadata_flags(metadata_list, metadata_def={}):  # pylint: disable=dangerous-default-value
    if not metadata_list:
        metadata_list = []
    for pair in metadata_list:
        key_val = pair.split('=', 1)
        if len(key_val) != 2:
            raise ValidationError("Metadata must be in format \"<key>=<value> <key>=<value> ...\".")
        if key_val[0] in metadata_def:
            raise ValidationError("Duplicate metadata \"{metadata}\" found, metadata keys must be unique.".format(metadata=key_val[0]))
        metadata_def[key_val[0]] = key_val[1]

    return metadata_def


def parse_auth_flags(auth_list):
    auth_pairs = {}
    if not auth_list:
        auth_list = []
    for pair in auth_list:
        key_val = pair.split('=', 1)
        if len(key_val) != 2:
            raise ValidationError("Auth parameters must be in format \"<triggerParameter>=<secretRef> <triggerParameter>=<secretRef> ...\".")
        if key_val[0] in auth_pairs:
            raise ValidationError("Duplicate trigger parameter \"{param}\" found, trigger paramaters must be unique.".format(param=key_val[0]))
        auth_pairs[key_val[0]] = key_val[1]

    auth_def = []
    for key, value in auth_pairs.items():
        auth_def.append({
            "triggerParameter": key,
            "secretRef": value
        })

    return auth_def


def _update_revision_env_secretrefs(containers, name):
    for container in containers:
        if "env" in container:
            for var in container["env"]:
                if "secretRef" in var:
                    var["secretRef"] = var["secretRef"].replace("{}-".format(name), "")


def store_as_secret_and_return_secret_ref(secrets_list, registry_user, registry_server, registry_pass, update_existing_secret=False, disable_warnings=False):
    def make_dns1123_compliant(name):
        logger.debug(f"To construct the registry secret name, format the username '{name}' to DNS1123-compliant format.")

        # Replace invalid characters with a hyphen and ensure lowercase
        compliant_name = re.sub(r'[^a-z0-9\-]', '-', name.lower())

        logger.debug(f"DNS1123-compliant name: '{compliant_name}' (original: '{name}')")

        return compliant_name

    if registry_pass.startswith("secretref:"):
        # If user passed in registry password using a secret
        registry_pass = registry_pass.split("secretref:")
        if len(registry_pass) <= 1:
            raise ValidationError("Invalid registry password secret. Value must be a non-empty value starting with 'secretref:'.")
        registry_pass = registry_pass[1:]
        registry_pass = ''.join(registry_pass)

        if not any(secret for secret in secrets_list if secret['name'].lower() == registry_pass.lower()):
            raise ValidationError("Registry password secret with name '{}' does not exist. Add the secret using --secrets".format(registry_pass))

        return registry_pass
    else:
        # If user passed in registry password
        registry_server = registry_server.replace(':', '-')
        if urlparse(registry_server).hostname is not None:
            registry_secret_name = "{server}-{user}".format(
                server=urlparse(registry_server).hostname.replace('.', ''),
                user=make_dns1123_compliant(registry_user)
            )
        else:
            registry_secret_name = "{server}-{user}".format(
                server=registry_server.replace('.', ''),
                user=make_dns1123_compliant(registry_user)
            )

        for secret in secrets_list:
            if secret['name'].lower() == registry_secret_name.lower():
                if secret['value'].lower() != registry_pass.lower():
                    if update_existing_secret:
                        secret['value'] = registry_pass
                    else:
                        raise ValidationError('Found secret with name \"{}\" but value does not equal the supplied registry password.'.format(registry_secret_name))
                return registry_secret_name

        if not disable_warnings:
            logger.warning('Adding registry password as a secret with name \"{}\"'.format(registry_secret_name))  # pylint: disable=logging-format-interpolation
        secrets_list.append({
            "name": registry_secret_name,
            "value": registry_pass
        })

        return registry_secret_name


def parse_list_of_strings(comma_separated_string):
    comma_separated = comma_separated_string.split(',')
    return [s.strip() for s in comma_separated]


def raise_missing_token_suggestion():
    pat_documentation = "https://help.github.com/en/articles/creating-a-personal-access-token-for-the-command-line"
    raise RequiredArgumentMissingError("GitHub access token is required to authenticate to your repositories. "
                                       "If you need to create a Github Personal Access Token, "
                                       "please run with the '--login-with-github' flag or follow "
                                       "the steps found at the following link:\n{0}".format(pat_documentation))


def _get_default_log_analytics_location(cmd):
    default_location = "eastus"
    providers_client = None
    try:
        providers_client = providers_client_factory(cmd.cli_ctx, get_subscription_id(cmd.cli_ctx))
        resource_types = getattr(providers_client.get(LOG_ANALYTICS_RP), 'resource_types', [])
        res_locations = []
        for res in resource_types:
            if res and getattr(res, 'resource_type', "") == "workspaces":
                res_locations = getattr(res, 'locations', [])

        if len(res_locations) > 0:
            location = res_locations[0].lower().replace(" ", "").replace("(", "").replace(")", "")
            if location:
                return location

    except Exception:  # pylint: disable=broad-except
        return default_location
    return default_location


def get_container_app_if_exists(cmd, resource_group_name, name):
    app = None
    try:
        app = ContainerAppClient.show(cmd=cmd, resource_group_name=resource_group_name, name=name)
    except:  # pylint: disable=bare-except
        pass
    return app


def get_containerapps_job_if_exists(cmd, resource_group_name, name):
    job = None
    try:
        job = ContainerAppsJobClient.show(cmd=cmd, resource_group_name=resource_group_name, name=name)
    except:  # pylint: disable=bare-except
        pass
    return job


def _get_name(name_or_rid):
    if is_valid_resource_id(name_or_rid):
        return parse_resource_id(name_or_rid)["name"]
    return name_or_rid


def _get_default_containerapps_location(cmd, location=None):
    if location:
        return location
    default_location = "eastus"
    providers_client = None
    try:
        providers_client = providers_client_factory(cmd.cli_ctx, get_subscription_id(cmd.cli_ctx))
        resource_types = getattr(providers_client.get(CONTAINER_APPS_RP), 'resource_types', [])
        res_locations = []
        for res in resource_types:
            if res and getattr(res, 'resource_type', "") == "workspaces":
                res_locations = getattr(res, 'locations', [])

        if len(res_locations) > 0:
            location = res_locations[0].lower().replace(" ", "").replace("(", "").replace(")", "")
            if location:
                return location

    except Exception:  # pylint: disable=broad-except
        return default_location
    return default_location


# Generate random 4 character string
def _new_tiny_guid():
    import random
    import string
    return ''.join(random.choices(string.ascii_letters + string.digits, k=4))


#  Generate a random volume name using same method as log analytics workspace
def _generate_secret_volume_name():
    import re
    prefix = "secret-volume"
    # volume name must be lowercase
    suffix = _new_tiny_guid().lower()
    maxLength = 40

    name = "{}-{}".format(
        prefix,
        suffix
    )

    if len(name) > maxLength:
        name = name[:maxLength]
    return name


# Follow same naming convention as Portal
def _generate_log_analytics_workspace_name(resource_group_name):
    import re
    prefix = "workspace"
    suffix = _new_tiny_guid()
    alphaNumericRG = resource_group_name
    alphaNumericRG = re.sub(r'[^0-9a-z]', '', resource_group_name)
    maxLength = 40

    name = "{}-{}{}".format(
        prefix,
        alphaNumericRG,
        suffix
    )

    if len(name) > maxLength:
        name = name[:maxLength]
    return name


def _get_log_analytics_workspace_name(cmd, logs_customer_id, resource_group_name):
    log_analytics_client = log_analytics_client_factory(cmd.cli_ctx)
    logs_list = log_analytics_client.list_by_resource_group(resource_group_name)
    for log in logs_list:
        if log.customer_id.lower() == logs_customer_id.lower():
            return log.name
    raise ResourceNotFoundError("Cannot find Log Analytics workspace with customer ID {}".format(logs_customer_id))


def _generate_log_analytics_if_not_provided(cmd, logs_customer_id, logs_key, location, resource_group_name):  # pylint: disable=too-many-statements
    if logs_customer_id is None and logs_key is None:
        logger.warning("No Log Analytics workspace provided.")
        _validate_subscription_registered(cmd, LOG_ANALYTICS_RP)

        try:
            log_analytics_client = log_analytics_client_factory(cmd.cli_ctx)
            log_analytics_shared_key_client = log_analytics_shared_key_client_factory(cmd.cli_ctx)
        except Exception as ex:
            handle_raw_exception(ex)

        log_analytics_location = location
        try:
            _ensure_location_allowed(cmd, log_analytics_location, LOG_ANALYTICS_RP, "workspaces")
        except ValidationError:  # pylint: disable=broad-except
            log_analytics_location = _get_default_log_analytics_location(cmd)

        from azure.cli.core.commands import LongRunningOperation
        from azure.mgmt.loganalytics.models import Workspace

        workspace_name = _generate_log_analytics_workspace_name(resource_group_name)
        workspace_instance = Workspace(location=log_analytics_location)
        logger.warning("Generating a Log Analytics workspace with name \"{}\"".format(workspace_name))  # pylint: disable=logging-format-interpolation

        try:
            poller = log_analytics_client.begin_create_or_update(resource_group_name, workspace_name, workspace_instance)
            log_analytics_workspace = LongRunningOperation(cmd.cli_ctx)(poller)
        except Exception as ex:
            handle_raw_exception(ex)

        logs_customer_id = log_analytics_workspace.customer_id
        try:
            logs_key = log_analytics_shared_key_client.get_shared_keys(
                workspace_name=workspace_name,
                resource_group_name=resource_group_name).primary_shared_key
        except Exception as ex:
            handle_raw_exception(ex)

    elif logs_customer_id is None:
        raise ValidationError("Usage error: Supply the --logs-customer-id associated with the --logs-key")
    elif logs_key is None:  # Try finding the logs-key
        log_analytics_client = log_analytics_client_factory(cmd.cli_ctx)
        log_analytics_shared_key_client = log_analytics_shared_key_client_factory(cmd.cli_ctx)

        log_analytics_name = None
        log_analytics_rg = None

        try:
            log_analytics = log_analytics_client.list()
        except Exception as ex:
            handle_raw_exception(ex)

        for la in log_analytics:
            if la.customer_id and la.customer_id.lower() == logs_customer_id.lower():
                log_analytics_name = la.name
                parsed_la = parse_resource_id(la.id)
                log_analytics_rg = parsed_la['resource_group']

        if log_analytics_name is None:
            raise ValidationError('Usage error: Supply the --logs-key associated with the --logs-customer-id')

        try:
            shared_keys = log_analytics_shared_key_client.get_shared_keys(workspace_name=log_analytics_name, resource_group_name=log_analytics_rg)
        except Exception as ex:
            handle_raw_exception(ex)

        if not shared_keys or not shared_keys.primary_shared_key:
            raise ValidationError('Usage error: Supply the --logs-key associated with the --logs-customer-id')

        logs_key = shared_keys.primary_shared_key

    return logs_customer_id, logs_key


def _get_existing_secrets(cmd, resource_group_name, name, containerapp_def, appType=AppType.ContainerApp):
    if "secrets" not in containerapp_def["properties"]["configuration"]:
        containerapp_def["properties"]["configuration"]["secrets"] = []
    else:
        secrets = []
        try:
            if appType == AppType.ContainerApp:
                secrets = ContainerAppClient.list_secrets(cmd=cmd, resource_group_name=resource_group_name, name=name)
            if appType == AppType.ContainerAppJob:
                secrets = ContainerAppsJobClient.list_secrets(cmd=cmd, resource_group_name=resource_group_name, name=name)
        except Exception as e:  # pylint: disable=broad-except
            handle_raw_exception(e)

        containerapp_def["properties"]["configuration"]["secrets"] = secrets["value"]


def _ensure_identity_resource_id(subscription_id, resource_group, resource):
    if is_valid_resource_id(resource):
        return resource

    return resource_id(subscription=subscription_id,
                       resource_group=resource_group,
                       namespace='Microsoft.ManagedIdentity',
                       type='userAssignedIdentities',
                       name=resource)


def _add_or_update_secrets(containerapp_def, add_secrets):
    if "secrets" not in containerapp_def["properties"]["configuration"]:
        containerapp_def["properties"]["configuration"]["secrets"] = []
    for new_secret in add_secrets:
        is_existing = False
        for existing_secret in containerapp_def["properties"]["configuration"]["secrets"]:
            if existing_secret["name"].lower() == new_secret["name"].lower():
                is_existing = True
                existing_secret["value"] = new_secret["value"]
                existing_secret["keyVaultUrl"] = new_secret["keyVaultUrl"]
                existing_secret["identity"] = new_secret["identity"]
                break

        if not is_existing:
            containerapp_def["properties"]["configuration"]["secrets"].append(new_secret)


def _remove_registry_secret(containerapp_def, server, username):
    if urlparse(server).hostname is not None:
        registry_secret_name = "{server}-{user}".format(server=urlparse(server).hostname.replace('.', ''), user=username.lower())
    else:
        registry_secret_name = "{server}-{user}".format(server=server.replace('.', ''), user=username.lower())

    _remove_secret(containerapp_def, secret_name=registry_secret_name)


def _remove_secret(containerapp_def, secret_name):
    if "secrets" not in containerapp_def["properties"]["configuration"]:
        containerapp_def["properties"]["configuration"]["secrets"] = []

    for index, value in enumerate(containerapp_def["properties"]["configuration"]["secrets"]):
        existing_secret = value
        if existing_secret["name"].lower() == secret_name.lower():
            containerapp_def["properties"]["configuration"]["secrets"].pop(index)
            break


def _add_or_update_env_vars(existing_env_vars, new_env_vars):
    for new_env_var in new_env_vars:

        # Check if updating existing env var
        is_existing = False
        for existing_env_var in existing_env_vars:
            if existing_env_var["name"].lower() == new_env_var["name"].lower():
                is_existing = True

                if "value" in new_env_var:
                    existing_env_var["value"] = new_env_var["value"]
                else:
                    existing_env_var["value"] = None

                if "secretRef" in new_env_var:
                    existing_env_var["secretRef"] = new_env_var["secretRef"]
                else:
                    existing_env_var["secretRef"] = None
                break

        # If not updating existing env var, add it as a new env var
        if not is_existing:
            existing_env_vars.append(new_env_var)


def _remove_env_vars(existing_env_vars, remove_env_vars):
    for old_env_var in remove_env_vars:

        # Check if updating existing env var
        is_existing = False
        for i, value in enumerate(existing_env_vars):
            existing_env_var = value
            if existing_env_var["name"].lower() == old_env_var.lower():
                is_existing = True
                existing_env_vars.pop(i)
                break

        # If not updating existing env var, add it as a new env var
        if not is_existing:
            logger.warning("Environment variable {} does not exist.".format(old_env_var))  # pylint: disable=logging-format-interpolation


def _remove_env_vars(existing_env_vars, remove_env_vars):
    for old_env_var in remove_env_vars:

        # Check if updating existing env var
        is_existing = False
        for index, value in enumerate(existing_env_vars):
            existing_env_var = value
            if existing_env_var["name"].lower() == old_env_var.lower():
                is_existing = True
                existing_env_vars.pop(index)
                break

        # If not updating existing env var, add it as a new env var
        if not is_existing:
            logger.warning("Environment variable {} does not exist.".format(old_env_var))  # pylint: disable=logging-format-interpolation


def _add_or_update_tags(containerapp_def, tags):
    if 'tags' not in containerapp_def:
        if tags:
            containerapp_def['tags'] = tags
        else:
            containerapp_def['tags'] = {}
    else:
        for key in tags:
            containerapp_def['tags'][key] = tags[key]


def _object_to_dict(obj):

    def default_handler(x):
        if isinstance(x, datetime):
            return x.isoformat()
        return x.__dict__

    return json.loads(json.dumps(obj, default=default_handler))


def _to_camel_case(snake_str):
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


def _convert_object_from_snake_to_camel_case(o):
    if isinstance(o, list):
        return [_convert_object_from_snake_to_camel_case(i) if isinstance(i, (dict, list)) else i for i in o]
    return {
        _to_camel_case(a): _convert_object_from_snake_to_camel_case(b) if isinstance(b, (dict, list)) else b for a, b in o.items()
    }


def _remove_additional_attributes(o):
    if isinstance(o, list):
        for i in o:
            _remove_additional_attributes(i)
    elif isinstance(o, dict):
        if "additionalProperties" in o:
            del o["additionalProperties"]

        for key in o:
            _remove_additional_attributes(o[key])


def _remove_readonly_attributes(containerapp_def):
    unneeded_properties = [
        "id",
        "name",
        "type",
        "systemData",
        "provisioningState",
        "latestRevisionName",
        "latestRevisionFqdn",
        "customDomainVerificationId",
        "outboundIpAddresses",
        "fqdn",
        "runningStatus",
        "runningState"
    ]

    for unneeded_property in unneeded_properties:
        if unneeded_property in containerapp_def:
            del containerapp_def[unneeded_property]
        elif unneeded_property in containerapp_def['properties']:
            del containerapp_def['properties'][unneeded_property]


# Remove null/None/empty properties in a model since the PATCH API will delete those. Not needed once we move to the SDK
def clean_null_values(d):
    if isinstance(d, dict):
        return {
            k: v
            for k, v in ((k, clean_null_values(v)) for k, v in d.items())
            if (isinstance(v, dict) and len(v.items()) > 0) or (not isinstance(v, dict) and v is not None)
        }
    if isinstance(d, list):
        return [v for v in map(clean_null_values, d) if v]
    return d


def _populate_secret_values(containerapp_def, secret_values):
    secrets = safe_get(containerapp_def, "properties", "configuration", "secrets", default=None)
    if not secrets:
        secrets = []
    if not secret_values:
        secret_values = []
    index = 0
    while index < len(secrets):
        value = secrets[index]
        if "value" not in value or not value["value"]:
            try:
                value["value"] = next(s["value"] for s in secret_values if s["name"] == value["name"])
            except StopIteration:
                pass
        index += 1


def _remove_dapr_readonly_attributes(daprcomponent_def):
    unneeded_properties = [
        "id",
        "name",
        "type",
        "systemData",
        "provisioningState",
        "latestRevisionName",
        "latestRevisionFqdn",
        "customDomainVerificationId",
        "outboundIpAddresses",
        "deploymentErrors",
        "fqdn"
    ]

    for unneeded_property in unneeded_properties:
        if unneeded_property in daprcomponent_def:
            del daprcomponent_def[unneeded_property]


def update_nested_dictionary(orig_dict, new_dict):
    # Recursively update a nested dictionary. If the value is a list, replace the old list with new list
    from collections.abc import Mapping

    for key, val in new_dict.items():
        if isinstance(val, Mapping):
            tmp = update_nested_dictionary(orig_dict.get(key, {}), val)
            orig_dict[key] = tmp
        elif isinstance(val, list):
            if new_dict[key]:
                orig_dict[key] = new_dict[key]
        else:
            if new_dict[key] is not None:
                orig_dict[key] = new_dict[key]
    return orig_dict


def _validate_weight(weight):
    try:
        n = int(weight)
        if 0 <= n <= 100:
            return True
        raise ValidationError('Traffic weights must be integers between 0 and 100')
    except ValueError as ex:
        raise ValidationError('Traffic weights must be integers between 0 and 100') from ex


def _update_revision_weights(containerapp_def, list_weights):
    old_weight_sum = 0
    if "traffic" not in containerapp_def["properties"]["configuration"]["ingress"]:
        containerapp_def["properties"]["configuration"]["ingress"]["traffic"] = []

    if not list_weights:
        return 0

    for new_weight in list_weights:
        key_val = new_weight.split('=', 1)
        if len(key_val) != 2:
            raise ValidationError('Traffic weights must be in format \"<revision>=<weight> <revision2>=<weight2> ...\"')
        revision = key_val[0]
        weight = key_val[1]
        _validate_weight(weight)
        is_existing = False

        for existing_weight in containerapp_def["properties"]["configuration"]["ingress"]["traffic"]:
            if "latestRevision" in existing_weight and existing_weight["latestRevision"]:
                if revision.lower() == "latest":
                    old_weight_sum += existing_weight["weight"]
                    existing_weight["weight"] = weight
                    is_existing = True
                    break
            elif "revisionName" in existing_weight and existing_weight["revisionName"].lower() == revision.lower():
                old_weight_sum += existing_weight["weight"]
                existing_weight["weight"] = weight
                is_existing = True
                break
        if not is_existing:
            containerapp_def["properties"]["configuration"]["ingress"]["traffic"].append({
                "revisionName": revision if revision.lower() != "latest" else None,
                "weight": int(weight),
                "latestRevision": revision.lower() == "latest"
            })
    return old_weight_sum


def _validate_revision_name(cmd, revision, resource_group_name, name):
    if revision.lower() == "latest":
        return
    revision_def = None
    try:
        revision_def = ContainerAppClient.show_revision(cmd, resource_group_name, name, revision)
    except:  # pylint: disable=bare-except
        pass

    if not revision_def:
        raise ValidationError(f"Revision '{revision}' is not a valid revision name.")


def _append_label_weights(containerapp_def, label_weights, revision_weights):
    if "traffic" not in containerapp_def["properties"]["configuration"]["ingress"]:
        containerapp_def["properties"]["configuration"]["ingress"]["traffic"] = []

    if not label_weights:
        return

    bad_labels = []
    revision_weight_names = [w.split('=', 1)[0].lower() for w in revision_weights]  # this is to check if we already have that revision weight passed
    for new_weight in label_weights:
        key_val = new_weight.split('=', 1)
        if len(key_val) != 2:
            raise ValidationError('Traffic weights must be in format \"<revision>=<weight> <revision2>=<weight2> ...\"')
        label = key_val[0]
        weight = key_val[1]
        _validate_weight(weight)
        is_existing = False

        for existing_weight in containerapp_def["properties"]["configuration"]["ingress"]["traffic"]:
            if "label" in existing_weight and existing_weight["label"].lower() == label.lower():
                if "revisionName" in existing_weight and existing_weight["revisionName"] and existing_weight["revisionName"].lower() in revision_weight_names:
                    logger.warning("Already passed value for revision {}, will not overwrite with {}.".format(existing_weight["revisionName"], new_weight))  # pylint: disable=logging-format-interpolation
                    is_existing = True
                    break
                revision_weights.append("{}={}".format(existing_weight["revisionName"] if "revisionName" in existing_weight and existing_weight["revisionName"] else "latest", weight))
                is_existing = True
                break

        if not is_existing:
            bad_labels.append(label)

    if len(bad_labels) > 0:
        raise ValidationError(f"No labels '{', '.join(bad_labels)}' assigned to any traffic weight.")


def _update_weights(containerapp_def, revision_weights, old_weight_sum):

    new_weight_sum = sum([int(w.split('=', 1)[1]) for w in revision_weights])
    revision_weight_names = [w.split('=', 1)[0].lower() for w in revision_weights]
    divisor = sum([int(w["weight"]) for w in containerapp_def["properties"]["configuration"]["ingress"]["traffic"]]) - new_weight_sum
    # if there is no change to be made, don't even try (also can't divide by zero)
    if divisor == 0:
        return

    scale_factor = (old_weight_sum - new_weight_sum) / divisor + 1

    for existing_weight in containerapp_def["properties"]["configuration"]["ingress"]["traffic"]:
        if "latestRevision" in existing_weight and existing_weight["latestRevision"]:
            if "latest" not in revision_weight_names:
                existing_weight["weight"] = round(scale_factor * existing_weight["weight"])
        elif "revisionName" in existing_weight and existing_weight["revisionName"].lower() not in revision_weight_names:
            existing_weight["weight"] = round(scale_factor * existing_weight["weight"])

    total_sum = sum([int(w["weight"]) for w in containerapp_def["properties"]["configuration"]["ingress"]["traffic"]])
    index = 0
    while total_sum < 100:
        weight = containerapp_def["properties"]["configuration"]["ingress"]["traffic"][index % len(containerapp_def["properties"]["configuration"]["ingress"]["traffic"])]
        index += 1
        total_sum += 1
        weight["weight"] += 1


def _validate_traffic_sum(revision_weights):
    weight_sum = sum([int(w.split('=', 1)[1]) for w in revision_weights if len(w.split('=', 1)) == 2 and _validate_weight(w.split('=', 1)[1])])
    if weight_sum > 100:
        raise ValidationError("Traffic sums may not exceed 100.")


def _get_app_from_revision(revision):
    if not revision:
        raise ValidationError('Invalid revision. Revision must not be empty')
    if revision.lower() == "latest":
        raise ValidationError('Please provide a name for your containerapp. Cannot lookup name of containerapp without a full revision name.')
    revision = revision.split('--')
    revision.pop()
    revision = "--".join(revision)
    return revision


def _infer_acr_credentials(cmd, registry_server, disable_warnings=False):
    # If registry is Azure Container Registry, we can try inferring credentials
    if ACR_IMAGE_SUFFIX not in registry_server:
        raise RequiredArgumentMissingError('Registry username and password are required if not using Azure Container Registry.')
    not disable_warnings and logger.warning('No credential was provided to access Azure Container Registry. Trying to look up credentials...')
    parsed = urlparse(registry_server)
    registry_name = (parsed.netloc if parsed.scheme else parsed.path).split('.')[0]

    try:
        registry_user, registry_pass, registry_rg = _get_acr_cred(cmd.cli_ctx, registry_name)  # pylint: disable=unused-variable
        return (registry_user, registry_pass)
    except Exception as ex:
        raise RequiredArgumentMissingError('Failed to retrieve credentials for container registry {}. Please provide the registry username and password'.format(registry_name)) from ex


def _registry_exists(containerapp_def, registry_server):
    exists = False
    if "properties" in containerapp_def and "configuration" in containerapp_def["properties"] and "registries" in containerapp_def["properties"]["configuration"]:
        for registry in containerapp_def["properties"]["configuration"]["registries"]:
            if "server" in registry and registry["server"] and registry["server"].lower() == registry_server.lower():
                exists = True
                break
    return exists


# get a value from nested dict without getting IndexError (returns None instead)
# for example, model["key1"]["key2"]["key3"] would become safe_get(model, "key1", "key2", "key3")
def safe_get(model, *keys, default=None):
    if not model:
        return default
    for k in keys[:-1]:
        model = model.get(k)
        if model is None:
            return default
    value = model.get(keys[-1], default)
    return default if not value else value


def safe_set(model, *keys, value):
    penult = {}
    for k in keys:
        if k not in model:
            model[k] = {}
        penult = model
        model = model[k]
    penult[keys[-1]] = value


def is_platform_windows():
    return platform.system() == "Windows"


def get_randomized_name(prefix, name=None, initial="rg"):
    from random import randint
    default = "{}_{}_{:04}".format(prefix, initial, randint(0, 9999))
    if name is not None:
        return name
    return default


def generate_randomized_cert_name(thumbprint, prefix, initial="rg"):
    from random import randint
    cert_name = "{}-{}-{}-{:04}".format(prefix[:14], initial[:14], thumbprint[:4].lower(), randint(0, 9999))
    for c in cert_name:
        if not (c.isalnum() or c == '-' or c == '.'):
            cert_name = cert_name.replace(c, '-')
    return cert_name.lower()


def generate_randomized_managed_cert_name(hostname, env_name):
    from random import randint
    cert_name = "mc-{}-{}-{:04}".format(env_name[:14], hostname[:16].lower(), randint(0, 9999))
    for c in cert_name:
        if not (c.isalnum() or c == '-'):
            cert_name = cert_name.replace(c, '-')
    return cert_name.lower()


def _set_webapp_up_default_args(cmd, resource_group_name, location, name, registry_server):
    from azure.cli.core.util import ConfiguredDefaultSetter
    with ConfiguredDefaultSetter(cmd.cli_ctx.config, True):
        logger.warning("Setting 'az containerapp up' default arguments for current directory. "
                       "Manage defaults with 'az configure --scope local'")

        cmd.cli_ctx.config.set_value('defaults', 'resource_group_name', resource_group_name)
        logger.warning("--resource-group/-g default: %s", resource_group_name)

        cmd.cli_ctx.config.set_value('defaults', 'location', location)
        logger.warning("--location/-l default: %s", location)

        cmd.cli_ctx.config.set_value('defaults', 'name', name)
        logger.warning("--name/-n default: %s", name)

        # cmd.cli_ctx.config.set_value('defaults', 'managed_env', managed_env)
        # logger.warning("--environment default: %s", managed_env)

        cmd.cli_ctx.config.set_value('defaults', 'registry_server', registry_server)
        logger.warning("--registry-server default: %s", registry_server)


def get_profile_username():
    from azure.cli.core._profile import Profile
    user = Profile().get_current_account_user()
    user = user.split('@', 1)[0]
    if len(user.split('#', 1)) > 1:  # on cloudShell user is in format live.com#user@domain.com
        user = user.split('#', 1)[1]
    return user


def create_resource_group(cmd, rg_name, location):
    from azure.cli.core.profiles import get_sdk
    rcf = _resource_client_factory(cmd.cli_ctx)
    resource_group = get_sdk(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES, 'ResourceGroup', mod='models')
    rg_params = resource_group(location=location)
    return rcf.resource_groups.create_or_update(rg_name, rg_params)


def get_resource_group(cmd, rg_name):
    rcf = _resource_client_factory(cmd.cli_ctx)
    return rcf.resource_groups.get(rg_name)


def _resource_client_factory(cli_ctx, **_):
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES)


def queue_acr_build(cmd, registry_rg, registry_name, img_name, src_dir, dockerfile="Dockerfile", quiet=False):
    import os
    import uuid
    import tempfile
    from ._archive_utils import upload_source_code
    from azure.cli.command_modules.acr._stream_utils import stream_logs
    from azure.cli.command_modules.acr._client_factory import cf_acr_registries_tasks
    from azure.cli.core.commands import LongRunningOperation

    # client_registries = get_acr_service_client(cmd.cli_ctx).registries
    client_registries = cf_acr_registries_tasks(cmd.cli_ctx)

    if not os.path.isdir(src_dir):
        raise ValidationError("Source directory should be a local directory path.")

    docker_file_path = os.path.join(src_dir, dockerfile)
    if not os.path.isfile(docker_file_path):
        raise ValidationError("Unable to find '{}'.".format(docker_file_path))

    # NOTE: os.path.basename is unable to parse "\" in the file path
    original_docker_file_name = os.path.basename(docker_file_path.replace("\\", "/"))
    docker_file_in_tar = '{}_{}'.format(uuid.uuid4().hex, original_docker_file_name)
    tar_file_path = os.path.join(tempfile.gettempdir(), 'build_archive_{}.tar.gz'.format(uuid.uuid4().hex))

    source_location = upload_source_code(cmd, client_registries, registry_name, registry_rg, src_dir, tar_file_path, docker_file_path, docker_file_in_tar)

    # For local source, the docker file is added separately into tar as the new file name (docker_file_in_tar)
    # So we need to update the docker_file_path
    docker_file_path = docker_file_in_tar

    OS, Architecture = cmd.get_models('OS', 'Architecture', resource_type=ResourceType.MGMT_CONTAINERREGISTRY, operation_group='runs')
    # Default platform values
    platform_os = OS.linux.value
    platform_arch = Architecture.amd64.value
    platform_variant = None

    DockerBuildRequest, PlatformProperties = cmd.get_models('DockerBuildRequest', 'PlatformProperties',
                                                            resource_type=ResourceType.MGMT_CONTAINERREGISTRY, operation_group='runs')
    docker_build_request = DockerBuildRequest(
        image_names=[img_name],
        is_push_enabled=True,
        source_location=source_location,
        platform=PlatformProperties(
            os=platform_os,
            architecture=platform_arch,
            variant=platform_variant
        ),
        docker_file_path=docker_file_path,
        timeout=None,
        arguments=[])

    queued_build = client_registries.schedule_run(
        resource_group_name=registry_rg,
        registry_name=registry_name,
        run_request=docker_build_request)

    run_id = queued_build.run_id
    logger.info("Queued a build with ID: %s", run_id)
    not quiet and logger.info("Waiting for agent...")

    from azure.cli.command_modules.acr._client_factory import (cf_acr_runs)
    from ._acr_run_polling import get_run_with_polling
    client_runs = cf_acr_runs(cmd.cli_ctx)

    if quiet:
        lro_poller = get_run_with_polling(cmd, client_runs, run_id, registry_name, registry_rg)
        acr = LongRunningOperation(cmd.cli_ctx)(lro_poller)
        logger.info("Build {}.".format(acr.status.lower()))  # pylint: disable=logging-format-interpolation
        if acr.status.lower() != "succeeded":
            raise CLIInternalError("ACR build {}.".format(acr.status.lower()))
        return acr

    return stream_logs(cmd, client_runs, run_id, registry_name, registry_rg, None, False, True)


def _get_acr_cred(cli_ctx, registry_name):
    from azure.cli.core.commands.parameters import get_resources_in_subscription

    client = get_mgmt_service_client(cli_ctx, ContainerRegistryManagementClient).registries

    result = get_resources_in_subscription(cli_ctx, 'Microsoft.ContainerRegistry/registries')
    result = [item for item in result if item.name.lower() == registry_name]
    if not result or len(result) > 1:
        raise ResourceNotFoundError("No resource or more than one were found with name '{}'.".format(registry_name))
    resource_group_name = parse_resource_id(result[0].id)['resource_group']

    registry = client.get(resource_group_name, registry_name)

    if registry.admin_user_enabled:  # pylint: disable=no-member
        cred = client.list_credentials(resource_group_name, registry_name)
        return cred.username, cred.passwords[0].value, resource_group_name
    raise ResourceNotFoundError("Failed to retrieve container registry credentials. Please either provide the "
                                "credentials or run 'az acr update -n {} --admin-enabled true' to enable "
                                "admin first.".format(registry_name))


def create_new_acr(cmd, registry_name, resource_group_name, location=None, sku="Basic"):
    # from azure.cli.command_modules.acr.custom import acr_create
    from azure.cli.command_modules.acr._client_factory import cf_acr_registries
    from azure.cli.core.commands import LongRunningOperation

    client = cf_acr_registries(cmd.cli_ctx)
    # return acr_create(cmd, client, registry_name, resource_group_name, sku, location)

    Registry, Sku = cmd.get_models('Registry', 'Sku', resource_type=ResourceType.MGMT_CONTAINERREGISTRY, operation_group="registries")
    registry = Registry(location=location, sku=Sku(name=sku), admin_user_enabled=True,
                        zone_redundancy=None, tags=None)

    lro_poller = client.begin_create(resource_group_name, registry_name, registry)
    acr = LongRunningOperation(cmd.cli_ctx)(lro_poller)
    return acr


def set_field_in_auth_settings(auth_settings, set_string):
    if set_string is not None:
        split1 = set_string.split("=", 1)
        fieldName = split1[0]
        fieldValue = split1[1]
        split2 = fieldName.split(".")
        auth_settings = set_field_in_auth_settings_recursive(split2, fieldValue, auth_settings)
    return auth_settings


def set_field_in_auth_settings_recursive(field_name_split, field_value, auth_settings):
    if len(field_name_split) == 1:
        if not field_value.startswith('[') or not field_value.endswith(']'):
            auth_settings[field_name_split[0]] = field_value
        else:
            field_value_list_string = field_value[1:-1]
            auth_settings[field_name_split[0]] = field_value_list_string.split(",")
        return auth_settings

    remaining_field_names = field_name_split[1:]
    if field_name_split[0] not in auth_settings:
        auth_settings[field_name_split[0]] = {}
    auth_settings[field_name_split[0]] = set_field_in_auth_settings_recursive(remaining_field_names,
                                                                              field_value,
                                                                              auth_settings[field_name_split[0]])
    return auth_settings


def update_http_settings_in_auth_settings(auth_settings, require_https, proxy_convention,
                                          proxy_custom_host_header, proxy_custom_proto_header):
    if require_https is not None:
        if "httpSettings" not in auth_settings:
            auth_settings["httpSettings"] = {}
        auth_settings["httpSettings"]["requireHttps"] = require_https

    if proxy_convention is not None:
        if "httpSettings" not in auth_settings:
            auth_settings["httpSettings"] = {}
        if "forwardProxy" not in auth_settings["httpSettings"]:
            auth_settings["httpSettings"]["forwardProxy"] = {}
        auth_settings["httpSettings"]["forwardProxy"]["convention"] = proxy_convention

    if proxy_custom_host_header is not None:
        if "httpSettings" not in auth_settings:
            auth_settings["httpSettings"] = {}
        if "forwardProxy" not in auth_settings["httpSettings"]:
            auth_settings["httpSettings"]["forwardProxy"] = {}
        auth_settings["httpSettings"]["forwardProxy"]["customHostHeaderName"] = proxy_custom_host_header

    if proxy_custom_proto_header is not None:
        if "httpSettings" not in auth_settings:
            auth_settings["httpSettings"] = {}
        if "forwardProxy" not in auth_settings["httpSettings"]:
            auth_settings["httpSettings"]["forwardProxy"] = {}
        auth_settings["httpSettings"]["forwardProxy"]["customProtoHeaderName"] = proxy_custom_proto_header

    return auth_settings


def get_oidc_client_setting_app_setting_name(provider_name):
    provider_name_prefix = provider_name.lower()[:10]  # secret names can't be too long
    return provider_name_prefix + "-authentication-secret"


# only accept .pfx or .pem file
def load_cert_file(file_path, cert_password=None):
    from base64 import b64encode
    from OpenSSL import crypto
    from cryptography.hazmat.primitives.serialization import pkcs12
    from cryptography.hazmat.primitives import hashes
    import os

    cert_data = None
    thumbprint = None
    blob = None
    try:
        with open(file_path, "rb") as f:
            if os.path.splitext(file_path)[1] in ['.pem']:
                cert_data = f.read()
                x509 = crypto.load_certificate(crypto.FILETYPE_PEM, cert_data)
                digest_algorithm = 'sha256'
                thumbprint = x509.digest(digest_algorithm).decode("utf-8").replace(':', '')
                blob = b64encode(cert_data).decode("utf-8")
            elif os.path.splitext(file_path)[1] in ['.pfx']:
                cert_data = f.read()
                try:
                    # The password to use to decrypt the data. None if the PKCS12 is not encrypted.
                    cert_password_bytes = cert_password.encode('utf-8') if cert_password else None
                    p12 = pkcs12.load_pkcs12(cert_data, cert_password_bytes)
                except Exception as e:
                    raise FileOperationError('Failed to load the certificate file. This may be due to an incorrect or missing password. Please double check and try again.\nError: {}'.format(e)) from e
                if p12.cert is None:
                    raise ValidationError("Failed to load the certificate file. The loading result is None.")
                x509 = p12.cert.certificate
                thumbprint = x509.fingerprint(hashes.SHA256()).hex().upper()
                blob = b64encode(cert_data).decode("utf-8")
            else:
                raise FileOperationError('Not a valid file type. Only .PFX and .PEM files are supported.')
    except Exception as e:
        raise CLIInternalError(e) from e
    return blob, thumbprint


def check_cert_name_availability(cmd, resource_group_name, name, cert_name):
    name_availability_request = {}
    name_availability_request["name"] = cert_name
    name_availability_request["type"] = CHECK_CERTIFICATE_NAME_AVAILABILITY_TYPE
    try:
        r = ManagedEnvironmentClient.check_name_availability(cmd, resource_group_name, name, name_availability_request)
    except CLIError as e:
        handle_raw_exception(e)
    return r


def prepare_managed_certificate_envelop(cmd, name, resource_group_name, hostname, validation_method, location=None):
    certificate_envelop = ManagedCertificateEnvelopModel
    certificate_envelop["location"] = location
    certificate_envelop["properties"]["subjectName"] = hostname
    certificate_envelop["properties"]["validationMethod"] = validation_method
    if not location:
        try:
            managed_env = ManagedEnvironmentClient.show(cmd, resource_group_name, name)
            certificate_envelop["location"] = managed_env["location"]
        except Exception as e:
            handle_raw_exception(e)
    return certificate_envelop


def check_managed_cert_name_availability(cmd, resource_group_name, name, cert_name):
    try:
        certs = ManagedEnvironmentClient.list_managed_certificates(cmd, resource_group_name, name)
        r = any(cert["name"] == cert_name and cert["properties"]["provisioningState"] in [PENDING_STATUS, SUCCEEDED_STATUS, UPDATING_STATUS] for cert in certs)
    except CLIError as e:
        handle_raw_exception(e)
    return not r


def validate_hostname(cmd, resource_group_name, name, hostname):
    passed = False
    message = None
    try:
        r = ContainerAppClient.validate_domain(cmd, resource_group_name, name, hostname)
        passed = r["customDomainVerificationTest"] == "Passed" and not r["hasConflictOnManagedEnvironment"]
        if "customDomainVerificationFailureInfo" in r:
            message = r["customDomainVerificationFailureInfo"]["message"]
        elif r["hasConflictOnManagedEnvironment"] and ("conflictingContainerAppResourceId" in r):
            message = "Custom Domain {} Conflicts on the same environment with {}.".format(hostname, r["conflictingContainerAppResourceId"])
    except CLIError as e:
        handle_raw_exception(e)
    return passed, message


def patch_new_custom_domain(cmd, resource_group_name, name, new_custom_domains):
    envelope = ContainerAppCustomDomainEnvelopeModel
    envelope["properties"]["configuration"]["ingress"]["customDomains"] = new_custom_domains
    try:
        r = ContainerAppClient.update(cmd, resource_group_name, name, envelope)
    except CLIError as e:
        handle_raw_exception(e)
    return safe_get(r, "properties", "configuration", "ingress", "customDomains", default=[])


def get_custom_domains(cmd, resource_group_name, name, location=None, environment=None):
    try:
        app = ContainerAppClient.show(cmd=cmd, resource_group_name=resource_group_name, name=name)
        if location:
            _ensure_location_allowed(cmd, location, "Microsoft.App", "containerApps")
            if _normalize_location(cmd, app["location"]) != _normalize_location(cmd, location):
                raise ResourceNotFoundError('Container app {} is not in location {}.'.format(name, location))
        if environment and (_get_name(environment) != _get_name(app["properties"]["environmentId"])):
            raise ResourceNotFoundError('Container app {} is not under environment {}.'.format(name, environment))
        custom_domains = safe_get(app, "properties", "configuration", "ingress", "customDomains", default=[])
    except CLIError as e:
        handle_raw_exception(e)
    return custom_domains


def set_managed_identity(cmd, resource_group_name, containerapp_def, system_assigned=False, user_assigned=None):
    assign_system_identity = system_assigned
    if not user_assigned:
        user_assigned = []
    assign_user_identities = [x.lower() for x in user_assigned]

    # If identity not returned
    try:
        containerapp_def["identity"]
        containerapp_def["identity"]["type"]
    except:
        containerapp_def["identity"] = {}
        containerapp_def["identity"]["type"] = "None"

    if assign_system_identity and "SystemAssigned" in containerapp_def["identity"]["type"]:
        logger.warning("System identity is already assigned to containerapp")

    # Assign correct type
    try:
        if containerapp_def["identity"]["type"] != "None":
            if containerapp_def["identity"]["type"] == "SystemAssigned" and assign_user_identities:
                containerapp_def["identity"]["type"] = "SystemAssigned,UserAssigned"
            if containerapp_def["identity"]["type"] == "UserAssigned" and assign_system_identity:
                containerapp_def["identity"]["type"] = "SystemAssigned,UserAssigned"
        else:
            if assign_system_identity and assign_user_identities:
                containerapp_def["identity"]["type"] = "SystemAssigned,UserAssigned"
            elif assign_system_identity:
                containerapp_def["identity"]["type"] = "SystemAssigned"
            elif assign_user_identities:
                containerapp_def["identity"]["type"] = "UserAssigned"
    except:
        # Always returns "type": "None" when CA has no previous identities
        pass

    if assign_user_identities:
        try:
            containerapp_def["identity"]["userAssignedIdentities"]
        except:
            containerapp_def["identity"]["userAssignedIdentities"] = {}

        subscription_id = get_subscription_id(cmd.cli_ctx)

        for r in assign_user_identities:
            r = _ensure_identity_resource_id(subscription_id, resource_group_name, r).replace("resourceGroup", "resourcegroup")
            isExisting = False

            if not containerapp_def["identity"].get("userAssignedIdentities"):
                containerapp_def["identity"]["userAssignedIdentities"] = {}

            for old_user_identity in containerapp_def["identity"]["userAssignedIdentities"]:
                if old_user_identity.lower() == r.lower():
                    isExisting = True
                    logger.warning("User identity %s is already assigned to containerapp", old_user_identity)
                    break

            if not isExisting:
                containerapp_def["identity"]["userAssignedIdentities"][r] = {}


def create_acrpull_role_assignment(cmd, registry_server, registry_identity=None, service_principal=None, skip_error=False):
    from azure.cli.command_modules.acr._utils import ResourceNotFound

    if registry_identity:
        registry_identity_parsed = parse_resource_id(registry_identity)
        registry_identity_name, registry_identity_rg, registry_identity_sub = registry_identity_parsed.get("name"), registry_identity_parsed.get("resource_group"), registry_identity_parsed.get("subscription")
        sp_id = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_MSI, subscription_id=registry_identity_sub).user_assigned_identities.get(resource_name=registry_identity_name, resource_group_name=registry_identity_rg).principal_id
    else:
        sp_id = service_principal

    client = get_mgmt_service_client(cmd.cli_ctx, ContainerRegistryManagementClient).registries
    try:
        acr_id = acr_show(cmd, client, registry_server[: registry_server.rindex(ACR_IMAGE_SUFFIX)]).id
    except ResourceNotFound as e:
        message = (f"Role assignment failed with error message: \"{' '.join(e.args)}\". \n"
                   f"To add the role assignment manually, please run 'az role assignment create --assignee {sp_id} --scope <container-registry-resource-id> --role acrpull'. \n"
                   "You may have to restart the containerapp with 'az containerapp revision restart'.")
        logger.warning(message)
        return

    retries = 10
    while retries > 0:
        try:
            create_role_assignment(cmd, role="acrpull", assignee=sp_id, scope=acr_id)
            return
        except Exception as e:
            retries -= 1
            if retries <= 0:
                message = (f"Role assignment failed with error message: \"{' '.join(e.args)}\". \n"
                           f"To add the role assignment manually, please run 'az role assignment create --assignee {sp_id} --scope {acr_id} --role acrpull'. \n"
                           "You may have to restart the containerapp with 'az containerapp revision restart'.")
                if skip_error:
                    logger.error(message)
                else:
                    raise UnauthorizedError(message) from e
            else:
                time.sleep(5)


def is_registry_msi_system(identity):
    if identity is None:
        return False
    return identity.lower() == "system"


def validate_environment_location(cmd, location):
    res_locations = list_environment_locations(cmd)

    allowed_locs = ", ".join(res_locations)

    if location:
        try:
            _ensure_location_allowed(cmd, location, CONTAINER_APPS_RP, "managedEnvironments")

            return location
        except Exception as e:  # pylint: disable=broad-except
            raise ValidationError("You cannot create a Containerapp environment in location {}. List of eligible locations: {}.".format(location, allowed_locs)) from e
    else:
        return res_locations[0]


def list_environment_locations(cmd):
    providers_client = providers_client_factory(cmd.cli_ctx, get_subscription_id(cmd.cli_ctx))
    resource_types = getattr(providers_client.get(CONTAINER_APPS_RP), 'resource_types', [])
    res_locations = []
    for res in resource_types:
        if res and getattr(res, 'resource_type', "") == "managedEnvironments":
            res_locations = getattr(res, 'locations', [])

    res_locations = [res_loc.lower().replace(" ", "").replace("(", "").replace(")", "") for res_loc in res_locations if res_loc.strip()]

    return res_locations


# normalizes workload profile type
def get_workload_profile_type(cmd, name, location):
    return name.upper()


def get_default_workload_profile(cmd, location):
    return "Consumption"


def get_default_workload_profile_name_from_env(cmd, env_def, resource_group):
    location = env_def["location"]
    api_default = get_default_workload_profile(cmd, location)
    env_profiles = WorkloadProfileClient.list(cmd, resource_group, env_def["name"])
    if api_default in [p["name"] for p in env_profiles]:
        return api_default
    return env_profiles[0]["name"]


def get_default_workload_profiles(cmd, location):
    profiles = [
        {
            "workloadProfileType": "Consumption",
            "Name": "Consumption"
        }
    ]
    return profiles


def ensure_workload_profile_supported(cmd, env_name, env_rg, workload_profile_name, managed_env_info):
    profile_names = [p["name"] for p in safe_get(managed_env_info, "properties", "workloadProfiles", default=[])]
    profile_names_lower = [p.lower() for p in profile_names]
    if workload_profile_name.lower() not in profile_names_lower:
        raise ValidationError(f"Not a valid workload profile name: '{workload_profile_name}'. The valid workload profiles names for this environment are: '{', '.join(profile_names)}'")


def set_ip_restrictions(ip_restrictions, ip_restriction_name, ip_address_range, description, action):
    updated = False
    for e in ip_restrictions:
        if e.get("name") and ip_restriction_name.lower() == e["name"].lower():
            e["description"] = description
            e["ipAddressRange"] = ip_address_range
            e["action"] = action
            updated = True
            break
    if not updated:
        new_ip_restriction = {
            "name": ip_restriction_name,
            "description": description,
            "ipAddressRange": ip_address_range,
            "action": action
        }
        ip_restrictions.append(new_ip_restriction)
    return ip_restrictions


def _azure_monitor_quickstart(cmd, name, resource_group_name, storage_account, logs_destination):
    if logs_destination != "azure-monitor":
        if storage_account:
            logger.warning("Storage accounts only accepted for Azure Monitor logs destination. Ignoring storage account value.")
        return
    if not storage_account:
        logger.warning("Azure monitor must be set up manually. Run `az monitor diagnostic-settings create --name mydiagnosticsettings --resource myEnvironmentId --storage-account myStorageAccountId --logs myJsonLogSettings` to set up Azure Monitor diagnostic settings on your storage account.")
        return

    from azure.cli.command_modules.monitor.operations.diagnostics_settings import create_diagnostics_settings
    from azure.cli.command_modules.monitor._client_factory import cf_diagnostics

    env_id = resource_id(subscription=get_subscription_id(cmd.cli_ctx),
                         resource_group=resource_group_name,
                         namespace='Microsoft.App',
                         type='managedEnvironments',
                         name=name)
    try:
        create_diagnostics_settings(client=cf_diagnostics(cmd.cli_ctx, None),
                                    name="diagnosticsettings",
                                    resource_uri=env_id,
                                    storage_account=storage_account,
                                    logs=json.loads(LOGS_STRING))
        logger.warning("Azure Monitor diagnastic settings created successfully.")
    except Exception as ex:
        handle_raw_exception(ex)


def certificate_location_matches(certificate_object, location=None):
    return format_location(certificate_object["location"]) == format_location(location) or not location


def certificate_thumbprint_matches(certificate_object, thumbprint=None):
    return certificate_object["properties"]["thumbprint"] == thumbprint or not thumbprint


def certificate_matches(certificate_object, location=None, thumbprint=None):
    return certificate_location_matches(certificate_object, location) and certificate_thumbprint_matches(certificate_object, thumbprint)


def format_location(location=None):
    if location:
        return location.lower().replace(" ", "").replace("(", "").replace(")", "")
    return location


def is_docker_running():
    try:
        # Run a simple 'docker stats --no-stream' command to check if the Docker daemon is running
        command = ["docker", "stats", "--no-stream"]
        with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as process:
            _, _ = process.communicate()
            return process.returncode == 0
    except Exception:
        return False


def get_pack_exec_path():
    try:
        dir_path = os.path.dirname(os.path.realpath(__file__))
        bin_folder = os.path.join(dir_path, "bin")
        if not os.path.exists(bin_folder):
            os.makedirs(bin_folder)

        pack_cli_version = "v0.29.0"
        exec_name = "pack"
        compressed_download_file_name = f"pack-{pack_cli_version}"
        host_os = platform.system()
        if host_os == "Windows":
            compressed_download_file_name = f"{compressed_download_file_name}-windows.zip"
            exec_name = "pack.exe"
        elif host_os == "Linux":
            compressed_download_file_name = f"{compressed_download_file_name}-linux.tgz"
        elif host_os == "Darwin":
            compressed_download_file_name = f"{compressed_download_file_name}-macos.tgz"
        else:
            raise Exception(f"Unsupported host OS: {host_os}")

        exec_path = os.path.join(bin_folder, exec_name)
        if os.path.exists(exec_path):
            return exec_path

        # Attempt to install the pack CLI
        url = f"https://github.com/buildpacks/pack/releases/download/{pack_cli_version}/{compressed_download_file_name}"
        with urlopen(url) as req:
            compressed_file = io.BytesIO(req.read())
            if host_os == "Windows":
                with zipfile.ZipFile(compressed_file) as zip_file:
                    for file in zip_file.namelist():
                        if file.endswith(exec_name):
                            with open(exec_path, "wb") as f:
                                f.write(zip_file.read(file))
            else:
                with tarfile.open(fileobj=compressed_file, mode="r:gz") as tar:
                    for tar_info in tar:
                        if tar_info.isfile() and tar_info.name.endswith(exec_name):
                            with open(exec_path, "wb") as f:
                                f.write(tar.extractfile(tar_info).read())

        # Add executable permissions for the current user if they don't exist
        if not os.access(exec_path, os.X_OK):
            st = os.stat(exec_path)
            os.chmod(exec_path, st.st_mode | stat.S_IXUSR)

        return exec_path
    except Exception as e:
        # Swallow any exceptions thrown when attempting to install pack CLI
        logger.warning(f"Failed to install pack CLI: {e}\n")

    return None


def patchable_check(repo_tag_split: str, oryx_builder_run_img_tags, inspect_result):
    # Check if the run image is based from a dotnet Mariner image in mcr.microsoft.com/oryx/builder
    # Get all the dotnet mariner run image tags from mcr.microsoft.com/oryx/builder and
    # compare the customer's run image with the latest patch version of the run image
    tag_prop = parse_oryx_mariner_tag(repo_tag_split)
    # Parsing the tag to a tag object
    result = {
        "targetContainerAppName": inspect_result["targetContainerAppName"],
        "targetContainerName": inspect_result["targetContainerName"],
        "targetContainerAppEnvironmentName": inspect_result["targetContainerAppEnvironmentName"],
        "targetResourceGroup": inspect_result["targetResourceGroup"],
        "targetImageName": inspect_result["image_name"],
        "oldRunImage": repo_tag_split,
        "newRunImage": None,
        "id": None,
    }
    if tag_prop is None:
        # If customer run image is not dotnet and tag doesn't match with oryx run image tag format,
        # return the result with the reason
        result["reason"] = "Image not based from a Mariner tag in mcr.microsoft.com/oryx/dotnet."
        return result
    elif len(str(tag_prop["version"]).split(".")) == 2:
        # If customer run image is dotnet, but the tag doesn't contain a patch version
        # e.g.: run-dontnet-aspnet-7.0-cbl-mariner2.0-xxxxxxx
        result["reason"] = "Image is using a run image version that doesn't contain a patch information."
        return result
    repo_tag_split = repo_tag_split.split("-")
    if repo_tag_split[1] == "dotnet":
        # If customer run image is dotnet, and successfully parsed, check if the run image is based from a dotnet Mariner image in mcr.microsoft.com/oryx/builder
        # Indexing to the correct framework, support, major and minor version, and mariner version
        # e.g.: run_img_tags -> framework -> support -> major.minor -> mariner version
        matching_version_info = oryx_builder_run_img_tags[repo_tag_split[2]][str(tag_prop["version"].major) + "." + str(tag_prop["version"].minor)][tag_prop["support"]][tag_prop["marinerVersion"]]
    # Check if the image minor version is less than the latest minor version
    if tag_prop["version"] < matching_version_info[0]["version"]:
        result["oldRunImage"] = tag_prop["fullTag"]
        if (tag_prop["version"].minor == matching_version_info[0]["version"].minor) and (tag_prop["version"].micro < matching_version_info[0]["version"].micro):
            # Patchable
            result["newRunImage"] = "mcr.microsoft.com/oryx/builder:" + matching_version_info[0]["fullTag"]
            result["id"] = hashlib.md5(str(result["oldRunImage"] + result["targetContainerName"] + result["targetContainerAppName"] + result["targetResourceGroup"] + result["newRunImage"]).encode()).hexdigest()
            result["reason"] = "New security patch released for your current run image."
        else:
            # Not patchable
            result["newRunImage"] = "mcr.microsoft.com/oryx/builder:" + matching_version_info[0]["fullTag"]
            result["id"] = None
            result["reason"] = "The image is not patchable. Please check for major or minor version upgrade."
    else:
        # Image is already up to date
        result["oldRunImage"] = tag_prop["fullTag"]
        result["reason"] = "The image is already up to date."
    return result


def get_current_mariner_tags() -> list(OryxMarinerRunImgTagProperty):
    r = requests.get("https://mcr.microsoft.com/v2/oryx/builder/tags/list", timeout=30)
    tags = r.json()
    tag_list = {}
    # only keep entries that contain keyword "mariner"
    tags = [tag for tag in tags["tags"] if "mariner" in tag]
    for tag in tags:
        tag_obj = parse_oryx_mariner_tag(tag)
        if tag_obj:
            major_minor_ver = str(tag_obj["version"].major) + "." + str(tag_obj["version"].minor)
            support = tag_obj["support"]
            framework = tag_obj["framework"]
            mariner_ver = tag_obj["marinerVersion"]
            if framework not in tag_list:
                tag_list[framework] = {major_minor_ver: {support: {mariner_ver: [tag_obj]}}}
            elif major_minor_ver not in tag_list[framework]:
                tag_list[framework][major_minor_ver] = {support: {mariner_ver: [tag_obj]}}
            elif support not in tag_list[framework][major_minor_ver]:
                tag_list[framework][major_minor_ver][support] = {mariner_ver: [tag_obj]}
            elif mariner_ver not in tag_list[framework][major_minor_ver][support]:
                tag_list[framework][major_minor_ver][support][mariner_ver] = [tag_obj]
            else:
                tag_list[framework][major_minor_ver][support][mariner_ver].append(tag_obj)
                tag_list[framework][major_minor_ver][support][mariner_ver].sort(reverse=True, key=lambda x: x["version"])
    return tag_list


def get_latest_buildpack_run_tag(framework, version, support="lts", mariner_version="cbl-mariner2.0"):
    tags = get_current_mariner_tags()
    try:
        return tags[framework][version][support][mariner_version][0]["fullTag"]
    except KeyError:
        return None


def parse_oryx_mariner_tag(tag: str) -> OryxMarinerRunImgTagProperty:
    tag_split = tag.split("-")
    if tag_split[0] == "run" and tag_split[1] == "dotnet":
        # Example: run-dotnet-aspnet-7.0.1-cbl-mariner2.0-20210415.1
        # Result: tag_obj = {
        #    "fullTag": "run-dotnet-aspnet-7.0.1-cbl-mariner2.0-20210415.1",
        #    "version": "7.0.1",
        #    "framework": "aspnet",
        #    "marinerVersion": "cbl-mariner2.0",
        #    "architectures": None,
        #    "support": "lts"}
        version_re = r"(\d+\.\d+(\.\d+)?).*?(cbl-mariner(\d+\.\d+))"
        re_matches = re.findall(version_re, tag)
        if len(re_matches) == 0:
            tag_obj = None
        else:
            tag_obj = {
                "fullTag": tag,
                "version": SemVer.parse(re_matches[0][0]),
                "framework": tag_split[2],
                "marinerVersion": re_matches[0][2],
                "architectures": None,
                "support": "lts",
            }
    else:
        tag_obj = None
    return tag_obj
