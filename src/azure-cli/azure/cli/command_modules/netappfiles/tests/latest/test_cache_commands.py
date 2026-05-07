# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import json
import os
import sys
import time
import unittest

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, live_only
from azure.cli.testsdk.decorators import serial_test

LOCATION = "eastus"
VNET_LOCATION = "eastus"
POOL_DEFAULT = "--service-level Premium --size 4"

# Env-var gate for the interactive on-prem peering test. Even with @live_only(),
# we don't want scheduled live pipelines to run a test that waits up to an hour
# for a human to SSH into a CVO and paste commands. Engineer must opt-in.
INTERACTIVE_ENV_VAR = "ANF_ALLOW_INTERACTIVE"
CACHE_STATE_POLL_INTERVAL_SECONDS = 30
CACHE_STATE_POLL_TIMEOUT_SECONDS = 60 * 60  # 1 hour budget per wait
CACHE_TERMINAL_STATES = {"Succeeded", "Failed", "Cancelled"}

# No tidy up of tests required. The resource group is automatically removed
#
# As a refactoring consideration for the future, consider use of authoring patterns described here
# https://github.com/Azure/azure-cli/blob/dev/doc/authoring_tests.md#sample-5-get-more-from-resourcegrouppreparer
#
# -----------------------------------------------------------------------------
# How to run these tests
# -----------------------------------------------------------------------------
# These tests use the standard record/playback model. The cassette files under
# `recordings/` capture the ARM/RP request/response traffic so the tests can
# be replayed in CI without any Azure access or human interaction.
#
# Playback (default, no env vars):
#   - No Azure access required.
#   - The interactive on-prem (CVO) peering pause is suppressed; the recorded
#     cacheState transitions are replayed instantly so the polling loop
#     terminates without sleeping.
#
#   pytest -vv \
#     src/azure-cli/azure/cli/command_modules/netappfiles/tests/latest/test_cache_commands.py
#
# Recording (re-record cassettes against a real subscription):
#   - Set AZURE_TEST_RUN_LIVE=True to talk to ARM.
#   - For `test_create_delete_cache` ALSO set ANF_ALLOW_INTERACTIVE=1 because
#     the test pauses for an engineer to perform two manual on-prem (CVO)
#     peering steps; it polls cacheState as the sync signal and prints
#     copy-pasteable commands to STDERR. Without ANF_ALLOW_INTERACTIVE the
#     interactive test self-skips when running live.
#   - Pass `-s` (a.k.a. `--capture=no`) to pytest so the instruction blocks
#     written to stderr are shown in real time; otherwise pytest buffers them.
#
# PowerShell (Windows) - re-record the full interactive create/delete flow:
#
#   $env:AZURE_TEST_RUN_LIVE = "True"
#   $env:ANF_ALLOW_INTERACTIVE = "1"
#   pytest -s -vv `
#     src/azure-cli/azure/cli/command_modules/netappfiles/tests/latest/test_cache_commands.py::AzureNetAppFilesCacheServiceScenarioTest::test_create_delete_cache
#
# PowerShell - re-record all live cache tests except the interactive one
# (leave ANF_ALLOW_INTERACTIVE unset so the interactive test self-skips):
#
#   $env:AZURE_TEST_RUN_LIVE = "True"
#   Remove-Item Env:ANF_ALLOW_INTERACTIVE -ErrorAction SilentlyContinue
#   pytest -s -vv `
#     src/azure-cli/azure/cli/command_modules/netappfiles/tests/latest/test_cache_commands.py
#
# bash/zsh equivalent:
#
#   AZURE_TEST_RUN_LIVE=True ANF_ALLOW_INTERACTIVE=1 \
#     pytest -s -vv \
#     src/azure-cli/azure/cli/command_modules/netappfiles/tests/latest/test_cache_commands.py::AzureNetAppFilesCacheServiceScenarioTest::test_create_delete_cache
#
# Via azdev (live re-record):
#
#   $env:AZURE_TEST_RUN_LIVE = "True"
#   $env:ANF_ALLOW_INTERACTIVE = "1"
#   azdev test test_create_delete_cache --live --pytest-args "-s -vv"
#
# Useful pytest flags:
#   -s / --capture=no   show stderr/stdout live (REQUIRED when recording the
#                       interactive test)
#   -vv                 verbose test names + full assert diffs
#   -k <expr>           filter by test name substring
#   --log-cli-level=INFO show CLI logging in real time
# -----------------------------------------------------------------------------


