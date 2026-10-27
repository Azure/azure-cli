# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

import time

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, JMESPathCheck
from azure.cli.testsdk.scenario_tests import AllowLargeResponse


class SecurityVaSqlScenarioTest(ScenarioTest):
    """End-to-end scenario tests for ``az security va sql ...``.

    Each ``*_lifecycle`` test exercises the full happy-path flow against a single
    resource type. The flow covers every command in the ``security va sql`` tree
    except the deprecated ``baseline set`` alias (covered by the negative test).
    """

    @AllowLargeResponse(size_kb=4096)
    @ResourceGroupPreparer(name_prefix='cli_test_va_sql_paas_', location='eastus')
    def test_security_va_sql_paas_lifecycle(self, resource_group):
        """PaaS path: Azure SQL Server + Database.

        Steps (matching RESUME_HERE.md plan):
          1. settings create
          2. settings show
          3. settings update (Disabled)
          4. settings show     (verify Disabled)
          4b. settings update  (re-enable so we can scan)
          5. scans initiate-scan  (blocking LRO -- implicitly exercises scan-operation-result show internally)
          6. scans show --scan-id latest
          7. baseline add --latest-scan true
          8. baseline list
          9. baseline create --rule-id X
          10. baseline show
          11. results list
          12. results show --rule-id X        (preferred alias)
          13. results show --scan-result-id X (legacy alias on the same call)
          14. baseline delete
          15. results show                    (after baseline removed)
          16. scans list
          17. settings delete
        """
        self.kwargs.update({
            'srv': self.create_random_name('vasqlsrv', 20),
            'db': self.create_random_name('vasqldb', 20),
        })

        # ---- Resource setup ----------------------------------------------------------
        # The DS-SQLVA_Playground subscription (and any sub under the
        # CnAIOrchestrationServicePublicCorpprod management group) is governed by the
        # `SafeSec-SQLSr-OptIn-V2-0` policy assignment, which denies SQL server creation
        # unless `--enable-ad-only-auth` is set. We therefore create the server with the
        # signed-in user (the test runner) as the Entra-only admin -- no SQL password.
        # A second deny-policy at the same MG level
        # (`[CESEC][NonProduction] Deny SQL Servers with Public Networks Access Enabled`)
        # blocks server creation unless the RG carries the tag
        # `AllowSqlServersWithAllNetworksEnabled` (any value, since the policy checks
        # `Exists`). We add that tag here before creating the server. The VA scan
        # service reaches the SQL server over the public path via the
        # "Allow Azure Services" firewall rule below, so we cannot just set
        # `--public-network-access Disabled` as an alternative escape hatch.
        admin = self.cmd('ad signed-in-user show').get_output_in_json()
        self.kwargs['admin_upn'] = admin.get('userPrincipalName') or admin.get('mail')
        self.kwargs['admin_oid'] = admin['id']

        self.cmd('group update -n {rg} --tags AllowSqlServersWithAllNetworksEnabled=true')

        server = self.cmd(
            'sql server create -g {rg} -n {srv} '
            '--enable-ad-only-auth '
            '--external-admin-principal-type User '
            '--external-admin-name "{admin_upn}" '
            '--external-admin-sid {admin_oid}'
        ).get_output_in_json()
        # Allow Azure services so the VA service can reach the server.
        self.cmd(
            'sql server firewall-rule create -g {rg} --server {srv} '
            '--name AllowAzureServices --start-ip-address 0.0.0.0 --end-ip-address 0.0.0.0'
        )
        self.cmd('sql db create -g {rg} --server {srv} -n {db} --service-objective S0')
        # Two distinct scopes for the VA commands (2026-04-01-preview):
        #   - `srv_id`: server scope -- used by `security va sql {create,show,update,delete}` (settings singleton)
        #   - `db_id` : database scope -- used by `scans`, `baseline`, and `results`
        self.kwargs['srv_id'] = server['id']
        self.kwargs['db_id'] = '{0}/databases/{1}'.format(server['id'], self.kwargs['db'])

        # ---- Step 1: settings create -------------------------------------------------
        self.cmd(
            'security va sql create --resource-id {srv_id} --state Enabled',
            checks=[
                JMESPathCheck('name', 'default'),
                JMESPathCheck('properties.state', 'Enabled'),
            ],
        )

        # ---- Step 2: settings show ---------------------------------------------------
        self.cmd(
            'security va sql show --resource-id {srv_id}',
            checks=[
                JMESPathCheck('name', 'default'),
                JMESPathCheck('properties.state', 'Enabled'),
            ],
        )

        # ---- Step 3: settings update -> Disabled -------------------------------------
        self.cmd(
            'security va sql update --resource-id {srv_id} --state Disabled',
            checks=[JMESPathCheck('properties.state', 'Disabled')],
        )

        # ---- Step 4: settings show (verify Disabled) ---------------------------------
        self.cmd(
            'security va sql show --resource-id {srv_id}',
            checks=[JMESPathCheck('properties.state', 'Disabled')],
        )

        # ---- Step 4b: re-enable so the scan can run ---------------------------------
        self.cmd(
            'security va sql update --resource-id {srv_id} --state Enabled',
            checks=[JMESPathCheck('properties.state', 'Enabled')],
        )

        # ---- Step 5: initiate scan (blocking LRO) -----------------------------------
        # The LRO poller hits the same endpoint as `scan-operation-result show`
        # internally, so this single call covers both commands. NOTE: the
        # response is the LRO *operation* result (its `name` is the operationId,
        # NOT a scan id), so we don't capture scan_id from here -- we get it
        # from `scans show --scan-id latest` below.
        op_result = self.cmd(
            'security va sql scans initiate-scan --resource-id {db_id}'
        ).get_output_in_json()
        assert op_result, 'initiate-scan should return an operation result once polling completes'

        # ---- Step 6: scans show ------------------------------------------------------
        # `latest` is a server-side alias resolving to the most recent scan.
        # The `scans/{scanId}` GET endpoint can briefly return
        # `ResultsAreNotAvailableYet` (404) right after the LRO completes, so
        # we retry that specific transient error with a small backoff. Any
        # other failure is propagated immediately.
        scans_show_cmd = 'security va sql scans show --resource-id {db_id} --scan-id latest'
        result = None
        for attempt in range(8):  # up to ~160s of waiting
            try:
                result = self.cmd(scans_show_cmd)
                break
            except Exception as ex:  # pylint: disable=broad-except
                msg = str(ex)
                is_transient = (
                    'ResultsAreNotAvailableYet' in msg
                    or 'Results are not available yet' in msg
                )
                if attempt < 7 and is_transient:
                    time.sleep(20)
                    continue
                raise
        data = result.get_output_in_json()
        assert data.get('name'), 'scans show should return a record with a name (the scan id)'
        assert data.get('properties', {}).get('totalRulesCount', 0) >= 1, \
            'scan record should report at least one rule'
        # Canonical scan id for downstream calls (also matches what `latest` resolves to).
        self.kwargs['scan_id'] = data['name']

        # ---- Step 7: baseline add --latest-scan true (bulk) -------------------------
        bulk = self.cmd(
            'security va sql baseline add --resource-id {db_id} --latest-scan true'
        ).get_output_in_json()
        # `baseline add` is a bulk POST returning a {value: [...]} envelope.
        # In a defensive form, accept either shape (some azure-cli versions
        # unwrap, some don't).
        if isinstance(bulk, dict):
            bulk_list = bulk.get('value') or []
        else:
            bulk_list = bulk or []
        assert len(bulk_list) >= 1, \
            'baseline add --latest-scan true should return at least one baselined rule'

        # ---- Step 8: baseline list ---------------------------------------------------
        # Azure CLI's `list` commands unwrap the {value: [...]} envelope and
        # return a plain list, so iterate directly.
        baselines = self.cmd(
            'security va sql baseline list --resource-id {db_id}'
        ).get_output_in_json()
        assert isinstance(baselines, list) and len(baselines) >= 1, \
            'baseline list should return entries after bulk add'
        # Pick the first rule for single-rule operations below.
        self.kwargs['rule_id'] = baselines[0]['name']

        # ---- Step 9: baseline create (single rule, from latest scan) ----------------
        # Using --latest-scan rather than --results avoids guessing the rule's
        # expected-results schema (each rule has its own column shape) and keeps
        # the test recording stable across rule sets. The mutex with --results
        # is exercised by `test_security_va_sql_negative`.
        # NOTE: JMESPathCheck does NOT run `.format()` on the expected value,
        # so we must resolve `{rule_id}` to its actual value here (and below).
        rule_id = self.kwargs['rule_id']
        self.cmd(
            'security va sql baseline create --resource-id {db_id} '
            '--rule-id {rule_id} --latest-scan true',
            checks=[JMESPathCheck('name', rule_id)],
        )

        # ---- Step 10: baseline show --------------------------------------------------
        self.cmd(
            'security va sql baseline show --resource-id {db_id} --rule-id {rule_id}',
            checks=[
                JMESPathCheck('name', rule_id),
            ],
        )

        # ---- Step 11: results list -------------------------------------------------
        results = self.cmd(
            'security va sql results list --resource-id {db_id} --scan-id latest'
        ).get_output_in_json()
        assert isinstance(results, list) and len(results) >= 1, \
            'results list should return scan results'

        # ---- Step 12: results show via --rule-id (preferred alias) -------------------
        self.cmd(
            'security va sql results show --resource-id {db_id} '
            '--scan-id latest --rule-id {rule_id}',
            checks=[JMESPathCheck('properties.ruleMetadata.ruleId', rule_id)],
        )

        # ---- Step 13: results show via --scan-result-id (legacy alias) --------------
        # Same call, different option name. Both must work after the alias change.
        self.cmd(
            'security va sql results show --resource-id {db_id} '
            '--scan-id latest --scan-result-id {rule_id}',
            checks=[JMESPathCheck('properties.ruleMetadata.ruleId', rule_id)],
        )

        # ---- Step 14: baseline delete ------------------------------------------------
        self.cmd(
            'security va sql baseline delete --resource-id {db_id} --rule-id {rule_id} --yes'
        )
        # Sanity: show should now 404 (or return without a baseline section).
        self.cmd(
            'security va sql baseline show --resource-id {db_id} --rule-id {rule_id}',
            expect_failure=True,
        )

        # ---- Step 15: results show after baseline removed ----------------------------
        # We don't assert the adjusted status (it depends on the rule's real results);
        # just verify the call still succeeds.
        self.cmd(
            'security va sql results show --resource-id {db_id} '
            '--scan-id latest --rule-id {rule_id}',
            checks=[JMESPathCheck('properties.ruleMetadata.ruleId', rule_id)],
        )

        # ---- Step 16: scans list -----------------------------------------------------
        scans = self.cmd(
            'security va sql scans list --resource-id {db_id}'
        ).get_output_in_json()
        assert isinstance(scans, list) and len(scans) >= 1, \
            'scans list should include at least the scan we initiated'

        # ---- Step 17: settings delete ------------------------------------------------
        self.cmd('security va sql delete --resource-id {srv_id} --yes')
        # After delete the resource is not removed; service flips state to
        # "Disabled" and resets creationTime. Verify the state transition.
        self.cmd(
            'security va sql show --resource-id {srv_id}',
            checks=[self.check('properties.state', 'Disabled')],
        )

    @AllowLargeResponse(size_kb=4096)
    @ResourceGroupPreparer(name_prefix='cli_test_va_sql_dbname_', location='eastus')
    def test_security_va_sql_paas_dbname_form(self, resource_group):
        """PaaS path exercising the ``--database-name`` query-string form.

        For database-scoped commands (scans / baseline / results), the new API
        accepts two URL shapes:

          1. ``--resource-id /sub/.../servers/{srv}/databases/{db}``
             (DB embedded in the resource id -- covered by ``*_lifecycle``)

          2. ``--resource-id /sub/.../servers/{srv} --database-name {db}``
             (server-level URL with a ``?databaseName=`` query string -- the
             ONLY way to assess system databases like ``master``)

        This test covers form 2 end-to-end. Each command below uses ``srv_id``
        (NOT ``db_id``) plus ``--database-name``, so we exercise the
        ``serialize_query_param("databaseName", ...)`` path in the codegen.
        """
        self.kwargs.update({
            'srv': self.create_random_name('vasqlsrv', 20),
            'db': self.create_random_name('vasqldb', 20),
        })

        # ---- Resource setup (mirrors test_security_va_sql_paas_lifecycle) ----------
        admin = self.cmd('ad signed-in-user show').get_output_in_json()
        self.kwargs['admin_upn'] = admin.get('userPrincipalName') or admin.get('mail')
        self.kwargs['admin_oid'] = admin['id']

        self.cmd('group update -n {rg} --tags AllowSqlServersWithAllNetworksEnabled=true')

        server = self.cmd(
            'sql server create -g {rg} -n {srv} '
            '--enable-ad-only-auth '
            '--external-admin-principal-type User '
            '--external-admin-name "{admin_upn}" '
            '--external-admin-sid {admin_oid}'
        ).get_output_in_json()
        self.cmd(
            'sql server firewall-rule create -g {rg} --server {srv} '
            '--name AllowAzureServices --start-ip-address 0.0.0.0 --end-ip-address 0.0.0.0'
        )
        self.cmd('sql db create -g {rg} --server {srv} -n {db} --service-objective S0')
        self.kwargs['srv_id'] = server['id']

        # ---- Enable VA at the server (settings call, no --database-name needed) ----
        self.cmd(
            'security va sql create --resource-id {srv_id} --state Enabled',
            checks=[JMESPathCheck('properties.state', 'Enabled')],
        )

        # ---- scans initiate-scan via --database-name -------------------------------
        # Blocking LRO; implicitly exercises scan-operation-result polling on the
        # server+dbname URL shape.
        self.cmd(
            'security va sql scans initiate-scan --resource-id {srv_id} '
            '--database-name {db}'
        )

        # ---- scans show via --database-name (with backoff on transient 404) -------
        scans_show_cmd = (
            'security va sql scans show --resource-id {srv_id} '
            '--database-name {db} --scan-id latest'
        )
        result = None
        for attempt in range(8):
            try:
                result = self.cmd(scans_show_cmd)
                break
            except Exception as ex:  # pylint: disable=broad-except
                msg = str(ex)
                is_transient = (
                    'ResultsAreNotAvailableYet' in msg
                    or 'Results are not available yet' in msg
                )
                if attempt < 7 and is_transient:
                    time.sleep(20)
                    continue
                raise
        data = result.get_output_in_json()
        assert data.get('name'), 'scans show should return a scan record with a name'

        # ---- baseline add via --database-name --------------------------------------
        bulk = self.cmd(
            'security va sql baseline add --resource-id {srv_id} '
            '--database-name {db} --latest-scan true'
        ).get_output_in_json()
        bulk_list = bulk.get('value') if isinstance(bulk, dict) else (bulk or [])
        assert bulk_list, 'baseline add via --database-name should return baselined rules'

        # ---- baseline list via --database-name -------------------------------------
        baselines = self.cmd(
            'security va sql baseline list --resource-id {srv_id} --database-name {db}'
        ).get_output_in_json()
        assert isinstance(baselines, list) and len(baselines) >= 1, \
            'baseline list via --database-name should return entries'
        self.kwargs['rule_id'] = baselines[0]['name']
        rule_id = self.kwargs['rule_id']

        # ---- baseline show via --database-name -------------------------------------
        self.cmd(
            'security va sql baseline show --resource-id {srv_id} '
            '--database-name {db} --rule-id {rule_id}',
            checks=[JMESPathCheck('name', rule_id)],
        )

        # ---- results list via --database-name --------------------------------------
        results = self.cmd(
            'security va sql results list --resource-id {srv_id} '
            '--database-name {db} --scan-id latest'
        ).get_output_in_json()
        assert isinstance(results, list) and len(results) >= 1, \
            'results list via --database-name should return scan results'

        # ---- results show via --database-name --------------------------------------
        self.cmd(
            'security va sql results show --resource-id {srv_id} '
            '--database-name {db} --scan-id latest --rule-id {rule_id}',
            checks=[JMESPathCheck('properties.ruleMetadata.ruleId', rule_id)],
        )

        # ---- baseline delete via --database-name -----------------------------------
        self.cmd(
            'security va sql baseline delete --resource-id {srv_id} '
            '--database-name {db} --rule-id {rule_id} --yes'
        )

        # ---- Cleanup: disable VA on the server -------------------------------------
        self.cmd('security va sql delete --resource-id {srv_id} --yes')

    @AllowLargeResponse(size_kb=4096)
    def test_security_va_sql_arc_lifecycle(self):
        """Arc-enabled SQL path (IaaS-flavor) against a *pre-existing* resource.

        Arc-enabled SQL Server uses a different resource hierarchy than Azure SQL
        PaaS but the same Microsoft.Security extension routes apply::

          srv_id = /subscriptions/.../Microsoft.HybridCompute/machines/{arc}/sqlServers/{srv}
          db_id  = {srv_id}/databases/{db}

        On Arc, **the following commands are NOT supported** by the RP and return
        404 -- so they are deliberately excluded from this test:

          * ``security va sql {create,show,update,delete}`` -- settings singleton
          * ``security va sql scans initiate-scan``         -- scans are
                                                              auto-scheduled by
                                                              the Arc SQL agent
                                                              (MicrosoftDefenderForSQL
                                                              extension)
          * ``security va sql scans scan-operation-result show`` -- no on-demand
                                                                    scan to poll

        Read-only and baseline mutation flows ARE supported. This test
        therefore exercises:

          * scans (show via ``--scan-id latest`` + list)
          * results (list + show via both --rule-id and --scan-result-id)
          * baseline (create + show + delete on a *single* rule that is NOT
            already baselined, so we never touch the user's existing baselines)

        Setup: this test targets a fixed real resource (the agent must be
        installed and reporting scans). We do NOT use ``ResourceGroupPreparer``
        -- the RG is pre-existing and we never create or delete any Arc/SQL
        infra. The only mutation is creating then deleting one baseline entry.

        Re-recording: requires ``az account set --subscription
        cca24ec8-99b5-4aa7-9ff6-486e886f304c`` and the galLaptop Arc SQL agent
        to be reporting at least one completed scan. After recording, anonymize
        the subscription id in the cassette (see paas_lifecycle for the
        recipe).
        """
        # Use ``self.get_subscription_id()`` rather than hardcoding the real
        # subscription id: during live recording it returns the currently
        # active subscription (the user must ``az account set --subscription
        # cca24ec8-99b5-4aa7-9ff6-486e886f304c`` first), and during replay it
        # returns the testsdk's mock subscription (matching the anonymized
        # cassette). Hardcoding the real sub would break replay because the
        # cassette URLs are anonymized.
        srv_id = (
            '/subscriptions/{0}'
            '/resourceGroups/ggoldshtein'
            '/providers/Microsoft.HybridCompute/machines/galLaptop'
            '/sqlServers/SQLEXPRESS'
        ).format(self.get_subscription_id())
        self.kwargs.update({
            'srv_id': srv_id,
            'db_id': srv_id + '/databases/master',
        })

        # ---- Step 1: scans show --scan-id latest -----------------------------------
        scan = self.cmd(
            'security va sql scans show --resource-id {db_id} --scan-id latest'
        ).get_output_in_json()
        assert scan.get('name'), 'Arc scans show should return a scan record with a name'
        assert scan.get('properties', {}).get('totalRulesCount', 0) >= 1, \
            'Arc scan record should report at least one rule'
        self.kwargs['scan_id'] = scan['name']

        # ---- Step 2: scans list ----------------------------------------------------
        scans = self.cmd(
            'security va sql scans list --resource-id {db_id}'
        ).get_output_in_json()
        assert isinstance(scans, list) and len(scans) >= 1, \
            'Arc scans list should include at least the latest scan'

        # ---- Step 3: snapshot pre-existing baselines (so we can avoid them) -------
        # NOTE: the service returns a 404 ``NoBaseline`` when zero baselines
        # exist on the DB (instead of an empty list). The aaz codegen surfaces
        # that as ``ResourceNotFoundError``. We treat it as "empty set" here.
        try:
            existing_baselines = self.cmd(
                'security va sql baseline list --resource-id {db_id}'
            ).get_output_in_json()
        except Exception as ex:  # pylint: disable=broad-except
            if 'NoBaseline' in str(ex) or 'No baseline have been found' in str(ex):
                existing_baselines = []
            else:
                raise
        if not isinstance(existing_baselines, list):
            existing_baselines = []
        existing_rule_ids = {b['name'] for b in existing_baselines if 'name' in b}

        # ---- Step 4: results list --------------------------------------------------
        results = self.cmd(
            'security va sql results list --resource-id {db_id} --scan-id latest'
        ).get_output_in_json()
        assert isinstance(results, list) and len(results) >= 1, \
            'Arc results list should return entries for the latest scan'
        # Pick the first rule that:
        #   1. Has status == 'Finding' (NonFinding/Failed rules have empty
        #      queryResults; the service returns 400 ``EmptyBaseline`` when you
        #      try to create a baseline from --latest-scan on such a rule), AND
        #   2. Does NOT already have a baseline on this machine -- this
        #      guarantees the baseline-create/delete pair is a round-trip and
        #      we never overwrite the user's real baselines.
        candidate = next(
            (r for r in results
             if r.get('name')
             and r.get('properties', {}).get('status') == 'Finding'
             and r['name'] not in existing_rule_ids),
            None,
        )
        assert candidate is not None, \
            ('Could not find a scan rule with status="Finding" that is not '
             'already baselined; the test DB has no baselineable rules')
        rule_id = candidate['name']
        self.kwargs['rule_id'] = rule_id

        # ---- Step 5: results show via --rule-id (preferred alias) -----------------
        self.cmd(
            'security va sql results show --resource-id {db_id} '
            '--scan-id latest --rule-id {rule_id}',
            checks=[JMESPathCheck('properties.ruleMetadata.ruleId', rule_id)],
        )

        # ---- Step 6: results show via --scan-result-id (legacy alias) -------------
        self.cmd(
            'security va sql results show --resource-id {db_id} '
            '--scan-id latest --scan-result-id {rule_id}',
            checks=[JMESPathCheck('properties.ruleMetadata.ruleId', rule_id)],
        )

        # ---- Step 7: baseline create (single rule, from latest scan) --------------
        # Using --latest-scan instead of --results avoids guessing the rule's
        # expected-results schema and keeps the test recording stable.
        self.cmd(
            'security va sql baseline create --resource-id {db_id} '
            '--rule-id {rule_id} --latest-scan true',
            checks=[JMESPathCheck('name', rule_id)],
        )

        # ---- Step 8: baseline show (verify created) -------------------------------
        self.cmd(
            'security va sql baseline show --resource-id {db_id} --rule-id {rule_id}',
            checks=[JMESPathCheck('name', rule_id)],
        )

        # ---- Step 9: baseline delete (CLEANUP -- restore the user's prior state) --
        self.cmd(
            'security va sql baseline delete --resource-id {db_id} '
            '--rule-id {rule_id} --yes'
        )

        # ---- Step 10: baseline show after delete -- should 404 --------------------
        self.cmd(
            'security va sql baseline show --resource-id {db_id} --rule-id {rule_id}',
            expect_failure=True,
        )

        # ---- Step 11: results show after baseline removed -------------------------
        # The same scan results call still returns 200 (the underlying scan data
        # is unchanged); just verifies the read path is independent of baseline
        # state.
        self.cmd(
            'security va sql results show --resource-id {db_id} '
            '--scan-id latest --rule-id {rule_id}',
            checks=[JMESPathCheck('properties.ruleMetadata.ruleId', rule_id)],
        )

    def test_security_va_sql_negative(self):
        """Negative-path coverage that doesn't need any cloud resources.

        - The argument validators run during argparse, before any HTTP call, so
          a fake ``--resource-id`` is sufficient to trigger them.
        - The deprecated ``baseline set`` alias should still be registered and
          should emit a deprecation warning (visible in --help).

        NOTE on brace escaping: ``self.cmd()`` runs ``cmd.format(**self.kwargs)``
        on the command string, so literal ``{`` / ``}`` (from JSON object syntax)
        must be doubled to survive the format call.
        """
        self.kwargs.update({
            'fake_rid': ('/subscriptions/00000000-0000-0000-0000-000000000000'
                         '/resourceGroups/x/providers/Microsoft.Sql/servers/s/databases/d'),
        })

        # 1. --latest-scan and --results are mutually exclusive on `baseline create`.
        #    NOTE: ExecutionResult doesn't capture stderr (testsdk limitation -- see
        #    azure.cli.testsdk.base.ExecutionResult._in_process_execute), so we cannot
        #    assert on the validator message text. expect_failure=True is sufficient
        #    because the validator runs in pre_operations() before any HTTP call, so
        #    the failure cannot come from the fake resource-id reaching the wire.
        self.cmd(
            'security va sql baseline create --resource-id "{fake_rid}" '
            '--rule-id VA1234 --latest-scan true '
            '--results "[[\\"a\\",\\"b\\"]]"',
            expect_failure=True,
        )

        # 2. Same for `baseline add`.
        #    `baseline add --results` takes a {rule_id: rows} JSON object, hence
        #    the doubled braces around "VA1234".
        self.cmd(
            'security va sql baseline add --resource-id "{fake_rid}" '
            '--latest-scan true --results "{{\\"VA1234\\":[[\\"a\\",\\"b\\"]]}}"',
            expect_failure=True,
        )

        # 3. Deprecated `baseline set` is still registered as a command, with a
        #    Deprecated marker pointing at `baseline add` as the redirect target.
        #    We use command-table introspection rather than parsing help text
        #    because the in-process invocation routes help output to stderr,
        #    which the testsdk does not capture (`ExecutionResult.output` is
        #    stdout-only). The lazy loader only loads what we've parsed, so we
        #    explicitly request the `baseline set` subtree first.
        loader = self.cli_ctx.invocation.commands_loader
        loader.load_command_table(['security', 'va', 'sql', 'baseline', 'set'])
        cmd = loader.command_table.get('security va sql baseline set')
        assert cmd is not None, \
            '`security va sql baseline set` should be registered'
        deprecate_info = getattr(cmd, 'deprecate_info', None)
        assert deprecate_info is not None, \
            '`baseline set` should carry a Deprecated marker'
        assert getattr(deprecate_info, 'redirect', '') == 'az security va sql baseline add', \
            'Deprecated marker on `baseline set` should redirect to `az security va sql baseline add`'
