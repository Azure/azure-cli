from azure.appconfiguration import AzureAppConfigurationClient
from azure.appconfiguration._generated.models import Error as AppConfigError
from enum import Enum
from azure.core.rest import HttpRequest
from azure.core.utils import case_insensitive_dict
from azure.core.exceptions import ClientAuthenticationError, ResourceExistsError, ResourceNotFoundError, HttpResponseError, ResourceModifiedError, map_error
from msrest import Serializer
from typing import Dict, List, Optional, Any
import json

from ._snapshotmodels import Snapshot, SnapshotListResult

class ProvisioningStatus(Enum):
    PROVISIONING = "provisioning"
    READY = "ready"
    ARCHIVED = "archived"
    FAILED = "failed"

class RequestMethod(Enum):
    GET = "GET"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


_ERROR_MAP = {
            401: ClientAuthenticationError,
            404: ResourceNotFoundError,
            409: ResourceExistsError,
            412: ResourceModifiedError
        }


def _build_request(
    template_url_default: str,
    method: str,
    *,
    path_arguments: dict[str] = {},
    if_match: Optional[str] = None,
    if_none_match: Optional[str] = None,
    sync_token: Optional[str] = None,
    **kwargs: Any
) -> HttpRequest:
    _headers = case_insensitive_dict(kwargs.pop("headers", {}) or {})
    _params = case_insensitive_dict(kwargs.pop("params", {}) or {})

    api_version = kwargs.pop("api_version", "2022-11-01-preview")  # type: str
    accept = _headers.pop(
        "Accept", "application/vnd.microsoft.appconfig.keyset+json, application/json, application/problem+json"
    )

     # Construct URL
    _url = kwargs.pop("template_url", template_url_default)
    _url = _format_url_section(_url, **path_arguments)

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
    name: str,
    if_match: Optional[str] = None,
    if_none_match: Optional[str] = None,
    sync_token: Optional[str] = None,
    **kwargs: Any
) -> HttpRequest:
    return _build_request(
        "/snapshots/{name}",
        RequestMethod.GET.value,
        path_arguments={"name": name},
        if_match=if_match,
        if_none_match=if_none_match,
        sync_token=sync_token,
        **kwargs
    )


def build_list_snapshots_request(
    name_filter = None,
    status_filter = None,
    sync_token: Optional[str] = None,
    **kwargs: Any
) -> HttpRequest:
    _params = {}
    
    if name_filter:
        _params['name'] = name_filter

    if status_filter:
        _params['status'] = status_filter
    
    return _build_request(
        "/snapshots",
        RequestMethod.GET.value,
        sync_token=sync_token,
        params=_params,
        **kwargs
    )


def build_status_update_request(
    name: str,
    archive_snapshot: bool,
    if_match: Optional[str] = None,
    if_none_match: Optional[str] = None,
    sync_token: Optional[str] = None,
    **kwargs: Any
) -> HttpRequest:
    request_body = { "status" : "archived" if archive_snapshot else "ready" }

    return _build_request(
        "/snapshots/{name}",
        RequestMethod.PATCH.value,
        path_arguments={"name": name},
        json=request_body,
        if_match=if_match,
        if_none_match=if_none_match,
        sync_token=sync_token,
        **kwargs
    )


def build_put_snapshot_request(
    name: str,
    filters: List[Dict[str, str]],
    composition_type: str,
    retention_period: int=None,
    tags: Dict[str, str]=None,
    if_match: Optional[str] = None,
    if_none_match: Optional[str] = None,
    sync_token: Optional[str] = None,
    **kwargs: Any
) -> HttpRequest:

    request_body = {}

    if not filters or len(filters) < 1:
        raise ValueError("There should be at least one filter specified.")

    request_body["filters"] = filters

    if composition_type:
        if composition_type not in ("all", "group_by_key"):
            raise ValueError("Value should either be 'all' or 'group_by_key'.")

        request_body["composition_type"] = composition_type

    if retention_period != None:
        if not isinstance(retention_period, int) or retention_period < 0:
            raise ValueError("Retention period value should be a non-negative integer value.")

        request_body["retention_period"] = retention_period

    if tags:
        request_body["tags"] = tags

    return _build_request(
        "/snapshots/{name}",
        RequestMethod.PUT.value,
        path_arguments={"name": name},
        json=request_body,
        if_match=if_match,
        if_none_match=if_none_match,
        sync_token=sync_token,
        **kwargs
    )

