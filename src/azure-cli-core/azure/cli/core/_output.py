# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import errno
import sys

import knack.output
from knack.util import CommandResultItem


class AzOutputProducer(knack.output.OutputProducer):
    _TSV_FORMATTER = knack.output.format_tsv

    def check_valid_format_type(self, format_type):
        return format_type in self._FORMAT_DICT

    def out(self, obj, formatter=None, out_file=None):
        if formatter != type(self)._TSV_FORMATTER:
            return super().out(obj, formatter=formatter, out_file=out_file)

        if not isinstance(obj, CommandResultItem):
            raise TypeError('Expected CommandResultItem, got {}'.format(type(obj)))

        output = formatter(obj)
        stream = out_file or sys.stdout
        binary_stream = getattr(stream, 'buffer', None)
        encoding = stream.encoding or 'utf-8'

        try:
            if binary_stream is not None:
                binary_stream.write(output.encode(encoding))
            else:
                stream.write(output)
        except IOError as ex:
            if ex.errno != errno.EPIPE:
                raise
        except UnicodeEncodeError:
            knack.output.logger.warning("Unable to encode the output with %s encoding. Unsupported characters are discarded.",
                                        encoding)
            fallback_output = output.encode('ascii', 'ignore').decode('ascii')
            if binary_stream is not None:
                binary_stream.write(fallback_output.encode('ascii'))
            else:
                stream.write(fallback_output)


def get_output_format(cli_ctx):
    return cli_ctx.invocation.data.get("output", None)


def set_output_format(cli_ctx, desired_format):
    if cli_ctx.output.check_valid_format_type(desired_format):
        cli_ctx.invocation.data["output"] = desired_format