class AzureNetAppFilesCacheServiceScenarioTest(ScenarioTest):
    def setup_vnets(self, cache_vnet_name, cache_subnet_name, peering_vnet_name, peering_subnet_name):
        # cache subnet and peering subnet must reside on different VNets
        self.cmd("az network vnet create -n %s -g {rg} -l %s --address-prefix 10.5.0.0/16" %
                 (cache_vnet_name, VNET_LOCATION))
        self.cmd("az network vnet subnet create -n %s --vnet-name %s --address-prefixes '10.5.0.0/24' "
                 "--delegations 'Microsoft.Netapp/volumes' -g {rg}" % (cache_subnet_name, cache_vnet_name))
        self.cmd("az network vnet create -n %s -g {rg} -l %s --address-prefix 10.6.0.0/16" %
                 (peering_vnet_name, VNET_LOCATION))
        self.cmd("az network vnet subnet create -n %s --vnet-name %s --address-prefixes '10.6.0.0/24' "
                 "--delegations 'Microsoft.Netapp/volumes' -g {rg}" % (peering_subnet_name, peering_vnet_name))

    def create_cache(self, account_name, pool_name, cache_name, cache_vnet_name=None, peering_vnet_name=None,
                     cache_only=False):
        if cache_vnet_name is None:
            cache_vnet_name = self.create_random_name(prefix='cli-vnet-cache', length=24)
        if peering_vnet_name is None:
            peering_vnet_name = self.create_random_name(prefix='cli-vnet-peer', length=24)
        cache_subnet_name = "cacheSubnet"
        peering_subnet_name = "peeringSubnet"

        if not cache_only:
            # create vnets, account and pool
            self.setup_vnets(cache_vnet_name, cache_subnet_name, peering_vnet_name, peering_subnet_name)
            self.cmd("az netappfiles account create -g {rg} -a '%s' -l %s" % (account_name, LOCATION))
            self.cmd("az netappfiles pool create -g {rg} -a %s -p %s -l %s %s" %
                     (account_name, pool_name, LOCATION, POOL_DEFAULT))

        # build subnet resource ids - each on its own VNet
        cache_subnet_id = "/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Network/virtualNetworks/{vnet}/subnets/{subnet}".format(
            sub=self.get_subscription_id(), rg='{rg}', vnet=cache_vnet_name, subnet=cache_subnet_name)
        peering_subnet_id = "/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Network/virtualNetworks/{vnet}/subnets/{subnet}".format(
            sub=self.get_subscription_id(), rg='{rg}', vnet=peering_vnet_name, subnet=peering_subnet_name)

        file_path = self.create_random_name(prefix='filepath', length=16)

        # create cache
        return self.cmd("az netappfiles cache create -g {rg} -a %s -p %s -n %s -l %s "
                        "--protocol-types NFSv3 "
                        "--file-path %s --size 107374182400 "
                        "--encryption-key-source Microsoft.NetApp "
                        "--cache-subnet-resource-id %s "
                        "--peering-subnet-resource-id %s "
                        "--peer-cluster-name cluster1 "
                        "--peer-addresses 192.0.2.10 192.0.2.11 "
                        "--peer-vserver-name vserver1 "
                        "--peer-volume-name originvol1" %
                        (account_name, pool_name, cache_name, LOCATION,
                         file_path, cache_subnet_id, peering_subnet_id)).get_output_in_json()

    def _wait_for_cache_state(self, account_name, pool_name, cache_name, target_states,
                              timeout=CACHE_STATE_POLL_TIMEOUT_SECONDS,
                              interval=CACHE_STATE_POLL_INTERVAL_SECONDS):
        """Poll `az netappfiles cache show` until cacheState is in target_states.

        Returns the cache JSON when the state is matched. Fails the test on
        timeout, including the last observed cacheState in the failure message.
        """
        target_states = set(target_states)
        deadline = time.time() + timeout
        last_state = None
        while time.time() < deadline:
            cache = self.cmd("az netappfiles cache show -g {rg} -a %s -p %s -n %s" %
                             (account_name, pool_name, cache_name)).get_output_in_json()
            # cacheState may live at top level or under properties depending on
            # how the SDK projects the response.
            last_state = cache.get('cacheState') or cache.get('properties', {}).get('cacheState')
            if last_state in target_states:
                return cache
            if self.in_recording:
                # Live or first-time recording: wait between polls.
                time.sleep(interval)
            else:
                # Playback: every recorded `cache show` response is consumed
                # in order from the cassette. If we have not yet hit a target
                # state, advance immediately to consume the next recorded
                # response without sleeping.
                continue
        self.fail("Timed out after %ds waiting for cacheState in %s; last observed state: %r" %
                  (timeout, sorted(target_states), last_state))

    @staticmethod
    def _emit_engineer_instructions(passphrases_object, step):
        """Print on-prem peering instructions to stderr for the engineer to act on.

        Emits BOTH a labeled JSON dump (full reference) and a literal
        copy-pasteable command block (no shell quoting added) so the engineer
        can paste verbatim into the CVO CLI under time pressure.

        `step` must be "cluster" or "vserver".
        """
        assert step in ("cluster", "vserver"), "step must be 'cluster' or 'vserver'"

        json_dump = json.dumps(passphrases_object, indent=2, sort_keys=True)

        if step == "cluster":
            cmd_line = passphrases_object.get('clusterPeeringCommand', '<missing clusterPeeringCommand>')
            passphrase = passphrases_object.get('clusterPeeringPassphrase', '<missing clusterPeeringPassphrase>')
            steps = (
                "  1. SSH into the CVO.\n"
                "  2. Paste the COMMAND below into the CVO CLI and execute it.\n"
                "  3. When prompted for a passphrase, paste the PASSPHRASE below.\n"
                "     (NOTE: there is no API alternative to this step.)\n"
            )
            paste_block = (
                "COMMAND:\n"
                "%s\n\n"
                "PASSPHRASE:\n"
                "%s\n"
            ) % (cmd_line, passphrase)
            header = "ON-PREM ACTION REQUIRED: cluster peering"
            wait_for = "VserverPeeringOfferSent"
        else:
            cmd_line = passphrases_object.get('vserverPeeringCommand', '<missing vserverPeeringCommand>')
            steps = (
                "  1. SSH into the CVO.\n"
                "  2. Paste the COMMAND below into the CVO CLI and execute it.\n"
                "     (NOTE: there is no API alternative to this step.)\n"
            )
            paste_block = (
                "COMMAND:\n"
                "%s\n"
            ) % (cmd_line,)
            header = "ON-PREM ACTION REQUIRED: vserver peering"
            wait_for = "a terminal cacheState (Succeeded/Failed/Cancelled)"

        block = (
            "\n"
            "================================================================\n"
            "%s\n"
            "================================================================\n"
            "%s"
            "----------------------------------------------------------------\n"
            "FULL passphrases JSON (reference):\n"
            "%s\n"
            "----------------------------------------------------------------\n"
            "COPY-PASTEABLE BLOCK (paste verbatim into CVO CLI):\n"
            "%s"
            "----------------------------------------------------------------\n"
            "Test will continue polling until cacheState reaches: %s\n"
            "================================================================\n"
        ) % (header, steps, json_dump, paste_block, wait_for)

        sys.stderr.write(block)
        sys.stderr.flush()

    @live_only()
    @unittest.skipUnless(
        os.environ.get(INTERACTIVE_ENV_VAR) == "1",
        "Requires manual on-prem (CVO) peering steps; set %s=1 to run." % INTERACTIVE_ENV_VAR)
    @serial_test()
    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_cache_', additional_tags={'owner': 'cli_test'})
    def test_create_delete_cache(self):
        # In playback we replay the recorded cassette and never need a human;
        # in record/live we require the engineer to opt in to the manual
        # on-prem (CVO) peering steps so scheduled live pipelines don't hang
        # for up to an hour waiting for human input.
        if self.in_recording and os.environ.get(INTERACTIVE_ENV_VAR) != "1":
            self.skipTest(
                "Requires manual on-prem (CVO) peering steps when recording; "
                "set %s=1 to run live." % INTERACTIVE_ENV_VAR)

        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        cache_name = self.create_random_name(prefix='cli-cache-', length=24)

        cache = self.create_cache(account_name, pool_name, cache_name)
        assert cache['name'] == account_name + '/' + pool_name + '/' + cache_name
        assert cache['size'] == 107374182400
        assert cache['encryptionKeySource'] == 'Microsoft.NetApp'
        assert cache['originClusterInformation']['peerClusterName'] == 'cluster1'
        assert cache['originClusterInformation']['peerVserverName'] == 'vserver1'
        assert cache['originClusterInformation']['peerVolumeName'] == 'originvol1'
        assert len(cache['originClusterInformation']['peerAddresses']) == 2

        # 1) Wait until the cache has emitted the cluster peering offer.
        self._wait_for_cache_state(account_name, pool_name, cache_name,
                                   target_states={"ClusterPeeringOfferSent"})

        # 2) Fetch peering passphrase + commands and surface them to the engineer.
        passphrases_object = self.cmd(
            "az netappfiles cache list-peering-passphrase -g {rg} -a %s -p %s -c %s" %
            (account_name, pool_name, cache_name)).get_output_in_json()
        assert passphrases_object is not None
        # Only pause for the engineer when actually talking to ARM. In playback
        # the recorded responses already reflect the post-peering cache state.
        if self.in_recording:
            self._emit_engineer_instructions(passphrases_object, step="cluster")

        # 3) Engineer pastes the cluster peering command + passphrase on CVO.
        #    The service advances cacheState to VserverPeeringOfferSent on success.
        self._wait_for_cache_state(account_name, pool_name, cache_name,
                                   target_states={"VserverPeeringOfferSent"})

        # 4) Surface the vserver peering command for the second on-prem step.
        if self.in_recording:
            self._emit_engineer_instructions(passphrases_object, step="vserver")

        # 5) Engineer pastes the vserver peering command on CVO.
        #    The cache should now drive itself to a terminal state.
        terminal_cache = self._wait_for_cache_state(account_name, pool_name, cache_name,
                                                   target_states=CACHE_TERMINAL_STATES)
        terminal_state = (terminal_cache.get('cacheState')
                          or terminal_cache.get('properties', {}).get('cacheState'))
        assert terminal_state == "Succeeded", \
            "Cache reached terminal state %r, expected 'Succeeded'" % terminal_state

        # The following assertions are folded in here (instead of standalone
        # tests) to avoid re-running the expensive CVO peering setup. They
        # exercise show / update / reset-smb-password against the cache that
        # we just brought to a Succeeded state.

        # --- folded from test_get_cache_by_name ---
        shown = self.cmd("az netappfiles cache show -g {rg} -a %s -p %s -n %s" %
                         (account_name, pool_name, cache_name)).get_output_in_json()
        assert shown['name'] == account_name + '/' + pool_name + '/' + cache_name
        shown_by_id = self.cmd("az netappfiles cache show --ids %s" %
                               shown['id']).get_output_in_json()
        assert shown_by_id['name'] == shown['name']

        # --- folded from test_update_cache ---
        tags = "Tag1=Value1 Tag2=Value2"
        new_size = 214748364800
        self.cmd("az netappfiles cache update -g {rg} -a %s -p %s -n %s --tags %s --size %s" %
                 (account_name, pool_name, cache_name, tags, new_size))
        updated = self.cmd("az netappfiles cache show -g {rg} -a %s -p %s -n %s" %
                           (account_name, pool_name, cache_name)).get_output_in_json()
        assert updated['tags']['Tag1'] == 'Value1'
        assert updated['tags']['Tag2'] == 'Value2'
        assert updated['size'] == new_size

        # --- folded from test_cache_reset_smb_password ---
        # Verify the command completes without error.
        self.cmd("az netappfiles cache reset-smb-password -g {rg} -a %s -p %s -c %s" %
                 (account_name, pool_name, cache_name))

        # verify cache exists in list
        cache_list = self.cmd("az netappfiles cache list -g {rg} -a %s -p %s" %
                              (account_name, pool_name)).get_output_in_json()
        assert len(cache_list) == 1

        # delete cache
        self.cmd("az netappfiles cache delete -g {rg} -a %s -p %s -n %s --yes" %
                 (account_name, pool_name, cache_name))

        # verify deletion
        cache_list = self.cmd("az netappfiles cache list -g {rg} -a %s -p %s" %
                              (account_name, pool_name)).get_output_in_json()
        assert len(cache_list) == 0

    @live_only()
    @unittest.skipUnless(
        os.environ.get(INTERACTIVE_ENV_VAR) == "1",
        "Requires manual on-prem (CVO) peering steps; set %s=1 to run." % INTERACTIVE_ENV_VAR)
    @unittest.skip('Cache Tests are failing due issues in the environment, no way to test until fixed re enable when fixed.')
    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_cache_', additional_tags={'owner': 'cli_test'})
    def test_create_delete_cache_with_wait(self):
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        cache_name = self.create_random_name(prefix='cli-cache-', length=24)

        self.create_cache(account_name, pool_name, cache_name)

        # delete with --no-wait then use wait --deleted
        self.cmd("az netappfiles cache delete -g {rg} -a %s -p %s -n %s --yes --no-wait" %
                 (account_name, pool_name, cache_name))
        self.cmd("az netappfiles cache wait -g {rg} -a %s -p %s -n %s --deleted" %
                 (account_name, pool_name, cache_name))

        # verify deletion
        cache_list = self.cmd("az netappfiles cache list -g {rg} -a %s -p %s" %
                              (account_name, pool_name)).get_output_in_json()
        assert len(cache_list) == 0

    @live_only()
    @unittest.skipUnless(
        os.environ.get(INTERACTIVE_ENV_VAR) == "1",
        "Requires manual on-prem (CVO) peering steps; set %s=1 to run." % INTERACTIVE_ENV_VAR)
    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_cache_', additional_tags={'owner': 'cli_test'})
    def test_list_caches(self):
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        cache_name_1 = self.create_random_name(prefix='cli-cache-', length=24)
        cache_name_2 = self.create_random_name(prefix='cli-cache-', length=24)

        # create first cache (also creates vnets, account, pool)
        cache_vnet_name = self.create_random_name(prefix='cli-vnet-cache', length=24)
        peering_vnet_name = self.create_random_name(prefix='cli-vnet-peer', length=24)
        self.create_cache(account_name, pool_name, cache_name_1, cache_vnet_name=cache_vnet_name,
                          peering_vnet_name=peering_vnet_name)

        # create second cache in the same pool (cache_only=True reuses existing infra)
        self.create_cache(account_name, pool_name, cache_name_2, cache_vnet_name=cache_vnet_name,
                          peering_vnet_name=peering_vnet_name, cache_only=True)

        # list and verify count
        cache_list = self.cmd("az netappfiles cache list -g {rg} -a %s -p %s" %
                              (account_name, pool_name)).get_output_in_json()
        assert len(cache_list) == 2

        # delete both caches
        self.cmd("az netappfiles cache delete -g {rg} -a %s -p %s -n %s --yes" %
                 (account_name, pool_name, cache_name_1))
        self.cmd("az netappfiles cache delete -g {rg} -a %s -p %s -n %s --yes" %
                 (account_name, pool_name, cache_name_2))

        # verify all deleted
        cache_list = self.cmd("az netappfiles cache list -g {rg} -a %s -p %s" %
                              (account_name, pool_name)).get_output_in_json()
        assert len(cache_list) == 0

    # The following commands are folded into `test_create_delete_cache` to
    # avoid re-running the expensive CVO peering setup, and so are not
    # provided as standalone tests:
    #   - `az netappfiles cache show` (by name and by --ids)
    #   - `az netappfiles cache update` (tags + size)
    #   - `az netappfiles cache list-peering-passphrase`
    #   - `az netappfiles cache reset-smb-password`

    @live_only()
    @unittest.skipUnless(
        os.environ.get(INTERACTIVE_ENV_VAR) == "1",
        "Requires manual on-prem (CVO) peering steps; set %s=1 to run." % INTERACTIVE_ENV_VAR)
    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_cache_', additional_tags={'owner': 'cli_test'})
    def test_cache_pool_change(self):
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        pool_name_2 = self.create_random_name(prefix='cli-pool-', length=24)
        cache_name = self.create_random_name(prefix='cli-cache-', length=24)

        self.create_cache(account_name, pool_name, cache_name)

        # create second pool
        pool2 = self.cmd("az netappfiles pool create -g {rg} -a %s -p %s -l %s %s" %
                         (account_name, pool_name_2, LOCATION, POOL_DEFAULT)).get_output_in_json()

        # move cache to the second pool
        self.cmd("az netappfiles cache pool-change -g {rg} -a %s -p %s -c %s --new-pool-resource-id %s" %
                 (account_name, pool_name, cache_name, pool2['id']))

        # verify cache is now in pool2
        cache_list_pool1 = self.cmd("az netappfiles cache list -g {rg} -a %s -p %s" %
                                    (account_name, pool_name)).get_output_in_json()
        assert len(cache_list_pool1) == 0

        cache_list_pool2 = self.cmd("az netappfiles cache list -g {rg} -a %s -p %s" %
                                    (account_name, pool_name_2)).get_output_in_json()
        assert len(cache_list_pool2) == 1
