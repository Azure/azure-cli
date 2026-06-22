# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import errno
import sys

import knack.output
from knack.util import CommandResultItem


class AzOutputProducer(knack.output.OutputProducer):

    _LF_ONLY_FORMATTERS = {
        knack.output.format_tsv
    }

    def check_valid_format_type(self, format_type):
        return format_type in self._FORMAT_DICT

    def out(self, obj, formatter=None, out_file=None):
        if formatter not in self._LF_ONLY_FORMATTERS:
            return super().out(obj, formatter=formatter, out_file=out_file)

        if not isinstance(obj, CommandResultItem):
            raise TypeError('Expected {} got {}'.format(CommandResultItem.__name__, type(obj)))

        output = formatter(obj)
        stream = out_file or sys.stdout

        try:
            binary_stream = getattr(stream, 'buffer', None)
            if binary_stream is not None:
                binary_stream.write(output.encode(stream.encoding or 'utf-8'))
            else:
                stream.write(output)
        except IOError as ex:
            if ex.errno != errno.EPIPE:
                raise
        except UnicodeEncodeError:
            knack.output.logger.warning("Unable to encode the output with %s encoding. Unsupported characters are discarded.",
                                        stream.encoding)
            fallback_output = output.encode('ascii', 'ignore')
            if binary_stream is not None:
                binary_stream.write(fallback_output)
            else:
                stream.write(fallback_output.decode('utf-8', 'ignore'))


def get_output_format(cli_ctx):
    return cli_ctx.invocation.data.get("output", None)


def set_output_format(cli_ctx, desired_format):
    if cli_ctx.output.check_valid_format_type(desired_format):
        cli_ctx.invocation.data["output"] = desired_format
