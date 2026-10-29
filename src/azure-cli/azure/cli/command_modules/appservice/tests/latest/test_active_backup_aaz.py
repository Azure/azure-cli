# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from contextlib import ExitStack, redirect_stderr, redirect_stdout
import io
import json
import os
from pathlib import Path
import shlex
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from azure.core.credentials import AccessToken
from azure.core.pipeline.transport import HttpRequest, HttpResponse
from requests.structures import CaseInsensitiveDict

from azure.cli.core import get_default_cli
from azure.cli.core._profile import Profile
from azure.cli.command_modules.appservice import COMMAND_LOADER_CLS


CATALOG = json.loads(Path(__file__).with_name("active_backup_command_catalog.json").read_text(encoding="utf-8"))
API_VERSION = CATALOG["apiVersion"]
COMMANDS = CATALOG["commands"]
SUBSCRIPTION = "00000000-0000-0000-0000-000000000001"
RESOURCE_ROOT = "/subscriptions/{}/resourceGroups/group/providers/Microsoft.Web".format(SUBSCRIPTION)
SUBNET = RESOURCE_ROOT.replace("Microsoft.Web", "Microsoft.Network") + "/virtualNetworks/net/subnets/integration"
ORIGIN = RESOURCE_ROOT + "/sites/primary/silos/origin"


class _Credential:
    def get_token(self, *_args, **_kwargs):
        return AccessToken("offline-active-backup-test", 9999999999)


class _Response(HttpResponse):
    def __init__(self, request, status, payload=None, headers=None):
        super().__init__(request, None)
        self.status_code = status
        self.reason = "Conflict" if status == 409 else "Offline test response"
        self.headers = CaseInsensitiveDict({"content-type": "application/json", **(headers or {})})
        self.content_type = "application/json"
        self._body = b"" if payload is None else json.dumps(payload).encode("utf-8")

    def body(self):
        return self._body


def _resource(path):
    result = {"id": path, "name": path.rsplit("/", 1)[-1], "properties": {}}
    if "/managedTrafficConfig/" in path:
        result["type"] = "Microsoft.Web/sites/managedTrafficConfig"
        result["properties"] = {
            "trafficMode": "Active",
            "endpoints": [{"region": "eastus", "weight": 700}, {"region": "westus2", "weight": 300}],
        }
    elif "/lastKnownGood/" in path:
        result["type"] = "Microsoft.Web/sites/lastKnownGood"
        result["properties"] = {"revisionNumber": 7, "siteName": "primary"}
    elif "/virtualNetworkConnections/" in path:
        result["type"] = "Microsoft.Web/sites/silos/virtualNetworkConnections"
        result["properties"] = {"subnetResourceId": SUBNET, "swiftSupported": True}
    else:
        plan = "/serverfarms/" in path
        result["type"] = "Microsoft.Web/{}/silos".format("serverfarms" if plan else "sites")
        result["location"] = "eastus" if path.casefold().endswith("/silos/origin") else "westus2"
        result["properties"] = {
            "primaryLocation": "eastus", "provisioningState": "Succeeded",
            "primaryServerFarmName" if plan else "primarySiteName": "primary",
        }
        if plan:
            result["properties"].update(instanceNumberOverride=1, zoneRedundantOverride=True)
        else:
            result["properties"].update(
                trafficMode="Active", endpointStatus="Enabled", followLastKnownGood=False, revisionNumber=7,
                defaultHostName="secondary.example.test",
            )
    return result


class ActiveBackupAAZTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[8]
        cache = root / ".x" / "active-backup" / "offline-cli"
        cache.mkdir(parents=True, exist_ok=True)
        cls.directory = tempfile.TemporaryDirectory(dir=cache)
        cls.isolation = ExitStack()
        cls.isolation.enter_context(patch.dict(os.environ, {
            "AZURE_CONFIG_DIR": cls.directory.name,
            "AZURE_EXTENSION_DIR": str(Path(cls.directory.name) / "extensions"),
            "AZURE_EXTENSION_USE_DYNAMIC_INSTALL": "no",
            "AZURE_CORE_COLLECT_TELEMETRY": "false",
        }))
        cls.isolation.enter_context(patch("azure.cli.core._config.GLOBAL_CONFIG_DIR", cls.directory.name))
        cls.isolation.enter_context(patch(
            "azure.cli.core.extension.EXTENSIONS_DIR", str(Path(cls.directory.name) / "extensions")))
        cls.isolation.enter_context(patch(
            "azure.cli.core.extension.EXTENSIONS_SYS_DIR", str(Path(cls.directory.name) / "system-extensions")))
        cls.isolation.enter_context(patch("azure.cli.core.extension.DEV_EXTENSION_SOURCES", []))

    @classmethod
    def tearDownClass(cls):
        cls.isolation.close()
        cls.directory.cleanup()

    def setUp(self):
        self.calls = []
        self.async_operation = False
        self.operation_status = "Succeeded"
        self.location_operation = False
        self.location_responses = []
        self.operation_method = None
        self.http_status = None
        self.paginate = False
        self.reads = []
        self.responses = []
        self.cloud = None
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch("socket.socket.connect", side_effect=AssertionError("Unexpected network")))
        self.stack.enter_context(patch("socket.create_connection", side_effect=AssertionError("Unexpected network")))
        self.stack.enter_context(patch("azure.cli.core.util.handle_version_update"))
        self.stack.enter_context(patch("azure.cli.core.util.check_connectivity", return_value=False))
        self.stack.enter_context(patch.object(
            Profile, "get_subscription",
            return_value={"id": SUBSCRIPTION, "tenantId": SUBSCRIPTION, "name": "Offline"},
        ))
        self.stack.enter_context(patch.object(
            Profile, "get_login_credentials", return_value=(_Credential(), SUBSCRIPTION, SUBSCRIPTION),
        ))
        self.stack.enter_context(patch("azure.core.pipeline.transport.RequestsTransport.send",
                                       autospec=True, side_effect=self.send))
        self.stack.enter_context(patch("time.sleep"))

    def send(self, _transport, request, **_kwargs):
        url = urlsplit(request.url)
        query = parse_qs(url.query)
        self.assertEqual(query.get("api-version"), [API_VERSION])
        body = request.body
        if isinstance(body, bytes):
            body = body.decode("utf-8")
        body = json.loads(body) if body else None
        self.calls.append({"method": request.method, "url": request.url, "path": url.path, "body": body})
        if self.http_status:
            return _Response(request, self.http_status, {
                "error": {"code": "FixtureError", "message": "The service rejected this operation."},
            })
        if self.responses:
            status, payload = self.responses.pop(0)
            return _Response(request, status, payload)
        if url.path.endswith("/operationresults/test-operation"):
            if self.location_operation:
                self.assertNotIn("azureAsyncOperation", query)
                status = self.location_responses.pop(0)
                if status == 202:
                    return _Response(request, 202, headers={"Retry-After": "0"})
                if status != 200:
                    return _Response(request, status, {
                        "error": {"code": "FixtureFailure", "message": "The operation failed."},
                    })
                payload = (None if self.operation_method == "DELETE" else
                           _resource(url.path.rsplit("/operationresults/", 1)[0]))
                return _Response(request, 200, payload)
            return _Response(request, 200, {
                "status": self.operation_status,
                **({"error": {"code": "FixtureFailure", "message": "The operation failed."}}
                   if self.operation_status == "Failed" else {}),
            }, {"Retry-After": "0"})
        if self.async_operation and request.method in ("PUT", "DELETE"):
            self.operation_method = request.method
            operation_url = (request.url.split("?", 1)[0] +
                             "/operationresults/test-operation?api-version=" + API_VERSION)
            headers = {"Azure-AsyncOperation": operation_url + "&azureAsyncOperation=1", "Retry-After": "0"}
            if self.location_operation:
                headers["Location"] = operation_url
            return _Response(request, 202, {"status": "InProgress"}, headers)
        if request.method == "POST" and url.path.endswith("/refreshSilos"):
            return _Response(request, 204)
        if request.method == "DELETE":
            return _Response(request, 204)
        if request.method == "GET" and url.path.endswith(("/silos", "/managedTrafficConfig", "/lastKnownGood")):
            payload = {"value": [_resource(url.path + ("/backup" if url.path.endswith("/silos") else "/default"))]}
            if self.paginate and "page" not in query:
                payload["nextLink"] = request.url + "&page=2"
            return _Response(request, 200, payload)
        if request.method == "GET" and url.path.endswith("/virtualNetworkIntegrations"):
            return _Response(request, 200, [{"properties": {"subnetResourceId": SUBNET}}])
        payload = self.reads.pop(0) if self.reads and request.method == "GET" else _resource(url.path)
        if body:
            payload["properties"].update(body.get("properties", {}))
            if "location" in body:
                payload["location"] = body["location"]
        return _Response(request, 200, payload)

    def invoke(self, arguments, expected=0, location_default=None):
        stdout, stderr = io.StringIO(), io.StringIO()
        cli = get_default_cli()
        if self.cloud is not None:
            cli.cloud = self.cloud
        if location_default:
            cli.config.set_value("defaults", "location", location_default)
        with redirect_stdout(stdout), redirect_stderr(stderr):
            try:
                code = cli.invoke(arguments, out_file=stdout)
            except SystemExit as ex:
                code = ex.code
        self.assertEqual(code, expected, "{}\n{}\n{}".format(
            arguments, stderr.getvalue(), getattr(cli.result, "error", None)))
        output_format = "json"
        for flag in ("--output", "-o"):
            if flag in arguments:
                output_format = arguments[arguments.index(flag) + 1]
        if stdout.getvalue().strip() and "--help" not in arguments and output_format == "json":
            return json.loads(stdout.getvalue())
        return stdout.getvalue()

    @staticmethod
    def arguments(entry):
        command = entry["command"]
        args = command.split() + ["-g", "group", "-n", "primary", "--output", "json"]
        if "{silo}" in entry["path"]:
            args += ["--silo", "backup"]
        if command.endswith((" delete", " remove")):
            args += ["--yes"]
        if command.endswith("silo create"):
            args += ["--location", "westus2", "--primary-location", "eastus"]
            args += (["--number-of-workers", "2", "--zone-redundant", "false"]
                     if command.startswith("appservice") else
                     ["--traffic-mode", "Active", "--follow-last-known-good", "false"])
        if command.endswith("silo update"):
            args += (["--number-of-workers", "2", "--zone-redundant", "false"]
                     if command.startswith("appservice") else
                     ["--endpoint-status", "Disabled", "--follow-last-known-good", "false"])
        if command == "webapp managed-traffic update":
            args += ["--traffic-mode", "Passive"]
        if command.endswith(("vnet-integration add", "vnet-integration update")):
            args += ["--subnet", SUBNET]
        if command.endswith(" wait"):
            args += ["--exists", "--interval", "1", "--timeout", "2"]
        return args

    def test_appservice_active_backup_inventory_is_spec_limited_and_preview(self):
        table = COMMAND_LOADER_CLS(cli_ctx=get_default_cli()).load_command_table(None)
        prefixes = ("appservice plan silo ", "webapp silo ", "webapp managed-traffic ", "webapp last-known-good ")
        actual = {name for name in table if name.startswith(prefixes)}
        self.assertEqual(actual, {entry["command"] for entry in COMMANDS})
        self.assertEqual(len(actual), 24)
        for command in actual:
            self.assertIsNotNone(table[command].preview_info, command)

    def test_appservice_active_backup_all_help_loads(self):
        for entry in COMMANDS:
            with self.subTest(command=entry["command"]):
                output = self.invoke(entry["command"].split() + ["--help"])
                self.assertIn("Examples", output)
        self.assertEqual(self.calls, [])

    def test_appservice_active_backup_examples_parse_and_execute(self):
        table = COMMAND_LOADER_CLS(cli_ctx=get_default_cli()).load_command_table(None)
        for entry in COMMANDS:
            command = table[entry["command"]]
            examples = command.help.get("examples", [])
            self.assertGreaterEqual(len(examples), 2, entry["command"])
            for example in examples:
                with self.subTest(command=entry["command"], example=example["name"]):
                    arguments = shlex.split(example["text"])[1:]
                    arguments = [arg.replace("MyGroup", "group").replace("MyPlan", "primary")
                                 .replace("MyApp", "primary").replace("WestPlan", "backup")
                                 .replace("WestApp", "backup") for arg in arguments]
                    if "--deleted" in arguments:
                        self.http_status = 404
                    result = self.invoke(arguments)
                    if entry["command"] == "appservice plan silo vnet-integration list" and "--query" in arguments:
                        self.assertEqual(result, [SUBNET])
                    self.http_status = None

    def test_appservice_active_backup_exact_spec_routes(self):
        expected = set()
        actual = set()
        for entry in COMMANDS:
            with self.subTest(command=entry["command"]):
                self.calls.clear()
                self.invoke(self.arguments(entry))
                path = RESOURCE_ROOT + entry["path"].format(name="primary", silo="backup")
                self.assertEqual([(call["method"], call["path"]) for call in self.calls],
                                 [(method, path) for method in entry["methods"]])
                expected.update((method, path) for method in entry["methods"])
                actual.update((call["method"], call["path"]) for call in self.calls)
        self.assertEqual(actual, expected)
        self.assertEqual(len(actual), 20)

    def test_appservice_active_backup_create_adds_arm_location_and_keeps_generated_fields(self):
        for entry in COMMANDS:
            if not entry["command"].endswith("silo create"):
                continue
            self.calls.clear()
            output = self.invoke(self.arguments(entry))
            body = self.calls[0]["body"]
            self.assertEqual(body["location"], "westus2")
            self.assertEqual(output["location"], "westus2")
            self.assertEqual(body["properties"]["siloLocation"], "westus2")
            self.assertEqual(body["properties"]["primaryLocation"], "eastus")
            field = "zoneRedundantOverride" if entry["command"].startswith("appservice") else "followLastKnownGood"
            self.assertIs(body["properties"][field], False)

    def test_appservice_active_backup_updates_preserve_fields_without_readonly_roundtrip(self):
        for family, flag, value in (
            ("appservice plan", "--number-of-workers", "2"), ("webapp", "--endpoint-status", "Disabled"),
        ):
            self.calls.clear()
            self.invoke(family.split() + [
                "silo", "update", "-g", "group", "-n", "primary", "--silo", "backup", flag, value,
            ])
            props = self.calls[-1]["body"]["properties"]
            self.assertEqual(self.calls[-1]["body"]["location"], "westus2")
            self.assertEqual(props["primaryLocation"], "eastus")
            self.assertNotIn("provisioningState", props)
            self.assertNotIn("revisionNumber", props)
            if family == "webapp":
                self.assertIs(props["followLastKnownGood"], False)

    def test_appservice_active_backup_async_and_no_wait(self):
        self.async_operation = True
        for entry in COMMANDS:
            if not entry["command"].endswith("silo create"):
                continue
            for no_wait in (False, True):
                self.calls.clear()
                args = self.arguments(entry) + (["--no-wait"] if no_wait else [])
                output = self.invoke(args)
                self.assertEqual(len(self.calls), 1 if no_wait else 3)
                if no_wait:
                    self.assertEqual(output, "")
                else:
                    self.assertEqual(output["id"], self.calls[0]["path"])
                    self.assertIn("/operationresults/test-operation", self.calls[1]["path"])
                    self.assertEqual(self.calls[2]["path"], self.calls[0]["path"])

    def test_appservice_active_backup_async_failure_is_not_success(self):
        self.async_operation = True
        self.operation_status = "Failed"
        self.invoke([
            "webapp", "silo", "create", "-g", "group", "-n", "primary", "--silo", "backup",
            "--location", "westus2", "--primary-location", "eastus",
        ], expected=1)
        self.assertEqual(len(self.calls), 2)

    def test_appservice_active_backup_synchronous_no_wait_has_no_receipt(self):
        for entry in COMMANDS:
            if entry["command"].endswith("silo create"):
                self.calls.clear()
                self.assertEqual(self.invoke(self.arguments(entry) + ["--no-wait"]), "")
                self.assertEqual(len(self.calls), 1)

    def test_appservice_active_backup_async_delete_has_no_resource_readback(self):
        self.async_operation = True
        for entry in COMMANDS:
            if not entry["command"].endswith("silo delete"):
                continue
            for no_wait in (False, True):
                self.calls.clear()
                result = self.invoke(self.arguments(entry) + (["--no-wait"] if no_wait else []))
                self.assertEqual(result, "")
                self.assertEqual(len(self.calls), 1 if no_wait else 2)
                self.assertEqual(self.calls[0]["method"], "DELETE")
                if not no_wait:
                    self.assertTrue(self.calls[1]["path"].endswith("/operationresults/test-operation"))

    def test_appservice_active_backup_plan_delete_preserves_standard_and_legacy_conflict_details(self):
        message = "Cannot delete this plan silo because it has site silos associated with it. Delete site silos first."
        for payload in (
            {"error": {"code": "Conflict", "message": message}},
            {"Code": "Conflict", "Message": message},
            {"Error": {"Code": "Conflict", "Message": message}},
        ):
            with self.subTest(payload=payload):
                self.calls.clear()
                self.responses = [(409, payload)]
                with self.assertLogs("cli.azure.cli.core.azclierror", level="ERROR") as logged:
                    self.invoke([
                        "appservice", "plan", "silo", "delete", "-g", "group", "-n", "primary",
                        "--silo", "backup", "--yes",
                    ], expected=1)
                output = "\n".join(logged.output)
                self.assertIn(message, output)
                self.assertNotIn("invalid status", output)
                self.assertEqual([call["method"] for call in self.calls], ["DELETE"])

    def test_appservice_active_backup_plan_delete_does_not_invent_dependency_errors(self):
        message = "Another operation is in progress."
        self.responses = [(409, {"Code": "Conflict", "Message": message})]
        with self.assertLogs("cli.azure.cli.core.azclierror", level="ERROR") as logged:
            self.invoke([
                "appservice", "plan", "silo", "delete", "-g", "group", "-n", "primary",
                "--silo", "backup", "--yes",
            ], expected=1)
        output = "\n".join(logged.output)
        self.assertIn(message, output)
        self.assertNotIn("site silo", output)
        self.assertEqual(len(self.calls), 1)

    def test_appservice_active_backup_plan_delete_unstructured_conflicts_still_fail(self):
        for payload in (None, {"unexpected": "value"}, "not an error object"):
            with self.subTest(payload=payload):
                self.calls.clear()
                self.responses = [(409, payload)]
                with self.assertLogs("cli.azure.cli.core.azclierror", level="ERROR") as logged:
                    self.invoke([
                        "appservice", "plan", "silo", "delete", "-g", "group", "-n", "primary",
                        "--silo", "backup", "--yes",
                    ], expected=1)
                output = "\n".join(logged.output)
                self.assertIn("Operation returned an invalid status 'Conflict'", output)
                self.assertNotIn("site silo", output)
                self.assertEqual(len(self.calls), 1)

    def test_appservice_active_backup_plan_delete_keeps_conflict_exception_type_and_status(self):
        from types import SimpleNamespace
        from azure.core.exceptions import ResourceExistsError
        from azure.cli.core.aaz._command_ctx import AAZCommandCtx
        from azure.cli.command_modules.appservice.operations.active_backup import PlanSiloDelete
        operation = PlanSiloDelete.ServerFarmSiloResourcesDeleteServerFarmSilo(ctx=SimpleNamespace(
            get_http_client=lambda _kind: None, get_error_format=AAZCommandCtx.get_error_format,
        ))
        response = _Response(HttpRequest("DELETE", "https://management.azure.com/example"), 409, {
            "Code": "Conflict", "Message": "Service-provided failure.",
        })
        with self.assertRaises(ResourceExistsError) as caught:
            operation.on_error(response)
        self.assertEqual(caught.exception.status_code, 409)
        self.assertIs(caught.exception.response, response)
        self.assertEqual(caught.exception.error.message, "Service-provided failure.")

    def test_appservice_active_backup_resource_waits(self):
        path = RESOURCE_ROOT + "/sites/primary/silos/backup"
        pending = _resource(path)
        pending["properties"]["provisioningState"] = "Creating"
        self.reads = [pending, _resource(path)]
        result = self.invoke([
            "webapp", "silo", "wait", "--ids", path, "--created", "--interval", "1", "--timeout", "2",
        ])
        self.assertEqual(result, "")
        self.assertEqual(len(self.calls), 2)
        self.calls.clear()
        self.http_status = 404
        result = self.invoke([
            "webapp", "silo", "wait", "--ids", path, "--deleted", "--interval", "1", "--timeout", "2",
        ])
        self.assertEqual(result, "")
        self.assertEqual(len(self.calls), 1)

    def test_appservice_active_backup_refresh_acceptance_and_conflict(self):
        args = ["webapp", "silo", "refresh", "-g", "group", "-n", "primary"]
        self.assertEqual(self.invoke(args), "")
        self.assertEqual(len(self.calls), 1)
        self.calls.clear()
        self.http_status = 409
        self.invoke(args, expected=1)
        self.assertEqual(len(self.calls), 1)

    def test_appservice_active_backup_origin_read_uses_matching_collection_resource_and_warns(self):
        for identity in (["--ids", ORIGIN], ["-g", "group", "-n", "primary", "--silo", "ORIGIN"]):
            with self.subTest(identity=identity):
                self.calls.clear()
                origin = _resource(ORIGIN)
                self.responses = [(404, None), (200, {"value": [_resource(ORIGIN + "-other"), origin]})]
                with self.assertLogs(
                        "cli.azure.cli.command_modules.appservice.operations.active_backup", level="WARNING") as logged:
                    output = self.invoke(["webapp", "silo", "show"] + identity)
                self.assertEqual(output["id"], ORIGIN)
                self.assertEqual(output["location"], "eastus")
                self.assertEqual(output["properties"]["endpointStatus"], "Enabled")
                self.assertNotIn("inboundIpAddress", output["properties"])
                self.assertIn("Origin point GET returned HTTP 404", logged.output[0])
                self.assertEqual([call["method"] for call in self.calls], ["GET", "GET"])
                self.assertEqual(self.calls[1]["path"], ORIGIN.rsplit("/", 1)[0])

    def test_appservice_active_backup_successful_origin_read_does_not_use_collection(self):
        output = self.invoke(["webapp", "silo", "show", "--ids", ORIGIN])
        self.assertEqual(output["id"], ORIGIN)
        self.assertEqual([(call["method"], call["path"]) for call in self.calls], [("GET", ORIGIN)])

    def test_appservice_active_backup_origin_read_searches_generated_pagination(self):
        next_link = "https://management.azure.com" + ORIGIN.rsplit("/", 1)[0] + "?api-version=" + API_VERSION + "&page=2"
        self.responses = [
            (404, None), (200, {"value": [], "nextLink": next_link}),
            (200, {"value": [_resource(ORIGIN)]}),
        ]
        output = self.invoke(["webapp", "silo", "show", "--ids", ORIGIN])
        self.assertEqual(output["id"], ORIGIN)
        self.assertEqual(len(self.calls), 3)
        self.assertEqual(parse_qs(urlsplit(self.calls[-1]["url"]).query)["page"], ["2"])
        self.assertEqual(self.responses, [])

    def test_appservice_active_backup_origin_read_preserves_missing_and_unrelated_errors(self):
        for command, status, expected in (
            (["webapp", "silo", "show", "--ids", ORIGIN + "-missing"], 404, 3),
            (["appservice", "plan", "silo", "show", "--ids", ORIGIN.replace("/sites/", "/serverfarms/")], 404, 3),
            *[(["webapp", "silo", "show", "--ids", ORIGIN], status, 1) for status in (400, 401, 403, 409)],
        ):
            with self.subTest(command=command, status=status):
                self.calls.clear()
                self.responses = [(status, {"error": {"code": "FixtureError", "message": "Original failure."}})]
                self.invoke(command, expected=expected)
                self.assertEqual(len(self.calls), 1)
        self.calls.clear()
        self.responses = [(404, None), (403, {"error": {"code": "Forbidden", "message": "Collection denied."}})]
        self.invoke(["webapp", "silo", "show", "--ids", ORIGIN], expected=1)
        self.assertEqual(len(self.calls), 2)

    def test_appservice_active_backup_origin_read_requires_exact_id_and_unique_valid_resource(self):
        for resource_id in (
            ORIGIN + "-other", ORIGIN.replace("/primary/", "/other/"),
            ORIGIN.replace(SUBSCRIPTION, "00000000-0000-0000-0000-000000000002"),
            ORIGIN.replace("/silos/", "/providers/Other.Provider/silos/"),
        ):
            with self.subTest(resource_id=resource_id):
                self.calls.clear()
                self.responses = [(404, None), (200, {"value": [_resource(resource_id)]})]
                self.invoke(["webapp", "silo", "show", "--ids", ORIGIN], expected=3)
                self.assertEqual(len(self.calls), 2)
        for field, value in (("type", "Microsoft.Web/serverfarms/silos"), ("properties", None)):
            with self.subTest(field=field):
                origin = _resource(ORIGIN)
                origin[field] = value
                self.responses = [(404, None), (200, {"value": [origin]})]
                self.invoke(["webapp", "silo", "show", "--ids", ORIGIN], expected=1)
        next_link = "https://management.azure.com" + ORIGIN.rsplit("/", 1)[0] + "?api-version=" + API_VERSION + "&page=2"
        self.responses = [
            (404, None), (200, {"value": [_resource(ORIGIN)], "nextLink": next_link}),
            (200, {"value": [_resource(ORIGIN.upper())]}),
        ]
        self.invoke(["webapp", "silo", "show", "--ids", ORIGIN], expected=1)
        self.assertEqual(self.responses, [])

    def test_appservice_active_backup_origin_update_reuses_generated_get_and_put(self):
        origin = _resource(ORIGIN)
        origin["properties"]["followLastKnownGood"] = True
        self.responses = [(404, None), (200, {"value": [origin]})]
        output = self.invoke(["webapp", "silo", "update", "--ids", ORIGIN, "--endpoint-status", "Disabled"])
        self.assertEqual([call["method"] for call in self.calls], ["GET", "GET", "PUT"])
        self.assertEqual(self.calls[-1]["path"], ORIGIN)
        body = self.calls[-1]["body"]
        self.assertEqual(body["location"], "eastus")
        self.assertEqual(body["properties"]["endpointStatus"], "Disabled")
        self.assertIs(body["properties"]["followLastKnownGood"], True)
        self.assertNotIn("revisionNumber", body["properties"])
        self.assertEqual(output["properties"]["endpointStatus"], "Disabled")

    def test_appservice_active_backup_origin_fallback_does_not_mask_update_failure(self):
        self.responses = [
            (404, None), (200, {"value": [_resource(ORIGIN)]}),
            (409, {"error": {"code": "Conflict", "message": "Update rejected."}}),
        ]
        self.invoke(["webapp", "silo", "update", "--ids", ORIGIN, "--endpoint-status", "Disabled"], expected=1)
        self.assertEqual([call["method"] for call in self.calls], ["GET", "GET", "PUT"])
        self.assertEqual(self.responses, [])

    def test_appservice_active_backup_origin_wait_checks_collection_state_and_actual_absence(self):
        pending = _resource(ORIGIN)
        pending["properties"]["provisioningState"] = "Creating"
        for condition, pages in (
            ("--created", [{"value": [pending]}, {"value": [_resource(ORIGIN)]}]),
            ("--deleted", [{"value": [_resource(ORIGIN)]}, {"value": []}]),
        ):
            with self.subTest(condition=condition):
                self.calls.clear()
                self.responses = [(404, None), (200, pages[0]), (404, None), (200, pages[1])]
                self.invoke(["webapp", "silo", "wait", "--ids", ORIGIN, condition, "--interval", "1", "--timeout", "2"])
                self.assertEqual([call["method"] for call in self.calls], ["GET"] * 4)
                self.assertEqual(self.responses, [])

    def test_appservice_active_backup_origin_read_preserves_cloud_subscription_and_encoded_identity(self):
        from azure.cli.core.cloud import get_cloud
        self.cloud = get_cloud(get_default_cli(), "AzureUSGovernment")
        target = ORIGIN.replace(SUBSCRIPTION, "00000000-0000-0000-0000-000000000002").replace("/group/", "/group space/")
        self.responses = [(404, None), (200, {"value": [_resource(target.upper())]})]
        output = self.invoke(["webapp", "silo", "show", "--ids", target])
        self.assertEqual(output["id"], target.upper())
        self.assertEqual(len(self.calls), 2)
        for call in self.calls:
            self.assertEqual(urlsplit(call["url"]).hostname, "management.usgovcloudapi.net")
            self.assertIn("/subscriptions/00000000-0000-0000-0000-000000000002/", call["path"])
            self.assertIn("/resourceGroups/group%20space/", call["path"])

    def test_appservice_active_backup_lists_follow_next_link(self):
        self.paginate = True
        result = self.invoke(["webapp", "silo", "list", "-g", "group", "-n", "primary"])
        self.assertEqual(len(result), 2)
        self.assertEqual(len(self.calls), 2)
        self.assertEqual(parse_qs(urlsplit(self.calls[1]["url"]).query)["page"], ["2"])

    def test_appservice_active_backup_traffic_uses_structured_arguments(self):
        self.invoke([
            "webapp", "managed-traffic", "update", "-g", "group", "-n", "primary",
            "--traffic-mode", "Active",
            "--endpoints", "[{region:eastus,weight:1},{region:westus2,weight:1000,is-weight-auto-computed:false}]",
        ])
        endpoints = self.calls[-1]["body"]["properties"]["endpoints"]
        self.assertEqual([item["weight"] for item in endpoints], [1, 1000])
        self.assertIs(endpoints[1]["isWeightAutoComputed"], False)
        self.calls.clear()
        self.invoke([
            "webapp", "managed-traffic", "list", "-g", "group", "-n", "primary", "--expand", "endpoints",
        ])
        self.assertEqual(parse_qs(urlsplit(self.calls[0]["url"]).query)["$expand"], ["endpoints"])

    def test_appservice_active_backup_invalid_traffic_bounds_send_no_request(self):
        for value in ("0", "1001"):
            self.invoke([
                "webapp", "managed-traffic", "update", "-g", "group", "-n", "primary",
                "--endpoints", "[{region:eastus,weight:" + value + "}]",
            ], expected=1)
        self.assertEqual(self.calls, [])

    def test_appservice_active_backup_vnet_update_is_patch(self):
        self.invoke([
            "webapp", "silo", "vnet-integration", "update", "-g", "group", "-n", "primary", "--silo", "backup",
            "--subnet", SUBNET, "--swift-supported", "false",
        ])
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(self.calls[0]["method"], "PATCH")
        self.assertEqual(self.calls[0]["body"]["properties"], {"subnetResourceId": SUBNET, "swiftSupported": False})

    def test_appservice_active_backup_plan_vnet_list_accepts_array_and_arm_envelope(self):
        properties = {"subnetResourceId": SUBNET, "swiftSupported": False}
        for payload in (
            [{"properties": properties}],
            {"id": RESOURCE_ROOT + "/serverfarms/physical/virtualNetworkIntegrations",
             "type": "Microsoft.Web/serverfarms/virtualNetworkIntegrations", "location": "westus2",
             "properties": [{**properties, "subnetIpAllocation": {"subnetIpAddressesAvailable": 59}}]},
        ):
            with self.subTest(payload=payload):
                self.calls.clear()
                self.responses = [(200, payload)]
                output = self.invoke([
                    "appservice", "plan", "silo", "vnet-integration", "list",
                    "-g", "group", "-n", "primary", "--silo", "backup",
                ])
                self.assertEqual(output, [properties])
                self.assertNotIn("id", output[0])
                self.assertEqual(len(self.calls), 1)
                self.assertEqual(self.calls[0]["method"], "GET")

    def test_appservice_active_backup_plan_vnet_list_empty_results(self):
        for payload in ([], {"type": "Microsoft.Web/serverfarms/virtualNetworkIntegrations", "properties": []}):
            self.responses = [(200, payload)]
            self.assertEqual(self.invoke([
                "appservice", "plan", "silo", "vnet-integration", "list",
                "-g", "group", "-n", "primary", "--silo", "backup",
            ]), [])

    def test_appservice_active_backup_plan_vnet_list_rejects_unexpected_shapes(self):
        envelope = {"type": "Microsoft.Web/serverfarms/virtualNetworkIntegrations", "properties": []}
        for payload in (
            None, {}, {"value": []}, [None], {**envelope, "type": "Microsoft.Web/sites/silos"},
            {**envelope, "properties": {}}, {**envelope, "properties": [None]},
            {**envelope, "properties": [{}]}, {**envelope, "properties": [{"subnetResourceId": ""}]},
        ):
            with self.subTest(payload=payload):
                self.calls.clear()
                self.responses = [(200, payload)]
                self.invoke([
                    "appservice", "plan", "silo", "vnet-integration", "list",
                    "-g", "group", "-n", "primary", "--silo", "backup",
                ], expected=1)
                self.assertEqual(len(self.calls), 1)

    def test_appservice_active_backup_plan_vnet_list_preserves_service_errors(self):
        for status, expected in ((403, 1), (404, 3)):
            self.calls.clear()
            self.responses = [(status, {"error": {"code": "FixtureError", "message": "List rejected."}})]
            self.invoke([
                "appservice", "plan", "silo", "vnet-integration", "list",
                "-g", "group", "-n", "primary", "--silo", "backup",
            ], expected=expected)
            self.assertEqual(len(self.calls), 1)

    def test_appservice_active_backup_create_requires_explicit_locations(self):
        self.invoke([
            "webapp", "silo", "create", "-g", "group", "-n", "primary", "--silo", "backup",
            "--primary-location", "eastus",
        ], expected=2, location_default="centralus")
        self.assertEqual(self.calls, [])

    def test_appservice_active_backup_update_does_not_inherit_location_default(self):
        self.invoke([
            "webapp", "silo", "update", "-g", "group", "-n", "primary", "--silo", "backup",
            "--endpoint-status", "Disabled",
        ], location_default="centralus")
        self.assertEqual(self.calls[-1]["body"]["location"], "westus2")

    def test_appservice_active_backup_generic_set_is_supported(self):
        self.invoke([
            "appservice", "plan", "silo", "update", "-g", "group", "-n", "primary", "--silo", "backup",
            "--set", "properties.instanceNumberOverride=2",
        ])
        self.assertEqual(self.calls[-1]["body"]["properties"]["instanceNumberOverride"], 2)

    def test_appservice_active_backup_nested_ids(self):
        for family, segment in (("appservice plan", "serverfarms"), ("webapp", "sites")):
            self.calls.clear()
            target = RESOURCE_ROOT + "/{}/primary/silos/backup".format(segment)
            self.invoke(family.split() + ["silo", "show", "--ids", target])
            self.assertEqual(self.calls[0]["path"], target)

    def test_appservice_active_backup_ids_do_not_retarget_other_resource_types(self):
        invalid = [
            RESOURCE_ROOT + "/serverfarms/primary/silos/backup",
            RESOURCE_ROOT + "/sites/primary/slots/staging/silos/backup",
            RESOURCE_ROOT + "/sites/primary/providers/Other.Provider/silos/backup",
        ]
        for target in invalid:
            with self.subTest(resource_id=target):
                self.calls.clear()
                self.invoke(["webapp", "silo", "show", "--ids", target], expected=1)
                self.assertEqual(self.calls, [])

    def test_appservice_active_backup_parent_ids(self):
        for command in ("webapp managed-traffic show", "webapp last-known-good show", "webapp silo refresh"):
            self.calls.clear()
            self.invoke(command.split() + ["--ids", RESOURCE_ROOT + "/sites/primary"])
            self.assertEqual(len(self.calls), 1)
            self.calls.clear()
            self.invoke(command.split() + ["--ids", RESOURCE_ROOT + "/serverfarms/primary"], expected=1)
            self.assertEqual(self.calls, [])

    def test_appservice_active_backup_invalid_ids_cannot_mutate_or_wait_on_other_silos(self):
        for entry in COMMANDS:
            if "{silo}" not in entry["path"] or entry["command"].endswith((" create", " show")):
                continue
            command = entry["command"]
            wrong_parent = "sites" if command.startswith("appservice") else "serverfarms"
            target = RESOURCE_ROOT + "/{}/primary/silos/backup".format(wrong_parent)
            args = command.split() + ["--ids", target]
            if command.endswith((" delete", " remove")):
                args += ["--yes"]
            if command.endswith(" wait"):
                args += ["--exists"]
            with self.subTest(command=command):
                self.invoke(args, expected=2 if entry.get("key") == "C07" else 1)
                self.assertEqual(self.calls, [])

    def test_appservice_active_backup_selected_cloud(self):
        from azure.cli.core.cloud import get_cloud
        self.cloud = get_cloud(get_default_cli(), "AzureUSGovernment")
        self.invoke(["webapp", "silo", "show", "-g", "group", "-n", "primary", "--silo", "backup"])
        self.assertEqual(urlsplit(self.calls[0]["url"]).hostname, "management.usgovcloudapi.net")

    def test_appservice_active_backup_does_not_mark_existing_groups_preview(self):
        loader = COMMAND_LOADER_CLS(cli_ctx=get_default_cli())
        table = loader.load_command_table(None)
        self.assertIsNone(table["webapp show"].preview_info)
        self.assertIsNone(table["appservice plan show"].preview_info)
        self.assertNotIn("preview_info", loader.command_group_table["webapp"].group_kwargs)

    def test_appservice_active_backup_location_customizations_inherit_generated_commands(self):
        from azure.cli.command_modules.appservice.operations import active_backup as custom
        from azure.cli.command_modules.appservice.aaz.latest.appservice.plan import silo as plan
        from azure.cli.command_modules.appservice.aaz.latest.webapp import silo as site
        from azure.cli.command_modules.appservice.aaz.latest.appservice.plan.silo.vnet_integration import List
        self.assertEqual(custom.PlanSiloVnetList.__bases__, (List,))
        self.assertEqual(
            custom.PlanSiloVnetList.ServerFarmSiloResourcesGetServerFarmSiloVnetIntegrations.__bases__,
            (List.ServerFarmSiloResourcesGetServerFarmSiloVnetIntegrations,),
        )
        for prefix, generated in (("PlanSilo", plan), ("SiteSilo", site)):
            for verb in ("Create", "Update", "Delete", "Show", "List", "Wait"):
                cls = getattr(custom, prefix + verb)
                self.assertEqual(cls.__bases__, (getattr(generated, verb),))
        self.assertEqual(
            custom.PlanSiloCreate.ServerFarmSiloResourcesCreateOrUpdateServerFarmSilo.__bases__,
            (plan.Create.ServerFarmSiloResourcesCreateOrUpdateServerFarmSilo,),
        )
        self.assertEqual(
            custom.SiteSiloCreate.SiteSiloResourcesCreateOrUpdateSiteSilo.__bases__,
            (site.Create.SiteSiloResourcesCreateOrUpdateSiteSilo,),
        )

    def test_appservice_active_backup_read_and_list_preserve_service_location(self):
        for family in ("appservice plan", "webapp"):
            shown = self.invoke(family.split() + ["silo", "show", "-g", "group", "-n", "primary", "--silo", "backup"])
            self.assertEqual(shown["location"], "westus2")
            listed = self.invoke(family.split() + ["silo", "list", "-g", "group", "-n", "primary"])
            self.assertEqual(listed[0]["location"], "westus2")

    def test_appservice_active_backup_update_accepts_nested_location_metadata(self):
        for family, segment in (("appservice plan", "serverfarms"), ("webapp", "sites")):
            self.calls.clear()
            data = _resource(RESOURCE_ROOT + "/{}/primary/silos/backup".format(segment))
            del data["location"]
            data["properties"]["siloLocation"] = "westus2"
            self.reads = [data]
            self.invoke(family.split() + ["silo", "update", "-g", "group", "-n", "primary", "--silo", "backup"])
            self.assertEqual(self.calls[-1]["body"]["location"], "westus2")

    def test_appservice_active_backup_update_requires_real_location_metadata(self):
        for missing in (True, False):
            self.calls.clear()
            data = _resource(RESOURCE_ROOT + "/sites/primary/silos/backup")
            if missing:
                del data["location"]
            else:
                data["properties"]["siloLocation"] = "eastus"
            self.reads = [data]
            self.invoke([
                "webapp", "silo", "update", "-g", "group", "-n", "primary", "--silo", "backup",
                "--endpoint-status", "Enabled",
            ], expected=1, location_default="centralus")
            self.assertEqual([call["method"] for call in self.calls], ["GET"])

    def test_appservice_active_backup_update_cannot_change_or_remove_location(self):
        for flags in (
            ["--location", "eastus"],
            ["--set", "location=eastus"],
            ["--set", "properties.siloLocation=eastus"],
            ["--remove", "location"],
        ):
            self.calls.clear()
            self.invoke([
                "webapp", "silo", "update", "-g", "group", "-n", "primary", "--silo", "backup",
            ] + flags, expected=1)
            self.assertEqual([call["method"] for call in self.calls], ["GET"])

    def test_appservice_active_backup_update_retains_service_location_spelling(self):
        data = _resource(RESOURCE_ROOT + "/sites/primary/silos/backup")
        data["location"] = "West US 2"
        self.reads = [data]
        self.invoke([
            "webapp", "silo", "update", "-g", "group", "-n", "primary", "--silo", "backup", "--location", "westus2",
        ])
        self.assertEqual(self.calls[-1]["body"]["location"], "West US 2")

    def test_appservice_active_backup_location_polling_accepts_empty_pending_responses(self):
        self.async_operation = True
        self.location_operation = True
        for entry in COMMANDS:
            if not entry["command"].endswith(("silo create", "silo update", "silo delete")):
                continue
            with self.subTest(command=entry["command"]):
                self.calls.clear()
                self.location_responses = [202, 200]
                result = self.invoke(self.arguments(entry))
                self.assertEqual([call["method"] for call in self.calls],
                                 entry["methods"] + ["GET", "GET"])
                self.assertEqual(self.location_responses, [])
                if entry["command"].endswith("delete"):
                    self.assertEqual(result, "")
                else:
                    self.assertEqual(result["id"], self.calls[-1]["path"].rsplit("/operationresults/", 1)[0])

    def test_appservice_active_backup_location_polling_preserves_no_wait(self):
        self.async_operation = True
        self.location_operation = True
        for entry in COMMANDS:
            if not entry["command"].endswith(("silo create", "silo update", "silo delete")):
                continue
            self.calls.clear()
            self.assertEqual(self.invoke(self.arguments(entry) + ["--no-wait"]), "")
            self.assertEqual([call["method"] for call in self.calls], entry["methods"])

    def test_appservice_active_backup_location_polling_preserves_core_error_handling(self):
        self.async_operation = True
        self.location_operation = True
        for entry in COMMANDS:
            if not entry["command"].endswith(("silo create", "silo update", "silo delete")):
                continue
            for status, exit_code in ((409, 1), (404, 3)):
                # CLI core already treats a polling 404 as completion for long-running deletes, not PUTs.
                expected = 0 if status == 404 and entry["command"].endswith("delete") else exit_code
                with self.subTest(command=entry["command"], status=status):
                    self.calls.clear()
                    self.location_responses = [202, status]
                    self.invoke(self.arguments(entry), expected=expected)
                    self.assertEqual(self.location_responses, [])
                    self.assertEqual([call["method"] for call in self.calls],
                                     entry["methods"] + ["GET", "GET"])

    def test_appservice_active_backup_polling_hook_preserves_other_hooks_and_async_only_headers(self):
        from types import SimpleNamespace
        from azure.cli.command_modules.appservice.operations.active_backup import _prefer_location_polling
        original = CaseInsensitiveDict({"Location": "location-monitor", "Azure-AsyncOperation": "async-monitor"})
        response = SimpleNamespace(http_response=SimpleNamespace(headers=original))
        observed = []
        _prefer_location_polling(response, hook=lambda value: observed.append(
            value.http_response.headers["Azure-AsyncOperation"]))
        self.assertEqual(observed, ["async-monitor"])
        self.assertNotIn("Azure-AsyncOperation", original)
        original.pop("Location")
        original["Azure-AsyncOperation"] = "async-only"
        _prefer_location_polling(response)
        self.assertEqual(original["Azure-AsyncOperation"], "async-only")
