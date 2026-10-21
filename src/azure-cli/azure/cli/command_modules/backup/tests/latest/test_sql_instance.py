# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import shlex
import unittest
from contextlib import ExitStack
from datetime import datetime, timezone
from io import StringIO
from types import SimpleNamespace
from unittest.mock import Mock, patch

from azure.core.credentials import AccessToken
from azure.core.pipeline.transport import HttpResponse, HttpTransport
from azure.mgmt.recoveryservicesbackup import RecoveryServicesBackupClient
from azure.mgmt.recoveryservicesbackup import models

from azure.cli.command_modules.backup import _client_factory, custom_base, custom_common, custom_help, custom_wl
from azure.cli.core.mock import DummyCli
from azure.cli.core.azclierror import (
    ArgumentUsageError, AzureResponseError, InvalidArgumentValueError, RequiredArgumentMissingError
)


ITEM_ID = (
    "/subscriptions/sub/resourceGroups/rg/providers/Microsoft.RecoveryServices/vaults/vault/"
    "backupFabrics/Azure/protectionContainers/VMAppContainer;Compute;rg;vm/protectedItems/"
)
CONTAINER = "VMAppContainer;Compute;rg;vm"
INSTANCE = "SQLInstance;mssqlserver"
DATABASE = "SQLDataBase;mssqlserver;db"
IDENTITY = "/subscriptions/sub/resourceGroups/identity-rg/providers/Microsoft.ManagedIdentity/userAssignedIdentities/uami"
DISK = "/subscriptions/sub/resourceGroups/disk-rg/providers/Microsoft.Compute/disks/disk1"


def protected_item(workload="SQLInstance", raw=False):
    model = (models.AzureVmWorkloadSQLInstanceProtectedItem if workload == "SQLInstance"
             else models.AzureVmWorkloadSQLDatabaseProtectedItem)
    name = INSTANCE if workload == "SQLInstance" else DATABASE
    item = models.ProtectedItemResource(
        id=ITEM_ID + name, name=name,
        properties=model(workload_type=workload, backup_management_type="AzureWorkload",
                         container_name=CONTAINER, protected_item_data_source_id="instance-datasource",
                         source_resource_id="/subscriptions/sub/resourceGroups/rg/providers/"
                                            "Microsoft.Compute/virtualMachines/vm"))
    return models.ProtectedItemResource(item.as_dict()) if raw else item


def snapshot_point(raw=False):
    point = models.RecoveryPointResource(
        name="snapshot-rp",
        properties=models.AzureWorkloadSQLRecoveryPoint(
            type="SnapshotFull", extended_info=models.AzureWorkloadSQLRecoveryPointExtendedInfo(
                included_databases=[models.DatabaseInRP(datasource_id="db-source", datasource_name="db")],
                snapshot_recovery_point_info=models.SnapshotRecoveryPointInfo(
                    snapshot_resource_group="snapshot-rg",
                    source_filesystem_info=[models.FilesystemInfo(access_paths=["E:\\", "F:\\"])]))))
    return models.RecoveryPointResource(point.as_dict()) if raw else point


