# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long, consider-using-f-string, logging-format-interpolation, inconsistent-return-statements, broad-except, bare-except, too-many-statements, too-many-locals, too-many-boolean-expressions, too-many-branches, too-many-nested-blocks, pointless-statement, expression-not-assigned, unbalanced-tuple-unpacking, unsupported-assignment-operation
# pylint: disable=super-with-arguments, too-many-instance-attributes, no-else-return, no-self-use, useless-return, reimported, redefined-outer-name, no-else-raise, too-few-public-methods

import json
import time
import sys

from azure.cli.core.azclierror import AzureResponseError, ResourceNotFoundError
from azure.cli.core.util import send_raw_request
from azure.cli.core.commands.client_factory import get_subscription_id
from knack.log import get_logger

logger = get_logger(__name__)

CURRENT_API_VERSION = "2025-07-01"
POLLING_TIMEOUT = 1200  # how many seconds before exiting
POLLING_SECONDS = 2  # how many seconds between requests
POLLING_TIMEOUT_FOR_MANAGED_CERTIFICATE = 1500  # how many seconds before exiting
POLLING_INTERVAL_FOR_MANAGED_CERTIFICATE = 4  # how many seconds between requests
HEADER_AZURE_ASYNC_OPERATION = "azure-asyncoperation"
HEADER_LOCATION = "location"


class PollingAnimation:
    def __init__(self):
        self.tickers = ["/", "|", "\\", "-", "/", "|", "\\", "-"]
        self.currTicker = 0

    def tick(self):
        sys.stderr.write('\r')
        sys.stderr.write(self.tickers[self.currTicker] + " Running ..")
        sys.stderr.flush()
        self.currTicker += 1
        self.currTicker = self.currTicker % len(self.tickers)

    def flush(self):
        sys.stderr.flush()
        sys.stderr.write("\r\033[K")


def poll_status(cmd, request_url):  # pylint: disable=inconsistent-return-statements
    from azure.core.exceptions import HttpResponseError
    from ._utils import safe_get

    if not request_url:
        raise AzureResponseError(f"Http response lack of necessary header: '{HEADER_AZURE_ASYNC_OPERATION}'")

    start = time.time()
    end = time.time() + POLLING_TIMEOUT
    animation = PollingAnimation()

    animation.tick()
    r = send_raw_request(cmd.cli_ctx, "GET", request_url)

    while r.status_code in [200] and start < end:
        time.sleep(_extract_delay(r))
        animation.tick()
        r = send_raw_request(cmd.cli_ctx, "GET", request_url)
        response_body = json.loads(r.text)
        status = safe_get(response_body, "status")
        if not status:
            raise AzureResponseError("Http response body lack of necessary property: status")
        if response_body["status"].lower() in ["failed", "canceled"]:
            message = json.dumps(response_body["error"]) if "error" in response_body else "Operation failed or canceled"
            raise HttpResponseError(
                response=r,
                message=message
            )
        if response_body["status"].lower() in ["succeeded"]:
            break
        start = time.time()

    animation.flush()
    return


def poll_results(cmd, request_url):  # pylint: disable=inconsistent-return-statements
    if not request_url:
        raise AzureResponseError(f"Http response lack of necessary header: '{HEADER_LOCATION}'")

    start = time.time()
    end = time.time() + POLLING_TIMEOUT
    animation = PollingAnimation()

    animation.tick()
    r = send_raw_request(cmd.cli_ctx, "GET", request_url)

    while r.status_code in [202] and start < end:
        time.sleep(_extract_delay(r))
        animation.tick()
        r = send_raw_request(cmd.cli_ctx, "GET", request_url)
        start = time.time()

    animation.flush()
    if r.text:
        return json.loads(r.text)


def _extract_delay(response):
    try:
        retry_after = response.headers.get("retry-after")
        if retry_after:
            return int(retry_after)
        for ms_header in ["retry-after-ms", "x-ms-retry-after-ms"]:
            retry_after = response.headers.get(ms_header)
            if retry_after:
                parsed_retry_after = int(retry_after)
                return parsed_retry_after / 1000.0
    except ValueError:
        pass
    return POLLING_SECONDS


