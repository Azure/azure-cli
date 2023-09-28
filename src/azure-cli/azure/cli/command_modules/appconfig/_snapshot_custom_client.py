# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, too-many-locals, too-many-statements, too-many-branches, too-few-public-methods

from azure.appconfiguration import AzureAppConfigurationClient, ConfigurationSetting
from azure.appconfiguration._generated.models import Error as AppConfigError
from azure.core.rest import HttpRequest
from azure.core.paging import ItemPaged
from azure.core.utils import case_insensitive_dict
from azure.core.exceptions import ClientAuthenticationError, ResourceExistsError, ResourceNotFoundError, HttpResponseError, ResourceModifiedError, map_error
from msrest import Serializer
import json

from ._constants import SnapshotConstants
from ._snapshotmodels import Snapshot, SnapshotListResult, OperationStatusResponse
from ._snapshot_exceptions import BadSnapshotRequestException


class ProvisioningStatus:
    RUNNING = "Running"
    SUCCEEDED = "Succeeded"
    FAILED = "Failed"


class RequestMethod:
    GET = "GET"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


_ERROR_MAP = {
    400: BadSnapshotRequestException,
    401: ClientAuthenticationError,
    404: ResourceNotFoundError,
    409: ResourceExistsError,
    412: ResourceModifiedError
}


def _build_request(
    template_url_default,
    method,
    *,
    path_arguments=None,
    if_match=None,
    if_none_match=None,
    sync_token=None,
    **kwargs
):
    _headers = case_insensitive_dict(kwargs.pop("headers", {}) or {})
    _params = case_insensitive_dict(kwargs.pop("params", {}) or {})

    api_version = kwargs.pop("api_version", SnapshotConstants.API_VERSION)
    accept = _headers.pop(
        "Accept", "application/json, application/problem+json"
    )

    # Construct URL
    _url = kwargs.pop("template_url", template_url_default)
    _path_arguments = path_arguments or {}
    _url = _format_url_section(_url, **_path_arguments)

    _serializer = Serializer()

    # Construct parameters
    _params["api-version"] = _serializer.query("api_version", api_version, "str")

    # Construct headers
    if sync_token is not None:
        _headers["Sync-Token"] = _serializer.header("sync_token", sync_token, "str")

    if if_match is not None:
        _headers["If-Match"] = _serializer.header("if_match", if_match, "str")
    if if_none_match is not None:
        _headers["If-None-Match"] = _serializer.header("if_none_match", if_none_match, "str")

    _headers["Accept"] = _serializer.header("accept", accept, "str")

    return HttpRequest(method=method.upper(), url=_url, params=_params, headers=_headers, **kwargs)


# Requests
def build_get_snapshot_request(
    name,
    select=None,
    if_match=None,
    if_none_match=None,
    sync_token=None,
    **kwargs
):
    _params = {}

    if select is not None:
        _params["$Select"] = Serializer().query("select", select, "[str]", div=",")

    return _build_request(
        "/snapshots/{name}",
        RequestMethod.GET,
        path_arguments={"name": name},
        if_match=if_match,
        if_none_match=if_none_match,
        sync_token=sync_token,
        params=_params,
        **kwargs
    )


def build_list_snapshots_request(
    name_filter=None,
    status_filter=None,
    select=None,
    sync_token=None,
    **kwargs
):
    _params = {}

    if name_filter is not None:
        _params['name'] = name_filter

    if status_filter is not None:
        _params['status'] = status_filter

    if select is not None:
        _params["$Select"] = Serializer().query("select", select, "[str]", div=",")

    return _build_request(
        "/snapshots",
        RequestMethod.GET,
        sync_token=sync_token,
        params=_params,
        **kwargs
    )


def build_list_snapshot_kvs_request(
    name,
    select=None,
    sync_token=None,
    **kwargs
):
    _params = {"snapshot": name}

    if select is not None:
        _params["$Select"] = Serializer().query("select", select, "[str]", div=",")

    return _build_request(
        "/kv",
        RequestMethod.GET,
        sync_token=sync_token,
        params=_params,
        **kwargs
    )


