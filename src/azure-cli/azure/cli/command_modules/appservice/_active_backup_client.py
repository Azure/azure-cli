# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import codecs
from contextlib import contextmanager
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import json
import math
import os
import sys
import tempfile
import time
from urllib.parse import parse_qsl, quote, unquote, urlencode, urljoin, urlsplit, urlunsplit
import uuid

import requests
from knack.log import get_logger

from azure.cli.core._profile import Profile
from azure.cli.core.azclierror import (AzureConnectionError, AzureInternalError, AzureResponseError, FileOperationError,
                                       InvalidArgumentValueError, ResourceNotFoundError, UnclassifiedUserFault)
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.core.sdk.policies import get_custom_hook_policy
from azure.cli.core.util import get_az_user_agent, get_error_type_by_status_code, should_disable_connection_verify


API_VERSION = '2026-08-01'
DEFAULT_TIMEOUT = 7200
_RUNNING = {'accepted', 'created', 'inprogress', 'running', 'waiting'}
_FAILED = {'failed', 'cancelled', 'canceled', 'timedout'}
logger = get_logger(__name__)


def segment(value):
    if not isinstance(value, str) or not value or value in ('.', '..') or any(
            char in value for char in ('/', '\\', '\r', '\n', '\x00')):
        raise InvalidArgumentValueError('Provide a non-empty resource name or identifier without path separators.')
    return quote(value, safe='')


def load_json(value, expected_type=dict):
    if expected_type is None and isinstance(value, (dict, list, int, float, bool)):
        return value
    if expected_type is not None and isinstance(value, expected_type):
        return value
    try:
        if isinstance(value, str) and value.startswith('@'):
            with open(value[1:], encoding='utf-8-sig') as handle:
                result = json.load(handle)
        else:
            result = json.loads(value)
    except OSError as ex:
        raise FileOperationError('Unable to read the JSON input file: {}.'.format(ex.strerror)) from ex
    except (TypeError, ValueError) as ex:
        raise InvalidArgumentValueError('Provide valid JSON or an @file containing JSON.') from ex
    if expected_type is not None and not isinstance(result, expected_type):
        raise InvalidArgumentValueError(
            'Expected a JSON {}.'.format('array' if expected_type is list else 'object'))
    return result


def _origin(url):
    parsed = urlsplit(url)
    try:
        return parsed.scheme.lower(), parsed.hostname, 443 if parsed.port is None else parsed.port
    except ValueError as ex:
        raise AzureResponseError('Invalid ARM request address.') from ex


def _service_error(response):
    try:
        payload = response.json()
    except ValueError:
        payload = {}
    detail = payload.get('error', payload.get('Error', payload)) if isinstance(payload, dict) else {}
    code = detail.get('code', detail.get('Code')) if isinstance(detail, dict) else None
    message = detail.get('message', detail.get('Message')) if isinstance(detail, dict) else None
    if isinstance(message, dict):
        message = message.get('value')
    message = message if isinstance(message, str) else 'The ARM request failed (HTTP {}).'.format(response.status_code)
    if code:
        message = '({}) {}'.format(code, message)
    request_id = response.headers.get('x-ms-request-id')
    if request_id:
        message += ' Request ID: {}.'.format(request_id)
    error_type = get_error_type_by_status_code(str(response.status_code))
    error = error_type(message)
    error.response = response
    return error


def _retry_delay(headers):
    retry = headers.get('Retry-After', '5')
    try:
        delay = float(retry)
    except ValueError:
        try:
            delay = (parsedate_to_datetime(retry) - datetime.now(timezone.utc)).total_seconds()
        except (TypeError, ValueError, OverflowError):
            delay = 5
    return max(delay, 0.1) if math.isfinite(delay) else 5


