# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import sys

import knack.output


class AzOutputProducer(knack.output.OutputProducer):

    def check_valid_format_type(self, format_type):
        return format_type in self._FORMAT_DICT

    def out(self, obj, formatter=None, out_file=None):
        file = out_file or sys.stdout
        if get_output_format(self.cli_ctx) == "tsv":
            if hasattr(file, "reconfigure"):
                file.reconfigure(newline="\n")
        return super().out(obj, formatter=formatter, out_file=file)


def get_output_format(cli_ctx):
    return cli_ctx.invocation.data.get("output", None)


def set_output_format(cli_ctx, desired_format):
    if cli_ctx.output.check_valid_format_type(desired_format):
        cli_ctx.invocation.data["output"] = desired_format
