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
