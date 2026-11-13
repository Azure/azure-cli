# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import os
import re
import stat

from azure.cli.core.azclierror import FileOperationError, ValidationError


_config_section = "bicep"

_use_binary_from_path_config_key = "use_binary_from_path"
_use_binary_from_path_config_default_value = "if_found_in_ci"

_check_version_config_key = "check_version"
_check_version_config_default_value = True

_max_config_chain_depth = 64
_json_comment_pattern = re.compile(r'"(?:\\.|[^"\\])*"|//[^\r\n]*|/\*.*?\*/|/\*', re.DOTALL)


def get_use_binary_from_path_config(cli_ctx):
    return cli_ctx.config.get(
        _config_section, _use_binary_from_path_config_key, _use_binary_from_path_config_default_value
    ).lower()


def set_use_binary_from_path_config(cli_ctx, value):
    cli_ctx.config.set_value(_config_section, _use_binary_from_path_config_key, value)


def remove_use_binary_from_path_config(cli_ctx):
    cli_ctx.config.remove_option(_config_section, _use_binary_from_path_config_key)


def get_check_version_config(cli_ctx):
    return cli_ctx.config.getboolean(_config_section, _check_version_config_key, _check_version_config_default_value)


def find_bicep_config_file(entrypoint_file):
    """Find the nearest bicepconfig.json starting at the source file's directory."""
    directory = os.path.dirname(os.path.abspath(entrypoint_file))
    while True:
        candidate = os.path.join(directory, "bicepconfig.json")
        try:
            if stat.S_ISREG(os.stat(candidate).st_mode):
                return candidate
        except FileNotFoundError:
            pass
        except OSError as err:
            raise FileOperationError(f"Unable to access Bicep configuration '{candidate}': {err}") from err

        parent = os.path.dirname(directory)
        if parent == directory:
            return None
        directory = parent


def resolve_bicep_version_constraint(entrypoint_file):
    """Resolve the raw effective bicep.version without selecting or installing a compiler."""
    config_file = find_bicep_config_file(entrypoint_file)
    if config_file is None:
        return None

    layers = []
    visited = set()
    current_file = config_file
    while True:
        normalized_path = os.path.normcase(current_file)
        if normalized_path in visited:
            raise ValidationError(
                f"Bicep configuration '{config_file}' has an extends cycle involving '{current_file}'."
            )
        if len(layers) >= _max_config_chain_depth:
            raise ValidationError(
                f"Bicep configuration '{config_file}' exceeds the maximum extends chain depth "
                f"of {_max_config_chain_depth} files."
            )
        visited.add(normalized_path)
        config = _load_bicep_config(current_file)
        layers.append(config)

        extends = config.get("extends")
        if extends is None:
            break
        if not isinstance(extends, str):
            raise ValidationError(f"The extends property in '{current_file}' must be a relative path string.")
        if not extends.strip():
            break
        if extends.startswith(("/", "\\")) or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", extends):
            raise ValidationError(
                f"The extends path '{extends}' in '{current_file}' must be a relative file path, not an absolute path "
                "or URI."
            )
        current_file = os.path.abspath(os.path.join(os.path.dirname(current_file), extends))

    # Validate the complete chain before using a constraint, even when the leaf declares one.
    compiler_config = {}
    for layer in reversed(layers):
        compiler_config = _merge_config_value(compiler_config, layer.get("bicep"))

    if not isinstance(compiler_config, dict):
        raise ValidationError(f"The effective bicep section in '{config_file}' must be a JSON object.")
    version = compiler_config.get("version")
    if version is not None and not isinstance(version, str):
        raise ValidationError(f"The effective bicep.version property in '{config_file}' must be a string.")
    return version


def _merge_config_value(base, derived):
    if derived is None:
        return base
    if isinstance(base, dict) and isinstance(derived, dict):
        merged = base.copy()
        for key, value in derived.items():
            merged[key] = _merge_config_value(base.get(key), value)
        return merged
    return derived


def _load_bicep_config(config_file):
    def replace_comment(match):
        token = match.group()
        if token.startswith('"'):
            return token
        if token == "/*":
            raise ValueError("Unterminated block comment.")
        # Preserve whitespace so comments cannot join JSON tokens or change line numbers.
        return re.sub(r"[^\r\n]", " ", token)

    def reject_constant(value):
        raise ValueError(f"Invalid JSON value '{value}'.")

    try:
        with open(config_file, encoding="utf-8-sig") as config:
            contents = config.read()
    except OSError as err:
        raise FileOperationError(f"Unable to read Bicep configuration '{config_file}': {err}") from err
    except UnicodeError as err:
        raise ValidationError(f"Unable to decode Bicep configuration '{config_file}': {err}") from err

    try:
        contents = _json_comment_pattern.sub(replace_comment, contents)
        parsed = json.loads(contents, parse_constant=reject_constant)
    except ValueError as err:
        raise ValidationError(f"Unable to parse Bicep configuration '{config_file}': {err}") from err
    if not isinstance(parsed, dict):
        raise ValidationError(f"Bicep configuration '{config_file}' must contain a JSON object.")
    return parsed
