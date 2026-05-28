# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
from enum import EnumMeta

import requests
import yaml
from azext_load.data_plane.utils.constants import LoadTestConfigKeys, LoadTestTrendsKeys
from azext_load.data_plane.utils import validators, utils_yaml_config
from azext_load.vendored_sdks.loadtesting_mgmt import LoadTestMgmtClient
from azure.cli.core.azclierror import (
    FileOperationError,
    InvalidArgumentValueError,
    RequiredArgumentMissingError,
    CLIInternalError,
)
from azure.mgmt.core.tools import is_valid_resource_id, parse_resource_id
from knack.log import get_logger

from .models import IdentityType, AllowedFileTypes, AllowedTestTypes, EngineIdentityType, AllowedTestPlanFileExtensions

logger = get_logger(__name__)


def get_load_test_resource_endpoint(
    cli_ctx, cred, load_test_resource, resource_group=None, subscription_id=None
):
    if subscription_id is None:
        return None
    if is_valid_resource_id(load_test_resource):
        # load_test_resource is a resource id
        logger.debug(
            "load-test-resource '%s' is an Azure Resource Id", load_test_resource
        )
        parsed = parse_resource_id(load_test_resource)
        resource_group, name = parsed["resource_group"], parsed["name"]
        if subscription_id != parsed["subscription"]:
            logger.info(
                "Subscription ID in load-test-resource parameter and CLI context do not match - %s and %s",
                subscription_id,
                parsed["subscription"],
            )
            return None
    else:
        # load_test_resource is a name
        logger.debug(
            "load-test-resource '%s' is an Azure Load Testing resource name. Using resource group name %s",
            load_test_resource,
            resource_group,
        )
        if resource_group is None:
            raise InvalidArgumentValueError(
                "Resource group name must be specified when load-test-resource is a name"
            )
        name = load_test_resource

    arm_endpoint, arm_token_scope = get_arm_endpoint_and_scope(cli_ctx)
    mgmt_client = LoadTestMgmtClient(
        credential=cred,
        subscription_id=subscription_id,
        base_url=arm_endpoint,
        credential_scopes=arm_token_scope,
    )
    data_plane_uri = mgmt_client.load_tests.get(resource_group, name).data_plane_uri
    logger.info("Azure Load Testing data plane URI: %s", data_plane_uri)
    return data_plane_uri


def get_login_credentials(cli_ctx, subscription_id=None):
    from azure.cli.core._profile import Profile

    credential, subscription_id, tenant_id = Profile(
        cli_ctx=cli_ctx
    ).get_login_credentials(subscription_id=subscription_id)
    logger.debug("Fetched login credentials for subscription %s", subscription_id)
    return credential, subscription_id, tenant_id


def get_admin_data_plane_client(cmd, load_test_resource, resource_group_name=None):
    from azext_load.data_plane.client_factory import admin_data_plane_client

    credential, subscription_id, _ = get_login_credentials(cmd.cli_ctx)
    endpoint = get_load_test_resource_endpoint(
        cmd.cli_ctx,
        credential,
        load_test_resource,
        resource_group=resource_group_name,
        subscription_id=subscription_id,
    )
    return admin_data_plane_client(
        cmd.cli_ctx,
        subscription=subscription_id,
        endpoint=endpoint,
        credential=credential,
    )


def get_testrun_data_plane_client(cmd, load_test_resource, resource_group_name=None):
    from azext_load.data_plane.client_factory import testrun_data_plane_client

    credential, subscription_id, _ = get_login_credentials(cmd.cli_ctx)
    endpoint = get_load_test_resource_endpoint(
        cmd.cli_ctx,
        credential,
        load_test_resource,
        resource_group=resource_group_name,
        subscription_id=subscription_id,
    )
    return testrun_data_plane_client(
        cmd.cli_ctx,
        subscription=subscription_id,
        endpoint=endpoint,
        credential=credential,
    )


def get_data_plane_scope(cli_ctx):
    cloud_name = cli_ctx.cloud.name
    if cloud_name.lower() == "azureusgovernment":
        return ["https://cnt-prod.loadtesting.azure.us/.default"]

    return ["https://cnt-prod.loadtesting.azure.com/.default"]


def get_arm_endpoint_and_scope(cli_ctx):
    cloud_name = cli_ctx.cloud.name
    if cloud_name.lower() == "azureusgovernment":
        return "https://management.usgovcloudapi.net", [
            "https://management.usgovcloudapi.net/.default"
        ]

    return "https://management.azure.com", ["https://management.azure.com/.default"]


def get_enum_values(enum):
    if not isinstance(enum, EnumMeta):
        raise CLIInternalError(f"Invalid enum type: {type(enum)}")
    return [item.value for item in enum]


def get_file_info_and_download(file_info, path):
    url = file_info.get("url")
    file_name = file_info.get("fileName")
    file_path = os.path.join(path, file_name)
    download_file(url, file_path)
    return file_path


def download_file(url, file_path):
    logger.debug("Downloading file started")
    response = None
    retries = 3
    ex = None
    while retries > 0:
        try:
            response = requests.get(url, stream=True, allow_redirects=True, timeout=60)
            break
        except Exception as e:  # pylint: disable=broad-except
            ex = e
            retries -= 1
            logger.debug(
                "Exception occurred while downloading file: %s. Retrying the request. Retries remaining: %d",
                str(ex),
                retries,
            )
    if retries == 0:
        msg = f"Request for {url} failed after all retries: {str(ex)}"
        logger.debug(msg)
        raise FileOperationError(msg)

    if response:
        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:  # ignore keep-alive new chunks
                    f.write(chunk)
    logger.debug("Downloading file completed")


