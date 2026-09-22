# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Native, host-owned installation of the full Azure plugin, after caller consent."""

import json
import os
import re
import shutil
import signal
import subprocess
import sys

from knack.log import get_logger
from knack.prompting import NoTTYException, prompt, prompt_y_n

from azure.cli.core.azclierror import (
    ClientRequestError, InvalidArgumentValueError, ResourceNotFoundError, ValidationError,
)

logger = get_logger(__name__)

HOST_IDS = ('claude-code', 'github-copilot', 'codex')
HOST_LABELS = {'claude-code': 'Claude Code', 'github-copilot': 'GitHub Copilot CLI', 'codex': 'Codex CLI'}
_EXECUTABLES = {'claude-code': 'claude', 'github-copilot': 'copilot', 'codex': 'codex'}


def validate_plugin_options(install_azure_plugin=None, plugin_hosts=None):
    """Validate consent and normalize explicit hosts before binary installation."""
    if install_azure_plugin is not True:
        if plugin_hosts is not None:
            raise InvalidArgumentValueError('--plugin-hosts requires --install-azure-plugin true.')
        return None
    if not plugin_hosts or any(host not in HOST_IDS for host in plugin_hosts):
        raise InvalidArgumentValueError(
            '--install-azure-plugin true requires --plugin-hosts with one or more of: ' + ', '.join(HOST_IDS))
    if _under_sudo():
        raise InvalidArgumentValueError(
            'Azure plugin setup cannot run under sudo. Run as the intended host user with writable binary paths.')
    return [host for host in HOST_IDS if host in plugin_hosts]


def _under_sudo():
    return bool(os.environ.get('SUDO_USER') or os.environ.get('SUDO_UID'))


def maybe_install_azure_plugin(cmd, install_azure_plugin=None, plugin_hosts=None):
    """Offer optional setup after both binaries succeed; explicit flags are consent."""
    hosts = validate_plugin_options(install_azure_plugin, plugin_hosts)
    if install_azure_plugin is False:
        return
    if install_azure_plugin is None:
        if (_under_sudo() or not sys.stdin.isatty() or
                cmd.cli_ctx.config.getboolean('core', 'disable_confirm_prompt', fallback=False)):
            return
        try:
            if not prompt_y_n('Set up the full Azure plugin for an AI CLI host?', default='n'):
                return
            hosts = _select_hosts()
            if not hosts:
                return
            _disclose_setup()
            labels = ', '.join(HOST_LABELS[host] for host in hosts)
            if not prompt_y_n(f'Authorize native user/global installation and enablement for {labels}?', default='n'):
                return
        except (NoTTYException, EOFError, KeyboardInterrupt):
            return
    else:
        _disclose_setup()
    _install_selected_hosts(hosts, explicit=install_azure_plugin is True)


def _install_selected_hosts(hosts, *, explicit):
    failures = []
    outcomes = []
    for host in hosts:
        try:
            installed = install_plugin(host)
        except KeyboardInterrupt:
            outcomes.append(f'{HOST_LABELS[host]}: interrupted; native state is uncertain.')
            # Cancellation must disclose partial state even with --only-show-errors.
            print(_setup_summary(outcomes), file=sys.stderr)
            raise
        except (ClientRequestError, ResourceNotFoundError, ValidationError) as ex:
            failures.append(ex)
            outcomes.append(f'{HOST_LABELS[host]}: failed. {ex}')
        else:
            status = ('installed; authentication/activation and hook trust may still be required' if installed else
                      'Azure already reported; plugin install skipped (a marketplace may have been added)')
            outcome = f'{HOST_LABELS[host]}: {status}.'
            outcomes.append(outcome)
            print(outcome, file=sys.stderr)
    if failures:
        message = _setup_summary(outcomes)
        if explicit:
            raise type(failures[0])(message) from None
        logger.warning(message)


def _setup_summary(outcomes):
    summary = '\n'.join(outcomes)
    return ('Azure plugin setup did not complete for all selected hosts. '
            f'kubectl and kubelogin remain installed.\n{summary}\n'
            "Inspect and recover using each host's native plugin commands. "
            'No automatic retry or rollback was attempted.')


def _select_hosts():
    detected = discover_hosts()
    choices = '\n'.join(f'  {index}. {HOST_LABELS[host]}' + (' [detected]' if host in detected else '')
                        for index, host in enumerate(HOST_IDS, 1))
    defaults = ' '.join(str(index) for index, host in enumerate(HOST_IDS, 1) if host in detected) or '0'
    while True:
        answer = prompt(f'{choices}\nSelect host numbers separated by spaces (replaces defaults); '
                        f'0 selects none. Enter keeps [{defaults}]: ').strip()
        if not answer:
            return detected
        if answer == '0':
            return []
        numbers = answer.split()
        if all(number in ('1', '2', '3') for number in numbers):
            return [host for index, host in enumerate(HOST_IDS, 1) if str(index) in numbers]
        print('Choose 1, 2 and/or 3 separated by spaces, or 0 for none.', file=sys.stderr)


