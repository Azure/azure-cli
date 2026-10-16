# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import configparser
import os
import sys

import knack.output
from knack.log import get_logger

from azure.cli.core._environment import _ENV_AZ_LAUNCHER

logger = get_logger(__name__)

_OUTPUT_NEWLINE_NATIVE = 'native'
_OUTPUT_NEWLINE_LF = 'lf'
# core.output_newline value -> newline for stdout.reconfigure(); None leaves stdout untouched.
_OUTPUT_NEWLINES = {
    _OUTPUT_NEWLINE_NATIVE: None,
    _OUTPUT_NEWLINE_LF: '\n',
}


class AzOutputProducer(knack.output.OutputProducer):

    def check_valid_format_type(self, format_type):
        return format_type in self._FORMAT_DICT


def get_output_format(cli_ctx):
    return cli_ctx.invocation.data.get("output", None)


def set_output_format(cli_ctx, desired_format):
    if cli_ctx.output.check_valid_format_type(desired_format):
        cli_ctx.invocation.data["output"] = desired_format


def get_output_newline(cli_ctx):
    """Resolve `core.output_newline`: AZURE_CORE_OUTPUT_NEWLINE, then global config, then launcher default.

    An empty value selects the default rather than falling back to the next source. The bash launcher shipped
    with the Windows MSI (used by WSL and Git Bash) sets AZ_LAUNCHER=bash, which defaults to LF so
    `$(az ... -o tsv)` does not capture a trailing carriage return.
    """
    value = (cli_ctx.config.get('core', 'output_newline', fallback=None) or '').strip().lower()
    if not value:
        return _OUTPUT_NEWLINE_LF if os.environ.get(_ENV_AZ_LAUNCHER) == 'bash' else _OUTPUT_NEWLINE_NATIVE
    return value


def apply_output_newline(cli_ctx, **_):
    """Stop Windows from translating '\\n' to '\\r\\n' in all text written to stdout (not just `-o` results)
    when `core.output_newline` is `lf`.

    Registered for EVENT_CLI_PRE_EXECUTE: logging is configured by then and no command output has been
    written yet. Streams are reconfigured in place because knack keeps a reference to sys.stdout as `out_file`.
    """
    try:
        value = get_output_newline(cli_ctx)
    except configparser.Error as ex:
        logger.warning("Ignoring unreadable core.output_newline value: %s", ex)
        return
    if value not in _OUTPUT_NEWLINES:
        logger.warning("Ignoring invalid core.output_newline value '%s'. Allowed values: %s",
                       value, ', '.join(_OUTPUT_NEWLINES))
        return
    newline = _OUTPUT_NEWLINES[value]
    if newline is None:
        return
    streams = []
    for stream in (getattr(cli_ctx, 'out_file', None), sys.stdout):
        if stream is not None and hasattr(stream, 'reconfigure') and all(stream is not s for s in streams):
            streams.append(stream)
    for stream in streams:
        stream.reconfigure(newline=newline)