def download_from_storage_container(sas_url, path):
    from azure.cli.core.util import run_az_cmd
    logger.debug("Downloading files from storage container")
    cmd = ["az", "storage", "copy", "--source", sas_url, "--destination", path, "--recursive"]
    logger.debug("Executing command: %s", cmd)
    result = run_az_cmd(cmd).result
    logger.debug("Execution result: %s", result)


def upload_file_to_test(client, test_id, file_path, file_type=None, wait=False):
    logger.debug(
        "Uploading file %s for the test %s with 'wait' %s",
        file_path,
        test_id,
        "enabled" if wait else "disabled",
    )
    # pylint: disable-next=protected-access
    file_path = validators._validate_path(file_path, is_dir=False)
    # pylint: disable-next=protected-access
    validators._validate_file_stats(file_path, file_type)
    with open(file_path, "rb") as file:
        upload_poller = client.begin_upload_test_file(
            test_id,
            file_name=os.path.basename(file.name),
            file_type=file_type,
            body=file,
        )
        response = (
            upload_poller.result()
            if wait
            else upload_poller.polling_method().resource()
        )
        logger.debug(
            "Upload result for file with --wait%s passed: %s",
            "" if wait else " not",
            response,
        )
        return response


def parse_cert(certificate):
    logger.debug("Parsing certificate")
    if len(certificate) != 1:
        raise InvalidArgumentValueError("Only one certificate is supported")
    certificate = certificate[0]
    name, value = certificate.get("name"), certificate.get("value")
    # pylint: disable-next=protected-access
    if not validators._validate_akv_url(value, "certificates"):
        raise InvalidArgumentValueError(f"Invalid AKV Certificate URL: {value}")
    certificate = {
        "name": name,
        "type": "AKV_CERT_URI",
        "value": value,
    }
    logger.debug("Parsed certificate: %s", certificate)
    logger.debug("Certificate parsed successfully")
    return certificate


def parse_secrets(secrets):
    logger.debug("Parsing secrets")
    secrets_dict = {}
    for secret in secrets:
        name, value = secret.get("name"), secret.get("value")
        if name is None or value is None:
            raise RequiredArgumentMissingError(
                "Both name and value are required for secret"
            )
        # pylint: disable-next=protected-access
        if not validators._validate_akv_url(value, "secrets"):
            raise InvalidArgumentValueError(f"Invalid AKV Certificate URL: {value}")
        secrets_dict[name] = {
            "type": "AKV_SECRET_URI",
            "value": value,
        }
    logger.debug("Parsed secrets: %s", secrets_dict)
    logger.debug("Secrets parsed successfully")
    return secrets_dict


def parse_env(envs):
    logger.debug("Parsing environment variables")
    env_dict = {}
    for env in envs:
        name, value = env.get("name"), env.get("value")
        if name is None:
            raise InvalidArgumentValueError("Name is required for environment variable")
        if value is None:
            value = ""
        env_dict[name] = value
    logger.debug("Parsed environment variables: %s", env_dict)
    logger.debug("Environment variables parsed successfully")
    return env_dict


def create_autostop_criteria_from_args(autostop, error_rate, time_window, max_vu_per_engine):
    if (autostop is None and error_rate is None and time_window is None and max_vu_per_engine is None):
        return None
    autostop_criteria = {}
    autostop_criteria["autoStopDisabled"] = not autostop if autostop is not None else False
    if error_rate is not None:
        autostop_criteria["errorRate"] = error_rate
    if time_window is not None:
        autostop_criteria["errorRateTimeWindowInSeconds"] = time_window
    if max_vu_per_engine is not None:
        autostop_criteria["maximumVirtualUsersPerEngine"] = max_vu_per_engine
    return autostop_criteria


def load_yaml(file_path):
    logger.debug("Loading yaml file: %s", file_path)
    try:
        with open(file_path, "r", encoding="UTF-8") as file:
            data = yaml.safe_load(file)
            logger.info("Yaml file loaded successfully")
            return data
    except yaml.YAMLError as e:
        raise FileOperationError(f"Error loading yaml file: {e}") from e
    except Exception as e:
        logger.debug(
            "Exception occurred while parsing load test configuration file: %s",
            str(e),
        )
        raise FileOperationError(
            f"Invalid load test configuration file : {file_path}. "
            f"Please check the file path and format. Exception: {str(e)}"
        ) from e