class ContainerAppClient:
    api_version = CURRENT_API_VERSION

    @classmethod
    def create_or_update(cls, cmd, resource_group_name, name, container_app_envelope, no_wait=False):
        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        url_fmt = "{}/subscriptions/{}/resourceGroups/{}/providers/Microsoft.App/containerApps/{}?api-version={}"
        request_url = url_fmt.format(
            management_hostname.strip('/'),
            sub_id,
            resource_group_name,
            name,
            cls.api_version)

        r = send_raw_request(cmd.cli_ctx, "PUT", request_url, body=json.dumps(container_app_envelope))

        if no_wait:
            return r.json()
        elif r.status_code == 201:
            operation_url = r.headers.get(HEADER_AZURE_ASYNC_OPERATION)
            poll_status(cmd, operation_url)
            r = send_raw_request(cmd.cli_ctx, "GET", request_url)

        return r.json()

    @classmethod
    def update(cls, cmd, resource_group_name, name, container_app_envelope, no_wait=False):
        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager

        sub_id = get_subscription_id(cmd.cli_ctx)
        url_fmt = "{}/subscriptions/{}/resourceGroups/{}/providers/Microsoft.App/containerApps/{}?api-version={}"
        request_url = url_fmt.format(
            management_hostname.strip('/'),
            sub_id,
            resource_group_name,
            name,
            cls.api_version)

        r = send_raw_request(cmd.cli_ctx, "PATCH", request_url, body=json.dumps(container_app_envelope))

        if no_wait:
            return
        elif r.status_code == 202:
            operation_url = r.headers.get(HEADER_AZURE_ASYNC_OPERATION)
            if operation_url:
                poll_status(cmd, operation_url)
                r = send_raw_request(cmd.cli_ctx, "GET", request_url)
                return r.json()
            else:
                operation_url = r.headers.get(HEADER_LOCATION)
                r = poll_results(cmd, operation_url)
                if r is None:
                    raise ResourceNotFoundError("Could not find a container app")
                else:
                    return r

        return r.json()

    @classmethod
    def delete(cls, cmd, resource_group_name, name, no_wait=False):
        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        url_fmt = "{}/subscriptions/{}/resourceGroups/{}/providers/Microsoft.App/containerApps/{}?api-version={}"
        request_url = url_fmt.format(
            management_hostname.strip('/'),
            sub_id,
            resource_group_name,
            name,
            cls.api_version)

        r = send_raw_request(cmd.cli_ctx, "DELETE", request_url)

        if no_wait:
            return  # API doesn't return JSON (it returns no content)
        elif r.status_code in [200, 201, 202, 204]:
            if r.status_code == 202:
                operation_url = r.headers.get(HEADER_LOCATION)
                poll_results(cmd, operation_url)
                logger.warning('Containerapp successfully deleted')

    @classmethod
    def show(cls, cmd, resource_group_name, name):
        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        url_fmt = "{}/subscriptions/{}/resourceGroups/{}/providers/Microsoft.App/containerApps/{}?api-version={}"
        request_url = url_fmt.format(
            management_hostname.strip('/'),
            sub_id,
            resource_group_name,
            name,
            cls.api_version)

        r = send_raw_request(cmd.cli_ctx, "GET", request_url)
        return r.json()

    @classmethod
    def list_by_subscription(cls, cmd, formatter=lambda x: x):
        app_list = []

        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        request_url = "{}/subscriptions/{}/providers/Microsoft.App/containerApps?api-version={}".format(
            management_hostname.strip('/'),
            sub_id,
            cls.api_version)

        r = send_raw_request(cmd.cli_ctx, "GET", request_url)
        j = r.json()
        for app in j["value"]:
            formatted = formatter(app)
            app_list.append(formatted)

        while j.get("nextLink") is not None:
            request_url = j["nextLink"]
            r = send_raw_request(cmd.cli_ctx, "GET", request_url)
            j = r.json()
            for app in j["value"]:
                formatted = formatter(app)
                app_list.append(formatted)

        return app_list

    @classmethod
    def list_by_resource_group(cls, cmd, resource_group_name, formatter=lambda x: x):
        app_list = []

        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        url_fmt = "{}/subscriptions/{}/resourceGroups/{}/providers/Microsoft.App/containerApps?api-version={}"
        request_url = url_fmt.format(
            management_hostname.strip('/'),
            sub_id,
            resource_group_name,
            cls.api_version)

        r = send_raw_request(cmd.cli_ctx, "GET", request_url)
        j = r.json()
        for app in j["value"]:
            formatted = formatter(app)
            app_list.append(formatted)

        while j.get("nextLink") is not None:
            request_url = j["nextLink"]
            r = send_raw_request(cmd.cli_ctx, "GET", request_url)
            j = r.json()
            for app in j["value"]:
                formatted = formatter(app)
                app_list.append(formatted)

        return app_list

    @classmethod
    def list_secrets(cls, cmd, resource_group_name, name):

        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        url_fmt = "{}/subscriptions/{}/resourceGroups/{}/providers/Microsoft.App/containerApps/{}/listSecrets?api-version={}"
        request_url = url_fmt.format(
            management_hostname.strip('/'),
            sub_id,
            resource_group_name,
            name,
            cls.api_version)

        r = send_raw_request(cmd.cli_ctx, "POST", request_url, body=None)
        return r.json()

    @classmethod
    def list_revisions(cls, cmd, resource_group_name, name, formatter=lambda x: x):

        revisions_list = []

        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        url_fmt = "{}/subscriptions/{}/resourceGroups/{}/providers/Microsoft.App/containerApps/{}/revisions?api-version={}"
        request_url = url_fmt.format(
            management_hostname.strip('/'),
            sub_id,
            resource_group_name,
            name,
            cls.api_version)

        r = send_raw_request(cmd.cli_ctx, "GET", request_url)
        j = r.json()
        for app in j["value"]:
            formatted = formatter(app)
            revisions_list.append(formatted)

        while j.get("nextLink") is not None:
            request_url = j["nextLink"]
            r = send_raw_request(cmd.cli_ctx, "GET", request_url)
            j = r.json()
            for app in j["value"]:
                formatted = formatter(app)
                revisions_list.append(formatted)

        return revisions_list

    @classmethod
    def show_revision(cls, cmd, resource_group_name, container_app_name, name):
        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        url_fmt = "{}/subscriptions/{}/resourceGroups/{}/providers/Microsoft.App/containerApps/{}/revisions/{}?api-version={}"
        request_url = url_fmt.format(
            management_hostname.strip('/'),
            sub_id,
            resource_group_name,
            container_app_name,
            name,
            cls.api_version)

        r = send_raw_request(cmd.cli_ctx, "GET", request_url)
        return r.json()

    @classmethod
    def restart_revision(cls, cmd, resource_group_name, container_app_name, name):
        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        url_fmt = "{}/subscriptions/{}/resourceGroups/{}/providers/Microsoft.App/containerApps/{}/revisions/{}/restart?api-version={}"
        request_url = url_fmt.format(
            management_hostname.strip('/'),
            sub_id,
            resource_group_name,
            container_app_name,
            name,
            cls.api_version)

        r = send_raw_request(cmd.cli_ctx, "POST", request_url)
        return r.json()

    @classmethod
    def activate_revision(cls, cmd, resource_group_name, container_app_name, name):
        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        url_fmt = "{}/subscriptions/{}/resourceGroups/{}/providers/Microsoft.App/containerApps/{}/revisions/{}/activate?api-version={}"
        request_url = url_fmt.format(
            management_hostname.strip('/'),
            sub_id,
            resource_group_name,
            container_app_name,
            name,
            cls.api_version)

        r = send_raw_request(cmd.cli_ctx, "POST", request_url)
        return r.json()

    @classmethod
    def deactivate_revision(cls, cmd, resource_group_name, container_app_name, name):
        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        url_fmt = "{}/subscriptions/{}/resourceGroups/{}/providers/Microsoft.App/containerApps/{}/revisions/{}/deactivate?api-version={}"
        request_url = url_fmt.format(
            management_hostname.strip('/'),
            sub_id,
            resource_group_name,
            container_app_name,
            name,
            cls.api_version)

        r = send_raw_request(cmd.cli_ctx, "POST", request_url)
        return r.json()

    @classmethod
    def list_replicas(cls, cmd, resource_group_name, container_app_name, revision_name):
        replica_list = []

        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        url_fmt = "{}/subscriptions/{}/resourceGroups/{}/providers/Microsoft.App/containerApps/{}/revisions/{}/replicas?api-version={}"
        request_url = url_fmt.format(
            management_hostname.strip('/'),
            sub_id,
            resource_group_name,
            container_app_name,
            revision_name,
            cls.api_version)

        r = send_raw_request(cmd.cli_ctx, "GET", request_url)
        j = r.json()
        for replica in j["value"]:
            replica_list.append(replica)

        while j.get("nextLink") is not None:
            request_url = j["nextLink"]
            r = send_raw_request(cmd.cli_ctx, "GET", request_url)
            j = r.json()
            for replica in j["value"]:
                replica_list.append(replica)

        return replica_list

    @classmethod
    def get_replica(cls, cmd, resource_group_name, container_app_name, revision_name, replica_name):
        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        url_fmt = "{}/subscriptions/{}/resourceGroups/{}/providers/Microsoft.App/containerApps/{}/revisions/{}/replicas/{}/?api-version={}"
        request_url = url_fmt.format(
            management_hostname.strip('/'),
            sub_id,
            resource_group_name,
            container_app_name,
            revision_name,
            replica_name,
            cls.api_version)

        r = send_raw_request(cmd.cli_ctx, "GET", request_url)
        return r.json()

    @classmethod
    def get_auth_token(cls, cmd, resource_group_name, name):
        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        url_fmt = "{}/subscriptions/{}/resourceGroups/{}/providers/Microsoft.App/containerApps/{}/getAuthToken?api-version={}"
        request_url = url_fmt.format(
            management_hostname.strip('/'),
            sub_id,
            resource_group_name,
            name,
            cls.api_version)

        r = send_raw_request(cmd.cli_ctx, "POST", request_url)
        return r.json()

    @classmethod
    def validate_domain(cls, cmd, resource_group_name, name, hostname):
        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        url_fmt = "{}/subscriptions/{}/resourceGroups/{}/providers/Microsoft.App/containerApps/{}/listCustomHostNameAnalysis?api-version={}&customHostname={}"
        request_url = url_fmt.format(
            management_hostname.strip('/'),
            sub_id,
            resource_group_name,
            name,
            cls.api_version,
            hostname)

        r = send_raw_request(cmd.cli_ctx, "POST", request_url)
        return r.json()


