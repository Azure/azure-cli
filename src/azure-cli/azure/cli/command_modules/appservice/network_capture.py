# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import time
import uuid

from knack.log import get_logger

from azure.cli.core.azclierror import (AzureConnectionError, AzureResponseError, CLIInternalError,
                                       ResourceNotFoundError, ValidationError)

from ._appservice_utils import _generic_site_operation
from .custom import _get_scm_url, get_scm_site_headers
from .utils import is_linux_webapp
from .webapp_exec import _resolve_target_instances

logger = get_logger(__name__)

_CAPTURE_API = '/api/networkcapture'
_TERMINAL_STATES = {'ready', 'captured', 'nopackets', 'failed'}
_DEFAULT_OPERATION_TIMEOUT = 10 * 60


# pylint: disable=too-many-locals
def collect_network_capture(cmd, resource_group_name, name, slot=None, instance=None, duration=None,
                            interface=None, snap_length=None, capture_filter=None,
                            artifact='both', destination='.'):
    webapp = _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'get', slot)
    if not webapp:
        raise ResourceNotFoundError(
            "Unable to find web app '{}' in resource group '{}'.".format(name, resource_group_name))
    if not is_linux_webapp(webapp):
        raise ValidationError(
            "Network capture is only supported for Linux web apps on dedicated App Service plans.")

    _validate_capture_options(duration, snap_length, artifact, destination)
    target = _resolve_single_instance(cmd, resource_group_name, name, instance, slot)

    scm_url = _get_scm_url(cmd, resource_group_name, name, slot).rstrip('/')
    headers = get_scm_site_headers(cmd.cli_ctx, name, resource_group_name, slot)
    session = _create_http_session(headers, target)

    config = _request_json(session, 'GET', scm_url + _CAPTURE_API + '/config')
    auto_analysis_enabled = bool(_value(config, 'autoAnalysisEnabled', 'AutoAnalysisEnabled', default=True))

    body = {key: value for key, value in {
        'iface': interface,
        'duration': duration,
        'snaplen': snap_length,
        'filter': capture_filter,
    }.items() if value is not None}

    logger.warning("Starting network capture on web app '%s'...", name)
    capture = _request_json(session, 'POST', scm_url + _CAPTURE_API + '/captures', json=body)
    session_id = _required_value(capture, 'sessionId', 'SessionId')
    capture_command = _required_value(capture, 'captureCommand', 'CaptureCommand')

    interrupted = _run_capture_command(scm_url, headers, session.cookies.get_dict(), capture_command,
                                       duration or 300)
    if interrupted:
        logger.warning('Capture interrupted. Finalizing packets collected so far...')
    else:
        logger.warning('Packet collection finished. Finalizing capture...')

    analyze_url = '{}/captures/{}/analyze'.format(scm_url + _CAPTURE_API, session_id)
    try:
        capture = _request_json(session, 'POST', analyze_url)
    except AzureResponseError as ex:
        if artifact == 'report':
            raise
        logger.warning('Capture analysis could not be started. The raw packet capture will still be downloaded.')
        logger.debug('Network capture analysis request failed: %s', ex)

    status_url = '{}/captures/{}'.format(scm_url + _CAPTURE_API, session_id)
    capture = _wait_for_terminal_state(session, status_url, capture, _DEFAULT_OPERATION_TIMEOUT)
    status = str(_required_value(capture, 'status', 'Status'))
    normalized_status = status.lower()

    if normalized_status == 'failed' and artifact == 'report':
        raise AzureResponseError(_capture_failure_message(capture))

    destination = os.path.abspath(os.path.expanduser(destination))
    os.makedirs(destination, exist_ok=True)
    file_stem = '{}_{}'.format(_safe_filename(name), _safe_filename(str(session_id)))
    pcap_path = None
    report_path = None

    if artifact in ('pcap', 'both'):
        pcap_path = os.path.join(destination, file_stem + '.pcap')
        _download_artifact(session, '{}/download'.format(status_url), pcap_path)
        logger.warning('Downloaded packet capture to %s', pcap_path)

    if artifact in ('report', 'both'):
        if normalized_status == 'ready':
            report_path = os.path.join(destination, file_stem + '.pcap.html')
            _download_artifact(session, '{}/report'.format(status_url), report_path)
            logger.warning('Downloaded network capture report to %s', report_path)
        elif not auto_analysis_enabled or normalized_status == 'captured':
            if artifact == 'report':
                raise AzureResponseError(
                    'Network capture analysis is disabled for this app. Request the pcap artifact instead.')
            logger.warning('Network capture analysis is disabled; only the raw packet capture was downloaded.')
        elif normalized_status == 'nopackets':
            logger.warning('The capture completed successfully but did not contain any packets.')
        elif normalized_status == 'failed':
            logger.warning('%s The raw packet capture was preserved.', _capture_failure_message(capture))

    return {
        'sessionId': session_id,
        'instance': target,
        'status': status,
        'truncated': bool(_value(capture, 'truncated', 'Truncated', default=False)),
        'packetCapture': pcap_path,
        'report': report_path,
    }
# pylint: enable=too-many-locals


def _validate_capture_options(duration, snap_length, artifact, destination):
    if duration is not None and not 1 <= duration <= 300:
        raise ValidationError('--duration must be between 1 and 300 seconds.')
    if snap_length is not None and snap_length != 0 and not 64 <= snap_length <= 65535:
        raise ValidationError('--snap-length must be 0, or between 64 and 65535 bytes.')
    if artifact not in ('pcap', 'report', 'both'):
        raise ValidationError("--artifact must be one of 'pcap', 'report', or 'both'.")
    if not destination or not destination.strip():
        raise ValidationError('--destination must not be empty.')