# pylint: disable=line-too-long
# Disabling this because dictionary key are too long
def convert_yaml_to_test(cmd, data):
    new_body = {}
    if LoadTestConfigKeys.DISPLAY_NAME in data:
        new_body["displayName"] = data[LoadTestConfigKeys.DISPLAY_NAME]
    if LoadTestConfigKeys.DESCRIPTION in data:
        new_body["description"] = data[LoadTestConfigKeys.DESCRIPTION]
    if LoadTestConfigKeys.TEST_TYPE in data:
        new_body["kind"] = data[LoadTestConfigKeys.TEST_TYPE]
    new_body["keyvaultReferenceIdentityType"] = IdentityType.SystemAssigned
    if LoadTestConfigKeys.KEYVAULT_REFERENCE_IDENTITY in data:
        if not is_valid_resource_id(data[LoadTestConfigKeys.KEYVAULT_REFERENCE_IDENTITY]):
            raise InvalidArgumentValueError(
                "Key vault reference identity should be a valid resource id."
            )
        new_body["keyvaultReferenceIdentityId"] = data[LoadTestConfigKeys.KEYVAULT_REFERENCE_IDENTITY]
        new_body["keyvaultReferenceIdentityType"] = IdentityType.UserAssigned

    if LoadTestConfigKeys.SUBNET_ID in data:
        new_body["subnetId"] = data[LoadTestConfigKeys.SUBNET_ID]

    new_body["loadTestConfiguration"] = utils_yaml_config.yaml_parse_loadtest_configuration(cmd=cmd, data=data)

    if data.get(LoadTestConfigKeys.CERTIFICATES):
        new_body["certificate"] = parse_cert(data.get(LoadTestConfigKeys.CERTIFICATES))
    if data.get(LoadTestConfigKeys.SECRETS):
        new_body["secrets"] = parse_secrets(data.get(LoadTestConfigKeys.SECRETS))
    if data.get(LoadTestConfigKeys.ENV):
        new_body["environmentVariables"] = parse_env(data.get(LoadTestConfigKeys.ENV))
    if data.get(LoadTestConfigKeys.PUBLIC_IP_DISABLED) is not None:
        new_body["publicIPDisabled"] = data.get(LoadTestConfigKeys.PUBLIC_IP_DISABLED)

    if data.get(LoadTestConfigKeys.FAILURE_CRITERIA):
        new_body["passFailCriteria"] = utils_yaml_config.yaml_parse_failure_criteria(data=data)
    if data.get(LoadTestConfigKeys.AUTOSTOP) is not None:
        new_body["autoStopCriteria"] = utils_yaml_config.yaml_parse_autostop_criteria(data=data)

    utils_yaml_config.update_reference_identities(new_body, data)
    logger.debug("Converted yaml to test body: %s", new_body)
    return new_body
# pylint: enable=line-too-long


# pylint: disable=line-too-long
# Disabling this because if conditions are too long
def parse_app_comps_and_server_metrics(data):
    app_components_yaml = data.get(LoadTestConfigKeys.APP_COMPONENTS)
    app_components = {}
    server_metrics = {}
    add_defaults_to_app_components = dict()
    if app_components_yaml is None:
        return None, None, None
    if not isinstance(app_components_yaml, list):
        raise InvalidArgumentValueError("App component name should be of type list")
    for app_component in app_components_yaml:
        if not isinstance(app_component, dict):
            raise InvalidArgumentValueError("App component name should be of type dictionary")
        resource_id = app_component.get(LoadTestConfigKeys.RESOURCEID)
        if resource_id is None:
            raise InvalidArgumentValueError("App component name is required")
        if not is_valid_resource_id(resource_id):
            raise InvalidArgumentValueError("App component name is not a valid resource id")
        if add_defaults_to_app_components.get(resource_id.lower()) is None:
            add_defaults_to_app_components[resource_id.lower()] = app_component.get(LoadTestConfigKeys.SERVER_METRICS_APP_COMPONENTS) is None
        else:
            add_defaults_to_app_components[resource_id.lower()] = add_defaults_to_app_components.get(resource_id.lower()) and app_component.get(LoadTestConfigKeys.SERVER_METRICS_APP_COMPONENTS) is None
        app_components[resource_id] = {}
        app_components[resource_id]["resourceId"] = resource_id
        app_components[resource_id]["resourceName"] = utils_yaml_config.get_resource_name_from_resource_id(resource_id)
        app_components[resource_id]["resourceType"] = utils_yaml_config.get_resource_type_from_resource_id(resource_id)
        if app_component.get(LoadTestConfigKeys.KIND) is not None:
            app_components[resource_id]["kind"] = app_component.get(LoadTestConfigKeys.KIND)
        if app_component.get(LoadTestConfigKeys.SERVER_METRICS_APP_COMPONENTS) is not None:
            if not isinstance(app_component.get(LoadTestConfigKeys.SERVER_METRICS_APP_COMPONENTS), list):
                raise InvalidArgumentValueError("Server metrics should be of type list")
            for server_metric in app_component.get(LoadTestConfigKeys.SERVER_METRICS_APP_COMPONENTS):
                if not isinstance(server_metric, dict):
                    raise InvalidArgumentValueError("Server metric should be of type dictionary")
                if server_metric.get(LoadTestConfigKeys.METRIC_NAME_SERVER_METRICS) is None or server_metric.get(LoadTestConfigKeys.AGGREGATION) is None:
                    raise InvalidArgumentValueError("Server metric name and aggregation are required, invalid dictionary for{}".format(resource_id))
                name_space = server_metric.get(LoadTestConfigKeys.METRIC_NAMESPACE_SERVER_METRICS) or utils_yaml_config.get_resource_type_from_resource_id(
                    resource_id
                )
                metric_name = server_metric.get(LoadTestConfigKeys.METRIC_NAME_SERVER_METRICS)
                key = "{}/{}/{}".format(resource_id, name_space, metric_name)
                server_metrics[key] = {}
                server_metrics[key]["name"] = metric_name
                server_metrics[key]["metricNamespace"] = name_space
                server_metrics[key]["resourceType"] = utils_yaml_config.get_resource_type_from_resource_id(
                    resource_id
                )
                server_metrics[key]["resourceId"] = resource_id
                server_metrics[key]["aggregation"] = server_metric.get(LoadTestConfigKeys.AGGREGATION)
                server_metrics[key]["id"] = key
    return app_components, add_defaults_to_app_components, server_metrics