def _disclose_setup():
    # Consent context must remain visible even with --only-show-errors.
    print(
        'Azure plugin setup installs the full Azure plugin (skills, MCP configuration and hooks) in native '
        'user/global scope, not repository scope. Native inventory-reported Azure installations, including '
        'disabled ones, are skipped. When inventory reports absence, consent authorizes normal native installation '
        'and enablement, including changes to hidden/stale disable preferences or registrations.\n'
        'New installations require an installed host CLI and Node.js 22+ with npx on PATH. '
        'The stock MCP runtime uses @azure/mcp@latest and is not pinned by the plugin version. '
        'Hosts own permissions, marketplace sources/pins and updates; Azure CLI adds no custom updater or bypass. '
        'Azure authentication, MCP activation, hook trust and sovereign-cloud setup may still be required. '
        'No prerequisites are installed and no Azure login or resource operations are performed.',
        file=sys.stderr,
    )


def discover_hosts() -> list[str]:
    """Discover executables without running hosts or inspecting their configuration."""
    return [host for host in HOST_IDS if shutil.which(_EXECUTABLES[host])]


def install_plugin(host_id: str) -> bool:
    """Install after consent; False means Azure was found and no plugin install ran.

    A marketplace may have been added before an existing installation became visible.
    Native inventory can hide stale registrations; consent covers native install-and-enable.
    """
    if host_id not in HOST_IDS:
        raise InvalidArgumentValueError(f'Unsupported Azure plugin host: {host_id}. Choose from {", ".join(HOST_IDS)}.')
    executable = shutil.which(_EXECUTABLES[host_id])
    if not executable:
        raise ResourceNotFoundError(_failure(host_id, 'prerequisite check',
                                             f'Install {_EXECUTABLES[host_id]} and make it available on PATH.'))
    args = ['plugin', 'list', '--available', '--json'] if host_id == 'codex' else ['plugin', 'list', '--json']
    inventory = _inventory(host_id, [executable, *args], 'plugin inventory')
    if _azure_registered(host_id, inventory):
        return False

    if host_id == 'github-copilot':
        _check_copilot_mcp(executable)
    if host_id == 'claude-code':
        marketplace = 'claude-plugins-official'
        source = 'anthropics/claude-plugins-official'
        flags = ['--scope', 'user']
    else:
        marketplace = 'azure-skills'
        source = 'microsoft/azure-skills'
        flags = ['--json'] if host_id == 'codex' else []

    markets = _inventory(host_id, [executable, 'plugin', 'marketplace', 'list', '--json'], 'marketplace inventory')
    if host_id == 'codex':
        markets = markets.get('marketplaces') if isinstance(markets, dict) else None
    origin = 'root' if host_id == 'codex' else 'source'
    if not isinstance(markets, list) or any(
            not isinstance(row, dict) or not _text(row.get('name')) or not _text(row.get(origin))
            for row in markets):
        raise ValidationError(_failure(host_id, 'marketplace inventory', 'Unrecognized native JSON schema.'))
    _check_runtime(host_id)
    if not any(row['name'] == marketplace for row in markets):
        _run(host_id, [executable, 'plugin', 'marketplace', 'add', source, *flags], 'marketplace add')
        # Adding a catalog can expose installed or live plugins hidden from the first inventory.
        inventory = _inventory(host_id, [executable, *args], 'plugin inventory')
        if _azure_registered(host_id, inventory):
            return False
    action = 'add' if host_id == 'codex' else 'install'
    _run(host_id, [executable, 'plugin', action, f'azure@{marketplace}', *flags], 'plugin install')
    return True


def _check_runtime(host_id):
    node = shutil.which('node')
    if not node or not shutil.which('npx'):
        raise ResourceNotFoundError(_failure(host_id, 'runtime prerequisite check',
                                             'Install Node.js 22 or later with node and npx available on PATH.'))
    result = _run(host_id, [node, '--version'], 'Node.js version check')
    version = re.fullmatch(r'v(\d+)\.\d+\.\d+', result.stdout.strip())
    if not version or int(version[1]) < 22:
        raise ValidationError(_failure(host_id, 'runtime prerequisite check',
                                       'Node.js 22 or later is required for a new Azure plugin installation. '
                                       f'Reported version: {_diagnostic(result.stdout)}'))


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _azure_registered(host_id, inventory):
    error = _failure(host_id, 'plugin inventory', 'Unrecognized native JSON schema.')
    if host_id == 'codex':
        if not isinstance(inventory, dict) or not all(
                isinstance(inventory.get(key), list) for key in ('installed', 'available')):
            raise ValidationError(error)
        for key, installed in (('installed', True), ('available', False)):
            for row in inventory[key]:
                if (not isinstance(row, dict) or not _text(row.get('name')) or
                        not _text(row.get('marketplaceName')) or not isinstance(row.get('enabled'), bool)):
                    raise ValidationError(error)
                if (row.get('installed') is not installed or
                        row.get('pluginId') != f"{row['name']}@{row['marketplaceName']}"):
                    raise ValidationError(error)
        return any(row['name'] == 'azure' for row in inventory['installed'])

    identity = 'id' if host_id == 'claude-code' else 'name'
    origin = 'scope' if host_id == 'claude-code' else 'source'
    if not isinstance(inventory, list) or any(
            not isinstance(row, dict) or not _text(row.get(identity)) or
            not _text(row.get(origin)) or not isinstance(row.get('enabled'), bool)
            for row in inventory):
        raise ValidationError(error)
    return any(row[identity].split('@', 1)[0] == 'azure' for row in inventory)


