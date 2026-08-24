# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import time

from knack.log import get_logger
from knack.prompting import NoTTYException, prompt_choice_list

from azure.cli.core.azclierror import (AzureConnectionError, AzureResponseError, CLIInternalError,
                                       ResourceNotFoundError, ValidationError)

from ._appservice_utils import _generic_site_operation
from .custom import _get_scm_url, get_scm_site_headers
from .utils import is_linux_webapp
from .webapp_exec import _resolve_target_instances

logger = get_logger(__name__)

_CAPTURE_API = '/api/networkcapture'
_TERMINAL_STATES = {'ready', 'nopackets', 'failed'}
_DEFAULT_OPERATION_TIMEOUT = 10 * 60
_PROGRESS_PHASES = ('prepare', 'capture', 'process', 'complete')


def collect_network_capture(cmd, resource_group_name, name, slot=None, instance=None, duration=60,
                            collect_only=False):
    webapp = _generic_site_operation(
        cmd.cli_ctx, resource_group_name, name, 'get', slot)
    if not webapp:
        raise ResourceNotFoundError(
            "Unable to find web app '{}' in resource group '{}'.".format(name, resource_group_name))
    if not is_linux_webapp(webapp):
        raise ValidationError(
            "Network capture is only supported for Linux web apps on dedicated App Service plans.")

    _validate_capture_options(duration)
    _log_capture_advisory()
    target = _select_target_instance(
        cmd, resource_group_name, name, instance, slot)

    scm_url = _get_scm_url(cmd, resource_group_name, name, slot).rstrip('/')
    headers = get_scm_site_headers(
        cmd.cli_ctx, name, resource_group_name, slot)
    session = _create_http_session(headers, target)

    logger.warning('')
    _log_progress('prepare', 'Preparing network capture...')
    body = {'durationSeconds': duration}

    _log_progress(
        'capture', "Capturing network traffic on web app '%s'...", name)
    capture = _request_json(session, 'POST', scm_url +
                            _CAPTURE_API + '/captures', json=body)
    session_id = _required_value(capture, 'id', 'Id', 'sessionId', 'SessionId')
    capture_command = _required_value(
        capture, 'captureCommand', 'CaptureCommand')

    interrupted = _run_capture_command(scm_url, headers, session.cookies.get_dict(), capture_command,
                                       duration)
    status_url = '{}/captures/{}'.format(scm_url + _CAPTURE_API, session_id)
    message = ('Capture interrupted. Analyzing packets collected so far...' if interrupted else
               'Packet collection finished. Analyzing capture...')
    _log_progress('process', message)
    capture = _request_json(session, 'POST', status_url + '/analyze')

    capture = _wait_for_terminal_state(
        session, status_url, capture, _DEFAULT_OPERATION_TIMEOUT)
    status = str(_required_value(capture, 'status', 'Status'))
    normalized_status = status.lower()

    if normalized_status == 'failed':
        raise AzureResponseError(_capture_failure_message(capture))

    _log_progress('complete', 'Network capture collected successfully.')

    download_url = _value(capture, 'downloadUrl', 'DownloadUrl')
    report_url = _value(capture, 'reportUrl', 'ReportUrl')
    result = {
        'captureId': session_id,
        'instance': target,
        'status': status,
        'truncated': bool(_value(capture, 'truncated', 'Truncated', default=False)),
        'packetCaptureUrl': _with_instance(scm_url + download_url, target) if download_url else None,
        'reportUrl': _with_instance(scm_url + report_url, target) if report_url else None,
    }
    _render_capture_summary(result, collect_only)


def _log_progress(phase, message, *args):
    step = _PROGRESS_PHASES.index(phase) + 1
    logger.warning('[%d/%d] ' + message, step, len(_PROGRESS_PHASES), *args)


