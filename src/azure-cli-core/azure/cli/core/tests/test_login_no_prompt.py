# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest
from unittest import mock

from azure.cli.core._profile import Profile
from azure.cli.core.mock import DummyCli


class TestNoPromptRouting(unittest.TestCase):

    @mock.patch('azure.cli.core._profile.SubscriptionFinder')
    @mock.patch('azure.cli.core._profile._create_identity_instance')
    @mock.patch('azure.cli.core._profile.can_launch_browser')
    def test_profile_login_silent_login_does_not_attempt_interactive_fallback(self, browser_mock,
                                                                 identity_factory, finder_factory):
        identity = identity_factory.return_value
        identity.login_silently.return_value = {'username': 'user@example.com', 'tenant_id': 'tenant'}
        finder = finder_factory.return_value
        finder.tenants = []
        cli = DummyCli()
        profile = Profile(cli_ctx=cli, storage={'subscriptions': []})

        with mock.patch.object(profile, '_build_tenant_level_accounts', return_value=[]), \
             mock.patch.object(profile, '_normalize_properties', return_value=[]), \
             mock.patch.object(profile, '_set_subscriptions'):
            profile.login(True, None, None, False, 'tenant',
                          no_prompt=True, skip_subscription_discovery=True,
                          allow_no_subscriptions=True)

        identity.login_silently.assert_called_once_with(scopes=mock.ANY, claims_challenge=None)
        identity.login_with_auth_code.assert_not_called()
        identity.login_with_device_code.assert_not_called()
        browser_mock.assert_not_called()
