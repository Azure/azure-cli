#!/usr/bin/env python

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Generate or verify packaged latest command/help index assets.

This script updates or validates:
- src/azure-cli-core/azure/cli/core/commandIndex.latest.json
- src/azure-cli-core/azure/cli/core/helpIndex.latest.json

The script runs in an isolated temp AZURE_CONFIG_DIR and with extension directories
redirected to empty folders to avoid local machine state affecting output.
"""

import argparse
import json
import os
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CORE_DIR = REPO_ROOT / 'src' / 'azure-cli-core' / 'azure' / 'cli' / 'core'
COMMAND_INDEX_PATH = CORE_DIR / 'commandIndex.latest.json'
HELP_INDEX_PATH = CORE_DIR / 'helpIndex.latest.json'
CORE_COMMAND_MODULE_PREFIX = 'azure.cli.command_modules.'


def _bootstrap_repo_paths():
    """Ensure local source trees are importable when running from repo root."""
    source_roots = [
        REPO_ROOT / 'src' / 'azure-cli-core',
        REPO_ROOT / 'src' / 'azure-cli',
        REPO_ROOT / 'src' / 'azure-cli-telemetry',
        REPO_ROOT / 'src' / 'azure-cli-testsdk',
    ]

    for source_root in source_roots:
        source_root_str = str(source_root)
        if source_root_str not in sys.path:
            sys.path.insert(0, source_root_str)


@contextmanager
def _isolated_cli_environment():
    """Temporarily isolate config/extension directories for deterministic output."""
    tracked_vars = ['AZURE_CONFIG_DIR', 'AZURE_EXTENSION_DIR']
    previous = {name: os.environ.get(name) for name in tracked_vars}

    with tempfile.TemporaryDirectory(prefix='az-index-gen-') as temp_config_dir:
        extension_dir = os.path.join(temp_config_dir, 'cliextensions')
        os.makedirs(extension_dir, exist_ok=True)

        os.environ['AZURE_CONFIG_DIR'] = temp_config_dir
        os.environ['AZURE_EXTENSION_DIR'] = extension_dir

        try:
            yield temp_config_dir, extension_dir
        finally:
            for name, value in previous.items():
                if value is None:
                    os.environ.pop(name, None)
                else:
                    os.environ[name] = value


def _read_json(path):
    if not path.is_file():
        return None
    with path.open('r', encoding='utf-8-sig') as handle:
        return json.load(handle)


def _order_keys_like_template(generated, template):
    """Preserve existing key order when possible, append new keys in sorted order."""
    if not isinstance(generated, dict):
        return generated

    if not isinstance(template, dict):
        return {key: generated[key] for key in sorted(generated)}

    ordered = {}
    for key in template:
        if key in generated:
            ordered[key] = generated[key]

    for key in sorted(generated):
        if key not in ordered:
            ordered[key] = generated[key]

    return ordered


def _extract_builtin_module_name(command):
    """Return built-in module name for a command table entry, or None for extension entries."""
    command_source = getattr(command, 'command_source', None)
    if isinstance(command_source, str) and command_source.startswith(CORE_COMMAND_MODULE_PREFIX):
        return command_source

    command_loader = getattr(command, 'loader', None)
    loader_module = getattr(command_loader, '__module__', None)
    if isinstance(loader_module, str) and loader_module.startswith(CORE_COMMAND_MODULE_PREFIX):
        return loader_module

    return None


def _build_command_index_map(command_table):
    command_index = {}
    for command_name, command in command_table.items():
        top_command = command_name.split()[0]
        module_name = _extract_builtin_module_name(command)
        if not module_name:
            continue

        modules = command_index.setdefault(top_command, [])
        if module_name not in modules:
            modules.append(module_name)

    for top_command, modules in command_index.items():
        command_index[top_command] = sorted(modules)

    return command_index


def _build_help_index_map(cli_ctx, commands_loader):
    from azure.cli.core._help import CliGroupHelpFile, extract_help_index_data
    from azure.cli.core.parser import AzCliCommandParser

    parser = AzCliCommandParser(cli_ctx)
    parser.load_command_table(commands_loader)

    root_subparser = parser.subparsers.get(tuple())
    if not root_subparser:
        return {'groups': {}, 'commands': {}}

    help_obj = cli_ctx.help_cls(cli_ctx)
    root_help = CliGroupHelpFile(help_obj, '', root_subparser)
    root_help.load(root_subparser)

    groups, commands = extract_help_index_data(root_help)

    normalized_groups = {
        group_name: {
            'summary': group_data.get('summary', ''),
            'tags': group_data.get('tags', '')
        }
        for group_name, group_data in groups.items()
    }
    normalized_commands = {
        command_name: {
            'summary': command_data.get('summary', ''),
            'tags': command_data.get('tags', '')
        }
        for command_name, command_data in commands.items()
    }

    return {
        'groups': {key: normalized_groups[key] for key in sorted(normalized_groups)},
        'commands': {key: normalized_commands[key] for key in sorted(normalized_commands)}
    }


def _generate_documents():
    _bootstrap_repo_paths()

    with _isolated_cli_environment() as (temp_config_dir, extension_dir):
        from azure.cli.core import CommandIndex, __version__, get_default_cli
        import azure.cli.core.extension as extension_module

        # Hard pin extension discovery directories so local/global installed extensions do not leak in.
        extension_module.EXTENSIONS_DIR = extension_dir
        extension_module.EXTENSIONS_SYS_DIR = os.path.join(temp_config_dir, 'empty-system-extensions')
        extension_module.DEV_EXTENSION_SOURCES = []
        os.makedirs(extension_module.EXTENSIONS_SYS_DIR, exist_ok=True)

        cli = get_default_cli()
        cli.cloud.profile = 'latest'
        cli.data['completer_active'] = False

        invoker = cli.invocation_cls(
            cli_ctx=cli,
            commands_loader_cls=cli.commands_loader_cls,
            parser_cls=cli.parser_cls,
            help_cls=cli.help_cls
        )
        cli.invocation = invoker
        commands_loader = invoker.commands_loader
        command_table = commands_loader.load_command_table(None)

        current_command_doc = _read_json(COMMAND_INDEX_PATH) or {}
        current_help_doc = _read_json(HELP_INDEX_PATH) or {}

        generated_command_index = _build_command_index_map(command_table)
        generated_help_index = _build_help_index_map(cli, commands_loader)

        ordered_command_index = _order_keys_like_template(
            generated_command_index,
            current_command_doc.get(CommandIndex._COMMAND_INDEX)  # pylint: disable=protected-access
        )

        help_template = current_help_doc.get(CommandIndex._HELP_INDEX, {})  # pylint: disable=protected-access
        ordered_help_groups = _order_keys_like_template(generated_help_index['groups'], help_template.get('groups'))
        ordered_help_commands = _order_keys_like_template(generated_help_index['commands'], help_template.get('commands'))

        command_doc = {
            CommandIndex._COMMAND_INDEX_VERSION: __version__,  # pylint: disable=protected-access
            CommandIndex._COMMAND_INDEX_CLOUD_PROFILE: 'latest',  # pylint: disable=protected-access
            CommandIndex._COMMAND_INDEX: ordered_command_index  # pylint: disable=protected-access
        }

        help_doc = {
            CommandIndex._COMMAND_INDEX_VERSION: __version__,  # pylint: disable=protected-access
            CommandIndex._COMMAND_INDEX_CLOUD_PROFILE: 'latest',  # pylint: disable=protected-access
            CommandIndex._HELP_INDEX: {  # pylint: disable=protected-access
                'groups': ordered_help_groups,
                'commands': ordered_help_commands
            }
        }

        return command_doc, help_doc


def _serialize_json(document):
    return json.dumps(document, indent=2) + '\n'


def _write_file(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='\n') as handle:
        handle.write(content)


def _load_text(path):
    if not path.is_file():
        return None
    return path.read_text(encoding='utf-8-sig')


def _run_generate(command_text, help_text):
    current_command_text = _load_text(COMMAND_INDEX_PATH)
    current_help_text = _load_text(HELP_INDEX_PATH)

    updated_files = []

    if current_command_text != command_text:
        _write_file(COMMAND_INDEX_PATH, command_text)
        updated_files.append(COMMAND_INDEX_PATH)

    if current_help_text != help_text:
        _write_file(HELP_INDEX_PATH, help_text)
        updated_files.append(HELP_INDEX_PATH)

    if updated_files:
        print('Updated generated latest index files:')
        for path in updated_files:
            print(f'  - {path.relative_to(REPO_ROOT)}')
    else:
        print('Latest index files are already up-to-date.')

    return 0


def _run_verify(command_text, help_text):
    mismatched = []

    if _load_text(COMMAND_INDEX_PATH) != command_text:
        mismatched.append(COMMAND_INDEX_PATH)
    if _load_text(HELP_INDEX_PATH) != help_text:
        mismatched.append(HELP_INDEX_PATH)

    if mismatched:
        print('Generated latest index files are out of date:')
        for path in mismatched:
            print(f'  - {path.relative_to(REPO_ROOT)}')
        print('Run:')
        print('  python scripts/generate_latest_indices.py generate')
        return 1

    print('Verified: latest index files are up-to-date.')
    return 0


def _parse_args():
    parser = argparse.ArgumentParser(
        description='Generate or verify packaged latest command and help index JSON files.'
    )
    parser.add_argument(
        'mode',
        nargs='?',
        choices=['generate', 'verify'],
        default='generate',
        help='Mode to run. generate writes files; verify checks drift and exits non-zero on mismatch.'
    )
    return parser.parse_args()


def main():
    args = _parse_args()

    command_doc, help_doc = _generate_documents()
    command_text = _serialize_json(command_doc)
    help_text = _serialize_json(help_doc)

    if args.mode == 'verify':
        return _run_verify(command_text, help_text)

    return _run_generate(command_text, help_text)


if __name__ == '__main__':
    sys.exit(main())
