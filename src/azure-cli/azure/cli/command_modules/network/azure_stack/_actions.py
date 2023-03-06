# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from collections import defaultdict

import argparse
from knack.util import CLIError
from azure.cli.core.azclierror import UnrecognizedArgumentError
from ._validators import read_base_64_file
from ._util import enum_check


# pylint: disable=protected-access
class AddBackendAddressCreate(argparse._AppendAction):
    def __call__(self, parser, namespace, values, option_string=None):
        action = self.get_action(values, option_string)
        super(AddBackendAddressCreate, self).__call__(parser, namespace, action, option_string)

    def get_action(self, values, option_string):  # pylint: disable=no-self-use
        try:
            properties = defaultdict(list)
            for (k, v) in (x.split('=', 1) for x in values):
                properties[k].append(v)
            properties = dict(properties)
        except ValueError:
            raise CLIError('usage error: {} [KEY=VALUE ...]'.format(option_string))
        d = {}
        for k in properties:
            kl = k.lower()
            v = properties[k]
            if kl == 'name':
                d['name'] = v[0]
            elif kl == 'ip-address':
                d['ip_address'] = v[0]
            elif kl == 'subnet':
                d['subnet'] = v[0]
            else:
                raise CLIError('key error: key must be one of name, ip-address and subnet.')
        return d


def _split(param):
    return param.split(',')


class NatRuleCreate(argparse._AppendAction):
    def __call__(self, parser, namespace, values, option_string=None):
        action = self.get_action(values, option_string)
        super(NatRuleCreate, self).__call__(parser, namespace, action, option_string)

    def get_action(self, values, option_string):  # pylint: disable=no-self-use
        try:
            properties = defaultdict(list)
            for (k, v) in (x.split('=', 1) for x in values):
                properties[k].append(v)
            properties = dict(properties)
        except ValueError:
            raise UnrecognizedArgumentError('usage error: {} [KEY=VALUE ...]'.format(option_string))
        d = {}
        for k in properties:
            kl = k.lower()
            v = properties[k]
            if kl == 'type':
                d['type'] = enum_check(v[0], ['Static', 'Dynamic'])
            elif kl == 'name':
                d['name'] = v[0]
            elif kl == 'mode':
                d['mode'] = enum_check(v[0], ['EgressSnat', 'IngressSnat'])
            elif kl == 'internal-mappings':
                d['internal_mappings'] = _split(v[0])
            elif kl == 'external-mappings':
                d['external_mappings'] = _split(v[0])
            elif kl == 'ip-config-id':
                d['ip_config_id'] = v[0]
            else:
                raise UnrecognizedArgumentError('key error: key must be one of type, mode, internal-mappings,'
                                                'external-mappings, ip-config-id')
        return d


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