class ManagedEnvironmentClient:
    api_version = CURRENT_API_VERSION

    @classmethod
    def create(cls, cmd, resource_group_name, name, managed_environment_envelope, no_wait=False):
        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        url_fmt = "{}/subscriptions/{}/resourceGroups/{}/providers/Microsoft.App/managedEnvironments/{}?api-version={}"
        request_url = url_fmt.format(
            management_hostname.strip('/'),
            sub_id,
            resource_group_name,
            name,
            cls.api_version)

        r = send_raw_request(cmd.cli_ctx, "PUT", request_url, body=json.dumps(managed_environment_envelope))

        if no_wait:
            return r.json()
        elif r.status_code == 201:
            operation_url = r.headers.get(HEADER_AZURE_ASYNC_OPERATION)
            poll_status(cmd, operation_url)
            r = send_raw_request(cmd.cli_ctx, "GET", request_url)

        return r.json()

    @classmethod
    def update(cls, cmd, resource_group_name, name, managed_environment_envelope, no_wait=False):
        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        url_fmt = "{}/subscriptions/{}/resourceGroups/{}/providers/Microsoft.App/managedEnvironments/{}?api-version={}"
        request_url = url_fmt.format(
            management_hostname.strip('/'),
            sub_id,
            resource_group_name,
            name,
            cls.api_version)

        r = send_raw_request(cmd.cli_ctx, "PATCH", request_url, body=json.dumps(managed_environment_envelope))

        if no_wait:
            return
        elif r.status_code == 202:
            operation_url = r.headers.get(HEADER_LOCATION)
            if "managedEnvironmentOperationStatuses" in operation_url:
                poll_status(cmd, operation_url)
                r = send_raw_request(cmd.cli_ctx, "GET", request_url)
            elif "managedEnvironmentOperationResults" in operation_url:
                response = poll_results(cmd, operation_url)
                if response is None:
                    raise ResourceNotFoundError("Could not find a managed environment")
                else:
                    return response
            else:
                raise AzureResponseError(f"Invalid operation URL: '{operation_url}'")

        return r.json()

    @classmethod
    def delete(cls, cmd, resource_group_name, name, no_wait=False):
        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        url_fmt = "{}/subscriptions/{}/resourceGroups/{}/providers/Microsoft.App/managedEnvironments/{}?api-version={}"
        request_url = url_fmt.format(
            management_hostname.strip('/'),
            sub_id,
            resource_group_name,
            name,
            cls.api_version)

        r = send_raw_request(cmd.cli_ctx, "DELETE", request_url)

        if no_wait:
            return  # API doesn't return JSON (it returns no content)
        elif r.status_code in [200, 201, 202, 204]:
            if r.status_code == 202:
                operation_url = r.headers.get(HEADER_LOCATION)
                poll_results(cmd, operation_url)
                logger.warning('Containerapp environment successfully deleted')
        return

    @classmethod
    def show(cls, cmd, resource_group_name, name):
        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        url_fmt = "{}/subscriptions/{}/resourceGroups/{}/providers/Microsoft.App/managedEnvironments/{}?api-version={}"
        request_url = url_fmt.format(
            management_hostname.strip('/'),
            sub_id,
            resource_group_name,
            name,
            cls.api_version)

        r = send_raw_request(cmd.cli_ctx, "GET", request_url)
        return r.json()

    @classmethod
    def list_by_subscription(cls, cmd, formatter=lambda x: x):
        env_list = []

        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        request_url = "{}/subscriptions/{}/providers/Microsoft.App/managedEnvironments?api-version={}".format(
            management_hostname.strip('/'),
            sub_id,
            cls.api_version)

        r = send_raw_request(cmd.cli_ctx, "GET", request_url)
        j = r.json()
        for env in j["value"]:
            formatted = formatter(env)
            env_list.append(formatted)

        while j.get("nextLink") is not None:
            request_url = j["nextLink"]
            r = send_raw_request(cmd.cli_ctx, "GET", request_url)
            j = r.json()
            for env in j["value"]:
                formatted = formatter(env)
                env_list.append(formatted)

        return env_list

    @classmethod
    def list_by_resource_group(cls, cmd, resource_group_name, formatter=lambda x: x):
        env_list = []

        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        url_fmt = "{}/subscriptions/{}/resourceGroups/{}/providers/Microsoft.App/managedEnvironments?api-version={}"
        request_url = url_fmt.format(
            management_hostname.strip('/'),
            sub_id,
            resource_group_name,
            cls.api_version)

        r = send_raw_request(cmd.cli_ctx, "GET", request_url)
        j = r.json()
        for env in j["value"]:
            formatted = formatter(env)
            env_list.append(formatted)

        while j.get("nextLink") is not None:
            request_url = j["nextLink"]
            r = send_raw_request(cmd.cli_ctx, "GET", request_url)
            j = r.json()
            for env in j["value"]:
                formatted = formatter(env)
                env_list.append(formatted)

        return env_list

    @classmethod
    def show_certificate(cls, cmd, resource_group_name, name, certificate_name):
        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        url_fmt = "{}/subscriptions/{}/resourceGroups/{}/providers/Microsoft.App/managedEnvironments/{}/certificates/{}?api-version={}"
        request_url = url_fmt.format(
            management_hostname.strip('/'),
            sub_id,
            resource_group_name,
            name,
            certificate_name,
            cls.api_version)

        r = send_raw_request(cmd.cli_ctx, "GET", request_url, body=None)
        return r.json()

    @classmethod
    def show_managed_certificate(cls, cmd, resource_group_name, name, certificate_name):
        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        url_fmt = "{}/subscriptions/{}/resourceGroups/{}/providers/Microsoft.App/managedEnvironments/{}/managedCertificates/{}?api-version={}"
        request_url = url_fmt.format(
            management_hostname.strip('/'),
            sub_id,
            resource_group_name,
            name,
            certificate_name,
            cls.api_version)

        r = send_raw_request(cmd.cli_ctx, "GET", request_url, body=None)
        return r.json()

    @classmethod
    def list_certificates(cls, cmd, resource_group_name, name, formatter=lambda x: x):
        certs_list = []

        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        url_fmt = "{}/subscriptions/{}/resourceGroups/{}/providers/Microsoft.App/managedEnvironments/{}/certificates?api-version={}"
        request_url = url_fmt.format(
            management_hostname.strip('/'),
            sub_id,
            resource_group_name,
            name,
            cls.api_version)

        r = send_raw_request(cmd.cli_ctx, "GET", request_url, body=None)
        j = r.json()
        for cert in j["value"]:
            formatted = formatter(cert)
            certs_list.append(formatted)
        return certs_list

    @classmethod
    def list_managed_certificates(cls, cmd, resource_group_name, name, formatter=lambda x: x):
        certs_list = []

        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        url_fmt = "{}/subscriptions/{}/resourceGroups/{}/providers/Microsoft.App/managedEnvironments/{}/managedCertificates?api-version={}"
        request_url = url_fmt.format(
            management_hostname.strip('/'),
            sub_id,
            resource_group_name,
            name,
            cls.api_version)

        r = send_raw_request(cmd.cli_ctx, "GET", request_url, body=None)
        j = r.json()
        for cert in j["value"]:
            formatted = formatter(cert)
            certs_list.append(formatted)
        return certs_list

    @classmethod
    def create_or_update_certificate(cls, cmd, resource_group_name, name, certificate_name, certificate):
        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        url_fmt = "{}/subscriptions/{}/resourceGroups/{}/providers/Microsoft.App/managedEnvironments/{}/certificates/{}?api-version={}"
        request_url = url_fmt.format(
            management_hostname.strip('/'),
            sub_id,
            resource_group_name,
            name,
            certificate_name,
            cls.api_version)

        r = send_raw_request(cmd.cli_ctx, "PUT", request_url, body=json.dumps(certificate))
        return r.json()

    @classmethod
    def create_or_update_managed_certificate(cls, cmd, resource_group_name, name, certificate_name, certificate_envelop, no_wait=False, is_TXT=False):
        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        url_fmt = "{}/subscriptions/{}/resourceGroups/{}/providers/Microsoft.App/managedEnvironments/{}/managedCertificates/{}?api-version={}"
        request_url = url_fmt.format(
            management_hostname.strip('/'),
            sub_id,
            resource_group_name,
            name,
            certificate_name,
            cls.api_version)
        r = send_raw_request(cmd.cli_ctx, "PUT", request_url, body=json.dumps(certificate_envelop))

        if no_wait and not is_TXT:
            return r.json()
        elif r.status_code == 201:
            try:
                start = time.time()
                end = time.time() + POLLING_TIMEOUT_FOR_MANAGED_CERTIFICATE
                animation = PollingAnimation()
                animation.tick()
                r = send_raw_request(cmd.cli_ctx, "GET", request_url)
                message_logged = False
                while r.status_code in [200, 201] and start < end:
                    time.sleep(POLLING_INTERVAL_FOR_MANAGED_CERTIFICATE)
                    animation.tick()
                    r = send_raw_request(cmd.cli_ctx, "GET", request_url)
                    r2 = r.json()
                    if is_TXT and not message_logged and "properties" in r2 and "validationToken" in r2["properties"]:
                        logger.warning('\nPlease copy the token below for TXT record and enter it with your domain provider:\n%s\n', r2["properties"]["validationToken"])
                        message_logged = True
                        if no_wait:
                            break
                    if "properties" not in r2 or "provisioningState" not in r2["properties"] or r2["properties"]["provisioningState"].lower() in ["succeeded", "failed", "canceled"]:
                        break
                    start = time.time()
                animation.flush()
                return r.json()
            except Exception as e:  # pylint: disable=broad-except
                animation.flush()
                raise e
        return r.json()

    @classmethod
    def delete_certificate(cls, cmd, resource_group_name, name, certificate_name):
        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        url_fmt = "{}/subscriptions/{}/resourceGroups/{}/providers/Microsoft.App/managedEnvironments/{}/certificates/{}?api-version={}"
        request_url = url_fmt.format(
            management_hostname.strip('/'),
            sub_id,
            resource_group_name,
            name,
            certificate_name,
            cls.api_version)

        return send_raw_request(cmd.cli_ctx, "DELETE", request_url, body=None)

    @classmethod
    def delete_managed_certificate(cls, cmd, resource_group_name, name, certificate_name):
        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        url_fmt = "{}/subscriptions/{}/resourceGroups/{}/providers/Microsoft.App/managedEnvironments/{}/managedCertificates/{}?api-version={}"
        request_url = url_fmt.format(
            management_hostname.strip('/'),
            sub_id,
            resource_group_name,
            name,
            certificate_name,
            cls.api_version)

        return send_raw_request(cmd.cli_ctx, "DELETE", request_url, body=None)

    @classmethod
    def check_name_availability(cls, cmd, resource_group_name, name, name_availability_request):
        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        url_fmt = "{}/subscriptions/{}/resourceGroups/{}/providers/Microsoft.App/managedEnvironments/{}/checkNameAvailability?api-version={}"
        request_url = url_fmt.format(
            management_hostname.strip('/'),
            sub_id,
            resource_group_name,
            name,
            cls.api_version)

        r = send_raw_request(cmd.cli_ctx, "POST", request_url, body=json.dumps(name_availability_request))
        return r.json()

    @classmethod
    def get_auth_token(cls, cmd, resource_group_name, name):
        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        url_fmt = "{}/subscriptions/{}/resourceGroups/{}/providers/Microsoft.App/managedEnvironments/{}/getAuthToken?api-version={}"
        request_url = url_fmt.format(
            management_hostname.strip('/'),
            sub_id,
            resource_group_name,
            name,
            cls.api_version)

        r = send_raw_request(cmd.cli_ctx, "POST", request_url)
        return r.json()

    @classmethod
    def list_usages(cls, cmd, resource_group_name, name):
        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        url_fmt = "{}/subscriptions/{}/resourceGroups/{}/providers/Microsoft.App/managedEnvironments/{}/usages?api-version={}"
        request_url = url_fmt.format(
            management_hostname.strip('/'),
            sub_id,
            resource_group_name,
            name,
            cls.api_version)

        r = send_raw_request(cmd.cli_ctx, "GET", request_url)
        return r.json()