def _convert_request(request, files=None):
    data = request.content if not files else None
    request = HttpRequest(method=request.method, url=request.url, headers=request.headers, data=data)
    if files:
        request.set_formdata_body(files)
    return request


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
        self.appConfigurationImpl = appConfigClient._impl
        self._serializer = self.appConfigurationImpl._serialize
        self._deserializer = self.appConfigurationImpl._deserialize
        self._sync_token = self.appConfigurationImpl._config.sync_token


    @classmethod
    def from_connection_string(cls, connection_string):
        return cls(AzureAppConfigurationClient.from_connection_string(connection_string))


    def begin_create_snapshot(self,
                              name: str,
                              filters: List[Dict[str, str]],
                              composition_type: str = None,
                              retention_period: int = None,
                              tags: Dict[str, str] = None,
                              if_match: Optional[str] = None,
                              if_none_match: Optional[str] = None,
                              **kwargs: Any):
        """
        Poll after a given interval (default 5s) to ensure that the snapshot is in 'ready' status. 
        The request times out after 30s by default unless specified otherwise.
        """
        timeout = kwargs.pop("timeout", 30)
        polling_interval = kwargs.pop("polling_interval", 5)

        from datetime import datetime

        def _get_elapsed_time(start_time: datetime):
            return (datetime.now() - start_time).total_seconds()

        print("Starting...")
        current_state = self.create_snapshot(
            name,
            filters,
            composition_type,
            retention_period,
            tags,
            if_match=if_match,
            if_none_match=if_none_match,
            **kwargs
        )

        print("Provisioning...")

        import time
        start_time = datetime.now()
        while current_state.status == ProvisioningStatus.PROVISIONING.value:
            if _get_elapsed_time(start_time) > timeout:
                raise TimeoutError("The create request timed out.")
            
            time.sleep(polling_interval)
            current_state = self.get_snapshot(name)

        if current_state.status == ProvisioningStatus.READY.value:
            return current_state

        raise HttpResponseError('Snapshot creation failed with status code: {}'.format(current_state.status_code))


    def create_snapshot(self,
                        name: str,
                        filters: List[Dict[str, str]],
                        composition_type: str=None,
                        retention_period: int=None,
                        tags: Dict[str, str]=None,
                        if_match: Optional[str] = None,
                        if_none_match: Optional[str] = None,
                        **kwargs: Any):
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

        request = _convert_request(request)

        serialized_endpoint = self._serializer.url("endpoint", self.appConfigurationImpl._config.endpoint, 'str', skip_quote=True)
        request.url = serialized_endpoint + request.url

        response = self.appConfigurationImpl._client.send_request(request)

        if response.status_code not in [201]:
            map_error(status_code=response.status_code,
                      response=response, error_map=_ERROR_MAP)
            error = self._deserializer.failsafe_deserialize(AppConfigError, response)
            raise HttpResponseError(response=response, model=error)

        return Snapshot.from_json(json.loads(response.body().decode()))


    def get_snapshot(self,
                     name: str,
                     if_match: Optional[str] = None,
                     if_none_match: Optional[str] = None,
                     **kwargs: Any):

        _headers = kwargs.pop("headers", {}) or {}

        request = build_get_snapshot_request(
            name=name,
            if_match=if_match,
            if_none_match=if_none_match,
            sync_token=self._sync_token,
            headers=_headers
        )

        request = _convert_request(request)

        serialized_endpoint = self._serializer.url("endpoint", self.appConfigurationImpl._config.endpoint, 'str', skip_quote=True)
        request.url = serialized_endpoint + request.url

        response = self.appConfigurationImpl._client.send_request(request)

        if response.status_code not in [200]:
            map_error(status_code=response.status_code, response=response, error_map=_ERROR_MAP)
            error = self._deserializer.failsafe_deserialize(AppConfigError, response)
            raise HttpResponseError(response=response, model=error)

        return Snapshot.from_json(json.loads(response.body().decode()))
            


    def list_snapshots(self,
                       name=None,
                       status=None,
                       **kwargs: Any):

        _headers = kwargs.pop("headers", {}) or {}

        request = build_list_snapshots_request(
            name_filter=name,
            status_filter=status,
            sync_token=self._sync_token,
            headers=_headers
        )

        request = _convert_request(request)

        serialized_endpoint = self._serializer.url("endpoint", self.appConfigurationImpl._config.endpoint, 'str', skip_quote=True)
        request.url = serialized_endpoint + request.url

        response = self.appConfigurationImpl._client.send_request(request)

        if response.status_code not in [200]:
            map_error(status_code=response.status_code, response=response, error_map=_ERROR_MAP)
            error = self._deserializer.failsafe_deserialize(AppConfigError, response)
            raise HttpResponseError(response=response, model=error)

        return SnapshotListResult.from_json(json.loads(response.body().decode()))


    def archive_snapshot(self,
                         name: str,
                         if_match: Optional[str] = None,
                         if_none_match: Optional[str] = None,
                         **kwargs: Any):
        _headers = kwargs.pop("headers", {}) or {}

        request = build_status_update_request(
            name=name,
            archive_snapshot=True,
            if_match=if_match,
            if_none_match=if_none_match,
            sync_token=self._sync_token,
            headers=_headers
        )

        request = _convert_request(request)

        serialized_endpoint = self._serializer.url("endpoint", self.appConfigurationImpl._config.endpoint, 'str', skip_quote=True)
        request.url = serialized_endpoint + request.url

        response = self.appConfigurationImpl._client.send_request(request)

        if response.status_code not in [200]:
            map_error(status_code=response.status_code, response=response, error_map=_ERROR_MAP)
            error = self._deserializer.failsafe_deserialize(AppConfigError, response)
            raise HttpResponseError(response=response, model=error)

        return Snapshot.from_json(json.loads(response.body().decode()))


    def recover_snapshot(self,
                         name: str,
                         if_match: Optional[str] = None,
                         if_none_match: Optional[str] = None,
                         **kwargs: Any):
        _headers = kwargs.pop("headers", {}) or {}

        request = build_status_update_request(
            name=name,
            archive_snapshot=False,
            if_match=if_match,
            if_none_match=if_none_match,
            sync_token=self._sync_token,
            headers=_headers
        )

        request = _convert_request(request)

        serialized_endpoint = self._serializer.url("endpoint", self.appConfigurationImpl._config.endpoint, 'str', skip_quote=True)
        request.url = serialized_endpoint + request.url

        response =self.appConfigurationImpl._client.send_request(request)

        if response.status_code not in [200]:
            map_error(status_code=response.status_code, response=response, error_map=_ERROR_MAP)
            error = self._deserializer.failsafe_deserialize(AppConfigError, response)
            raise HttpResponseError(response=response, model=error)

        return Snapshot.from_json(json.loads(response.body().decode()))