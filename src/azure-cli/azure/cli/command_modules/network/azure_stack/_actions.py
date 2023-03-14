# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from collections import defaultdict

import argparse
from azure.cli.core.azclierror import UnrecognizedArgumentError


def _split(param):
    return param.split(',')


class AddMappingRequest(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        action = self.get_action(values, option_string)
        namespace.request = action

    def get_action(self, values, option_string):  # pylint: disable=no-self-use
        try:
            properties = defaultdict(list)
            for (k, v) in (x.split('=', 1) for x in values):
                properties[k].append(v)
            properties = dict(properties)
        except ValueError:
            raise UnrecognizedArgumentError('Usage error: {} [KEY=VALUE ...]'.format(option_string))
        d = {}
        for k in properties:
            kl = k.lower()
            v = properties[k]
            if kl == 'ip':
                d['ip_address'] = v[0]
            elif kl == 'nic':
                d['ip_configuration'] = v[0]
            else:
                raise UnrecognizedArgumentError('key error: key must be one of {ip, nic}.')
        return d
