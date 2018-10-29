# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import knack.output


class AzOutputProducer(knack.output.OutputProducer):
    def __init__(self, cli_ctx=None):
        super(AzOutputProducer, self).__init__(cli_ctx)
        super(AzOutputProducer, self)._FORMAT_DICT['yaml'] = self.format_yaml

    @staticmethod
    def format_yaml(obj):
        import yaml
        return yaml.safe_dump(obj.result, default_flow_style=False)

    def check_valid_format_type(self, format_type):
        return format_type in self._FORMAT_DICT


def get_output_format(cli_ctx):
    return cli_ctx.invocation.data.get("output", None)


def set_output_format(cli_ctx, desired_format):
    if cli_ctx.output.check_valid_format_type(desired_format):
        cli_ctx.invocation.data["output"] = desired_format