def build_status_update_request(
    name,
    archive_snapshot,
    if_match=None,
    if_none_match=None,
    sync_token=None,
    **kwargs
):
    request_body = {"status": "archived" if archive_snapshot else "ready"}

    return _build_request(
        "/snapshots/{name}",
        RequestMethod.PATCH,
        path_arguments={"name": name},
        json=request_body,
        if_match=if_match,
        if_none_match=if_none_match,
        sync_token=sync_token,
        **kwargs
    )


def build_put_snapshot_request(
    name,
    filters,
    composition_type=None,
    retention_period=None,
    tags=None,
    if_match=None,
    if_none_match=None,
    sync_token=None,
    **kwargs
):

    request_body = {}

    if not filters or len(filters) < 1:
        raise ValueError("There should be at least one filter specified.")

    request_body["filters"] = filters

    if composition_type is not None:
        if composition_type not in ("key", "key_label"):
            raise ValueError("Value should either be 'key' or 'key_label'.")

        request_body["composition_type"] = composition_type

    if retention_period is not None:
        if not isinstance(retention_period, int) or retention_period < 0:
            raise ValueError("Retention period value should be a non-negative integer value.")

        request_body["retention_period"] = retention_period

    if tags:
        request_body["tags"] = tags

    return _build_request(
        "/snapshots/{name}",
        RequestMethod.PUT,
        path_arguments={"name": name},
        json=request_body,
        if_match=if_match,
        if_none_match=if_none_match,
        sync_token=sync_token,
        **kwargs
    )


def _format_url_section(template, **kwargs):
    components = template.split("/")
    while components:
        try:
            return template.format(**kwargs)
        except KeyError as key:
            formatted_components = template.split("/")
            components = [c for c in formatted_components if "{}".format(key.args[0]) not in c]
            template = "/".join(components)