class ActiveBackupClient:
    """ARM-only transport for the silo APIs absent from the Web SDK."""

    def __init__(self, cli_ctx, resource_group_name, name, resource_type='sites', subscription=None):
        self.cli_ctx = cli_ctx
        self._resource_type = resource_type
        self._origin_fallback_warned = False
        self.subscription = subscription or get_subscription_id(cli_ctx)
        self.endpoint = cli_ctx.cloud.endpoints.resource_manager.rstrip('/') + '/'
        self.parent = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Web/{}/{}'.format(
            segment(self.subscription), segment(resource_group_name), resource_type, segment(name))

    def resource(self, silo=None):
        return self.parent + '/silos' + ('/' + segment(silo) if silo is not None else '')

    def operation_url(self, silo, operation_id):
        """Select the CRUD status response rather than the final-resource response."""
        return self.url(self.resource(silo) + '/operationresults/' + segment(operation_id),
                        {'azureAsyncOperation': 1})

    def url(self, path, query=None):
        try:
            url = urljoin(self.endpoint, path)
            parsed = urlsplit(url)
        except ValueError as ex:
            raise AzureResponseError('The service returned an invalid ARM address.') from ex
        if (parsed.scheme != 'https' or parsed.username or parsed.password or parsed.fragment or
                _origin(url) != _origin(self.endpoint)):
            raise AzureResponseError('The service returned an address outside the configured ARM endpoint.')
        parameters = list(parse_qsl(parsed.query, keep_blank_values=True))
        if not any(key.lower() == 'api-version' for key, _ in parameters):
            parameters.append(('api-version', API_VERSION))
        for key, value in (query or {}).items():
            values = value if isinstance(value, (list, tuple)) else [value]
            for item in values:
                if item is not None:
                    parameters.append((key, str(item).lower() if isinstance(item, bool) else str(item)))
        return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urlencode(parameters), ''))

    @contextmanager
    def _response(self, method, path, body=None, query=None, timeout=60, stream=False, content_type=None):
        url = self.url(path, query)
        token_type, token, _ = Profile(cli_ctx=self.cli_ctx).get_raw_token(
            resource=self.cli_ctx.cloud.endpoints.active_directory_resource_id,
            subscription=self.subscription)[0]
        headers = {
            'Authorization': '{} {}'.format(token_type, token),
            'User-Agent': get_az_user_agent(),
            'x-ms-client-request-id': str(uuid.uuid4()),
            'CommandName': self.cli_ctx.data.get('command', ''),
        }
        if body is not None:
            headers['Content-Type'] = content_type or 'application/json'
            if (not content_type or 'json' in content_type.lower()) and not isinstance(body, bytes):
                body = json.dumps(body)
        policy = get_custom_hook_policy(self.cli_ctx)
        if policy is not None:
            from azure.core.pipeline import PipelineContext, PipelineRequest
            from azure.core.pipeline.transport import HttpRequest
            policy_request = HttpRequest(method, url, headers=headers, data=body)
            policy.on_request(PipelineRequest(policy_request, PipelineContext(None)))
            headers = dict(policy_request.headers)
        # Do not log bodies or URLs: these operations can return secrets or accept SAS queries.
        try:
            with requests.Session() as session:
                with session.request(
                        method, url, data=body, headers=headers, stream=stream, allow_redirects=False,
                        timeout=(min(10, timeout), timeout),
                        verify=not should_disable_connection_verify()) as response:
                    if not 200 <= response.status_code < 300:
                        raise _service_error(response)
                    yield response
        except requests.RequestException as ex:
            raise AzureConnectionError(
                'The Active Backup ARM request could not complete ({}).'.format(type(ex).__name__),
                recommendation='Check network connectivity and the configured cloud/TLS settings.') from None

    def request(self, method, path, body=None, query=None, timeout=60, content_type=None):
        with self._response(method, path, body, query, timeout, content_type=content_type) as response:
            return response

    @staticmethod
    def decode(response):
        if response.status_code == 204 or not response.content:
            return None
        content_type = response.headers.get('Content-Type', '').lower()
        if 'json' in content_type:
            try:
                return response.json()
            except ValueError as ex:
                raise AzureResponseError('ARM returned an invalid JSON response.') from ex
        if 'octet-stream' in content_type or 'zip' in content_type:
            raise InvalidArgumentValueError('Use --file to save the binary response.')
        if content_type.startswith('text/') or 'xml' in content_type:
            return {'content': response.text}
        try:
            return response.json()
        except ValueError as ex:
            raise AzureResponseError('ARM returned an unsupported response content type. Use --file.') from ex

    def get_resource(self, path):
        try:
            return self.decode(self.request('GET', path))
        except ResourceNotFoundError:
            if (self._resource_type != 'sites' or
                    unquote(path).casefold() != unquote(self.resource('origin')).casefold()):
                raise
            matches = [
                resource for resource in self.list(self.resource())
                if isinstance(resource, dict) and isinstance(resource.get('id'), str) and
                unquote(resource['id']).casefold() == unquote(path).casefold()
            ]
            if not matches:
                raise
            if len(matches) != 1:
                raise AzureResponseError('ARM returned duplicate origin resources in the silo collection.')
            resource = matches[0]
            resource_type = resource.get('type')
            if (not isinstance(resource_type, str) or resource_type.casefold() != 'microsoft.web/sites/silos' or
                    not isinstance(resource.get('properties'), dict)):
                raise AzureResponseError('ARM returned an invalid origin resource in the silo collection.')
            if not self._origin_fallback_warned:
                logger.warning(
                    'Origin point GET returned HTTP 404; using the matching origin from the silo collection. '
                    'Stamp-derived IP fields may be absent.')
                self._origin_fallback_warned = True
            return resource

    def list(self, path, query=None):
        result = []
        visited = set()
        while path:
            address = self.url(path, query)
            if address in visited:
                raise AzureResponseError('ARM returned a repeated pagination link.')
            visited.add(address)
            payload = self.decode(self.request('GET', address))
            if isinstance(payload, list):
                result.extend(payload)
                break
            if not isinstance(payload, dict) or not isinstance(payload.get('value'), list):
                raise AzureResponseError('ARM did not return a resource collection.')
            result.extend(payload['value'])
            path = payload.get('nextLink')
            if path is not None and not isinstance(path, str):
                raise AzureResponseError('ARM returned an invalid pagination link.')
            query = None
        return result

    def operation(self, path, response=None):
        response = response if response is not None else self.request('GET', path)
        payload = self.decode(response)
        state = payload.get('status') if isinstance(payload, dict) else None
        if isinstance(state, str) and state.lower() in _FAILED:
            detail = payload.get('error') or {}
            if not isinstance(detail, dict):
                detail = {}
            raise AzureResponseError('({}) {}'.format(
                detail.get('code', state), detail.get('message', 'The Active Backup operation failed.')))
        if isinstance(state, str) and state.lower() in _RUNNING:
            state = 'InProgress'
        elif response.status_code == 202:
            state = 'InProgress'
        elif state and str(state).lower() != 'succeeded':
            raise AzureResponseError('ARM returned an unrecognized operation status: {}.'.format(state))
        else:
            state = 'Succeeded'
        result = {
            'operationId': urlsplit(path).path.rstrip('/').split('/')[-1],
            'operationUrl': self.url(path),
            'status': state,
        }
        if (isinstance(payload, dict) and isinstance(payload.get('id'), str) and payload['id'].strip() and
                not payload.get('status')):
            result['resource'] = payload
        return result

    def wait(self, path, timeout=DEFAULT_TIMEOUT, initial=None):
        if timeout <= 0:
            raise InvalidArgumentValueError('--timeout must be greater than zero.')
        deadline = time.monotonic() + timeout
        response = initial
        read_retries = 0
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise AzureResponseError(
                    'Timed out waiting for operation {}. The service operation was not cancelled.'.format(
                        urlsplit(path).path.rstrip('/').split('/')[-1]))
            if response is None:
                try:
                    response = self.request('GET', path, timeout=min(60, remaining))
                    read_retries = 0
                except (ResourceNotFoundError, AzureResponseError, AzureInternalError, UnclassifiedUserFault) as ex:
                    failed_response = getattr(ex, 'response', None)
                    status = getattr(failed_response, 'status_code', None)
                    known_pending = isinstance(ex, ResourceNotFoundError) and initial is not None
                    read_retries += 1
                    if (not known_pending and status not in (429, 500, 502, 503, 504)) or read_retries > 3:
                        raise
                    delay = _retry_delay(failed_response.headers if failed_response is not None else {})
                    time.sleep(min(delay, max(0, deadline - time.monotonic())))
                    continue
            operation = self.operation(path, response)
            if operation['status'] == 'Succeeded':
                return operation
            delay = _retry_delay(response.headers)
            time.sleep(min(max(delay, 0.1), max(0, deadline - time.monotonic())))
            response = None

    def mutate(self, method, path, body=None, no_wait=False, timeout=DEFAULT_TIMEOUT, query=None):
        if timeout <= 0:
            raise InvalidArgumentValueError('--timeout must be greater than zero.')
        response = self.request(method, path, body, query)
        if response.status_code != 202:
            return None if method == 'DELETE' else self.decode(response)
        location = response.headers.get('Azure-AsyncOperation') or response.headers.get('Location')
        if not location:
            raise AzureResponseError('ARM accepted the operation without returning a polling address.')
        location = self.url(location)
        if no_wait:
            return {
                'resourceId': path,
                'operationId': urlsplit(location).path.rstrip('/').split('/')[-1],
                'operationUrl': location,
                'status': 'Accepted',
            }
        operation = self.wait(location, timeout, initial=response)
        if method in ('PUT', 'PATCH'):
            return self.get_resource(path)
        if method == 'DELETE':
            return None
        return operation.get('resource')

    def consume(self, method, path, filename=None, overwrite=False, query=None, body=None,
                content_type=None, tail=False):
        if filename is not None and not filename:
            raise InvalidArgumentValueError('--file must be a non-empty destination path.')
        destination = os.path.abspath(filename) if filename else None
        temporary = None
        if destination and os.path.exists(destination) and not overwrite:
            raise FileOperationError('The destination exists. Use --overwrite to replace it.')
        try:
            with self._response(method, path, body, query, stream=True, content_type=content_type) as response:
                if destination:
                    descriptor, temporary = tempfile.mkstemp(dir=os.path.dirname(destination))
                    with os.fdopen(descriptor, 'wb') as handle:
                        for chunk in response.iter_content(chunk_size=65536):
                            handle.write(chunk)
                    if overwrite:
                        os.replace(temporary, destination)
                        temporary = None
                    else:
                        os.link(temporary, destination)
                    return {'file': destination}
                if not tail:
                    raise InvalidArgumentValueError('Provide --file for this download.')
                decoder = codecs.getincrementaldecoder('utf-8')(errors='replace')
                for chunk in response.iter_content(chunk_size=1024):
                    sys.stdout.write(decoder.decode(chunk))
                    sys.stdout.flush()
                sys.stdout.write(decoder.decode(b'', final=True))
                sys.stdout.flush()
                return None
        except OSError as ex:
            raise FileOperationError('Unable to save the response: {}.'.format(ex.strerror)) from ex
        finally:
            if temporary is not None:
                os.unlink(temporary)