class WorkloadProfileClient:
    api_version = CURRENT_API_VERSION

    @classmethod
    def list_supported(cls, cmd, location):
        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        url_fmt = "{}/subscriptions/{}/providers/Microsoft.App/locations/{}/availableManagedEnvironmentsWorkloadProfileTypes?api-version={}"
        request_url = url_fmt.format(
            management_hostname.strip('/'),
            sub_id,
            location,
            cls.api_version)

        r = send_raw_request(cmd.cli_ctx, "GET", request_url)
        return r.json().get("value")

    @classmethod
    def list(cls, cmd, resource_group_name, env_name):
        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        url_fmt = "{}/subscriptions/{}/resourcegroups/{}/providers/Microsoft.App/managedEnvironments/{}/workloadProfileStates?api-version={}"
        request_url = url_fmt.format(
            management_hostname.strip('/'),
            sub_id,
            resource_group_name,
            env_name,
            cls.api_version)

        r = send_raw_request(cmd.cli_ctx, "GET", request_url)
        return r.json().get("value")


class ContainerAppsJobClient():
    api_version = CURRENT_API_VERSION

    @classmethod
    def create_or_update(cls, cmd, resource_group_name, name, containerapp_job_envelope, no_wait=False):
        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        url_fmt = "{}/subscriptions/{}/resourceGroups/{}/providers/Microsoft.App/jobs/{}?api-version={}"
        request_url = url_fmt.format(
            management_hostname.strip('/'),
            sub_id,
            resource_group_name,
            name,
            cls.api_version)

        r = send_raw_request(cmd.cli_ctx, "PUT", request_url, body=json.dumps(containerapp_job_envelope))

        if no_wait:
            return r.json()
        elif r.status_code == 201:
            operation_url = r.headers.get(HEADER_AZURE_ASYNC_OPERATION)
            poll_status(cmd, operation_url)
            r = send_raw_request(cmd.cli_ctx, "GET", request_url)

        return r.json()

    @classmethod
    def update(cls, cmd, resource_group_name, name, containerapp_job_envelope, no_wait=False):
        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager

        sub_id = get_subscription_id(cmd.cli_ctx)
        url_fmt = "{}/subscriptions/{}/resourceGroups/{}/providers/Microsoft.App/jobs/{}?api-version={}"
        request_url = url_fmt.format(
            management_hostname.strip('/'),
            sub_id,
            resource_group_name,
            name,
            cls.api_version)

        r = send_raw_request(cmd.cli_ctx, "PATCH", request_url, body=json.dumps(containerapp_job_envelope))

        if no_wait:
            return
        elif r.status_code == 202:
            operation_url = r.headers.get(HEADER_LOCATION)
            response = poll_results(cmd, operation_url)
            if response is None:
                raise ResourceNotFoundError("Could not find a container App Job")
            else:
                return response

        return r.json()

    @classmethod
    def show(cls, cmd, resource_group_name, name):
        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        url_fmt = "{}/subscriptions/{}/resourceGroups/{}/providers/Microsoft.App/jobs/{}?api-version={}"
        request_url = url_fmt.format(
            management_hostname.strip('/'),
            sub_id,
            resource_group_name,
            name,
            cls.api_version)

        r = send_raw_request(cmd.cli_ctx, "GET", request_url)
        return r.json()

    @classmethod
    def list_by_subscription(cls, cmd, formatter=lambda x: x):
        app_list = []

        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        request_url = "{}/subscriptions/{}/providers/Microsoft.App/jobs?api-version={}".format(
            management_hostname.strip('/'),
            sub_id,
            cls.api_version)

        r = send_raw_request(cmd.cli_ctx, "GET", request_url)
        j = r.json()
        for app in j["value"]:
            formatted = formatter(app)
            app_list.append(formatted)

        while j.get("nextLink") is not None:
            request_url = j["nextLink"]
            r = send_raw_request(cmd.cli_ctx, "GET", request_url)
            j = r.json()
            for app in j["value"]:
                formatted = formatter(app)
                app_list.append(formatted)

        return app_list

    @classmethod
    def list_by_resource_group(cls, cmd, resource_group_name, formatter=lambda x: x):
        app_list = []

        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        url_fmt = "{}/subscriptions/{}/resourceGroups/{}/providers/Microsoft.App/jobs?api-version={}"
        request_url = url_fmt.format(
            management_hostname.strip('/'),
            sub_id,
            resource_group_name,
            cls.api_version)

        r = send_raw_request(cmd.cli_ctx, "GET", request_url)
        j = r.json()
        for app in j["value"]:
            formatted = formatter(app)
            app_list.append(formatted)

        while j.get("nextLink") is not None:
            request_url = j["nextLink"]
            r = send_raw_request(cmd.cli_ctx, "GET", request_url)
            j = r.json()
            for app in j["value"]:
                formatted = formatter(app)
                app_list.append(formatted)

        return app_list

    @classmethod
    def delete(cls, cmd, resource_group_name, name, no_wait=False):
        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        url_fmt = "{}/subscriptions/{}/resourceGroups/{}/providers/Microsoft.App/jobs/{}?api-version={}"
        request_url = url_fmt.format(
            management_hostname.strip('/'),
            sub_id,
            resource_group_name,
            name,
            cls.api_version)

        r = send_raw_request(cmd.cli_ctx, "DELETE", request_url)

        if no_wait:
            return  # API doesn't return JSON (it returns no content)
        elif r.status_code in [200, 201, 202, 204]:
            if r.status_code == 202:
                operation_url = r.headers.get(HEADER_LOCATION)
                poll_results(cmd, operation_url)
                logger.warning('Containerapp job successfully deleted')

    @classmethod
    def start_job(cls, cmd, resource_group_name, name, containerapp_job_start_envelope):
        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        url_fmt = "{}/subscriptions/{}/resourceGroups/{}/providers/Microsoft.App/jobs/{}/start?api-version={}"
        request_url = url_fmt.format(
            management_hostname.strip('/'),
            sub_id,
            resource_group_name,
            name,
            cls.api_version)
        if containerapp_job_start_envelope is None:
            r = send_raw_request(cmd.cli_ctx, "POST", request_url)
        else:
            r = send_raw_request(cmd.cli_ctx, "POST", request_url, body=json.dumps(containerapp_job_start_envelope))

        return r.json()

    @classmethod
    def stop_job(cls, cmd, resource_group_name, name, job_execution_name):
        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)

        if not job_execution_name:
            url_fmt = "{}/subscriptions/{}/resourceGroups/{}/providers/Microsoft.App/jobs/{}/stop?api-version={}"
            request_url = url_fmt.format(
                management_hostname.strip('/'),
                sub_id,
                resource_group_name,
                name,
                cls.api_version)
            r = send_raw_request(cmd.cli_ctx, "POST", request_url)
            return r.json()
        else:
            url_fmt = "{}/subscriptions/{}/resourceGroups/{}/providers/Microsoft.App/jobs/{}/stop/{}?api-version={}"
            request_url = url_fmt.format(
                management_hostname.strip('/'),
                sub_id,
                resource_group_name,
                name,
                job_execution_name,
                cls.api_version)
            r = send_raw_request(cmd.cli_ctx, "POST", request_url)
            return r

    @classmethod
    def get_executions(cls, cmd, resource_group_name, name):
        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        url_fmt = "{}/subscriptions/{}/resourceGroups/{}/providers/Microsoft.App/jobs/{}/executions?api-version={}"
        request_url = url_fmt.format(
            management_hostname.strip('/'),
            sub_id,
            resource_group_name,
            name,
            cls.api_version)

        r = send_raw_request(cmd.cli_ctx, "GET", request_url)
        return r.json()

    @classmethod
    def get_single_execution(cls, cmd, resource_group_name, name, job_execution_name):
        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        url_fmt = "{}/subscriptions/{}/resourceGroups/{}/providers/Microsoft.App/jobs/{}/executions/{}?api-version={}"
        request_url = url_fmt.format(
            management_hostname.strip('/'),
            sub_id,
            resource_group_name,
            name,
            job_execution_name,
            cls.api_version)

        r = send_raw_request(cmd.cli_ctx, "GET", request_url)
        return r.json()

    @classmethod
    def list_secrets(cls, cmd, resource_group_name, name):

        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        url_fmt = "{}/subscriptions/{}/resourceGroups/{}/providers/Microsoft.App/jobs/{}/listSecrets?api-version={}"
        request_url = url_fmt.format(
            management_hostname.strip('/'),
            sub_id,
            resource_group_name,
            name,
            cls.api_version)

        r = send_raw_request(cmd.cli_ctx, "POST", request_url, body=None)
        return r.json()


