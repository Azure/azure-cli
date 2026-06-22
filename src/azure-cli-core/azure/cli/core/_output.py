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
        tsv_formatter = self._FORMAT_DICT['tsv']
        is_tsv_formatter = formatter == tsv_formatter
        if not is_tsv_formatter:
            return super().out(obj, formatter=formatter, out_file=out_file)

        output = formatter(obj)
        stream = out_file or sys.stdout
        binary_stream = getattr(stream, 'buffer', None)
        if binary_stream is None:
            knack.output.logger.warning("TSV output stream does not expose a binary buffer; falling back to default writer.")
            return super().out(obj, formatter=formatter, out_file=out_file)
        encoding = stream.encoding or 'utf-8'

        try:
            encoded_output = output.encode(encoding)
            binary_stream.write(encoded_output)
        except IOError as ex:
            if ex.errno != errno.EPIPE:
                raise
            return
        except UnicodeEncodeError:
            knack.output.logger.warning("Unable to encode TSV output with %s encoding. Unsupported characters are discarded.",
                                        encoding)
            binary_stream.write(output.encode('ascii', 'ignore'))


def get_output_format(cli_ctx):
    return cli_ctx.invocation.data.get("output", None)


def set_output_format(cli_ctx, desired_format):
    if cli_ctx.output.check_valid_format_type(desired_format):
        cli_ctx.invocation.data["output"] = desired_format