# pylint: disable=too-many-branches
# pylint: disable=too-many-statements
def create_or_update_test_with_config(
    test_id,
    body,
    yaml_test_body,
    display_name=None,
    test_description=None,
    test_type=None,
    engine_instances=None,
    env=None,
    secrets=None,
    certificate=None,
    key_vault_reference_identity=None,
    metrics_reference_identity=None,
    subnet_id=None,
    split_csv=None,
    disable_public_ip=None,
    autostop_criteria=None,
    regionwise_engines=None,
    engine_ref_id_type=None,
    engine_ref_ids=None,
):
    logger.info(
        "Creating a request body for create or update test using config and parameters."
    )
    new_body = {}
    new_body["displayName"] = (
        display_name
        or yaml_test_body.get("displayName")
        or body.get("displayName")
        or test_id
    )
    new_body["kind"] = test_type or yaml_test_body.get("kind") or body.get("kind")

    test_description = test_description or yaml_test_body.get("description")
    if test_description:
        new_body["description"] = test_description

    new_body["keyvaultReferenceIdentityType"] = IdentityType.SystemAssigned
    if key_vault_reference_identity is not None:
        new_body["keyvaultReferenceIdentityId"] = key_vault_reference_identity
        new_body["keyvaultReferenceIdentityType"] = IdentityType.UserAssigned
    elif yaml_test_body.get("keyvaultReferenceIdentityId") is not None:
        new_body["keyvaultReferenceIdentityId"] = yaml_test_body.get(
            "keyvaultReferenceIdentityId"
        )
        new_body["keyvaultReferenceIdentityType"] = IdentityType.UserAssigned
    if new_body["keyvaultReferenceIdentityType"] == IdentityType.UserAssigned:
        if new_body["keyvaultReferenceIdentityId"].casefold() in ["null", ""]:
            new_body["keyvaultReferenceIdentityType"] = IdentityType.SystemAssigned
            new_body.pop("keyvaultReferenceIdentityId")
    new_body["metricsReferenceIdentityType"] = IdentityType.SystemAssigned
    if metrics_reference_identity is not None:
        new_body["metricsReferenceIdentityId"] = metrics_reference_identity
        new_body["metricsReferenceIdentityType"] = IdentityType.UserAssigned
    elif yaml_test_body.get("metricsReferenceIdentityId") is not None:
        new_body["metricsReferenceIdentityId"] = yaml_test_body.get(
            "metricsReferenceIdentityId"
        )
        new_body["metricsReferenceIdentityType"] = IdentityType.UserAssigned
    if new_body["metricsReferenceIdentityType"] == IdentityType.UserAssigned:
        if new_body["metricsReferenceIdentityId"].casefold() in ["null", ""]:
            new_body["metricsReferenceIdentityType"] = IdentityType.SystemAssigned
            new_body.pop("metricsReferenceIdentityId")
    subnet_id = subnet_id or yaml_test_body.get("subnetId")
    if disable_public_ip is not None:
        new_body["publicIPDisabled"] = disable_public_ip
    else:
        new_body["publicIPDisabled"] = yaml_test_body.get("publicIPDisabled", False)
    if subnet_id:
        if subnet_id.casefold() in ["null", ""]:
            new_body["subnetId"] = None
        else:
            new_body["subnetId"] = subnet_id
    new_body["environmentVariables"] = {}
    if body.get("environmentVariables") is not None:
        for key in body.get("environmentVariables"):
            new_body["environmentVariables"].update({key: None})
    if yaml_test_body.get("environmentVariables") is not None:
        new_body["environmentVariables"].update(
            yaml_test_body.get("environmentVariables", {})
        )
    if env is not None:
        new_body["environmentVariables"].update(env)
    new_body["secrets"] = {}
    if body.get("secrets") is not None:
        for key in body.get("secrets", {}):
            new_body["secrets"].update({key: None})
    if yaml_test_body.get("secrets") is not None:
        new_body["secrets"].update(yaml_test_body.get("secrets", {}))
    if secrets is not None:
        new_body["secrets"].update(secrets)

    if certificate is not None:
        if certificate == "null":
            new_body["certificate"] = None
        else:
            new_body["certificate"] = certificate
    elif yaml_test_body.get("certificate") is not None:
        new_body["certificate"] = yaml_test_body.get("certificate")
    else:
        new_body["certificate"] = None

    new_body["loadTestConfiguration"] = {}
    if engine_instances:
        new_body["loadTestConfiguration"]["engineInstances"] = engine_instances
    elif (
        (yaml_test_body.get("loadTestConfiguration") or {}).get("engineInstances")
        is not None
    ):
        new_body["loadTestConfiguration"]["engineInstances"] = yaml_test_body[
            "loadTestConfiguration"
        ]["engineInstances"]
    else:
        new_body["loadTestConfiguration"]["engineInstances"] = body.get(
            "loadTestConfiguration", {}
        ).get("engineInstances", 1)
    if regionwise_engines:
        new_body["loadTestConfiguration"]["regionalLoadTestConfig"] = regionwise_engines
    elif (
        (yaml_test_body.get("loadTestConfiguration") or {}).get("regionalLoadTestConfig")
        is not None
    ):
        new_body["loadTestConfiguration"]["regionalLoadTestConfig"] = yaml_test_body[
            "loadTestConfiguration"
        ]["regionalLoadTestConfig"]
    else:
        new_body["loadTestConfiguration"]["regionalLoadTestConfig"] = body.get(
            "loadTestConfiguration", {}
        ).get("regionalLoadTestConfig")
    validate_engine_data_with_regionwiseload_data(
        new_body["loadTestConfiguration"]["engineInstances"],
        new_body["loadTestConfiguration"]["regionalLoadTestConfig"])
    # quick test is not supported in CLI
    new_body["loadTestConfiguration"]["quickStartTest"] = False

    # make all metrics in existing passFailCriteria None to remove it from the test and add passFailCriteria from yaml
    existing_pass_fail_Criteria = (body.get("passFailCriteria") or {})
    yaml_pass_fail_criteria = (yaml_test_body.get("passFailCriteria") or {})
    if existing_pass_fail_Criteria or yaml_pass_fail_criteria:
        new_body["passFailCriteria"] = {
            "passFailMetrics": {
                key: None
                for key in existing_pass_fail_Criteria.get("passFailMetrics", {})
            },
            "passFailServerMetrics": {
                key: None
                for key in existing_pass_fail_Criteria.get("passFailServerMetrics", {})
            }
        }
        new_body["passFailCriteria"]["passFailMetrics"].update(
            yaml_pass_fail_criteria.get("passFailMetrics", {})
        )
        new_body["passFailCriteria"]["passFailServerMetrics"].update(
            yaml_pass_fail_criteria.get("passFailServerMetrics", {})
        )
    if split_csv is not None:
        new_body["loadTestConfiguration"]["splitAllCSVs"] = split_csv
    elif (
        (yaml_test_body.get("loadTestConfiguration") or {}).get("splitAllCSVs") is not None
    ):
        new_body["loadTestConfiguration"]["splitAllCSVs"] = yaml_test_body[
            "loadTestConfiguration"
        ]["splitAllCSVs"]

    new_body["autoStopCriteria"] = {}
    if autostop_criteria is not None:
        new_body["autoStopCriteria"] = autostop_criteria
    elif yaml_test_body.get("autoStopCriteria") is not None:
        new_body["autoStopCriteria"] = yaml_test_body["autoStopCriteria"]
    if (
        new_body["autoStopCriteria"].get("autoStopDisabled") is None
        and (body.get("autoStopCriteria") or {}).get("autoStopDisabled") is not None
    ):
        new_body["autoStopCriteria"]["autoStopDisabled"] = body["autoStopCriteria"]["autoStopDisabled"]
    if (
        new_body["autoStopCriteria"].get("errorRate") is None
        and (body.get("autoStopCriteria") or {}).get("errorRate") is not None
    ):
        new_body["autoStopCriteria"]["errorRate"] = body["autoStopCriteria"]["errorRate"]
    if (
        new_body["autoStopCriteria"].get("errorRateTimeWindowInSeconds") is None
        and (body.get("autoStopCriteria") or {}).get("errorRateTimeWindowInSeconds") is not None
    ):
        new_body["autoStopCriteria"]["errorRateTimeWindowInSeconds"] = \
            body["autoStopCriteria"]["errorRateTimeWindowInSeconds"]
    if (
        new_body["autoStopCriteria"].get("maximumVirtualUsersPerEngine") is None
        and (body.get("autoStopCriteria") or {}).get("maximumVirtualUsersPerEngine") is not None
    ):
        new_body["autoStopCriteria"]["maximumVirtualUsersPerEngine"] = \
            body["autoStopCriteria"]["maximumVirtualUsersPerEngine"]

    if (new_body["autoStopCriteria"].get("autoStopDisabled") is True):
        logger.warning(
            "Auto stop is disabled. Error rate, time window and engine users will be ignored. "
            "This can lead to incoming charges for an incorrectly configured test."
        )

    # if argument is provided prefer that over yaml values
    if engine_ref_id_type:
        validators.validate_engine_ref_ids_and_type(engine_ref_id_type, engine_ref_ids)
        if engine_ref_id_type:
            new_body["engineBuiltinIdentityType"] = engine_ref_id_type
        if engine_ref_ids:
            new_body["engineBuiltinIdentityIds"] = engine_ref_ids
    elif yaml_test_body.get("engineBuiltinIdentityType"):
        new_body["engineBuiltinIdentityType"] = yaml_test_body.get("engineBuiltinIdentityType")
        new_body["engineBuiltinIdentityIds"] = yaml_test_body.get("engineBuiltinIdentityIds")
    else:
        new_body["engineBuiltinIdentityType"] = body.get("engineBuiltinIdentityType")
        new_body["engineBuiltinIdentityIds"] = body.get("engineBuiltinIdentityIds")

    logger.debug("Request body for create or update test: %s", new_body)
    return new_body


