# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import re
import shlex
import time
import uuid

from knack.log import get_logger
from knack.prompting import NoTTYException, prompt_choice_list

from azure.cli.core.azclierror import (AzureConnectionError, AzureResponseError, CLIInternalError,
                                       ResourceNotFoundError, ValidationError)

from ._appservice_utils import _generic_site_operation
from .custom import _get_scm_url, get_scm_site_headers
from .utils import is_linux_webapp
from .webapp_exec import _resolve_target_instances

logger = get_logger(__name__)

_DIAGNOSTICS = {
    'cpu': {
        'artifactExtension': '.cpuprofile',
        'defaultDuration': 30,
        'kuduPage': '/cpuprofiling',
        'reportScript': '/opt/Kudu/wwwroot/js/diagnostics/analyze-cpu.js',
        'resultType': 'cpuProfile',
    },
    'memory': {
        'artifactExtension': '.heapsnapshot',
        'defaultDuration': None,
        'kuduPage': '/memoryanalysis',
        'reportScript': '/opt/Kudu/wwwroot/js/diagnostics/analyze-heap.js',
        'resultType': 'memoryDump',
    },
}


def collect_cpu_profiler_trace(cmd, resource_group_name, name, slot=None, instance=None,
                               process_id=None, duration=30):
    return _collect_node_diagnostic(
        cmd, resource_group_name, name, 'cpu', slot, instance, process_id, duration)


def collect_memory_dump(cmd, resource_group_name, name, slot=None, instance=None, process_id=None):
    return _collect_node_diagnostic(
        cmd, resource_group_name, name, 'memory', slot, instance, process_id, None)


def _collect_node_diagnostic(cmd, resource_group_name, name, diagnostic_type, slot, instance,
                             process_id, duration):
    config = _DIAGNOSTICS[diagnostic_type]
    webapp = _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'get', slot)
    if not webapp:
        raise ResourceNotFoundError(
            "Unable to find web app '{}' in resource group '{}'.".format(name, resource_group_name))
    if not is_linux_webapp(webapp):
        raise ValidationError('Node diagnostics are only supported for Linux web apps.')
    if diagnostic_type == 'cpu' and (duration is None or not 5 <= duration <= 300):
        raise ValidationError('--duration must be between 5 and 300 seconds.')
    if process_id is not None and process_id <= 0:
        raise ValidationError('--process-id must be a positive integer.')

    target = _select_instance(cmd, resource_group_name, name, instance, slot)
    scm_url = _get_scm_url(cmd, resource_group_name, name, slot).rstrip('/')
    headers = get_scm_site_headers(cmd.cli_ctx, name, resource_group_name, slot)
    session = _create_http_session(headers, target)
    _ensure_diagnostics_available(session, scm_url, config['kuduPage'])

    logger.warning('Discovering Node.js processes on instance %s...', target)
    processes = _discover_node_processes(scm_url, headers, target)
    selected_process = _select_process(processes, process_id)

    base_name = _build_capture_name(diagnostic_type, target)
    base_dir = '/home/LogFiles/diagnostics/{}'.format(diagnostic_type)
    artifact_path = base_dir + '/' + base_name + config['artifactExtension']
    report_path = base_dir + '/' + base_name + '_report.html'
    operation_timeout = (duration + 30) if diagnostic_type == 'cpu' else 120

    logger.warning(
        'Collecting Node.js %s from process %s. Diagnostic artifacts can contain sensitive application data.',
        'CPU profile' if diagnostic_type == 'cpu' else 'memory dump', selected_process['pid'])
    collection_command = _get_collection_command(
        session, scm_url, diagnostic_type, selected_process['pid'], duration,
        artifact_path, operation_timeout)
    _run_shell_command(
        scm_url, headers, target, collection_command, operation_timeout + 30)

    logger.warning('Analyzing the collected artifact in Kudu...')
    _run_analyzer(session, scm_url, config['reportScript'], artifact_path, report_path)

    return {
        'captureId': base_name,
        'diagnosticType': config['resultType'],
        'instance': target,
        'processId': selected_process['pid'],
        'status': 'ready',
        'artifactUrl': _vfs_url(scm_url, diagnostic_type, base_name + config['artifactExtension'], target),
        'reportUrl': _vfs_url(scm_url, diagnostic_type, base_name + '_report.html', target),
        'diagnosticsPageUrl': _with_instance(scm_url + config['kuduPage'], target),
    }


def _select_instance(cmd, resource_group_name, name, instance, slot):
    if instance:
        if instance.strip().lower() == 'all' or ',' in instance:
            raise ValidationError('Node diagnostics support one web app instance at a time.')
        return _resolve_target_instances(cmd, resource_group_name, name, instance.strip(), slot)[0]

    instances = _resolve_target_instances(cmd, resource_group_name, name, 'all', slot)
    if len(instances) == 1:
        return instances[0]
    try:
        selected = prompt_choice_list('Select the web app instance to diagnose:', instances)
    except NoTTYException as ex:
        raise ValidationError(
            'No interactive terminal is available. Specify --instance <instance-id>. '
            'Run "az webapp list-instances" to list current instances.') from ex
    return instances[selected]


