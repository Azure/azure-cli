# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest
from unittest import mock

from azure.cli.command_modules.role.custom import _resolve_role_id

# pylint: disable=line-too-long


class TestRoleCustomCommands(unittest.TestCase):

    def test_resolve_role_id(self, ):
        mock_client = mock.Mock()
        mock_client.config.subscription_id = '123'
        test_role_id = 'b24988ac-6180-42a0-ab88-20f738123456'

        # action(using a logical name)
        result = _resolve_role_id(test_role_id, 'foobar', mock_client)

        # assert
        self.assertEqual('/subscriptions/123/providers/Microsoft.Authorization/roleDefinitions/{}'.format(test_role_id), result)

        # action (using a full id)
        test_full_id = '/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272123456/providers/microsoft.authorization/roleDefinitions/5370bbf4-6b73-4417-969b-8f2e6e123456'
        self.assertEqual(test_full_id, _resolve_role_id(test_full_id, 'foobar', mock_client))
