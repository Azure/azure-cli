# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=protected-access

import argparse
import json
from knack.util import CLIError


class GetExtension(argparse._AppendAction):

    def __call__(self, parser, namespace, values, option_string=None):
        action = self.get_action(values, option_string)
        super().__call__(parser, namespace, action, option_string)

    def get_action(self, values, option_string):  # pylint: disable=no-self-use
        try:
            properties = {}
            for (k, v) in (x.split('=', 1) for x in values):
                if k == "isEnabled":
                    properties["is_enabled"] = v
                elif k == "name":
                    properties["name"] = v
                elif k == "additionalExtensionProperties":
                    try:
                        properties["additional_extension_properties"] = json.loads(v)
                    except Exception:
                        msg = "usage error: make sure that additionalExtensionProperties is valid escaped JSON," \
                              " use online tools to escape the JSON"
                        raise CLIError(msg)
            return dict(properties)
        except ValueError:
            raise CLIError('usage error: {} [KEY=VALUE ...]'.format(option_string))