# Deprecated, workaround for sourcecontrols
def poll(cmd, request_url, poll_if_status):  # pylint: disable=inconsistent-return-statements
    from azure.cli.command_modules.containerapp._utils import safe_get
    try:
        start = time.time()
        end = time.time() + POLLING_TIMEOUT
        animation = PollingAnimation()

        animation.tick()
        r = send_raw_request(cmd.cli_ctx, "GET", request_url)

        while r.status_code in [200, 201] and start < end:
            time.sleep(POLLING_SECONDS)
            animation.tick()

            r = send_raw_request(cmd.cli_ctx, "GET", request_url)
            r2 = r.json()
            provisioning_state = safe_get(r2, "properties", "provisioningState")
            operation_state = safe_get(r2, "properties", "operationState")
            state = provisioning_state or operation_state
            if state is None or state.lower() in ["succeeded", "failed", "canceled"]:
                break
            start = time.time()

        animation.flush()
        return r.json()
    except Exception as e:  # pylint: disable=broad-except
        animation.flush()

        delete_statuses = ["scheduledfordelete", "cancelled"]

        if poll_if_status not in delete_statuses:  # Catch "not found" errors if polling for delete
            raise e


class GitHubActionClient:
    api_version = CURRENT_API_VERSION

    @classmethod
    def create_or_update(cls, cmd, resource_group_name, name, github_action_envelope, headers, no_wait=False):
        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        url_fmt = "{}/subscriptions/{}/resourceGroups/{}/providers/Microsoft.App/containerApps/{}/sourcecontrols/current?api-version={}"
        request_url = url_fmt.format(
            management_hostname.strip('/'),
            sub_id,
            resource_group_name,
            name,
            cls.api_version)

        r = send_raw_request(cmd.cli_ctx, "PUT", request_url, body=json.dumps(github_action_envelope), headers=headers)

        if no_wait:
            return r.json()
        elif r.status_code == 201:
            url_fmt = "{}/subscriptions/{}/resourceGroups/{}/providers/Microsoft.App/containerApps/{}/sourcecontrols/current?api-version={}"
            request_url = url_fmt.format(
                management_hostname.strip('/'),
                sub_id,
                resource_group_name,
                name,
                cls.api_version)
            return poll(cmd, request_url, "inprogress")

        return r.json()

    @classmethod
    def show(cls, cmd, resource_group_name, name):
        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        url_fmt = "{}/subscriptions/{}/resourceGroups/{}/providers/Microsoft.App/containerApps/{}/sourcecontrols/current?api-version={}"
        request_url = url_fmt.format(
            management_hostname.strip('/'),
            sub_id,
            resource_group_name,
            name,
            cls.api_version)

        r = send_raw_request(cmd.cli_ctx, "GET", request_url)
        return r.json()

    @classmethod
    def delete(cls, cmd, resource_group_name, name, headers, no_wait=False):
        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        url_fmt = "{}/subscriptions/{}/resourceGroups/{}/providers/Microsoft.App/containerApps/{}/sourcecontrols/current?api-version={}"
        request_url = url_fmt.format(
            management_hostname.strip('/'),
            sub_id,
            resource_group_name,
            name,
            cls.api_version)

        r = send_raw_request(cmd.cli_ctx, "DELETE", request_url, headers=headers)

        if no_wait:
            return  # API doesn't return JSON (it returns no content)
        elif r.status_code in [200, 201, 202, 204]:
            url_fmt = "{}/subscriptions/{}/resourceGroups/{}/providers/Microsoft.App/containerApps/{}/sourcecontrols/current?api-version={}"
            request_url = url_fmt.format(
                management_hostname.strip('/'),
                sub_id,
                resource_group_name,
                name,
                cls.api_version)

            if r.status_code == 202:
                from azure.cli.core.azclierror import ResourceNotFoundError
                try:
                    poll(cmd, request_url, "cancelled")
                except ResourceNotFoundError:
                    pass
                logger.warning('Containerapp github action successfully deleted')
        return

    @classmethod
    def get_workflow_name(cls, cmd, repo, branch_name, container_app_name, token):
        # Fetch files in the .github/workflows folder using the GitHub API
        # https://docs.github.com/en/rest/repos/contents#get-repository-content
        workflows_folder_name = ".github/workflows"
        url_fmt = "{}/repos/{}/contents/{}?ref={}"
        request_url = url_fmt.format(
            "https://api.github.com",
            repo,
            workflows_folder_name,
            branch_name)

        import re
        try:
            headers = ["Authorization=Bearer {}".format(token)]
            r = send_raw_request(cmd.cli_ctx, "GET", request_url, headers=headers)
            if r.status_code == 200:
                r_json = r.json()

                # See if any workflow file matches the expected naming pattern (including either .yml or .yaml)
                workflow_file = [x for x in r_json if x["name"].startswith(container_app_name) and re.match(r'.*AutoDeployTrigger.*\.y.?ml', x["name"])]
                if len(workflow_file) == 1:
                    return workflow_file[0]["name"].replace(".yaml", "").replace(".yml", "")
        except:  # pylint: disable=bare-except
            pass

        return None


