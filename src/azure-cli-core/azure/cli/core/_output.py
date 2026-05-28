# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import errno

import knack.output
from knack.log import get_logger
from knack.util import CommandResultItem

logger = get_logger(__name__)


class AzOutputProducer(knack.output.OutputProducer):

    def check_valid_format_type(self, format_type):
        return format_type in self._FORMAT_DICT

    def out(self, obj, formatter=None, out_file=None):
        if formatter == knack.output.format_tsv and hasattr(out_file, 'buffer'):
            if not isinstance(obj, CommandResultItem):
                raise TypeError('Expected {} got {}'.format(CommandResultItem.__name__, type(obj)))

            output = formatter(obj)
            try:
                out_file.buffer.write(output.encode(out_file.encoding or 'utf-8'))
                out_file.flush()
            except IOError as ex:
                if ex.errno == errno.EPIPE:
                    pass
                else:
                    raise
            except UnicodeEncodeError:
                logger.warning("Unable to encode the output with %s encoding. Unsupported characters are discarded.",
                               out_file.encoding)
                out_file.buffer.write(output.encode('ascii', 'ignore'))
                out_file.flush()
            return

        super().out(obj, formatter=formatter, out_file=out_file)


def get_output_format(cli_ctx):
    return cli_ctx.invocation.data.get("output", None)


def set_output_format(cli_ctx, desired_format):
    if cli_ctx.output.check_valid_format_type(desired_format):
        cli_ctx.invocation.data["output"] = desired_format