# pylint: disable=too-many-branches
# pylint: disable=too-many-statements
def create_or_update_test_without_config(
    test_id,
    body,
    display_name=None,
    test_description=None,
    test_type=None,
    engine_instances=None,
    env=None,
    secrets=None,
    certificate=None,
    key_vault_reference_identity=None,
    metrics_reference_identity=None,
    subnet_id=None,
    split_csv=None,
    disable_public_ip=None,
    autostop_criteria=None,
    regionwise_engines=None,
    baseline_test_run_id=None,
    engine_ref_id_type=None,
    engine_ref_ids=None,
):
    logger.info(
        "Creating a request body for test using parameters and old test body (in case of update)."
    )
    new_body = {}
    new_body["displayName"] = display_name or body.get("displayName") or test_id
    new_body["kind"] = test_type or body.get("kind")
    test_description = test_description or body.get("description")
    if test_description:
        new_body["description"] = test_description
    new_body["keyvaultReferenceIdentityType"] = IdentityType.SystemAssigned
    if key_vault_reference_identity is not None:
        new_body["keyvaultReferenceIdentityId"] = key_vault_reference_identity
        new_body["keyvaultReferenceIdentityType"] = IdentityType.UserAssigned
    elif body.get("keyvaultReferenceIdentityId") is not None:
        new_body["keyvaultReferenceIdentityId"] = body.get(
            "keyvaultReferenceIdentityId"
        )
        new_body["keyvaultReferenceIdentityType"] = body.get(
            "keyvaultReferenceIdentityType", IdentityType.UserAssigned
        )
    if new_body["keyvaultReferenceIdentityType"] == IdentityType.UserAssigned:
        if new_body["keyvaultReferenceIdentityId"].casefold() in ["null", ""]:
            new_body["keyvaultReferenceIdentityType"] = IdentityType.SystemAssigned
            new_body.pop("keyvaultReferenceIdentityId")
    new_body["metricsReferenceIdentityType"] = IdentityType.SystemAssigned
    if metrics_reference_identity is not None:
        new_body["metricsReferenceIdentityId"] = metrics_reference_identity
        new_body["metricsReferenceIdentityType"] = IdentityType.UserAssigned
    elif body.get("metricsReferenceIdentityId") is not None:
        new_body["metricsReferenceIdentityId"] = body.get(
            "metricsReferenceIdentityId"
        )
        new_body["metricsReferenceIdentityType"] = body.get(
            "metricsReferenceIdentityType", IdentityType.UserAssigned
        )
    if new_body["metricsReferenceIdentityType"] == IdentityType.UserAssigned:
        if new_body["metricsReferenceIdentityId"].casefold() in ["null", ""]:
            new_body["metricsReferenceIdentityType"] = IdentityType.SystemAssigned
            new_body.pop("metricsReferenceIdentityId")
    subnet_id = subnet_id or body.get("subnetId")
    if subnet_id:
        if subnet_id.casefold() in ["null", ""]:
            new_body["subnetId"] = None
        else:
            new_body["subnetId"] = subnet_id
    if body.get("environmentVariables") is not None:
        new_body["environmentVariables"] = body.get("environmentVariables", {})
    else:
        new_body["environmentVariables"] = {}
    if env is not None:
        new_body["environmentVariables"].update(env)
    if body.get("secrets") is not None:
        new_body["secrets"] = body.get("secrets", {})
    else:
        new_body["secrets"] = {}
    if secrets is not None:
        new_body["secrets"].update(secrets)
    if certificate is not None:
        if certificate == "null":
            new_body["certificate"] = None
        else:
            new_body["certificate"] = certificate
    elif body.get("certificate"):
        new_body["certificate"] = body.get("certificate")
    new_body["loadTestConfiguration"] = (body.get("loadTestConfiguration") or {})
    if engine_instances:
        new_body["loadTestConfiguration"]["engineInstances"] = engine_instances
    else:
        new_body["loadTestConfiguration"]["engineInstances"] = body.get(
            "loadTestConfiguration", {}
        ).get("engineInstances", 1)
    if regionwise_engines:
        new_body["loadTestConfiguration"]["regionalLoadTestConfig"] = regionwise_engines
    else:
        new_body["loadTestConfiguration"]["regionalLoadTestConfig"] = body.get(
            "loadTestConfiguration", {}
        ).get("regionalLoadTestConfig")
    validate_engine_data_with_regionwiseload_data(
        new_body["loadTestConfiguration"]["engineInstances"],
        new_body["loadTestConfiguration"]["regionalLoadTestConfig"])
    # quick test is not supported in CLI
    new_body["loadTestConfiguration"]["quickStartTest"] = False
    if split_csv is not None:
        new_body["loadTestConfiguration"]["splitAllCSVs"] = split_csv
    elif (body.get("loadTestConfiguration") or {}).get("splitAllCSVs") is not None:
        new_body["loadTestConfiguration"]["splitAllCSVs"] = body[
            "loadTestConfiguration"
        ]["splitAllCSVs"]
    if disable_public_ip is not None:
        new_body["publicIPDisabled"] = disable_public_ip

    new_body["autoStopCriteria"] = {}
    if autostop_criteria is not None:
        new_body["autoStopCriteria"] = autostop_criteria
    if (
        new_body["autoStopCriteria"].get("autoStopDisabled") is None
        and (body.get("autoStopCriteria") or {}).get("autoStopDisabled") is not None
    ):
        new_body["autoStopCriteria"]["autoStopDisabled"] = body["autoStopCriteria"]["autoStopDisabled"]
    if (
        new_body["autoStopCriteria"].get("errorRate") is None
        and (body.get("autoStopCriteria") or {}).get("errorRate") is not None
    ):
        new_body["autoStopCriteria"]["errorRate"] = body["autoStopCriteria"]["errorRate"]
    if (
        new_body["autoStopCriteria"].get("errorRateTimeWindowInSeconds") is None
        and (body.get("autoStopCriteria") or {}).get("errorRateTimeWindowInSeconds") is not None
    ):
        new_body["autoStopCriteria"]["errorRateTimeWindowInSeconds"] = \
            body["autoStopCriteria"]["errorRateTimeWindowInSeconds"]
    if (
        new_body["autoStopCriteria"].get("maximumVirtualUsersPerEngine") is None
        and (body.get("autoStopCriteria") or {}).get("maximumVirtualUsersPerEngine") is not None
    ):
        new_body["autoStopCriteria"]["maximumVirtualUsersPerEngine"] = \
            body["autoStopCriteria"]["maximumVirtualUsersPerEngine"]
    if (new_body["autoStopCriteria"].get("autoStopDisabled") is True):
        logger.warning(
            "Auto stop is disabled. Error rate, time window and engine users will be ignored. "
            "This can lead to incoming charges for an incorrectly configured test."
        )
    new_body["baselineTestRunId"] = baseline_test_run_id if baseline_test_run_id else body.get("baselineTestRunId")

    # pylint: disable=line-too-long
    # Disabling this because dictionary key are too long
    # raises error if engine_reference_identity_type and corresponding identities is not a valid combination
    validators.validate_engine_ref_ids_and_type(engine_ref_id_type, engine_ref_ids, body.get("engineBuiltinIdentityType"))
    if engine_ref_id_type:
        new_body["engineBuiltinIdentityType"] = engine_ref_id_type
        if engine_ref_ids:
            new_body["engineBuiltinIdentityIds"] = engine_ref_ids
    else:
        new_body["engineBuiltinIdentityType"] = body.get("engineBuiltinIdentityType")
        if engine_ref_ids and body.get("engineBuiltinIdentityType") != EngineIdentityType.UserAssigned:
            raise InvalidArgumentValueError("Engine reference identities can only be provided when engine reference identity type is user assigned")
        new_body["engineBuiltinIdentityIds"] = engine_ref_ids if engine_ref_ids else body.get("engineBuiltinIdentityIds")
    # pylint: enable=line-too-long

    logger.debug("Request body for create or update test: %s", new_body)
    return new_body


