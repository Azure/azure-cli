# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import argparse
from collections import defaultdict
from azure.cli.core.azclierror import ValidationError


class AddSecretAuthInfo(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        action = self.get_action(values, option_string)
        namespace.secret_auth_info = action

    def get_action(self, values, option_string):  # pylint: disable=no-self-use
        try:
            properties = defaultdict(list)
            for (k, v) in (x.split('=', 1) for x in values):
                properties[k].append(v)
            properties = dict(properties)
        except ValueError:
            raise ValidationError('Usage error: {} [KEY=VALUE ...]'.format(option_string))
        d = {}
        for k in properties:
            kl = k.lower()
            v = properties[k]
            if kl == 'name':
                d['name'] = v[0]
            elif kl == 'secret':
                d['secret_info'] = {
                    'secret_type': 'rawValue',
                    'value': v[0]
                }
            else:
                raise ValidationError('Unsupported Key {} is provided for parameter secret_auth_info. '
                                      'All possible keys are: name, secret'.format(k))
        if len(d) != 2:
            raise ValidationError('Required keys missing for parameter --secret. All possible keys are: name, secret')
        d['auth_type'] = 'secret'
        return d


class AddSecretAuthInfoAuto(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        action = self.get_action(values, option_string)
        namespace.secret_auth_info = action

    def get_action(self, values, option_string):  # pylint: disable=no-self-use
        try:
            properties = defaultdict(list)
            for (k, v) in (x.split('=', 1) for x in values):
                properties[k].append(v)
            properties = dict(properties)
        except ValueError:
            raise ValidationError('Usage error: {} [KEY=VALUE ...]'.format(option_string))
        d = {}
        for k in properties:
            raise ValidationError('Unsupported Key {} is provided for parameter --auto-secret')
        d['auth_type'] = 'secret'
        return d


class AddUserAssignedIdentityAuthInfo(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        action = self.get_action(values, option_string)
        namespace.user_identity_auth_info = action

    def get_action(self, values, option_string):  # pylint: disable=no-self-use
        try:
            properties = defaultdict(list)
            for (k, v) in (x.split('=', 1) for x in values):
                properties[k].append(v)
            properties = dict(properties)
        except ValueError:
            raise ValidationError('usage error: {} [KEY=VALUE ...]'.format(option_string))
        d = {}
        for k in properties:
            kl = k.lower()
            v = properties[k]
            if kl == 'client-id':
                d['client_id'] = v[0]
            elif kl == 'subs-id':
                d['subscription_id'] = v[0]
            else:
                raise ValidationError('Unsupported Key {} is provided for parameter --user-identity. All '
                                      'possible keys are: client-id, subs-id'.format(k))
        if len(d) != 2:
            raise ValidationError('Required keys missing for parameter --user-identity. '
                                  'All possible keys are: client-id, subs-id')
        d['auth_type'] = 'userAssignedIdentity'
        return d


class AddSystemAssignedIdentityAuthInfo(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        action = self.get_action(values, option_string)
        namespace.system_identity_auth_info = action

    def get_action(self, values, option_string):  # pylint: disable=no-self-use
        try:
            properties = defaultdict(list)
            for (k, v) in (x.split('=', 1) for x in values):
                properties[k].append(v)
            properties = dict(properties)
        except ValueError:
            raise ValidationError('Usage error: {} [KEY=VALUE ...]'.format(option_string))
        d = {}
        for k in properties:
            raise ValidationError('Unsupported Key {} is provided for parameter --system-identity')
        d['auth_type'] = 'systemAssignedIdentity'
        return d


class AddServicePrincipalAuthInfo(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        action = self.get_action(values, option_string)
        namespace.service_principal_auth_info_secret = action

    def get_action(self, values, option_string):  # pylint: disable=no-self-use
        try:
            properties = defaultdict(list)
            for (k, v) in (x.split('=', 1) for x in values):
                properties[k].append(v)
            properties = dict(properties)
        except ValueError:
            raise ValidationError('Usage error: {} [KEY=VALUE ...]'.format(option_string))
        d = {}
        for k in properties:
            kl = k.lower()
            v = properties[k]
            if kl == 'client-id':
                d['client_id'] = v[0]
            elif kl == 'object-id':
                d['principal_id'] = v[0]
            elif kl == 'secret':
                d['secret'] = v[0]
            else:
                raise ValidationError('Unsupported Key {} is provided for parameter --service-principal. All possible '
                                      'keys are: client-id, object-id, secret'.format(k))
        if 'client_id' not in d or 'secret' not in d:
            raise ValidationError('Required keys missing for parameter --service-principal. '
                                  'Required keys are: client-id, secret')
        if 'principal_id' not in d:
            from ._utils import run_cli_cmd
            output = run_cli_cmd('az ad sp show --id {}'.format(d['client_id']))
            if output:
                d['principal_id'] = output.get('id')
            else:
                raise ValidationError('Could not resolve object-id from the given client-id: {}. Please '
                                      'confirm the client-id and provide the object-id (Enterprise Application) '
                                      'of the service principal, by using --service-principal client-id=XX '
                                      'object-id=XX secret=XX'.format(d['client_id']))

        d['auth_type'] = 'servicePrincipalSecret'
        return d