def _resolve_single_instance(cmd, resource_group_name, name, instance, slot):
    if instance and (instance.strip().lower() == 'all' or ',' in instance):
        raise ValidationError('Network capture supports one web app instance at a time.')
    return _resolve_target_instances(cmd, resource_group_name, name, instance, slot)[0]


def _create_http_session(headers, instance):
    import requests
    from azure.cli.core.util import should_disable_connection_verify

    session = requests.Session()
    session.headers.update(headers)
    session.verify = not should_disable_connection_verify()
    if instance:
        session.cookies.set('ARRAffinity', instance)
    return session


def _request_json(session, method, url, **kwargs):
    import requests

    try:
        response = session.request(method, url, timeout=(30, 330), **kwargs)
    except requests.exceptions.RequestException as ex:
        raise AzureConnectionError('Could not connect to the web app diagnostics service: {}'.format(ex))

    if response.status_code < 200 or response.status_code >= 300:
        detail = _response_message(response)
        if response.status_code == 404:
            detail = ('Network capture is unavailable. Verify that the app is a supported Linux web app and '
                      'that the Kudu network diagnostics feature is enabled. ' + detail)
        elif response.status_code == 429:
            detail = 'The concurrent network capture limit has been reached. ' + detail
        raise AzureResponseError(detail.strip())

    if not response.content:
        return {}
    try:
        payload = response.json()
    except ValueError as ex:
        raise AzureResponseError('The web app diagnostics service returned an invalid JSON response.') from ex
    if not isinstance(payload, dict):
        raise AzureResponseError('The web app diagnostics service returned an unexpected response.')
    return payload


def _run_capture_command(scm_url, headers, cookies, capture_command, duration):
    import ssl
    import websocket
    from azure.cli.core.util import should_disable_connection_verify

    ws_url = scm_url.replace('https://', 'wss://', 1).replace('http://', 'ws://', 1) + '/exec/shell'
    cookie = '; '.join('{}={}'.format(key, value) for key, value in cookies.items()) or None
    verify_mode = ssl.CERT_NONE if should_disable_connection_verify() else ssl.CERT_REQUIRED
    try:
        ws = websocket.create_connection(
            ws_url, header=headers, cookie=cookie, sslopt={'cert_reqs': verify_mode}, timeout=30,
            enable_multithread=True)
        ws.settimeout(duration + 90)
        ws.send_binary((capture_command + '\nexit\n').encode('utf-8'))
        interrupted = False
        while True:
            try:
                message = ws.recv()
                if message in (None, b'', ''):
                    break
            except websocket.WebSocketConnectionClosedException:
                logger.debug('Network capture shell closed after the capture command was submitted.')
                break
            except KeyboardInterrupt:
                if interrupted:
                    raise
                interrupted = True
                ws.send_binary(b'\x03')
    except websocket.WebSocketBadStatusException as ex:
        raise CLIInternalError('The app container rejected the network capture session: {}'.format(
            getattr(ex, 'resp_body', None) or ex))
    except websocket.WebSocketTimeoutException as ex:
        raise AzureConnectionError('Timed out waiting for the network capture command to finish.') from ex
    except (OSError, websocket.WebSocketException) as ex:
        raise AzureConnectionError('The app container network capture session was interrupted: {}'.format(ex))
    finally:
        if 'ws' in locals():
            try:
                ws.close()
            except Exception:  # pylint: disable=broad-except
                pass
    return interrupted


def _wait_for_terminal_state(session, status_url, capture, timeout):
    deadline = time.monotonic() + timeout
    while True:
        status = str(_value(capture, 'status', 'Status', default='')).lower()
        if status in _TERMINAL_STATES:
            return capture
        if time.monotonic() >= deadline:
            raise AzureResponseError('Timed out waiting for network capture processing to finish.')
        time.sleep(2)
        capture = _request_json(session, 'GET', status_url)


def _download_artifact(session, url, destination):
    import requests

    if os.path.exists(destination):
        raise ValidationError("The destination file already exists: '{}'".format(destination))
    temporary_path = destination + '.{}.part'.format(uuid.uuid4().hex)
    try:
        try:
            response = session.get(url, timeout=(30, 330), stream=True)
        except requests.exceptions.RequestException as ex:
            raise AzureConnectionError('Could not download the network capture artifact: {}'.format(ex))
        if response.status_code < 200 or response.status_code >= 300:
            raise AzureResponseError(_response_message(response))
        with open(temporary_path, 'xb') as artifact_file:
            for chunk in response.iter_content(chunk_size=64 * 1024):
                if chunk:
                    artifact_file.write(chunk)
        if os.path.exists(destination):
            raise ValidationError("The destination file already exists: '{}'".format(destination))
        os.replace(temporary_path, destination)
    finally:
        if os.path.exists(temporary_path):
            os.remove(temporary_path)


def _response_message(response):
    try:
        payload = response.json()
        if isinstance(payload, dict):
            message = _value(payload, 'message', 'Message', 'error', 'Error')
            if message:
                return str(message)
    except ValueError:
        pass
    text = (getattr(response, 'text', '') or '').strip()
    return text or 'Request failed with HTTP status {}.'.format(response.status_code)


def _capture_failure_message(capture):
    detail = _value(capture, 'error', 'Error', 'message', 'Message')
    return 'Network capture processing failed{}.'.format(': ' + str(detail) if detail else '')


def _required_value(payload, *names):
    value = _value(payload, *names)
    if value is None or value == '':
        raise AzureResponseError(
            "The web app diagnostics service response did not contain '{}'.".format(names[0]))
    return value


def _value(payload, *names, default=None):
    for name in names:
        if name in payload:
            return payload[name]
    return default


def _safe_filename(value):
    return ''.join(character if character.isalnum() or character in ('-', '_') else '_'
                   for character in value)