# pylint: enable=too-many-branches
# pylint: enable=too-many-statements
def create_or_update_test_run_body(
    test_id,
    display_name=None,
    description=None,
    env=None,
    secrets=None,
    certificate=None,
    debug_mode=None,
):
    logger.info("Creating a request body for create test run")
    new_body = {"testId": test_id}
    if display_name is not None:
        new_body["displayName"] = display_name
    if description is not None:
        new_body["description"] = description
    if env is not None:
        new_body["environmentVariables"] = env
    if secrets is not None:
        new_body["secrets"] = secrets
    if certificate is not None:
        new_body["certificate"] = certificate
    if debug_mode is not None:
        new_body["debugLogsEnabled"] = debug_mode
    logger.debug("Request body for create test run: %s", new_body)
    return new_body


def upload_generic_files_helper(
    client, test_id, load_test_config_file, existing_files, file_to_upload, file_type, wait
):
    if not os.path.isabs(file_to_upload) and load_test_config_file:
        yaml_dir = os.path.dirname(load_test_config_file)
        file_to_upload = os.path.join(yaml_dir, file_to_upload)
    file_name = os.path.basename(file_to_upload)
    if file_name in [file["fileName"] for file in existing_files]:
        client.delete_test_file(test_id, file_name)
        logger.info(
            "File with name '%s' already exists in test %s. Deleting it!",
            file_name,
            test_id,
        )
    file_response = upload_file_to_test(
        client,
        test_id,
        file_to_upload,
        file_type=file_type,
        wait=wait,
    )
    logger.info(
        "Uploaded file '%s' of type %s to test %s",
        file_name,
        file_type,
        test_id,
    )
    return file_response