class SqlInstanceTests(unittest.TestCase):

    def setUp(self):
        self.cmd = SimpleNamespace(cli_ctx=Mock(), name="backup recoverypoint list")

    def test_backup_sql_instance_model_and_output(self):
        item = protected_item()
        item.properties.child_database_name_list = ["db1", "db2"]
        item.properties.instance_protection_readiness = "PartialProtection"
        output = custom_help.serialize_hybrid_model(item)
        self.assertEqual(["db1", "db2"], output["properties"]["childDatabaseNameList"])
        self.assertEqual("PartialProtection", output["properties"]["instanceProtectionReadiness"])
        self.assertIsInstance(custom_wl._get_protected_item_instance("SQLInstance"),
                              models.AzureVmWorkloadSQLInstanceProtectedItem)
        self.assertTrue(custom_help.is_sql("SQLInstance"))
        self.assertTrue(custom_help.is_sql("SQLDataBase"))
        self.assertFalse(custom_help.is_sql("SAPHanaDBInstance"))

    @patch.object(custom_wl.cust_help, "track_backup_job")
    @patch.object(custom_wl.cust_help, "get_initial_pipeline_response")
    def test_backup_enable_sql_instance_child_database_payload(self, initial_response, track_job):
        client = Mock()
        policy = models.ProtectionPolicyResource(
            id="policy-id", properties=models.AzureVmWorkloadProtectionPolicy(
                work_load_type="SQLInstance", vm_workload_policy_type="SnapshotV2"))
        item = SimpleNamespace(name=INSTANCE, id=ITEM_ID + INSTANCE,
                               properties=SimpleNamespace(protectable_item_type="SQLInstance"))

        custom_wl.enable_protection_for_azure_wl(
            self.cmd, client, "rg", "vault", policy, item, ["db1", "db2"])

        args = client.begin_create_or_update.call_args.args
        self.assertEqual(("vault", "rg", "Azure", CONTAINER, INSTANCE), args[:5])
        payload = args[5].as_dict()["properties"]
        self.assertEqual("AzureVmWorkloadSQLInstance", payload["protectedItemType"])
        self.assertEqual("SQLInstance", payload["workloadType"])
        self.assertEqual(["db1", "db2"], payload["childDatabaseNameList"])
        self.assertEqual("policy-id", payload["policyId"])
        track_job.assert_called_once_with(self.cmd.cli_ctx, initial_response.return_value, "vault", "rg")

    def test_backup_rejects_child_selection_for_database(self):
        policy = models.ProtectionPolicyResource(
            id="policy-id", properties=models.AzureVmWorkloadProtectionPolicy(work_load_type="SQLDataBase"))
        item = SimpleNamespace(name=DATABASE, id=ITEM_ID + DATABASE,
                               properties=SimpleNamespace(protectable_item_type="SQLDataBase"))
        with self.assertRaises(ArgumentUsageError):
            custom_wl.enable_protection_for_azure_wl(
                self.cmd, Mock(), "rg", "vault", policy, item, ["db"])

    def test_backup_rejects_instance_policy_for_database(self):
        policy = models.ProtectionPolicyResource(
            id="policy-id", properties=models.AzureVmWorkloadProtectionPolicy(work_load_type="SQLInstance"))
        item = SimpleNamespace(name=DATABASE, id=ITEM_ID + DATABASE,
                               properties=SimpleNamespace(protectable_item_type="SQLDataBase"))
        client = Mock()
        with self.assertRaisesRegex(ArgumentUsageError, "SQLInstance policies require"):
            custom_wl.enable_protection_for_azure_wl(self.cmd, client, "rg", "vault", policy, item)
        client.begin_create_or_update.assert_not_called()

    @patch.object(custom_wl.cust_help, "track_backup_job")
    @patch.object(custom_wl.cust_help, "get_initial_pipeline_response")
    def test_backup_legacy_database_protection_payload(self, _response, _job):
        policy = models.ProtectionPolicyResource(
            id="policy-id", properties=models.AzureVmWorkloadProtectionPolicy(work_load_type="SQLDataBase"))
        client = Mock()
        item = SimpleNamespace(name=DATABASE, id=ITEM_ID + DATABASE,
                               properties=SimpleNamespace(protectable_item_type="SQLDataBase"))
        custom_wl.enable_protection_for_azure_wl(self.cmd, client, "rg", "vault", policy, item)
        payload = client.begin_create_or_update.call_args.args[5].as_dict()["properties"]
        self.assertEqual("AzureVmWorkloadSQLDatabase", payload["protectedItemType"])
        self.assertNotIn("childDatabaseNameList", payload)

    @patch.object(custom_wl.cust_help, "has_resource_guard_mapping", return_value=False)
    @patch.object(custom_wl.cust_help, "track_backup_job")
    @patch.object(custom_wl.cust_help, "get_initial_pipeline_response")
    def test_backup_stops_instance_and_database_protection(self, _response, _job, _guard):
        for workload in ["SQLInstance", "SQLDataBase"]:
            for retain, expected in [(False, "ProtectionStopped"), (True, "BackupsSuspended")]:
                with self.subTest(workload=workload, retain=retain):
                    client = Mock()
                    custom_wl.disable_protection(
                        self.cmd, client, "rg", "vault", protected_item(workload), retain)
                    payload = client.begin_create_or_update.call_args.args[5].as_dict()["properties"]
                    expected_type = "AzureVmWorkload" + (
                        "SQLInstance" if workload == "SQLInstance" else "SQLDatabase")
                    self.assertEqual(expected_type, payload["protectedItemType"])
                    self.assertEqual(expected, payload["protectionState"])

    def test_backup_create_sql_instance_policy_preserves_snapshot_fields(self):
        policy = {
            "properties": {
                "backupManagementType": "AzureWorkload",
                "workLoadType": "SQLInstance",
                "vmWorkloadPolicyType": "SnapshotV2",
                "subProtectionPolicy": [{
                    "policyType": "SnapshotFull",
                    "snapshotBackupAdditionalDetails": {
                        "instantRpRetentionRangeInDays": 5,
                        "instantRPDetails": "snapshot-resource-group"
                    }
                }, {"policyType": "Log"}]
            }
        }
        client = Mock()
        client._deserialize.dependencies = {}
        custom_wl.create_policy(client, "rg", "vault", "SqlInst-SnapLog", json.dumps(policy), "SQLInstance")
        payload = client.create_or_update.call_args.args[3].as_dict()
        self.assertEqual("SQLInstance", payload["properties"]["workLoadType"])
        self.assertEqual("SnapshotV2", payload["properties"]["vmWorkloadPolicyType"])
        self.assertEqual(5, payload["properties"]["subProtectionPolicy"][0]
                         ["snapshotBackupAdditionalDetails"]["instantRpRetentionRangeInDays"])
        self.assertEqual(["SnapshotFull", "Log"],
                         [p["policyType"] for p in payload["properties"]["subProtectionPolicy"]])

    def test_backup_recovery_point_query_filters(self):
        client = Mock()
        client.list.return_value = []
        custom_wl.list_wl_recovery_points(
            self.cmd, client, "rg", "vault", protected_item(),
            restore_point_query_type="Snapshot", get_latest_recovery_point_only=True)
        filters = client.list.call_args.kwargs["filter"]
        self.assertIn("restorePointQueryType eq 'Snapshot'", filters)
        self.assertIn("getLatestRPOnly eq 'True'", filters)
        self.assertNotIn("baseSnapshotRPId", filters)

    def test_backup_snapshot_log_query_filters(self):
        self.cmd.name = "backup recoverypoint show-log-chain"
        client = Mock()
        client.list.return_value = []
        custom_wl.list_wl_recovery_points(
            self.cmd, client, "rg", "vault", protected_item("SQLDataBase"),
            recovery_mode="SnapshotAttachAndRecover", base_snapshot_recovery_point_id="snapshot-rp",
            base_recovery_point_datasource_id="instance-datasource")
        self.assertEqual(
            "baseRPDatasourceId eq 'instance-datasource' and baseSnapshotRPId eq 'snapshot-rp' and "
            "recoveryMode eq 'SnapshotAttachAndRecover' and restorePointQueryType eq 'Log'",
            client.list.call_args.kwargs["filter"])

    @patch.object(custom_base, "show_item")
    @patch.object(custom_base, "backup_protected_items_cf")
    def test_backup_snapshot_log_filters_must_be_complete(self, _factory, show_item):
        show_item.return_value = protected_item("SQLDataBase")
        with self.assertRaises(RequiredArgumentMissingError):
            custom_base.show_log_chain_recovery_points(
                self.cmd, Mock(), "rg", "vault", CONTAINER, DATABASE,
                base_snapshot_recovery_point_id="snapshot-rp")

    @patch.object(custom_common, "protected_items_cf")
    def test_backup_native_sql_instance_lookup(self, factory):
        client = Mock()
        factory.return_value.get.return_value = protected_item()
        item = custom_common.show_item(
            self.cmd, client, "rg", "vault", CONTAINER, INSTANCE, "AzureWorkload", "SQLInstance")
        self.assertEqual("SQLInstance", item.properties.workload_type)
        factory.return_value.get.assert_called_once_with("vault", "rg", "Azure", CONTAINER, INSTANCE)

    @patch.object(custom_wl.cust_help, "track_backup_job")
    def test_backup_snapshot_now_payload(self, _track):
        client = Mock()
        expiry = datetime(2026, 12, 1)
        custom_wl.backup_now(self.cmd, client, "rg", "vault", protected_item(), expiry, "SnapshotFull")
        request = client.trigger.call_args.args[5].as_dict()["properties"]
        self.assertEqual("SnapshotFull", request["backupType"])
        self.assertIn("2026-12-01", request["recoveryPointExpiryTimeInUTC"])

    @patch.object(custom_wl.cust_help, "track_register_operation")
    @patch.object(custom_wl.cust_help, "track_refresh_operation")
    @patch.object(custom_wl, "_get_protectable_container_name", side_effect=[None, CONTAINER])
    def test_backup_register_discovers_source_subscription(self, _name, track_refresh, _register):
        client = Mock()
        custom_wl.register_wl_container(
            self.cmd, client, "vault", "rg", "SQLInstance",
            "/subscriptions/vm-sub/resourceGroups/vm-rg/providers/Microsoft.Compute/virtualMachines/vm",
            "AzureWorkload", "vm-sub")
        self.assertEqual(
            "backupManagementType eq 'AzureWorkload' and containerSubscriptionId eq 'vm-sub'",
            client.refresh.call_args.kwargs["filter"])
        track_refresh.assert_called_once()
        self.assertEqual("SQLInstance", client.begin_register.call_args.args[4].properties.workload_type)

    def test_backup_target_instance_preserves_server_filter(self):
        items = [
            SimpleNamespace(name=INSTANCE, properties=SimpleNamespace(
                friendly_name="mssqlserver", protectable_item_type="SQLInstance", server_name=server))
            for server in ("source-vm", "target-vm")
        ]
        selected = custom_wl.show_protectable_instance(items, "target-vm", "SQLInstance", "mssqlserver")
        self.assertIs(items[1], selected)

    def test_backup_filter_literals_escape_quotes(self):
        self.assertEqual("baseSnapshotRPId eq 'snapshot''rp'",
                         custom_help.get_filter_string({"baseSnapshotRPId": "snapshot'rp"}))

    @patch.object(custom_help, "protection_container_refresh_operation_statuses_cf")
    @patch.object(custom_help.time, "sleep")
    def test_backup_refresh_polls_new_status_operation(self, _sleep, factory):
        factory.return_value.get.side_effect = [
            models.OperationStatus(status="InProgress"), models.OperationStatus(status="Succeeded")]
        response = SimpleNamespace(http_response=SimpleNamespace(headers={
            "Azure-AsyncOperation": "https://management.azure.com/operations/operation-id?api-version=2026-10-01"
        }))
        custom_help.track_refresh_operation(self.cmd.cli_ctx, response, "vault", "rg")
        self.assertEqual(2, factory.return_value.get.call_count)
        factory.return_value.get.assert_called_with("rg", "vault", "Azure", "operation-id")

    @patch.object(custom_help, "protection_container_refresh_operation_statuses_cf")
    def test_backup_refresh_surfaces_failure(self, factory):
        factory.return_value.get.return_value = models.OperationStatus(status="Failed")
        response = SimpleNamespace(http_response=SimpleNamespace(headers={
            "Azure-AsyncOperation": "https://management.azure.com/operations/operation-id"
        }))
        with self.assertRaises(AzureResponseError):
            custom_help.track_refresh_operation(self.cmd.cli_ctx, response, "vault", "rg")

    @patch.object(custom_help, "protection_container_refresh_operation_results_cf")
    @patch.object(custom_help.time, "sleep")
    def test_backup_refresh_preserves_location_polling(self, _sleep, factory):
        factory.return_value.get.side_effect = [
            SimpleNamespace(http_response=SimpleNamespace(status_code=202)),
            SimpleNamespace(http_response=SimpleNamespace(status_code=204))]
        response = SimpleNamespace(http_response=SimpleNamespace(headers={
            "Location": "https://management.azure.com/operations/operation-id"
        }))
        custom_help.track_refresh_operation(self.cmd.cli_ctx, response, "vault", "rg")
        self.assertEqual(2, factory.return_value.get.call_count)
        self.assertEqual(("vault", "rg", "Azure", "operation-id"), factory.return_value.get.call_args.args)

    @patch.object(custom_help, "protection_container_refresh_operation_statuses_cf")
    @patch.object(custom_help, "protection_container_refresh_operation_results_cf")
    @patch.object(custom_help.time, "sleep")
    def test_backup_refresh_prefers_location_when_both_headers_present(self, sleep, results, statuses):
        results.return_value.get.side_effect = [
            SimpleNamespace(http_response=SimpleNamespace(status_code=202)),
            SimpleNamespace(http_response=SimpleNamespace(status_code=204))]
        response = SimpleNamespace(http_response=SimpleNamespace(headers={
            "Location": "https://management.azure.com/operationResults/result-id",
            "Azure-AsyncOperation": "https://management.azure.com/operationsStatus/status-id"
        }))
        custom_help.track_refresh_operation(self.cmd.cli_ctx, response, "vault", "rg")
        self.assertEqual(2, results.return_value.get.call_count)
        results.return_value.get.assert_called_with(
            "vault", "rg", "Azure", "result-id", cls=custom_help.get_pipeline_response)
        sleep.assert_called_once_with(5)
        statuses.assert_not_called()

    @patch.object(custom_help, "protection_container_refresh_operation_statuses_cf")
    @patch.object(custom_help, "protection_container_refresh_operation_results_cf")
    def test_backup_refresh_does_not_fallback_after_location_failure(self, results, statuses):
        results.return_value.get.side_effect = AzureResponseError("Polling failed")
        response = SimpleNamespace(http_response=SimpleNamespace(headers={
            "Location": "https://management.azure.com/operationResults/result-id",
            "Azure-AsyncOperation": "https://management.azure.com/operationsStatus/status-id"
        }))
        with self.assertRaisesRegex(AzureResponseError, "Polling failed"):
            custom_help.track_refresh_operation(self.cmd.cli_ctx, response, "vault", "rg")
        statuses.assert_not_called()

    @patch.object(custom_help, "protection_container_refresh_operation_statuses_cf")
    @patch.object(custom_help, "protection_container_refresh_operation_results_cf")
    def test_backup_refresh_rejects_missing_polling_headers(self, results, statuses):
        response = SimpleNamespace(http_response=SimpleNamespace(headers={}))
        with self.assertRaisesRegex(AzureResponseError, "neither Location nor Azure-AsyncOperation"):
            custom_help.track_refresh_operation(self.cmd.cli_ctx, response, "vault", "rg")
        results.assert_not_called()
        statuses.assert_not_called()

    def _snapshot_config(self, workload, mode, point_in_time=None, original=False, raw=False):
        client = Mock()
        client.get.return_value = snapshot_point(raw)
        client.list.return_value = [snapshot_point(raw)]
        target_container = CONTAINER.replace(";vm", ";target-vm")
        target = SimpleNamespace(
            id=ITEM_ID.replace(CONTAINER, target_container) + "SQLInstance;targetinstance",
            properties=SimpleNamespace(protectable_item_type="SQLInstance", friendly_name="targetinstance"))
        return custom_wl._get_sql_snapshot_recovery_config(
            client, "rg", "vault", protected_item(workload),
            "OriginalWorkloadRestore" if original else "AlternateWorkloadRestore",
            None if point_in_time and workload == "SQLDataBase" else "snapshot-rp", point_in_time,
            target, None, None, mode, True, IDENTITY, "restore-rg")

    def test_backup_sql_snapshot_config_volume_mapping(self):
        for mode, pit, mapping_type, logical_name in [
                ("SnapshotAttachAndRecover", None, "Data", "mssqlserver"),
                ("SnapshotAttachAndRecover", "15-10-2026-12:00:00", "DiskDrives", "mssqlserver"),
                ("SnapshotAttach", None, "DiskDrives", None)]:
            with self.subTest(mode=mode, pit=pit):
                config = self._snapshot_config("SQLInstance", mode, pit)
                self.assertEqual("snapshot-rp", config["recovery_point_id"])
                self.assertTrue(config["database_name"].startswith("targetinstance/*_restored_"))
                self.assertEqual({
                    "mapping_type": mapping_type, "source_logical_name": logical_name,
                    "source_path": "E:\\", "target_path": ""
                }, config["target_physical_path"][0])
                self.assertEqual(2, len(config["target_physical_path"]))

    def test_backup_snapshot_config_from_base_sdk_recovery_point(self):
        self.assertIs(type(snapshot_point(raw=True).properties), models.RecoveryPoint)
        for workload, pit in [("SQLInstance", None), ("SQLDataBase", "15-10-2026-12:00:00")]:
            with self.subTest(workload=workload):
                config = self._snapshot_config(workload, "SnapshotAttachAndRecover", pit, raw=True)
                self.assertEqual(["E:\\", "F:\\"],
                                 [mapping["source_path"] for mapping in config["target_physical_path"]])
                self.assertEqual("DefaultRangeRecoveryPoint" if pit else "snapshot-rp",
                                 config["recovery_point_id"])

    def test_backup_snapshot_config_rejects_missing_metadata(self):
        client = Mock()
        client.get.return_value = models.RecoveryPointResource({
            "properties": {"objectType": "AzureWorkloadSQLRecoveryPoint"}})
        with self.assertRaisesRegex(InvalidArgumentValueError, "does not contain SQL snapshot metadata"):
            custom_wl._get_sql_snapshot_recovery_config(
                client, "rg", "vault", protected_item(), "OriginalWorkloadRestore",
                "snapshot", None, None, None, None, "SnapshotAttachAndRecover", False, IDENTITY, "restore-rg")

    @patch.object(custom_wl, "get_mgmt_service_client")
    @patch.object(custom_wl, "recovery_points_cf")
    @patch.object(custom_wl, "backup_protected_items_cf")
    @patch.object(custom_wl.common, "show_container")
    @patch.object(custom_wl.common, "show_item")
    @patch.object(custom_wl.common, "show_recovery_point")
    @patch.object(custom_wl.common, "list_items")
    @patch.object(custom_wl, "_get_log_time_range")
    @patch.object(custom_wl.cust_help, "has_resource_guard_mapping", return_value=False)
    @patch.object(custom_wl.cust_help, "track_backup_job")
    def test_backup_sql_snapshot_restore_scenarios(
            self, track_job, _guard, log_ranges, list_items, show_point, show_item, show_container,
            _items_factory, rp_factory, service_factory):
        service_factory.return_value.user_assigned_identities.get.return_value = SimpleNamespace(
            client_id="client", principal_id="principal")
        show_container.return_value = SimpleNamespace(properties=SimpleNamespace(
            source_resource_id="/subscriptions/sub/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/target"))
        show_point.return_value = snapshot_point()
        rp_factory.return_value.get.return_value = snapshot_point(raw=True)
        log_ranges.return_value = [SimpleNamespace(start_time=datetime(2026, 10, 1),
                                                   end_time=datetime(2026, 10, 31))]
        database = protected_item("SQLDataBase")
        database.properties.protected_item_data_source_id = "db-source"
        list_items.return_value = [database]
        scenarios = [
            ("SQLInstance", "SnapshotAttachAndRecover", None, True, False),
            ("SQLInstance", "SnapshotAttachAndRecover", None, False, False),
            ("SQLInstance", "SnapshotAttachAndRecover", "15-10-2026-12:00:00", False, False),
            ("SQLInstance", "SnapshotAttach", None, False, False),
            ("SQLDataBase", "SnapshotAttachAndRecover", None, False, False),
            ("SQLDataBase", "SnapshotAttachAndRecover", "15-10-2026-12:00:00", False, False),
            ("SQLDataBase", "SnapshotAttach", None, False, False),
            ("SQLDataBase", "SnapshotAttach", "15-10-2026-12:00:00", False, True)]
        for index, (workload, mode, pit, original, logs_as_files) in enumerate(scenarios * 2):
            raw = index >= len(scenarios)
            with self.subTest(workload=workload, mode=mode, pit=pit, original=original, raw=raw):
                show_item.return_value = protected_item(workload, raw)
                list_items.return_value = [models.ProtectedItemResource(database.as_dict()) if raw else database]
                config = self._snapshot_config(workload, mode, pit, original)
                config["target_physical_path"][0]["target_path"] = "X:\\"
                config["disks_to_detach_on_clash"] = [DISK]
                if logs_as_files:
                    config["target_directory_mapping"] = {"all": "C:\\temp"}
                client = Mock()
                result = custom_wl.restore_azure_wl(self.cmd, client, "rg", "vault", json.dumps(config))
                args = client.begin_trigger.call_args.args
                self.assertEqual(config["recovery_point_id"], args[5])
                payload = args[6].as_dict()["properties"]
                self.assertEqual(
                    "AzureWorkloadSQLPointInTimeRestoreRequest" if pit else "AzureWorkloadSQLRestoreRequest",
                    payload["objectType"])
                self.assertEqual(mode, payload["recoveryMode"])
                self.assertEqual("OriginalLocation" if original else "AlternateLocation", payload["recoveryType"])
                self.assertEqual(not original, payload["shouldUseAlternateTargetLocation"])
                self.assertTrue(payload["isNonRecoverable"])
                self.assertEqual("restore-rg", payload["targetResourceGroupName"])
                self.assertEqual(IDENTITY, payload["userAssignedManagedIdentityDetails"]["identityArmId"])
                self.assertEqual("uami", payload["userAssignedManagedIdentityDetails"]["identityName"])
                self.assertEqual("client", payload["userAssignedManagedIdentityDetails"]
                                 ["userAssignedIdentityProperties"]["clientId"])
                self.assertEqual([DISK], payload["snapshotRestoreParameters"]["disksToDetachOnClash"])
                self.assertEqual(1, len(payload["alternateDirectoryPaths"]))
                self.assertEqual("X:\\", payload["alternateDirectoryPaths"][0]["targetPath"])
                if original:
                    self.assertNotIn("targetInfo", payload)
                    self.assertNotIn("targetVirtualMachineId", payload)
                elif mode == "SnapshotAttach":
                    self.assertNotIn("databaseName", payload["targetInfo"])
                    self.assertNotIn("overwriteOption", payload["targetInfo"])
                    if logs_as_files:
                        self.assertEqual({"all": "C:\\temp"}, payload["targetInfo"]["targetDirectoryMapping"])
                else:
                    self.assertEqual(config["database_name"], payload["targetInfo"]["databaseName"])
                if pit:
                    self.assertIn("2026-10-15T12:00:00", payload["pointInTime"])
                    if workload == "SQLInstance":
                        self.assertEqual(("snapshot-rp", "instance-datasource", "SnapshotAttachAndRecover"),
                                         log_ranges.call_args.args[-3:])
                self.assertIs(track_job.return_value, result)

    @patch.object(custom_wl, "_get_log_time_range")
    @patch.object(custom_wl.common, "list_items")
    @patch.object(custom_wl, "backup_protected_items_cf")
    @patch.object(custom_wl, "recovery_points_cf")
    @patch.object(custom_wl, "_get_snapshot_identity")
    def test_backup_instance_pit_wire_fields_and_friendly_name(
            self, _identity, points, _items, list_items, log_ranges):
        points.return_value.get.return_value = snapshot_point(raw=True)
        source = protected_item(raw=True)
        self.assertIs(type(source.properties), models.ProtectedItem)
        database = protected_item("SQLDataBase", raw=True)
        database.properties.pop("protectedItemDataSourceId")
        database.properties["friendlyName"] = "db"
        list_items.return_value = [database]
        log_ranges.return_value = [SimpleNamespace(start_time=datetime(2026, 10, 1),
                                                   end_time=datetime(2026, 10, 31))]
        config = self._snapshot_config("SQLInstance", "SnapshotAttachAndRecover", "15-10-2026-12:00:00")
        request = models.AzureWorkloadSQLPointInTimeRestoreRequest()
        custom_wl._apply_sql_snapshot_restore(self.cmd, request, config, source, "rg", "vault")
        self.assertIs(log_ranges.call_args.args[3], database)
        self.assertEqual(("snapshot-rp", "instance-datasource", "SnapshotAttachAndRecover"),
                         log_ranges.call_args.args[-3:])
        self.assertEqual(datetime(2026, 10, 15, 12, tzinfo=timezone.utc), request.point_in_time)
        source.properties.pop("protectedItemDataSourceId")
        with self.assertRaisesRegex(InvalidArgumentValueError, "no ProtectedItemDataSourceId"):
            custom_wl._apply_sql_snapshot_restore(self.cmd, request, config, source, "rg", "vault")

    @patch.object(custom_wl, "recovery_points_cf")
    def test_backup_log_ranges_from_base_sdk_recovery_point(self, points):
        point = models.RecoveryPointResource({
            "properties": {
                "objectType": "AzureWorkloadSQLPointInTimeRecoveryPoint",
                "timeRanges": [{"startTime": "2026-10-01T00:00:00Z", "endTime": "2026-10-31T00:00:00Z"}]}})
        self.assertIs(type(point.properties), models.RecoveryPoint)
        points.return_value.list.return_value = [point]
        ranges = custom_wl._get_log_time_range(
            self.cmd, "rg", "vault", protected_item("SQLDataBase", raw=True), False,
            "snapshot-rp", "instance-datasource", "SnapshotAttachAndRecover")
        self.assertEqual(1, len(ranges))
        custom_wl.validate_log_point_in_time(datetime(2026, 10, 15, 12), ranges)
        filters = points.return_value.list.call_args.kwargs["filter"]
        self.assertIn("baseRPDatasourceId eq 'instance-datasource'", filters)
        point.properties.pop("timeRanges")
        with self.assertRaisesRegex(InvalidArgumentValueError, "does not contain time ranges"):
            custom_wl._get_log_time_range(self.cmd, "rg", "vault", protected_item("SQLDataBase"), False)

    def test_backup_snapshot_config_requires_identity_and_group(self):
        with self.assertRaises(RequiredArgumentMissingError):
            custom_wl._get_sql_snapshot_recovery_config(
                Mock(), "rg", "vault", protected_item(), "OriginalWorkloadRestore",
                "snapshot", None, None, None, None, "SnapshotAttachAndRecover", False, None, None)

    @patch.object(custom_wl, "_get_snapshot_identity")
    def test_backup_snapshot_rejects_invalid_config(self, _identity):
        config = self._snapshot_config("SQLInstance", "SnapshotAttachAndRecover")
        config["disks_to_detach_on_clash"] = ["not-a-disk-id"]
        with self.assertRaises(InvalidArgumentValueError):
            custom_wl._apply_sql_snapshot_restore(
                self.cmd, models.AzureWorkloadSQLRestoreRequest(), config, protected_item(), "rg", "vault")

    @patch.object(custom_wl.common, "show_item")
    @patch.object(custom_base.common, "show_container")
    @patch.object(custom_base, "show_protectable_instance")
    @patch.object(custom_base, "get_mgmt_service_client")
    @patch.object(custom_base, "get_subscription_id", return_value="sub")
    @patch.object(custom_wl, "backup_protected_items_cf")
    def test_backup_snapshot_config_public_handler(
            self, _items, _subscription, _client, target_item, target_container, source_item):
        target_id = ITEM_ID.replace(CONTAINER, CONTAINER.replace(";vm", ";target-vm")) + INSTANCE
        target_item.return_value = SimpleNamespace(
            id=target_id, properties=SimpleNamespace(protectable_item_type="SQLInstance", friendly_name="target"))
        target_container.return_value = SimpleNamespace(id="/".join(target_id.split("/")[:-2]))
        source_item.return_value = protected_item()
        client = Mock()
        client.get.return_value = snapshot_point()
        config = custom_base.show_recovery_config(
            self.cmd, client, "rg", "vault", "AlternateWorkloadRestore", CONTAINER, INSTANCE,
            rp_name="snapshot-rp", target_server_type="SQLInstance", target_server_name="target-vm",
            workload_type="SQLInstance", target_instance_name="mssqlserver",
            identity_arm_id=IDENTITY, snapshot_instance_resource_group="restore-rg")
        self.assertTrue(config["database_name"].startswith("target/*_restored_"))
        self.assertEqual("SnapshotAttachAndRecover", config["recovery_mode"])
        target_item.assert_called_once()

    def test_backup_sdk_wire_preserves_snapshot_extensions(self):
        class AcceptedResponse(HttpResponse):
            def __init__(self, request):
                super().__init__(request, None)
                self.status_code = 202
                self.reason = "Accepted"
                self.headers = {"Azure-AsyncOperation": "https://management.azure.com/operations/test",
                                "Content-Type": "application/json"}
                self.content_type = "application/json"

            def body(self):
                return b"{}"

            def iter_bytes(self):
                return iter([self.body()])

            def iter_raw(self):
                return self.iter_bytes()

            def read(self):
                return self.body()

        transport = Mock(spec=HttpTransport)
        transport.send.side_effect = lambda request, **kwargs: AcceptedResponse(request)
        credential = SimpleNamespace(get_token=lambda *args, **kwargs: AccessToken("unit-test", 2000000000))
        client = RecoveryServicesBackupClient(credential, "sub", transport=transport)
        target = models.TargetRestoreInfo(container_id="target-container")
        target["targetDirectoryMapping"] = {"all": "C:\\temp"}
        request = models.AzureWorkloadSQLPointInTimeRestoreRequest(
            recovery_mode="SnapshotAttach", target_info=target, point_in_time=datetime(2026, 10, 15),
            snapshot_restore_parameters=models.SnapshotRestoreParameters(disks_to_detach_on_clash=[DISK]))
        client.restores.begin_trigger(
            "vault", "rg", "Azure", CONTAINER, INSTANCE, "snapshot-rp",
            models.RestoreRequestResource(properties=request), polling=False)
        wire_request = transport.send.call_args.args[0]
        self.assertIn("/recoveryPoints/snapshot-rp/restore", wire_request.url)
        self.assertIn("api-version=2026-10-01", wire_request.url)
        payload = json.loads(wire_request.body)["properties"]
        self.assertEqual({"all": "C:\\temp"}, payload["targetInfo"]["targetDirectoryMapping"])
        self.assertEqual("AzureWorkloadSQLPointInTimeRestoreRequest", payload["objectType"])
        self.assertEqual([DISK], payload["snapshotRestoreParameters"]["disksToDetachOnClash"])


