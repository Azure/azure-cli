# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.auth.util import decode_access_token
from azure.cli.core._profile import _TENANT_LEVEL_ACCOUNT_NAME
from azure.cli.testsdk import LiveScenarioTest


class SubscriptionFilterScenarioTest(LiveScenarioTest):
    """Live scenario tests for --skip-subscription-discovery and --subscription on az login.

    Prerequisites:
      - Run with a user account that has access to at least two subscriptions.
      - Each test performs an initial interactive login to discover tenant/subscription info,
        then re-logins with the feature flags under test.
    """

    def setUp(self):
        super().setUp()
        self.cmd('az account clear')

    def tearDown(self):
        self.cmd('az account clear')

    def _login_and_get_account_info(self):
        """Login interactively and return (tenant_id, subscription_id, subscription_name) of a real subscription.

        Skips tenant-level accounts to avoid passing a tenant ID where a subscription ID is expected.
        The test account must have access to at least one real subscription.
        """
        self.cmd('az login')
        accounts = self.cmd('az account list').get_output_in_json()
        real_sub = next(a for a in accounts if a.get('name') != _TENANT_LEVEL_ACCOUNT_NAME)
        return real_sub['tenantId'], real_sub['id'], real_sub['name']

    def test_skip_discovery_fast_path(self):
        """
        az login --tenant T --skip-subscription-discovery --subscription S

        Fast path: only the specified subscription is fetched via a direct API call.
        It should be set as the default subscription.
        """
        tenant_id, sub_id, _ = self._login_and_get_account_info()
        self.cmd('az account clear')

        self.kwargs.update({'tenant': tenant_id, 'sub_id': sub_id})

        # Re-login with skip-discovery + specific subscription
        self.cmd('az login --tenant {tenant} --skip-subscription-discovery --subscription {sub_id}')

        # The specified subscription should be the default
        account = self.cmd('az account show').get_output_in_json()
        self.assertEqual(account['id'], sub_id)
        self.assertEqual(account['tenantId'], tenant_id)
        self.assertTrue(account['isDefault'])

        # Only the specified subscription should be present (no full discovery)
        accounts = self.cmd('az account list').get_output_in_json()
        self.assertEqual(len(accounts), 1)
        self.assertEqual(accounts[0]['id'], sub_id)

    def test_skip_discovery_bare_mode(self):
        """
        az login --tenant T --skip-subscription-discovery

        Bare mode: no ARM subscription discovery at all. Only a tenant-level account
        should exist, suitable for tenant-level operations like 'az ad'.
        """
        tenant_id, _, _ = self._login_and_get_account_info()
        self.cmd('az account clear')

        self.kwargs['tenant'] = tenant_id

        # Re-login in bare mode (no subscription discovery)
        self.cmd('az login --tenant {tenant} --skip-subscription-discovery')

        # Should have only a tenant-level account
        accounts = self.cmd('az account list').get_output_in_json()
        self.assertEqual(len(accounts), 1)
        self.assertEqual(accounts[0]['id'], tenant_id)
        self.assertEqual(accounts[0]['name'], _TENANT_LEVEL_ACCOUNT_NAME)

    def test_login_with_default_subscription(self):
        """
        az login --subscription S

        Full subscription discovery, but the specified subscription is set as the default.
        """
        _, sub_id, _ = self._login_and_get_account_info()
        self.cmd('az account clear')

        self.kwargs['sub_id'] = sub_id

        # Re-login with full discovery + explicit default subscription
        self.cmd('az login --subscription {sub_id}')

        # Full discovery should return more than one subscription
        accounts = self.cmd('az account list').get_output_in_json()
        self.assertGreater(len(accounts), 1, "Test requires access to more than one subscription")

        # The specified subscription should be the default
        account = self.cmd('az account show').get_output_in_json()
        self.assertEqual(account['id'], sub_id)
        self.assertTrue(account['isDefault'])

    def test_skip_discovery_inaccessible_subscription(self):
        """
        az login --tenant T --skip-subscription-discovery --subscription BAD --allow-no-subscriptions

        When the requested subscription is inaccessible, --allow-no-subscriptions should
        fall back to a tenant-level account with a warning instead of erroring.
        """
        tenant_id, _, _ = self._login_and_get_account_info()
        self.cmd('az account clear')

        self.kwargs.update({
            'tenant': tenant_id,
            'bad_sub': '00000000-0000-0000-0000-000000000000'
        })

        # Inaccessible subscription with --allow-no-subscriptions: warn and fall back
        self.cmd('az login --tenant {tenant} --skip-subscription-discovery '
                 '--subscription {bad_sub} --allow-no-subscriptions')

        # Should fall back to tenant-level account
        accounts = self.cmd('az account list').get_output_in_json()
        self.assertEqual(len(accounts), 1)
        self.assertEqual(accounts[0]['name'], _TENANT_LEVEL_ACCOUNT_NAME)

    def test_skip_discovery_inaccessible_subscription_no_allow(self):
        """
        az login --tenant T --skip-subscription-discovery --subscription BAD

        When the requested subscription is inaccessible and --allow-no-subscriptions
        is NOT set, should raise an error.
        """
        tenant_id, _, _ = self._login_and_get_account_info()
        self.cmd('az account clear')

        self.kwargs.update({
            'tenant': tenant_id,
            'bad_sub': '00000000-0000-0000-0000-000000000000'
        })

        with self.assertRaises(Exception):
            self.cmd('az login --tenant {tenant} --skip-subscription-discovery '
                     '--subscription {bad_sub}')

    def test_skip_discovery_preserves_prior_subscriptions(self):
        """
        Login normally first (full discovery), then re-login with --skip-subscription-discovery
        --subscription S. Prior subscriptions from the first login should be preserved
        in azureProfile.json (merged, not replaced).
        """
        tenant_id, sub_id, _ = self._login_and_get_account_info()

        # Full discovery should have returned more than one subscription
        subs_before = self.cmd('az account list').get_output_in_json()
        self.assertGreater(len(subs_before), 1, "Test requires access to more than one subscription")

        self.kwargs.update({'tenant': tenant_id, 'sub_id': sub_id})

        # Re-login with skip-discovery + specific subscription (should merge, not replace)
        self.cmd('az login --tenant {tenant} --skip-subscription-discovery --subscription {sub_id}')

        # The specified subscription should be the default
        account = self.cmd('az account show').get_output_in_json()
        self.assertEqual(account['id'], sub_id)

        # Prior subscriptions should still be in the profile (merged)
        subs_after = self.cmd('az account list').get_output_in_json()
        before_ids = {s['id'] for s in subs_before}
        after_ids = {s['id'] for s in subs_after}
        self.assertTrue(before_ids.issubset(after_ids),
                        "Prior subscriptions should be preserved after skip-discovery re-login")

    def test_login_subscription_by_name(self):
        """
        az login --subscription "Sub Name"

        Full discovery with --subscription matching by display name (case-insensitive).
        """
        _, _, sub_name = self._login_and_get_account_info()
        self.cmd('az account clear')

        self.kwargs['sub_name'] = sub_name

        # Re-login using subscription name
        self.cmd('az login --subscription "{sub_name}"')

        # Full discovery should return more than one subscription
        accounts = self.cmd('az account list').get_output_in_json()
        self.assertGreater(len(accounts), 1, "Test requires access to more than one subscription")

        # The named subscription should be the default
        account = self.cmd('az account show').get_output_in_json()
        self.assertEqual(account['name'], sub_name)
        self.assertTrue(account['isDefault'])

    def test_login_nonexistent_subscription_raises_error(self):
        """
        az login --subscription "nonexistent"

        Full discovery where --subscription doesn't match any discovered subscription
        should raise an error.
        """
        with self.assertRaises(Exception):
            self.cmd('az login --subscription "nonexistent-sub-00000000"')

    def test_skip_discovery_bare_mode_allows_ad_operations(self):
        """
        az login --tenant T --skip-subscription-discovery

        Bare mode should still allow tenant-level operations like 'az ad' to work,
        even without any subscription.
        """
        tenant_id, _, _ = self._login_and_get_account_info()
        self.cmd('az account clear')

        self.kwargs['tenant'] = tenant_id

        # Re-login in bare mode
        self.cmd('az login --tenant {tenant} --skip-subscription-discovery')

        # Should have only a tenant-level account
        accounts = self.cmd('az account list').get_output_in_json()
        self.assertEqual(len(accounts), 1)
        self.assertEqual(accounts[0]['name'], _TENANT_LEVEL_ACCOUNT_NAME)

        # Tenant-level operation should work
        # Use 'az account get-access-token' to verify the credential is functional
        # (avoid 'az ad' which may be blocked by Conditional Access policies)
        result = self.cmd('az account get-access-token').get_output_in_json()
        self.assertTrue(result.get('accessToken'), "accessToken should not be empty")

    def test_skip_discovery_fast_path_validates_token(self):
        """
        az login --tenant T --skip-subscription-discovery --subscription S

        After fast-path login, the credential should be functional for ARM calls
        against the fetched subscription.
        """
        tenant_id, sub_id, _ = self._login_and_get_account_info()
        self.cmd('az account clear')

        self.kwargs.update({'tenant': tenant_id, 'sub_id': sub_id})

        # Re-login with fast path
        self.cmd('az login --tenant {tenant} --skip-subscription-discovery --subscription {sub_id}')

        # Verify the token claims match the expected tenant
        result = self.cmd('az account get-access-token').get_output_in_json()
        self.assertIn('accessToken', result)
        self.assertIn('expiresOn', result)

        decoded = decode_access_token(result['accessToken'])
        self.assertEqual(decoded['tid'], tenant_id)

    def test_skip_discovery_requires_tenant(self):
        """
        az login --skip-subscription-discovery (without --tenant)

        Should fail with a clear error message requiring --tenant.
        """
        with self.assertRaises(Exception):
            self.cmd('az login --skip-subscription-discovery')

    def test_skip_discovery_rejects_subscription_name(self):
        """
        az login --tenant T --skip-subscription-discovery --subscription "My Sub"

        --skip-subscription-discovery requires a subscription GUID (not a name),
        because it uses GET /subscriptions/{id} directly.
        """
        tenant_id, _, sub_name = self._login_and_get_account_info()
        self.cmd('az account clear')

        self.kwargs.update({'tenant': tenant_id, 'sub_name': sub_name})

        with self.assertRaises(Exception):
            self.cmd('az login --tenant {tenant} --skip-subscription-discovery '
                     '--subscription "{sub_name}"')

    def test_full_discovery_with_tenant(self):
        """
        az login --tenant T

        Full discovery scoped to a specific tenant. Should list all subscriptions
        accessible in that tenant only.
        """
        tenant_id, _, _ = self._login_and_get_account_info()
        self.cmd('az account clear')

        self.kwargs['tenant'] = tenant_id

        # Re-login with specific tenant (full discovery within that tenant)
        self.cmd('az login --tenant {tenant}')

        # All returned subscriptions should belong to this tenant
        accounts = self.cmd('az account list').get_output_in_json()
        real_subs = [a for a in accounts if a.get('name') != _TENANT_LEVEL_ACCOUNT_NAME]
        self.assertGreater(len(real_subs), 1, "Test requires access to more than one subscription")
        for sub in real_subs:
            self.assertEqual(sub['tenantId'], tenant_id)

    def test_account_set_after_skip_discovery(self):
        """
        Login with --skip-subscription-discovery for two subscriptions sequentially.
        After the second login, both should be in the profile and the second should be default.
        Then 'az account set' should switch between them.
        """
        # Full discovery to get two real subscription IDs
        self.cmd('az login')
        accounts = self.cmd('az account list').get_output_in_json()
        real_subs = [a for a in accounts if a.get('name') != _TENANT_LEVEL_ACCOUNT_NAME]
        self.assertGreater(len(real_subs), 1, "Test requires access to more than one subscription")

        tenant_id = real_subs[0]['tenantId']
        sub_id_1 = real_subs[0]['id']
        sub_id_2 = real_subs[1]['id']
        self.cmd('az account clear')

        self.kwargs.update({'tenant': tenant_id, 'sub1': sub_id_1, 'sub2': sub_id_2})

        # Login with skip-discovery for sub 1
        self.cmd('az login --tenant {tenant} --skip-subscription-discovery --subscription {sub1}')

        # Should have only sub 1
        accounts = self.cmd('az account list').get_output_in_json()
        self.assertEqual(len(accounts), 1)
        self.assertEqual(accounts[0]['id'], sub_id_1)

        # Login with skip-discovery for sub 2 (should merge with sub 1)
        self.cmd('az login --tenant {tenant} --skip-subscription-discovery --subscription {sub2}')

        # Should have both subs, sub 2 is default
        accounts = self.cmd('az account list').get_output_in_json()
        self.assertEqual(len(accounts), 2)
        account = self.cmd('az account show').get_output_in_json()
        self.assertEqual(account['id'], sub_id_2)
        self.assertTrue(account['isDefault'])

        # Bare mode login (should add a tenant-level account, merging with existing subs)
        self.cmd('az login --tenant {tenant} --skip-subscription-discovery')

        # Should have 3: sub 1 + sub 2 + tenant-level account
        accounts = self.cmd('az account list').get_output_in_json()
        self.assertEqual(len(accounts), 3)
        tenant_accounts = [a for a in accounts if a['name'] == _TENANT_LEVEL_ACCOUNT_NAME]
        self.assertEqual(len(tenant_accounts), 1)