def upload_properties_file_helper(
    client, test_id, yaml_data, load_test_config_file, existing_test_files, wait
):
    properties = yaml_data.get("properties") if yaml_data else None
    if properties and properties.get("userPropertyFile") is not None:
        user_prop_file = properties.get("userPropertyFile")
        existing_properties_files = []
        for file in existing_test_files:
            if AllowedFileTypes.USER_PROPERTIES.value == file["fileType"]:
                existing_properties_files.append(file)
        upload_generic_files_helper(
            client=client, test_id=test_id, load_test_config_file=load_test_config_file,
            existing_files=existing_properties_files, file_to_upload=user_prop_file,
            file_type=AllowedFileTypes.USER_PROPERTIES, wait=wait
        )


def upload_configurations_files_helper(
    client, test_id, yaml_data, load_test_config_file, existing_test_files, wait
):
    if yaml_data and yaml_data.get("configurationFiles") is not None:
        logger.info("Uploading additional artifacts")
        for config_file in yaml_data.get("configurationFiles"):
            upload_generic_files_helper(
                client=client,
                test_id=test_id, load_test_config_file=load_test_config_file, existing_files=existing_test_files,
                file_to_upload=config_file, file_type=AllowedFileTypes.ADDITIONAL_ARTIFACTS,
                wait=wait
            )


def upload_zipped_artifacts_helper(
    client, test_id, yaml_data, load_test_config_file, existing_test_files, wait
):
    if yaml_data and yaml_data.get("zipArtifacts") is not None:
        logger.info("Uploading zipped artifacts")
        for zip_artifact in yaml_data.get("zipArtifacts"):
            file_response = upload_generic_files_helper(
                client=client,
                test_id=test_id, load_test_config_file=load_test_config_file, existing_files=existing_test_files,
                file_to_upload=zip_artifact, file_type=AllowedFileTypes.ZIPPED_ARTIFACTS,
                wait=wait
            )
            if wait and file_response.get("validationStatus") not in ("VALIDATION_SUCCESS", "NOT_VALIDATED"):
                # pylint: disable=line-too-long
                raise FileOperationError(
                    "ZIP artifact {} is not valid. Please check the file and try again. Current file status is {}".format(
                        zip_artifact, file_response.get("validationStatus")
                    )
                )


def infer_test_type_from_test_plan(test_plan):
    if test_plan is None:
        return None
    _, file_extension = os.path.splitext(test_plan)
    if file_extension.casefold() == AllowedTestPlanFileExtensions.JMX.value:
        return AllowedTestTypes.JMX.value
    if file_extension.casefold() == AllowedTestPlanFileExtensions.URL.value:
        return AllowedTestTypes.URL.value
    if file_extension.casefold() == AllowedTestPlanFileExtensions.LOCUST.value:
        return AllowedTestTypes.LOCUST.value
    return None


def _evaluate_file_type_for_test_script(test_type, test_plan):
    if test_type == AllowedTestTypes.URL.value:
        _, file_extension = os.path.splitext(test_plan)
        if file_extension.casefold() == ".json":
            return AllowedFileTypes.URL_TEST_CONFIG
        if file_extension.casefold() == ".jmx":
            return AllowedFileTypes.JMX_FILE
    return AllowedFileTypes.TEST_SCRIPT


