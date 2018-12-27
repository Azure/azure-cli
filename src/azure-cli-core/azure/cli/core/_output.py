# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import knack.output
from knack.events import EVENT_INVOKER_POST_PARSE_ARGS
from azure.cli.core.azlogging import AzCliLogging


class AzOutputProducer(knack.output.OutputProducer):
    def __init__(self, cli_ctx=None):
        super(AzOutputProducer, self).__init__(cli_ctx)
        super(AzOutputProducer, self)._FORMAT_DICT['yaml'] = self.format_yaml
        self.cli_ctx.register_event(EVENT_INVOKER_POST_PARSE_ARGS, AzOutputProducer.handle_mute_argument)
        self.is_muted = False

    def out(self, obj, formatter=None, out_file=None):  # pylint: disable=no-self-use
        if not self.is_muted:
            super(AzOutputProducer, self).out(obj, formatter=formatter, out_file=out_file)

    def check_valid_format_type(self, format_type):
        return format_type in self._FORMAT_DICT

    @staticmethod
    def format_yaml(obj):
        import yaml
        return yaml.safe_dump(obj.result, default_flow_style=False)

    @staticmethod
    def handle_mute_argument(cli_ctx, **kwargs):
        args = kwargs.get('args')
        # check if the output producer should be muted
        if getattr(args, AzCliLogging.MUTE_ARG_DEST, False):
            cli_ctx.output.is_muted = True


def get_output_format(cli_ctx):
    return cli_ctx.invocation.data.get("output", None)


def set_output_format(cli_ctx, desired_format):
    if cli_ctx.output.check_valid_format_type(desired_format):
        cli_ctx.invocation.data["output"] = desired_format