def _render_capture_summary(result, collect_only):
    status = result['status']
    if str(status).lower() == 'nopackets':
        instance = result['instance'][:6]
        print('\n\nNo packets were captured during the capture window.\n\n'
              'This could happen when the app running on instance ({}) was not receiving traffic or making any '
              'outbound calls.\n\n'
              'Please generate a repro and capture again.'.format(instance))
        return

    capture_id = result['captureId']
    lines = []
    lines.append('Capture ID: {}'.format(capture_id))
    if result['packetCaptureUrl']:
        lines.append('Download raw packet capture: {}'.format(result['packetCaptureUrl']))
    if result['reportUrl'] and not collect_only:
        lines.append('View analysis report: {}'.format(result['reportUrl']))
    lines.append('For deeper investigation, manually download the trace and analyze it in '
                 'Microsoft Network Monitor or Wireshark.')
    lines.append('Kudu access is required to open these links.')
    print('\n\n' + '\n\n'.join(lines))


def _validate_capture_options(duration):
    if duration is not None and not 1 <= duration <= 300:
        raise ValidationError('--duration must be between 1 and 300 seconds.')


def _with_instance(url, instance):
    from urllib.parse import urlencode

    separator = '&' if '?' in url else '?'
    return url + separator + urlencode({'instance': instance})


def _select_target_instance(cmd, resource_group_name, name, instance, slot):
    if instance:
        if instance.strip().lower() == 'all' or ',' in instance:
            raise ValidationError(
                'Network capture supports one web app instance at a time.')
        return _resolve_target_instances(cmd, resource_group_name, name, instance, slot)[0]

    instances = _resolve_target_instances(
        cmd, resource_group_name, name, 'all', slot)
    try:
        selected = prompt_choice_list(
            '\nSelect the instance where you will reproduce the issue:', instances)
    except NoTTYException as ex:
        raise ValidationError(
            'No interactive terminal is available. Specify --instance <instance-id>. '
            'Run "az webapp list-instances" to list current instances.') from ex
    return instances[selected]


def _log_capture_advisory():
    import sys

    logger.warning(
        'What you should know before collecting a network capture:\n'
        '  - Network traces help troubleshoot TCP packet loss and inspect HTTP communication between your app '
        'and remote endpoints.\n'
        '  - After the network trace starts, reproduce the problem so outbound traffic from your app is captured.\n'
        '  - Traffic to remote endpoints over TLS or SSL (for example, HTTPS) is encrypted in the trace.\n'
        '  - Network captures can contain credentials, cookies, request bodies, and other sensitive application '
        'data. Store and share capture artifacts securely.\n'
        '  - Network traces are collected on the selected instance serving your app.\n'
        '  - Capture duration is 60 seconds by default and can be set from 1 to 300 seconds.\n'
        '  - A network trace can capture up to 100 MB of data. The capture stops automatically at this limit, '
        'and only the 5 most recent captures are retained.\n'
        '  - For deeper analysis, use Microsoft Network Monitor '
        '(https://www.microsoft.com/en-in/download/details.aspx?id=4865) or Wireshark '
        '(https://www.wireshark.org/).')
    sys.stderr.flush()


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
        raise AzureConnectionError(
            'Could not connect to the web app diagnostics service: {}'.format(ex))

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
        raise AzureResponseError(
            'The web app diagnostics service returned an invalid JSON response.') from ex
    if not isinstance(payload, dict):
        raise AzureResponseError(
            'The web app diagnostics service returned an unexpected response.')
    return payload


def _run_capture_command(scm_url, headers, cookies, capture_command, duration):
    import ssl
    import websocket
    from azure.cli.core.util import should_disable_connection_verify

    ws_url = scm_url.replace('https://', 'wss://',
                             1).replace('http://', 'ws://', 1) + '/exec/shell'
    cookie = '; '.join('{}={}'.format(key, value)
                       for key, value in cookies.items()) or None
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
                logger.debug(
                    'Network capture shell closed after the capture command was submitted.')
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
        raise AzureConnectionError(
            'Timed out waiting for the network capture command to finish.') from ex
    except (OSError, websocket.WebSocketException) as ex:
        raise AzureConnectionError(
            'The app container network capture session was interrupted: {}'.format(ex))
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
        logger.debug("Network capture analysis status: '%s'.", status or 'unknown')
        if status in _TERMINAL_STATES:
            return capture
        if time.monotonic() >= deadline:
            raise AzureResponseError(
                'Timed out waiting for network capture processing to finish.')
        time.sleep(2)
        capture = _request_json(session, 'GET', status_url)


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
