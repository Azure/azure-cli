# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import knack.output


class AzOutputProducer(knack.output.OutputProducer):
    def __init__(self, cli_ctx=None):
        super(AzOutputProducer, self).__init__(cli_ctx)
        additional_formats = {
            'yaml': self.format_yaml,
            'none': self.format_none
        }
        super(AzOutputProducer, self)._FORMAT_DICT.update(additional_formats)

    @staticmethod
    def format_yaml(obj):
        from yaml import (safe_dump, representer)
        import json

        try:
            return safe_dump(obj.result, default_flow_style=False)
        except representer.RepresenterError:
            # yaml.safe_dump fails when obj.result is an OrderedDict. knack's --query implementation converts the result to an OrderedDict. https://github.com/microsoft/knack/blob/af674bfea793ff42ae31a381a21478bae4b71d7f/knack/query.py#L46. # pylint: disable=line-too-long
            return safe_dump(json.loads(json.dumps(obj.result)), default_flow_style=False)

    @staticmethod
    def format_none(_):
        return ""

    def check_valid_format_type(self, format_type):
        return format_type in self._FORMAT_DICT


def get_output_format(cli_ctx):
    return cli_ctx.invocation.data.get("output", None)


def set_output_format(cli_ctx, desired_format):
    if cli_ctx.output.check_valid_format_type(desired_format):
        cli_ctx.invocation.data["output"] = desired_format
