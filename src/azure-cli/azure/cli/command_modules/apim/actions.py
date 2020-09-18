# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import argparse

from knack.util import CLIError
from azure.mgmt.apimanagement.models import (ParameterContract)

# pylint:disable=protected-access, too-few-public-methods


class TemplateParameter(argparse._AppendAction):
    def __call__(self, parser, namespace, values, option_string=None):
        kwargs = {}
        for item in values:
            try:
                key, value = item.split('=', 1)
                kwargs[key] = value
            except ValueError:
                raise CLIError('usage error: {} KEY=VALUE [KEY=VALUE ...]'.format(option_string))

        super(TemplateParameter, self).__call__(parser, namespace, ParameterContract(**kwargs), option_string)