def upload_test_plan_helper(
    client, test_id, yaml_data, test_plan, load_test_config_file, existing_test_files, wait, test_type
):
    if test_plan is None and yaml_data is not None and yaml_data.get(LoadTestConfigKeys.TEST_PLAN) is not None:
        test_plan = yaml_data.get(LoadTestConfigKeys.TEST_PLAN)
    existing_test_plan_files = []
    for file in existing_test_files:
        if (
            validators.AllowedFileTypes.JMX_FILE.value == file["fileType"] or
            file["fileType"] == AllowedFileTypes.TEST_SCRIPT.value
        ):
            existing_test_plan_files.append(file)
    if test_plan:
        logger.info("Uploading test plan file %s to test %s of type %s", test_plan, test_id, test_type)
        file_type = _evaluate_file_type_for_test_script(test_type, test_plan)
        try:
            file_response = upload_generic_files_helper(
                client=client,
                test_id=test_id, load_test_config_file=load_test_config_file,
                existing_files=existing_test_files, file_to_upload=test_plan,
                file_type=file_type,
                wait=wait
            )
            if wait and file_response.get("validationStatus") != "VALIDATION_SUCCESS":
                raise FileOperationError(
                    f"Test plan file {test_plan} is not valid. Please check the file and try again."
                )
        except Exception as e:
            raise FileOperationError(
                f"Error occurred while uploading test plan file {test_plan} for test {test_id} of type {test_type}: {e}"
            ) from e


def upload_files_helper(
    client, test_id, yaml_data, test_plan, load_test_config_file, wait, test_type
):
    files = list(client.list_test_files(test_id))
    upload_properties_file_helper(
        client=client,
        test_id=test_id, yaml_data=yaml_data,
        load_test_config_file=load_test_config_file, existing_test_files=files, wait=wait)

    upload_configurations_files_helper(
        client=client,
        test_id=test_id, yaml_data=yaml_data,
        load_test_config_file=load_test_config_file, existing_test_files=files, wait=wait)

    upload_zipped_artifacts_helper(
        client=client,
        test_id=test_id, yaml_data=yaml_data,
        load_test_config_file=load_test_config_file, existing_test_files=files, wait=wait)

    upload_test_plan_helper(
        client=client,
        test_id=test_id, yaml_data=yaml_data, test_plan=test_plan,
        load_test_config_file=load_test_config_file, existing_test_files=files, wait=wait,
        test_type=test_type)


def validate_engine_data_with_regionwiseload_data(engine_instances, regionwise_engines):
    if regionwise_engines is None:
        return
    total_engines = 0
    for region in regionwise_engines:
        total_engines += region["engineInstances"]
    if total_engines != engine_instances:
        raise InvalidArgumentValueError(
            f"Sum of engine instances in regionwise load test configuration ({total_engines}) "
            f"should be equal to total engine instances ({engine_instances})"
        )


def _get_metrics_from_sampler(test_run, sampler_name, metric_name):
    return ((test_run.get("testRunStatistics") or {}).get(sampler_name) or {}).get(metric_name)


def generate_trends_row(test_run, response_time_aggregate=None):
    trends = {
        LoadTestTrendsKeys.NAME: test_run.get("displayName"),
        LoadTestTrendsKeys.DESCRIPTION: test_run.get("description"),
    }
    _add_basic_trends(trends, test_run)
    _add_response_time_trends(trends, test_run, response_time_aggregate)
    _add_error_and_throughput_trends(trends, test_run)
    return trends


def _add_basic_trends(trends, test_run):
    if test_run.get("status") is not None:
        trends[LoadTestTrendsKeys.STATUS] = test_run.get("status")
    if test_run.get("duration") is not None:
        trends[LoadTestTrendsKeys.DURATION] = round(test_run.get("duration") / (60 * 1000), 2)
    if test_run.get("virtualUsers") is not None:
        trends[LoadTestTrendsKeys.VUSERS] = test_run.get("virtualUsers")
    sample_count = _get_metrics_from_sampler(test_run, "Total", "sampleCount")
    if sample_count is not None:
        trends[LoadTestTrendsKeys.TOTAL_REQUESTS] = sample_count


def _add_response_time_trends(trends, test_run, response_time_aggregate):
    trends[LoadTestTrendsKeys.RESPONSE_TIME] = None
    for key, metric in LoadTestTrendsKeys.RESPONSE_TIME_METRICS.items():
        if response_time_aggregate == key:
            value = _get_metrics_from_sampler(test_run, "Total", metric)
            if value is not None:
                trends[LoadTestTrendsKeys.RESPONSE_TIME] = value
            break


def _add_error_and_throughput_trends(trends, test_run):
    error_pct = _get_metrics_from_sampler(test_run, "Total", "errorPct")
    if error_pct is not None:
        trends[LoadTestTrendsKeys.ERROR_PCT] = round(error_pct, 2)
    throughput = _get_metrics_from_sampler(test_run, "Total", "throughput")
    if throughput is not None:
        trends[LoadTestTrendsKeys.THROUGHPUT] = round(throughput, 2)


def merge_existing_app_components(app_components_yaml, existing_app_components):
    if existing_app_components is None:
        return app_components_yaml
    for key in existing_app_components:
        if key not in app_components_yaml:
            app_components_yaml[key] = None
    return app_components_yaml


def merge_existing_server_metrics(add_defaults_to_app_copmponents, existing_server_metrics, server_metrics_yaml):
    if existing_server_metrics is None:
        return server_metrics_yaml
    for key in existing_server_metrics:
        resourceid = (existing_server_metrics.get(key) or {}).get(LoadTestConfigKeys.RESOURCEID, "").lower()
        if key not in server_metrics_yaml and (add_defaults_to_app_copmponents.get(resourceid) is None or add_defaults_to_app_copmponents.get(resourceid) is False):
            server_metrics_yaml[key] = None
    return server_metrics_yaml


def is_not_empty_dictionary(dictionary):
    return dictionary is not None and len(dictionary) > 0