def _check_copilot_mcp(executable):
    inventory = _inventory('github-copilot', [executable, 'mcp', 'list', '--json'], 'MCP inventory')
    servers = inventory.get('mcpServers') if isinstance(inventory, dict) else None
    if not isinstance(servers, dict) or any(
            not isinstance(row, dict) or not _text(row.get('source')) or not isinstance(row.get('enabled'), bool)
            for row in servers.values()):
        raise ValidationError(_failure('github-copilot', 'MCP inventory', 'Unrecognized native JSON schema.'))
    if 'azure' in servers:
        raise ValidationError(_failure('github-copilot', 'MCP inventory',
                                       'An existing azure MCP server could be shadowed by the Azure plugin. '
                                       'Resolve this collision manually before installing.'))


def _inventory(host_id, argv, operation):
    # All inventories can carry credentials: Git URLs as well as MCP args/env.
    result = _run(host_id, argv, operation, sensitive=True)
    # A warning may mean the host skipped unreadable configuration, not an empty inventory.
    if result.stderr.strip():
        detail = f'Native inventory warning: {_diagnostic(result.stderr, sensitive=True)}'
        raise ValidationError(_failure(host_id, operation, detail))
    try:
        return json.loads(result.stdout, object_pairs_hook=_unique_object)
    except (ValueError, RecursionError):
        detail = 'Invalid native JSON (malformed, too deeply nested or duplicate object members).'
        raise ValidationError(_failure(host_id, operation, detail)) from None


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            # Do not put potentially sensitive keys or values in exception chains.
            raise ValueError('duplicate object member')
        result[key] = value
    return result


def _diagnostic(value, *, sensitive=False):
    if sensitive:
        return '[sensitive inventory output suppressed]'
    if isinstance(value, bytes):
        value = value.decode('utf-8', errors='replace')
    value = (value or '').strip()
    return value[:1500] + (' [truncated]' if len(value) > 1500 else '')


def _failure(host_id, operation, detail):
    return (f'{HOST_LABELS[host_id]}: {operation} failed. {detail} '
            "Inspect and recover using the host's native plugin commands; "
            'no automatic retry or rollback was attempted.')


def _stop_process_tree(process):
    # Own a POSIX session, or target only the Windows launcher's descendant tree.
    # This is not containment for a host that deliberately detaches its children.
    uncertain = False
    output = None
    try:
        if sys.platform == 'win32':
            taskkill = os.path.join(os.environ['SystemRoot'], 'System32', 'taskkill.exe')
            result = subprocess.run([taskkill, '/PID', str(process.pid), '/T', '/F'],
                                    stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                    timeout=5, check=False)
            uncertain = result.returncode != 0
        else:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
    except (OSError, subprocess.TimeoutExpired, KeyError):
        uncertain = True
    try:
        process.kill()
        output = process.communicate(timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        uncertain = True
        try:
            process.wait(timeout=5)
        except (OSError, subprocess.TimeoutExpired):
            pass
    if uncertain:
        print('Native process-tree cleanup could not be confirmed; native state is uncertain. '
              "Inspect the host's running processes and recover using its native plugin commands.", file=sys.stderr)
    return output


def _run(host_id, argv, operation, timeout=300, *, sensitive=False):
    try:
        windows = sys.platform == 'win32'
        process = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   encoding='utf-8', errors='replace', start_new_session=not windows,
                                   creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if windows else 0)
        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except (subprocess.TimeoutExpired, KeyboardInterrupt) as ex:
            output = _stop_process_tree(process)
            if isinstance(ex, subprocess.TimeoutExpired) and output is not None:
                # Windows reader threads only return partial output after EOF.
                ex.stdout, ex.stderr = output
            raise
        finally:
            # POSIX has no pipe-reader threads. On Windows communicate owns and
            # closes its pipes; closing them here after failed cleanup can block.
            if not windows:
                process.stdout.close()
                process.stderr.close()
        result = subprocess.CompletedProcess(argv, process.returncode, stdout, stderr)
    except subprocess.TimeoutExpired as ex:
        detail = (f'timed out after {timeout}s. {_diagnostic(ex.stdout, sensitive=sensitive)} '
                  f'{_diagnostic(ex.stderr, sensitive=sensitive)}')
        raise ClientRequestError(_failure(host_id, operation, detail)) from (None if sensitive else ex)
    except OSError as ex:
        detail = _diagnostic(str(ex), sensitive=sensitive)
        raise ClientRequestError(_failure(host_id, operation, detail)) from (None if sensitive else ex)
    if result.returncode:
        detail = (f'exit {result.returncode}. {_diagnostic(result.stdout, sensitive=sensitive)} '
                  f'{_diagnostic(result.stderr, sensitive=sensitive)}')
        raise ClientRequestError(_failure(host_id, operation, detail))
    return result
