# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=too-many-lines
# pylint: disable=protected-access
# pylint: disable=line-too-long
# pylint: disable=no-self-use

import argparse


class AlertAddEncryption(argparse._AppendAction):
    def __call__(self, parser, namespace, values, option_string=None):
        action = self.get_action(values, option_string)
        super().__call__(parser, namespace, action, option_string)

    def get_action(self, values, option_string):
        from azure.cli.core.azclierror import InvalidArgumentValueError
        from azure.cli.core import CLIError

        keyVaultObject = {}
        for (k, v) in (x.split('=', 1) for x in values):
            if k == 'key-name':
                keyVaultObject["key_name"] = v
            elif k == 'key-vault-uri':
                keyVaultObject["key_vault_uri"] = v
                if keyVaultObject["key_vault_uri"].endswith('/'):
                    keyVaultObject["key_vault_uri"] = keyVaultObject["key_vault_uri"][:-1]
            elif k == 'key-version':
                keyVaultObject["key_version"] = v
            elif k == 'user-assigned-identity':
                keyVaultObject["user_assigned_identity"] = v
                if keyVaultObject["user_assigned_identity"].endswith('/'):
                    keyVaultObject["user_assigned_identity"] = keyVaultObject["user_assigned_identity"][:-1]
            else:
                raise InvalidArgumentValueError("Invalid Argument for:'{}' Only allowed arguments are 'key-name, key-vault-uri, key-version and user-assigned-identity'".format(option_string))

        if (keyVaultObject["key_name"] is None) or (keyVaultObject["key_vault_uri"] is None):
            raise CLIError('key-name and key-vault-uri are mandatory properties')

        if "key_version" not in keyVaultObject:
            keyVaultObject["key_version"] = ''

        if "user_assigned_identity" not in keyVaultObject:
            keyVaultObject["user_assigned_identity"] = None

        return keyVaultObject


class AlertAddVirtualNetwork(argparse._AppendAction):
    def __call__(self, parser, namespace, values, option_string=None):
        action = self.get_action(values, option_string)
        super().__call__(parser, namespace, action, option_string)

    def get_action(self, values, option_string):  # pylint: disable=no-self-use
        from azure.cli.core import CLIError
        from azure.cli.core.azclierror import InvalidArgumentValueError
        VirtualNetworkList = {}
        for (k, v) in (x.split('=', 1) for x in values):
            if k == 'id':
                VirtualNetworkList["id"] = v
            elif k == 'ignore-missing-endpoint':
                if v == "true" or v == "True" or v == "TRUE":
                    VirtualNetworkList["ignore_missing_endpoint"] = True
                else:
                    VirtualNetworkList["ignore_missing_endpoint"] = False
            else:
                raise InvalidArgumentValueError("Invalid Argument for:'{}' Only allowed arguments are 'id, ignore-missing-endpoint'".format(option_string))

        if VirtualNetworkList["id"] is None:
            raise CLIError('id is mandatory properties')

        return VirtualNetworkList


class AlertAddIpRule(argparse._AppendAction):
    def __call__(self, parser, namespace, values, option_string=None):
        action = self.get_action(values, option_string)
        super().__call__(parser, namespace, action, option_string)

    def get_action(self, values, option_string):  # pylint: disable=no-self-use
        from azure.cli.core import CLIError
        from azure.cli.core.azclierror import InvalidArgumentValueError
        IpRuleList = {}
        for (k, v) in (x.split('=', 1) for x in values):
            if k == 'ip-address':
                IpRuleList["ip-address"] = v
            elif k == 'action':
                IpRuleList["action"] = v
            else:
                raise InvalidArgumentValueError(
                    "Invalid Argument for:'{}' Only allowed arguments are 'ip-address, action'".format(option_string))

        if IpRuleList["ip-address"] is None:
            raise CLIError('ip-address is mandatory properties')

        if "action" not in IpRuleList:
            IpRuleList["action"] = 'Allow'
        return IpRuleList


class AlertAddlocation(argparse._AppendAction):
    def __call__(self, parser, namespace, values, option_string=None):
        action = self.get_action(values, option_string)
        super().__call__(parser, namespace, action, option_string)

    def get_action(self, values, option_string):  # pylint: disable=no-self-use
        from azure.cli.core import CLIError
        from azure.cli.core.azclierror import InvalidArgumentValueError
        LocationObject = {}
        for (k, v) in (x.split('=', 1) for x in values):
            if k == 'location-name':
                LocationObject["location_name"] = v
            elif k == 'role-type':
                LocationObject["role_type"] = v
            elif k == 'cluster-arm-id':
                LocationObject["cluster_arm_id"] = v
            else:
                raise InvalidArgumentValueError(
                    "Invalid Argument for:'{}' Only allowed arguments are 'location-name, role-type and cluster-arm-id'".format(
                        option_string))

        if (LocationObject["location_name"] is None) or (LocationObject["role_type"] is None):
            raise CLIError('location-name and role-type are mandatory properties')

        if "cluster_arm_id" not in LocationObject:
            LocationObject["cluster_arm_id"] = ''

        return LocationObject