class SqlInstanceCommandTests(unittest.TestCase):

    def setUp(self):
        self.client = Mock()
        patches = ExitStack()
        self.addCleanup(patches.close)
        patches.enter_context(patch.object(_client_factory, "_backup_client_factory", return_value=self.client))
        patches.enter_context(patch(
            "azure.cli.core._profile.Profile.load_cached_subscriptions",
            return_value=[{
                "id": "00000000-0000-0000-0000-000000000000",
                "name": "Test subscription",
                "state": "Enabled",
                "tenantId": "00000000-0000-0000-0000-000000000001",
                "isDefault": True,
                "environmentName": "AzureCloud",
                "user": {"name": "test@example.com", "type": "user"}
            }]))
        patches.enter_context(patch(
            "requests.sessions.Session.request",
            side_effect=AssertionError("SQL instance command tests must not access the network")))
        self.cli_ctx = DummyCli()

    def cmd(self, command, expect_failure=False):
        output = StringIO()
        exit_code = self.cli_ctx.invoke(shlex.split(command), out_file=output)
        if expect_failure:
            self.assertNotEqual(0, exit_code, command)
            return None
        self.assertEqual(0, exit_code, output.getvalue())
        return json.loads(output.getvalue()) if output.getvalue().strip() else None

    @patch.object(custom_wl.cust_help, "track_register_operation", return_value={"status": "Succeeded"})
    @patch.object(custom_wl.cust_help, "track_refresh_operation")
    @patch.object(custom_wl, "_get_protectable_container_name")
    def test_backup_container_subscription_options(self, container_name, refresh, register):
        container_name.side_effect = [None, CONTAINER, None, CONTAINER]
        self.cmd('backup container register -g rg -v vault --workload-type SQLInstance '
                 '--resource-id /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/rg/'
                 'providers/Microsoft.Compute/virtualMachines/vm '
                 '--container-subscription-id 11111111-1111-1111-1111-111111111111')
        self._assert_container_registration()
        self.cmd('backup container register -g rg -v vault --workload-type SQLInstance '
                 '--resource-id /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/rg/'
                 'providers/Microsoft.Compute/virtualMachines/vm '
                 '--container-sub-id 11111111-1111-1111-1111-111111111111')
        self._assert_container_registration()
        self.assertEqual(2, refresh.call_count)
        self.assertEqual(2, register.call_count)

    def _assert_container_registration(self):
        self.assertEqual(("vault", "rg", "Azure"), self.client.protection_containers.refresh.call_args.args)
        filters = self.client.protection_containers.refresh.call_args.kwargs["filter"]
        self.assertIn("containerSubscriptionId eq '11111111-1111-1111-1111-111111111111'", filters)
        request = self.client.protection_containers.begin_register.call_args.args[4].as_dict()
        self.assertEqual("SQLInstance", request["properties"]["workloadType"])
        self.assertEqual("AzureWorkload", request["properties"]["backupManagementType"])

    @patch.object(custom_base.custom_afs, "register_afs_container", return_value={"status": "Succeeded"})
    def test_backup_container_registration_preserves_azure_files_identity(self, register_afs):
        self.assertEqual({"status": "Succeeded"}, self.cmd(
            'backup container register -g rg -v vault --backup-management-type AzureStorage '
            '--workload-type AzureFileShare --storage-account account --access-type IdentityBased '
            '--mi-system-assigned --yes'))
        args = register_afs.call_args.args
        self.assertEqual(("rg", "vault", "account", "IdentityBased", True, None, True), args[2:])
        self.client.protection_containers.refresh.assert_not_called()
        self.client.protection_containers.begin_register.assert_not_called()

    @patch.object(custom_base.custom_afs, "register_afs_container")
    def test_backup_container_registration_rejects_source_subscription_for_azure_files(self, register_afs):
        self.cmd('backup container register -g rg -v vault --backup-management-type AzureStorage '
                 '--workload-type AzureFileShare --storage-account account --container-sub-id source-sub',
                 expect_failure=True)
        register_afs.assert_not_called()
        self.client.protection_containers.refresh.assert_not_called()

    @patch.object(custom_base, "show_item")
    def test_backup_recovery_point_query_options(self, show_item):
        show_item.return_value = protected_item()
        self.client.recovery_points.list.return_value = []
        self.assertEqual([], self.cmd('backup recoverypoint list -g rg -v vault -c "VMAppContainer;Compute;rg;vm" '
                                      '-i "SQLInstance;mssqlserver" --backup-management-type AzureWorkload '
                                      '--workload-type SQLInstance --restore-point-query-type Snapshot '
                                      '--get-latest-recovery-point-only true'))
        self._assert_recovery_point_filters("Snapshot", "True")
        self.assertEqual([], self.cmd('backup recoverypoint list -g rg -v vault -c "VMAppContainer;Compute;rg;vm" '
                                      '-i "SQLInstance;mssqlserver" --backup-management-type AzureWorkload '
                                      '--workload-type SQLInstance --rp-query-type SnapshotFull --latest-rp-only false'))
        self._assert_recovery_point_filters("SnapshotFull", "False")
        self.cmd('backup recoverypoint list -g rg -v vault -c "VMAppContainer;Compute;rg;vm" '
                 '-i "SQLInstance;mssqlserver" --backup-management-type AzureWorkload --workload-type SQLInstance')
        self.assertIsNone(self.client.recovery_points.list.call_args.kwargs["filter"])

    def _assert_recovery_point_filters(self, query_type, latest):
        args = self.client.recovery_points.list.call_args
        self.assertEqual(("vault", "rg", "Azure", CONTAINER, INSTANCE), args.args)
        self.assertIn(f"restorePointQueryType eq '{query_type}'", args.kwargs["filter"])
        self.assertIn(f"getLatestRPOnly eq '{latest}'", args.kwargs["filter"])

    @patch.object(custom_base, "show_item")
    def test_backup_snapshot_log_chain_options(self, show_item):
        show_item.return_value = protected_item("SQLDataBase")
        self.client.recovery_points.list.return_value = []
        self.assertEqual([], self.cmd('backup recoverypoint show-log-chain -g rg -v vault -c "VMAppContainer;Compute;rg;vm" '
                                      '-i "SQLDataBase;mssqlserver;db" --backup-management-type AzureWorkload '
                                      '--workload-type MSSQL --recovery-mode SnapshotAttachAndRecover '
                                      '--base-snapshot-recovery-point-id snapshot-rp '
                                      '--base-recovery-point-datasource-id instance-datasource'))
        self._assert_snapshot_log_filters()
        self.assertEqual([], self.cmd('backup recoverypoint show-log-chain -g rg -v vault -c "VMAppContainer;Compute;rg;vm" '
                                      '-i "SQLDataBase;mssqlserver;db" --backup-management-type AzureWorkload '
                                      '--workload-type MSSQL --recovery-mode SnapshotAttachAndRecover '
                                      '--base-snapshot-rp-id snapshot-rp --base-datasource-id instance-datasource'))
        self._assert_snapshot_log_filters()
        self.cmd('backup recoverypoint show-log-chain -g rg -v vault -c "VMAppContainer;Compute;rg;vm" '
                 '-i "SQLDataBase;mssqlserver;db" --backup-management-type AzureWorkload --workload-type MSSQL')
        self.assertEqual("restorePointQueryType eq 'Log'",
                         self.client.recovery_points.list.call_args.kwargs["filter"])

    def _assert_snapshot_log_filters(self):
        args = self.client.recovery_points.list.call_args
        self.assertEqual(("vault", "rg", "Azure", CONTAINER, DATABASE), args.args)
        self.assertEqual(
            "baseRPDatasourceId eq 'instance-datasource' and baseSnapshotRPId eq 'snapshot-rp' and "
            "recoveryMode eq 'SnapshotAttachAndRecover' and restorePointQueryType eq 'Log'",
            args.kwargs["filter"])

    @patch.object(custom_base, "show_item")
    def test_backup_snapshot_log_chain_rejects_incomplete_filters(self, show_item):
        show_item.return_value = protected_item("SQLDataBase")
        self.cmd('backup recoverypoint show-log-chain -g rg -v vault -c "VMAppContainer;Compute;rg;vm" '
                 '-i "SQLDataBase;mssqlserver;db" --backup-management-type AzureWorkload --workload-type MSSQL '
                 '--base-snapshot-rp-id snapshot-rp', expect_failure=True)
        self.client.recovery_points.list.assert_not_called()

    @patch.object(custom_wl.cust_help, "track_backup_job", return_value={"status": "Completed"})
    @patch.object(custom_wl.cust_help, "get_initial_pipeline_response")
    @patch.object(custom_base, "show_protectable_item")
    def test_backup_child_database_names_option(self, protectable, _response, _job):
        protectable.return_value = SimpleNamespace(
            id=ITEM_ID + INSTANCE, name=INSTANCE, properties=SimpleNamespace(protectable_item_type="SQLInstance"))
        self.client.protection_policies.get.return_value = models.ProtectionPolicyResource(
            id="policy-id", properties=models.AzureVmWorkloadProtectionPolicy(
                work_load_type="SQLInstance", vm_workload_policy_type="SnapshotV2"))
        self.cmd('backup protection enable-for-azurewl -g rg -v vault --policy-name snapshot-policy '
                 '--protectable-item-type SQLInstance --protectable-item-name "SQLInstance;mssqlserver" '
                 '--server-name vm --workload-type SQLInstance --child-database-names db1 db2')
        args = self.client.protected_items.begin_create_or_update.call_args.args
        self.assertEqual(("vault", "rg", "Azure", CONTAINER, INSTANCE), args[:5])
        payload = args[5].as_dict()["properties"]
        self.assertEqual(["db1", "db2"], payload["childDatabaseNameList"])
        self.assertEqual("AzureVmWorkloadSQLInstance", payload["protectedItemType"])
        self.assertEqual("policy-id", payload["policyId"])


if __name__ == "__main__":
    unittest.main()
