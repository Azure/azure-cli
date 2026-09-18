# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""User-level agent discovery and preflight for optional Azure skills installation."""

import os
from dataclasses import dataclass
from pathlib import Path

from knack.util import CLIError
from azure.cli.core.azclierror import (
    ArgumentUsageError,
    InvalidArgumentValueError,
    RequiredArgumentMissingError,
)


AGENT_IDS = ('claude-code', 'codex', 'github-copilot', 'pi')


@dataclass(frozen=True)
class AgentTarget:
    identifier: str
    label: str
    destination: Path
    detected: bool


def _config_directory(variable: str, default: Path) -> Path:
    value = os.environ.get(variable)
    if value and value.strip():
        return Path(os.path.abspath(os.path.expanduser(value)))
    return default


def discover_agents() -> list[AgentTarget]:
    home = Path.home()
    claude = _config_directory('CLAUDE_CONFIG_DIR', home / '.claude')
    codex = _config_directory('CODEX_HOME', home / '.codex')
    copilot = home / '.copilot'
    pi = _config_directory('PI_CODING_AGENT_DIR', home / '.pi/agent')
    return [
        AgentTarget('claude-code', 'Claude Code', claude / 'skills', os.path.isdir(claude)),
        # Codex's config override affects detection, not its shared user skills location.
        AgentTarget('codex', 'Codex', home / '.agents/skills',
                    os.path.isdir(codex) or (os.name == 'posix' and os.path.isdir('/etc/codex'))),
        AgentTarget('github-copilot', 'GitHub Copilot', copilot / 'skills', os.path.isdir(copilot)),
        AgentTarget('pi', 'Pi', pi / 'skills', os.path.isdir(pi)),
    ]


def parse_agent_selection(value: str, defaults: list[str]) -> list[str]:
    text = value.strip()
    if not text:
        return list(defaults)
    if text.lower() == 'none':
        return []
    parts = [part.strip() for part in text.split(',')]
    if any(part not in ('1', '2', '3', '4') for part in parts):
        raise CLIError('Enter agent numbers 1-4 separated by commas, or "none".')
    selected = {int(part) - 1 for part in parts}
    return [identifier for index, identifier in enumerate(AGENT_IDS)
            if index in selected]


def _is_sudo() -> bool:
    # Treat even an empty marker conservatively; root alone does not imply sudo.
    return os.name == 'posix' and ('SUDO_UID' in os.environ or 'SUDO_USER' in os.environ)


def validate_skills_options(install_azure_skills: bool | None, skills_agents: list[str] | None) -> None:
    if skills_agents is not None and install_azure_skills is not True:
        raise ArgumentUsageError('--skills-agents requires --install-azure-skills true.')
    if install_azure_skills is not True:
        return
    if not skills_agents:
        raise RequiredArgumentMissingError('--install-azure-skills true requires a nonempty --skills-agents list.')
    unknown = [identifier for identifier in skills_agents if identifier not in AGENT_IDS]
    if unknown:
        raise InvalidArgumentValueError(
            f'Unknown --skills-agents: {", ".join(unknown)}. Choose from: {", ".join(AGENT_IDS)}.')
    if _is_sudo():
        raise CLIError(
            'Install Azure skills as an unprivileged user, not under sudo. '
            'Rerun with user-writable binary installation locations.')