class DaprComponentClient:
    api_version = CURRENT_API_VERSION

    @classmethod
    def create_or_update(cls, cmd, resource_group_name, environment_name, name, dapr_component_envelope):

        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        url_fmt = "{}/subscriptions/{}/resourceGroups/{}/providers/Microsoft.App/managedEnvironments/{}/daprComponents/{}?api-version={}"
        request_url = url_fmt.format(
            management_hostname.strip('/'),
            sub_id,
            resource_group_name,
            environment_name,
            name,
            cls.api_version)

        r = send_raw_request(cmd.cli_ctx, "PUT", request_url, body=json.dumps(dapr_component_envelope))

        return r.json()

    @classmethod
    def delete(cls, cmd, resource_group_name, environment_name, name):
        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        url_fmt = "{}/subscriptions/{}/resourceGroups/{}/providers/Microsoft.App/managedEnvironments/{}/daprComponents/{}?api-version={}"
        request_url = url_fmt.format(
            management_hostname.strip('/'),
            sub_id,
            resource_group_name,
            environment_name,
            name,
            cls.api_version)

        send_raw_request(cmd.cli_ctx, "DELETE", request_url)
        return

    @classmethod
    def show(cls, cmd, resource_group_name, environment_name, name):
        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        url_fmt = "{}/subscriptions/{}/resourceGroups/{}/providers/Microsoft.App/managedEnvironments/{}/daprComponents/{}?api-version={}"
        request_url = url_fmt.format(
            management_hostname.strip('/'),
            sub_id,
            resource_group_name,
            environment_name,
            name,
            cls.api_version)

        r = send_raw_request(cmd.cli_ctx, "GET", request_url)
        return r.json()

    @classmethod
    def list(cls, cmd, resource_group_name, environment_name, formatter=lambda x: x):
        app_list = []

        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        request_url = "{}/subscriptions/{}/resourceGroups/{}/providers/Microsoft.App/managedEnvironments/{}/daprComponents?api-version={}".format(
            management_hostname.strip('/'),
            sub_id,
            resource_group_name,
            environment_name,
            cls.api_version)

        r = send_raw_request(cmd.cli_ctx, "GET", request_url)
        j = r.json()
        for app in j["value"]:
            formatted = formatter(app)
            app_list.append(formatted)

        while j.get("nextLink") is not None:
            request_url = j["nextLink"]
            r = send_raw_request(cmd.cli_ctx, "GET", request_url)
            j = r.json()
            for app in j["value"]:
                formatted = formatter(app)
                app_list.append(formatted)

        return app_list