class AppConfigSnapshotClient:

    def __init__(self, appConfigClient):
        appConfiguration = appConfigClient._impl
        self._serializer = appConfiguration._serialize
        self._deserializer = appConfiguration._deserialize
        self._sync_token = appConfiguration._config.sync_token
        self._endpoint = appConfiguration._config.endpoint
        self._client = appConfiguration._client

    @classmethod
    def from_connection_string(cls, connection_string):
        return cls(AzureAppConfigurationClient.from_connection_string(connection_string))

    def begin_create_snapshot(
            self,
            name,
            filters,
            composition_type=None,
            retention_period=None,
            tags=None,
            if_match=None,
            if_none_match=None,
            **kwargs):
        """
        Poll the operation status after a given interval based on the retry-after header (default 10s) to ensure that
        the snapshot creation has succeeded or failed.
        The request times out after 10 mins by default unless otherwise specified.
        """
        timeout = kwargs.pop("timeout", 600)
        default_polling_interval = kwargs.pop("polling_interval", 10)

        from datetime import datetime
        import time
        from azure.cli.core.commands.progress import IndeterminateStandardOut

        progress = IndeterminateStandardOut()

        def _get_elapsed_time_from(start_time: datetime):
            return (datetime.now() - start_time).total_seconds()

        def _delay(sleep_time_seconds):
            delay_start = datetime.now()

            while _get_elapsed_time_from(delay_start) < sleep_time_seconds:
                progress.spinner.step(label="Provisioning")
                time.sleep(1)

        progress.write({"message": "Starting"})
        initial_response = self.create_snapshot(
            name,
            filters,
            composition_type,
            retention_period,
            tags,
            if_match=if_match,
            if_none_match=if_none_match,
            **kwargs
        )
        status_link = initial_response.headers["Operation-Location"]

        current_state = self._get_operation_status(status_link)

        start_time = datetime.now()
        while current_state.operation_status.status == ProvisioningStatus.RUNNING:
            progress.spinner.step(label="Provisioning")
            if _get_elapsed_time_from(start_time) > timeout:
                progress.clear()
                raise TimeoutError("The create request timed out.")

            polling_interval = current_state.retry_after or default_polling_interval
            _delay(polling_interval)

            current_state = self._get_operation_status(status_link)

        progress.clear()
        if current_state.operation_status.status == ProvisioningStatus.SUCCEEDED:
            return self.get_snapshot(name=name)

        error = current_state.operation_status.error

        raise HttpResponseError('Snapshot creation failed with status code {}. Reason: {}'.format(
            error.code, error.message))

    def _get_operation_status(self, status_link):
        request = HttpRequest(RequestMethod.GET, url=status_link)

        response = self._client.send_request(request)

        if response.status_code not in [200]:
            map_error(status_code=response.status_code, response=response, error_map=_ERROR_MAP)
            error = self._deserializer.failsafe_deserialize(AppConfigError, response)
            raise HttpResponseError(response=response, model=error)

        return OperationStatusResponse.from_response(response)

    def create_snapshot(
            self,
            name,
            filters,
            composition_type=None,
            retention_period=None,
            tags=None,
            if_match=None,
            if_none_match=None,
            **kwargs):
        _headers = kwargs.pop("headers", {}) or {}

        request = build_put_snapshot_request(
            name=name,
            filters=filters,
            composition_type=composition_type,
            retention_period=retention_period,
            tags=tags,
            sync_token=self._sync_token,
            if_match=if_match,
            if_none_match=if_none_match,
            headers=_headers
        )

        serialized_endpoint = self._serializer.url("endpoint", self._endpoint, 'str', skip_quote=True)
        request.url = serialized_endpoint + request.url

        response = self._client.send_request(request)

        if response.status_code not in [201]:
            map_error(status_code=response.status_code, response=response, error_map=_ERROR_MAP)
            error = self._deserializer.failsafe_deserialize(AppConfigError, response)
            raise HttpResponseError(response=response, model=error)

        return response

    def get_snapshot(
            self,
            name,
            fields=None,
            if_match=None,
            if_none_match=None,
            **kwargs):

        _headers = kwargs.pop("headers", {}) or {}

        request = build_get_snapshot_request(
            name=name,
            select=fields,
            if_match=if_match,
            if_none_match=if_none_match,
            sync_token=self._sync_token,
            headers=_headers
        )

        serialized_endpoint = self._serializer.url("endpoint", self._endpoint, 'str', skip_quote=True)
        request.url = serialized_endpoint + request.url

        response = self._client.send_request(request)

        if response.status_code not in [200]:
            map_error(status_code=response.status_code, response=response, error_map=_ERROR_MAP)
            error = self._deserializer.failsafe_deserialize(AppConfigError, response)
            raise HttpResponseError(response=response, model=error)

        return Snapshot.from_json(json.loads(response.text()))

    def list_snapshots(
            self,
            name=None,
            status=None,
            fields=None,
            **kwargs):

        _headers = kwargs.pop("headers", {}) or {}

        status_filter = ",".join(status) if status else None

        initial_request = build_list_snapshots_request(
            name_filter=name,
            status_filter=status_filter,
            select=fields,
            sync_token=self._sync_token,
            headers=_headers)

        # Extract next page link and page data
        def extract_data(response):
            deserialized_data = SnapshotListResult.from_json(json.loads(response.text()))
            return deserialized_data.next_link or None, iter(deserialized_data.items)

        return self._fetch_paged(initial_request, extract_data, **kwargs)

    def archive_snapshot(
            self,
            name,
            if_match=None,
            if_none_match=None,
            **kwargs):
        _headers = kwargs.pop("headers", {}) or {}

        request = build_status_update_request(
            name=name,
            archive_snapshot=True,
            if_match=if_match,
            if_none_match=if_none_match,
            sync_token=self._sync_token,
            headers=_headers
        )

        serialized_endpoint = self._serializer.url("endpoint", self._endpoint, 'str', skip_quote=True)
        request.url = serialized_endpoint + request.url

        response = self._client.send_request(request)

        if response.status_code not in [200]:
            map_error(status_code=response.status_code, response=response, error_map=_ERROR_MAP)
            error = self._deserializer.failsafe_deserialize(AppConfigError, response)
            raise HttpResponseError(response=response, model=error)

        return Snapshot.from_json(json.loads(response.text()))

    def recover_snapshot(
            self,
            name,
            if_match=None,
            if_none_match=None,
            **kwargs):
        _headers = kwargs.pop("headers", {}) or {}

        request = build_status_update_request(
            name=name,
            archive_snapshot=False,
            if_match=if_match,
            if_none_match=if_none_match,
            sync_token=self._sync_token,
            headers=_headers
        )

        serialized_endpoint = self._serializer.url("endpoint", self._endpoint, 'str', skip_quote=True)
        request.url = serialized_endpoint + request.url

        response = self._client.send_request(request)

        if response.status_code not in [200]:
            map_error(status_code=response.status_code, response=response, error_map=_ERROR_MAP)
            error = self._deserializer.failsafe_deserialize(AppConfigError, response)
            raise HttpResponseError(response=response, model=error)

        return Snapshot.from_json(json.loads(response.text()))

    def list_snapshot_kv(
            self,
            name,
            fields=None,
            **kwargs):

        _headers = kwargs.pop("headers", {}) or {}

        _params = {}

        if fields is not None:
            _params["$Select"] = Serializer().query("select", fields, "[str]", div=",")

        initial_request = build_list_snapshot_kvs_request(
            name,
            select=fields,
            sync_token=self._sync_token,
            headers=_headers
        )

        # Returns an iterable that converts returned items to Configuration Settings
        def _to_configurationsetting_iter(kv_items=None):
            if kv_items is None:
                return None

            for kv_dict in kv_items:
                if kv_dict is None:
                    yield None

                yield ConfigurationSetting(
                    key=kv_dict.get("key", None),
                    label=kv_dict.get("label", None),
                    content_type=kv_dict.get("content_type", None),
                    value=kv_dict.get("value", None),
                    last_modified=kv_dict.get("last_modified", None),
                    tags=kv_dict.get("tags", None),
                    read_only=kv_dict.get("locked", None),
                    etag=kv_dict.get("etag", None))

        def extract_kv_data(response):
            response_data_dict = json.loads(response.text())
            return response_data_dict.pop("@nextLink", None), _to_configurationsetting_iter(response_data_dict.pop("items", None))

        return self._fetch_paged(initial_request, extract_kv_data, **kwargs)

    def _fetch_paged(self, initial_request, data_extraction_method, **kwargs):
        '''
        Returns an "ItemPaged" object that takes two methods.
        One method to fetch the next page data, and another method to extract the next page link and output page data.
        '''

        def build_next_page_data_request(next_page_link=None):
            if not next_page_link:
                return initial_request

            return _build_request(
                next_page_link,
                RequestMethod.GET,
                sync_token=self._sync_token,
                **kwargs)

        # Fetch next page data
        def get_next_page_data(next_page_link=None):
            request = build_next_page_data_request(next_page_link)

            serialized_endpoint = self._serializer.url(
                "endpoint", self._endpoint, 'str', skip_quote=True)
            request.url = serialized_endpoint + request.url

            response = self._client.send_request(request)

            if response.status_code not in [200]:
                map_error(status_code=response.status_code, response=response, error_map=_ERROR_MAP)
                error = self._deserializer.failsafe_deserialize(AppConfigError, response)
                raise HttpResponseError(response=response, model=error)

            return response

        return ItemPaged(get_next_page_data, data_extraction_method)