def _discover_node_processes(scm_url, headers, instance):
    output = _run_shell_command(
        scm_url, headers, instance, 'ps -eo pid=,ppid=,comm=,args=', 30)
    return _parse_node_processes(output)


def _parse_node_processes(output):
    processes = []
    for line in output.splitlines():
        match = re.match(r'^\s*(\d+)\s+(\d+)\s+(\S+)\s+(.*)$', line.strip())
        if not match:
            continue
        process = {
            'pid': int(match.group(1)),
            'parentPid': int(match.group(2)),
            'command': match.group(3),
            'args': match.group(4).strip(),
        }
        if _is_node_process(process):
            processes.append(process)

    eligible = []
    for process in processes:
        if _is_shell_process(process['command']) and _has_descendant(process['pid'], processes):
            continue
        eligible.append(process)
    return eligible


def _is_node_process(process):
    command = process['command'].lower()
    args = process['args'].lower()
    return command == 'node' or command.endswith('/node') or bool(re.search(r'(^|[\s/])node(?:\s|$)', args))


def _is_shell_process(command):
    return bool(re.match(r'^(?:ba|da|a|z)?sh$', command, re.IGNORECASE))


def _has_descendant(parent_pid, processes):
    pending = [parent_pid]
    visited = set()
    while pending:
        current = pending.pop(0)
        if current in visited:
            continue
        visited.add(current)
        for process in processes:
            if process['parentPid'] != current:
                continue
            if process['pid'] != parent_pid:
                return True
            pending.append(process['pid'])
    return False


def _select_process(processes, process_id):
    if not processes:
        raise ValidationError('No eligible Node.js processes were found on the selected instance.')
    if process_id is not None:
        for process in processes:
            if process['pid'] == process_id:
                return process
        raise ValidationError(
            "Process ID '{}' is not an eligible Node.js process. Valid process IDs: {}.".format(
                process_id, ', '.join(str(process['pid']) for process in processes)))
    if len(processes) == 1:
        return processes[0]

    choices = ['{} (PID: {})'.format(process['args'] or process['command'], process['pid'])
               for process in processes]
    try:
        selected = prompt_choice_list('Select the Node.js process to diagnose:', choices)
    except NoTTYException as ex:
        raise ValidationError(
            'Multiple Node.js processes were found and no interactive terminal is available. '
            'Specify --process-id <process-id>.') from ex
    return processes[selected]


def _build_capture_name(diagnostic_type, instance):
    timestamp = time.strftime('%Y%m%d%H%M%S', time.gmtime())
    instance_token = re.sub(r'[^a-zA-Z0-9]', '', instance)[:12] or 'unknown'
    return '{}_{}_{}_{}'.format(diagnostic_type, instance_token, timestamp, uuid.uuid4().hex[:8])


def _get_collection_command(session, scm_url, diagnostic_type, process_id, duration,
                            artifact_path, timeout_seconds):
    arguments = [str(process_id)]
    if diagnostic_type == 'cpu':
        arguments.append(str(duration))
    arguments.append(json.dumps(artifact_path))
    invocation = 'DiagnosticStacks.node.{}.collectCmd({})'.format(diagnostic_type, ','.join(arguments))
    script = (
        "const fs=require('fs'),vm=require('vm');"
        "vm.runInThisContext(fs.readFileSync('/opt/Kudu/wwwroot/js/diagnostics/stacks.js','utf8'));"
        "vm.runInThisContext(fs.readFileSync('/opt/Kudu/wwwroot/js/diagnostics/analyzers.js','utf8'));"
        'const command={};'.format(invocation) +
        'process.stdout.write(wrapNodeDiagnosticCollectionCommand(command,{}));'.format(timeout_seconds)
    )
    result = _run_kudu_command(session, scm_url, 'node -e {}'.format(shlex.quote(script)), timeout=30)
    command = result.strip()
    if not command:
        raise AzureResponseError('Kudu did not return a Node.js diagnostic collection command.')
    return command


def _run_analyzer(session, scm_url, script_path, artifact_path, report_path):
    command = 'timeout --signal=TERM --kill-after=5s 115s node {} {} {} 2>&1'.format(
        shlex.quote(script_path), shlex.quote(artifact_path), shlex.quote(report_path))
    _run_kudu_command(session, scm_url, command, timeout=150)