class StorageClient:
    api_version = CURRENT_API_VERSION

    @classmethod
    def create_or_update(cls, cmd, resource_group_name, env_name, name, storage_envelope):
        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        url_fmt = "{}/subscriptions/{}/resourceGroups/{}/providers/Microsoft.App/managedEnvironments/{}/storages/{}?api-version={}"
        request_url = url_fmt.format(
            management_hostname.strip('/'),
            sub_id,
            resource_group_name,
            env_name,
            name,
            cls.api_version)

        r = send_raw_request(cmd.cli_ctx, "PUT", request_url, body=json.dumps(storage_envelope))

        return r.json()

    @classmethod
    def delete(cls, cmd, resource_group_name, env_name, name):
        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        url_fmt = "{}/subscriptions/{}/resourceGroups/{}/providers/Microsoft.App/managedEnvironments/{}/storages/{}?api-version={}"
        request_url = url_fmt.format(
            management_hostname.strip('/'),
            sub_id,
            resource_group_name,
            env_name,
            name,
            cls.api_version)

        send_raw_request(cmd.cli_ctx, "DELETE", request_url)

        return

    @classmethod
    def show(cls, cmd, resource_group_name, env_name, name):
        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        url_fmt = "{}/subscriptions/{}/resourceGroups/{}/providers/Microsoft.App/managedEnvironments/{}/storages/{}?api-version={}"
        request_url = url_fmt.format(
            management_hostname.strip('/'),
            sub_id,
            resource_group_name,
            env_name,
            name,
            cls.api_version)

        r = send_raw_request(cmd.cli_ctx, "GET", request_url)
        return r.json()

    @classmethod
    def list(cls, cmd, resource_group_name, env_name, formatter=lambda x: x):
        env_list = []

        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        url_fmt = "{}/subscriptions/{}/resourceGroups/{}/providers/Microsoft.App/managedEnvironments/{}/storages?api-version={}"
        request_url = url_fmt.format(
            management_hostname.strip('/'),
            sub_id,
            resource_group_name,
            env_name,
            cls.api_version)

        r = send_raw_request(cmd.cli_ctx, "GET", request_url)
        j = r.json()
        for env in j["value"]:
            formatted = formatter(env)
            env_list.append(formatted)

        while j.get("nextLink") is not None:
            request_url = j["nextLink"]
            r = send_raw_request(cmd.cli_ctx, "GET", request_url)
            j = r.json()
            for env in j["value"]:
                formatted = formatter(env)
                env_list.append(formatted)

        return env_list


