# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Native, host-owned installation of the full Azure plugin, after caller consent."""

import json
import re
import shutil
import subprocess

from azure.cli.core.azclierror import (
    ClientRequestError, InvalidArgumentValueError, ResourceNotFoundError, ValidationError,
)

HOST_IDS = ('claude-code', 'github-copilot', 'codex')
HOST_LABELS = {'claude-code': 'Claude Code', 'github-copilot': 'GitHub Copilot CLI', 'codex': 'Codex CLI'}
_EXECUTABLES = {'claude-code': 'claude', 'github-copilot': 'copilot', 'codex': 'codex'}


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
    result = _run(host_id, argv, operation)
    # A warning may mean the host skipped unreadable configuration, not an empty inventory.
    if result.stderr.strip():
        raise ValidationError(_failure(host_id, operation, _diagnostic(result.stderr)))
    try:
        return json.loads(result.stdout)
    except (ValueError, RecursionError) as ex:
        raise ValidationError(_failure(host_id, operation,
                                       f'Invalid native JSON: {_diagnostic(result.stdout)}')) from ex


def _diagnostic(value):
    if isinstance(value, bytes):
        value = value.decode('utf-8', errors='replace')
    value = (value or '').strip()
    return value[:1500] + (' [truncated]' if len(value) > 1500 else '')


def _failure(host_id, operation, detail):
    return (f'{HOST_LABELS[host_id]}: {operation} failed. {detail} '
            "Inspect and recover using the host's native plugin commands; "
            'no automatic retry or rollback was attempted.')


def _run(host_id, argv, operation, timeout=300):
    try:
        result = subprocess.run(argv, stdin=subprocess.DEVNULL, capture_output=True,
                                encoding='utf-8', errors='replace', timeout=timeout, check=False)
    except subprocess.TimeoutExpired as ex:
        detail = f'timed out after {timeout}s. {_diagnostic(ex.stdout)} {_diagnostic(ex.stderr)}'
        raise ClientRequestError(_failure(host_id, operation, detail)) from ex
    except OSError as ex:
        raise ClientRequestError(_failure(host_id, operation, _diagnostic(str(ex)))) from ex
    if result.returncode:
        detail = f'exit {result.returncode}. {_diagnostic(result.stdout)} {_diagnostic(result.stderr)}'
        raise ClientRequestError(_failure(host_id, operation, detail))
    return result