def _run_kudu_command(session, scm_url, command, timeout):
    import requests

    try:
        response = session.post(
            scm_url + '/api/command', json={'command': command, 'dir': '/'}, timeout=(30, timeout))
    except requests.exceptions.RequestException as ex:
        raise AzureConnectionError('Could not connect to the Kudu diagnostics service: {}'.format(ex)) from ex
    if not 200 <= response.status_code < 300:
        raise AzureResponseError(
            'Kudu diagnostics command failed with HTTP status {}: {}'.format(
                response.status_code, (response.text or '').strip()))
    try:
        payload = response.json()
    except ValueError as ex:
        raise AzureResponseError('Kudu returned an invalid diagnostics command response.') from ex
    exit_code = payload.get('ExitCode', payload.get('exitCode'))
    output = payload.get('Output', payload.get('output', '')) or ''
    error = payload.get('Error', payload.get('error', '')) or ''
    if exit_code != 0:
        detail = error.strip() or output.strip() or 'No error details were returned.'
        raise AzureResponseError('Kudu diagnostics command failed: {}'.format(detail))
    return output


def _run_shell_command(scm_url, headers, instance, command, timeout):
    import ssl
    import websocket
    from azure.cli.core.util import should_disable_connection_verify

    marker = '__AZ_CLI_DIAGNOSTIC_{}__'.format(uuid.uuid4().hex)
    wrapped = '{}; __az_diag_exit=$?; printf "\\n{}:%s\\n" "$__az_diag_exit"'.format(command, marker)
    ws_url = scm_url.replace('https://', 'wss://', 1).replace('http://', 'ws://', 1) + '/exec/shell'
    cookie = 'ARRAffinity={}'.format(instance)
    verify_mode = ssl.CERT_NONE if should_disable_connection_verify() else ssl.CERT_REQUIRED
    chunks = []
    try:
        ws = websocket.create_connection(
            ws_url, header=headers, cookie=cookie, sslopt={'cert_reqs': verify_mode},
            timeout=30, enable_multithread=True)
        ws.settimeout(timeout)
        ws.send_binary((wrapped + '\nexit\n').encode('utf-8'))
        while True:
            message = ws.recv()
            if message in (None, b'', ''):
                break
            chunks.append(message.decode('utf-8', 'replace') if isinstance(message, bytes) else message)
            output = ''.join(chunks).replace('\r', '')
            match = re.search(r'(?:^|\n){}:(\d+)(?:\n|$)'.format(re.escape(marker)), output)
            if match:
                if int(match.group(1)) != 0:
                    raise AzureResponseError(
                        'Node.js diagnostic command failed: {}'.format(_shell_error_detail(output, marker)))
                return output[:match.start()].strip()
    except websocket.WebSocketBadStatusException as ex:
        raise CLIInternalError(
            'The app container rejected the Node.js diagnostic session: {}'.format(
                getattr(ex, 'resp_body', None) or ex)) from ex
    except websocket.WebSocketTimeoutException as ex:
        raise AzureConnectionError('Timed out waiting for the Node.js diagnostic command to finish.') from ex
    except (OSError, websocket.WebSocketException) as ex:
        raise AzureConnectionError('The Node.js diagnostic session was interrupted: {}'.format(ex)) from ex
    finally:
        if 'ws' in locals():
            try:
                ws.close()
            except Exception:  # pylint: disable=broad-except
                pass
    raise AzureResponseError('The Node.js diagnostic command ended without returning an exit status.')


def _shell_error_detail(output, marker):
    lines = [line.strip() for line in output.replace('\r', '').splitlines()
             if line.strip() and marker not in line]
    return '\n'.join(lines[-10:]) or 'No error details were returned.'


def _create_http_session(headers, instance):
    import requests
    from azure.cli.core.util import should_disable_connection_verify

    session = requests.Session()
    session.headers.update(headers)
    session.verify = not should_disable_connection_verify()
    session.cookies.set('ARRAffinity', instance)
    return session


def _ensure_diagnostics_available(session, scm_url, page):
    import requests

    try:
        response = session.get(scm_url + page, timeout=(30, 30))
    except requests.exceptions.RequestException as ex:
        raise AzureConnectionError('Could not connect to the Kudu diagnostics page: {}'.format(ex)) from ex
    if response.status_code == 404:
        raise ValidationError(
            'Node.js diagnostics are unavailable. Verify that Kudu diagnostics are enabled and '
            'the web app uses a supported Node.js runtime.')
    if not 200 <= response.status_code < 300:
        raise AzureResponseError(
            'Kudu diagnostics availability check failed with HTTP status {}.'.format(response.status_code))


def _vfs_url(scm_url, diagnostic_type, filename, instance):
    from urllib.parse import quote
    return _with_instance(
        '{}/api/vfs/LogFiles/diagnostics/{}/{}'.format(
            scm_url, diagnostic_type, quote(filename, safe='')), instance)


def _with_instance(url, instance):
    from urllib.parse import urlencode
    separator = '&' if '?' in url else '?'
    return url + separator + urlencode({'instance': instance})