class AuthClient:
    api_version = CURRENT_API_VERSION

    @classmethod
    def create_or_update(cls, cmd, resource_group_name, container_app_name, auth_config_name, auth_config_envelope):
        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        request_url = f"{management_hostname}subscriptions/{sub_id}/resourceGroups/{resource_group_name}/providers/Microsoft.App/containerApps/{container_app_name}/authConfigs/{auth_config_name}?api-version={cls.api_version}"

        if "properties" not in auth_config_envelope:  # sdk does this for us
            temp_env = auth_config_envelope
            auth_config_envelope = {}
            auth_config_envelope["properties"] = temp_env

        r = send_raw_request(cmd.cli_ctx, "PUT", request_url, body=json.dumps(auth_config_envelope))

        return r.json()

    @classmethod
    def delete(cls, cmd, resource_group_name, container_app_name, auth_config_name):
        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        request_url = f"{management_hostname}subscriptions/{sub_id}/resourceGroups/{resource_group_name}/providers/Microsoft.App/containerApps/{container_app_name}/authConfigs/{auth_config_name}?api-version={cls.api_version}"

        send_raw_request(cmd.cli_ctx, "DELETE", request_url)
        return

    @classmethod
    def get(cls, cmd, resource_group_name, container_app_name, auth_config_name):
        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        request_url = f"{management_hostname}subscriptions/{sub_id}/resourceGroups/{resource_group_name}/providers/Microsoft.App/containerApps/{container_app_name}/authConfigs/{auth_config_name}?api-version={cls.api_version}"

        r = send_raw_request(cmd.cli_ctx, "GET", request_url)
        return r.json()


class SubscriptionClient:
    api_version = CURRENT_API_VERSION

    @classmethod
    def show_custom_domain_verification_id(cls, cmd):
        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        request_url = f"{management_hostname}subscriptions/{sub_id}/providers/Microsoft.App/getCustomDomainVerificationId?api-version={cls.api_version}"

        r = send_raw_request(cmd.cli_ctx, "POST", request_url)
        return r.json()

    @classmethod
    def list_usages(cls, cmd, location):
        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        request_url = f"{management_hostname}subscriptions/{sub_id}/providers/Microsoft.App/locations/{location}/usages?api-version={cls.api_version}"

        r = send_raw_request(cmd.cli_ctx, "GET", request_url)
        return r.json()


class HttpRouteConfigClient:
    api_version = CURRENT_API_VERSION

    @classmethod
    def create(cls, cmd, resource_group_name, name, http_route_config_name, http_route_config_envelope):
        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        url_fmt = "{}/subscriptions/{}/resourceGroups/{}/providers/Microsoft.App/managedEnvironments/{}/httpRouteConfigs/{}?api-version={}"
        request_url = url_fmt.format(
            management_hostname.strip('/'),
            sub_id,
            resource_group_name,
            name,
            http_route_config_name,
            cls.api_version)

        r = send_raw_request(cmd.cli_ctx, "PUT", request_url, body=json.dumps(http_route_config_envelope))
        return r.json()

    @classmethod
    def update(cls, cmd, resource_group_name, name, http_route_config_name, http_route_config_envelope):
        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        url_fmt = "{}/subscriptions/{}/resourceGroups/{}/providers/Microsoft.App/managedEnvironments/{}/httpRouteConfigs/{}?api-version={}"
        request_url = url_fmt.format(
            management_hostname.strip('/'),
            sub_id,
            resource_group_name,
            name,
            http_route_config_name,
            cls.api_version)

        r = send_raw_request(cmd.cli_ctx, "PATCH", request_url, body=json.dumps(http_route_config_envelope))
        return r.json()

    @classmethod
    def list(cls, cmd, resource_group_name, name):
        route_list = []
        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        url_fmt = "{}/subscriptions/{}/resourceGroups/{}/providers/Microsoft.App/managedEnvironments/{}/httpRouteConfigs?api-version={}"
        request_url = url_fmt.format(
            management_hostname.strip('/'),
            sub_id,
            resource_group_name,
            name,
            cls.api_version)

        r = send_raw_request(cmd.cli_ctx, "GET", request_url, body=None)
        j = r.json()
        for route in j["value"]:
            route_list.append(route)
        return route_list

    @classmethod
    def show(cls, cmd, resource_group_name, name, http_route_config_name):
        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        url_fmt = "{}/subscriptions/{}/resourceGroups/{}/providers/Microsoft.App/managedEnvironments/{}/httpRouteConfigs/{}?api-version={}"
        request_url = url_fmt.format(
            management_hostname.strip('/'),
            sub_id,
            resource_group_name,
            name,
            http_route_config_name,
            cls.api_version)

        r = send_raw_request(cmd.cli_ctx, "GET", request_url, body=None)
        return r.json()

    @classmethod
    def delete(cls, cmd, resource_group_name, name, http_route_config_name):
        management_hostname = cmd.cli_ctx.cloud.endpoints.resource_manager
        sub_id = get_subscription_id(cmd.cli_ctx)
        url_fmt = "{}/subscriptions/{}/resourceGroups/{}/providers/Microsoft.App/managedEnvironments/{}/httpRouteConfigs/{}?api-version={}"
        request_url = url_fmt.format(
            management_hostname.strip('/'),
            sub_id,
            resource_group_name,
            name,
            http_route_config_name,
            cls.api_version)

        send_raw_request(cmd.cli_ctx, "DELETE", request_url, body=None)
        # API doesn't return JSON (it returns no content)
        return
