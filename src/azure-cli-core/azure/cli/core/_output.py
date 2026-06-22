# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import errno
import sys

import knack.output


class AzOutputProducer(knack.output.OutputProducer):

    def check_valid_format_type(self, format_type):
        return format_type in self._FORMAT_DICT

    def out(self, obj, formatter=None, out_file=None):
        if formatter != self._FORMAT_DICT['tsv']:
            return super().out(obj, formatter=formatter, out_file=out_file)

        output = formatter(obj)
        stream = out_file or sys.stdout
        binary_stream = getattr(stream, 'buffer', None)
        if binary_stream is None:
            return super().out(obj, formatter=formatter, out_file=out_file)
        encoding = stream.encoding or 'utf-8'

        try:
            binary_stream.write(output.encode(encoding))
        except IOError as ex:
            if ex.errno != errno.EPIPE:
                raise
        except UnicodeEncodeError:
            knack.output.logger.warning("Unable to encode the output with %s encoding. Unsupported characters are discarded.",
                                        encoding)
            binary_stream.write(output.encode('ascii', 'ignore'))


def get_output_format(cli_ctx):
    return cli_ctx.invocation.data.get("output", None)


def set_output_format(cli_ctx, desired_format):
    if cli_ctx.output.check_valid_format_type(desired_format):
        cli_ctx.invocation.data["output"] = desired_format
