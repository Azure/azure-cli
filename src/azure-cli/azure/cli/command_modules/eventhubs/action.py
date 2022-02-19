# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
# pylint: disable=too-many-lines
# pylint: disable=inconsistent-return-statements
# pylint: disable=protected-access
# pylint: disable=too-many-locals

import argparse


class AlertAddEncryption(argparse._AppendAction):
    def __call__(self, parser, namespace, values, option_string=None):
        action = self.get_action(values, option_string)
        super(AlertAddEncryption, self).__call__(parser, namespace, action, option_string)

    def get_action(self, values, option_string):  # pylint: disable=no-self-use
        from azure.mgmt.eventhub.v2021_06_01_preview.models import KeyVaultProperties
        from azure.mgmt.eventhub.v2021_06_01_preview.models import UserAssignedIdentityProperties
        from azure.cli.core.azclierror import InvalidArgumentValueError

        keyVaultObject = KeyVaultProperties()

        for (k, v) in (x.split('=', 1) for x in values):
            if k == 'key-name':
                keyVaultObject.key_name = v
            elif k == 'key-vault-uri':
                keyVaultObject.key_vault_uri = v
                if keyVaultObject.key_vault_uri.endswith('/'):
                    keyVaultObject.key_vault_uri = keyVaultObject.key_vault_uri[:-1]
            elif k == 'key-version':
                keyVaultObject.key_version = v
            elif k == 'user-assigned-identity':
                keyVaultObject.identity = UserAssignedIdentityProperties()
                keyVaultObject.identity.user_assigned_identity = v
                if keyVaultObject.identity.user_assigned_identity.endswith('/'):
                    keyVaultObject.identity.user_assigned_identity = keyVaultObject.identity.user_assigned_identity[:-1]
            else:
                raise InvalidArgumentValueError("Invalid Argument:'{}' Only allowed arguments are 'key-name, key-vault-uri, key-version and user-assigned-identity'".format(option_string))

        if (keyVaultObject.key_name is None) or (keyVaultObject.key_vault_uri is None):
            raise CLIError('key-name and key-vault-uri are mandatory properties')

        if keyVaultObject.key_version is None:
            keyVaultObject.key_version = ''

        return keyVaultObject
