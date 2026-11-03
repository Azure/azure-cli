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
from azure.core.pipeline.transport import HttpResponse
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
        result["tags"] = {"existing": "preserved"}
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


def _plan_integrations():
    return {
        "id": RESOURCE_ROOT + "/serverfarms/physical/virtualNetworkIntegrations",
        "name": None,
        "type": "Microsoft.Web/serverfarms/virtualNetworkIntegrations",
        "location": "westus2",
        "properties": [{
            "subnetResourceId": SUBNET,
            "subnetIpAllocation": {"subnetIpAddressesAvailable": 59, "subnetIpAddressesUsed": 5},
            "resourceAllocation": {
                "connectedSitesId": [RESOURCE_ROOT + "/sites/primary"],
                "connectedServerFarmsId": [RESOURCE_ROOT + "/serverfarms/primary"],
            },
        }],
    }


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
        self.include_location_monitor = False
        self.empty_async_status = False
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
            self.assertIn("azureAsyncOperation", query)
            if self.empty_async_status:
                return _Response(request, 202)
            return _Response(request, 200, {
                "status": self.operation_status,
                **({"error": {"code": "FixtureFailure", "message": "The operation failed."}}
                   if self.operation_status in ("Failed", "Canceled") else {}),
            }, {"Retry-After": "0"})
        if self.async_operation and request.method in ("PUT", "DELETE"):
            self.operation_method = request.method
            operation_url = (request.url.split("?", 1)[0] +
                             "/operationresults/test-operation?api-version=" + API_VERSION)
            headers = {"Azure-AsyncOperation": operation_url + "&azureAsyncOperation=1", "Retry-After": "0"}
            if self.include_location_monitor:
                headers["Location"] = operation_url
            return _Response(request, 202, _resource(url.path), headers)
        if request.method == "POST" and url.path.endswith("/refreshSilos"):
            return _Response(request, 204)
        if request.method == "DELETE":
            return _Response(request, 204)
        if request.method == "GET" and url.path.endswith(
                ("/silos", "/managedTrafficConfig", "/lastKnownGood", "/virtualNetworkConnections")):
            suffix = ("/backup" if url.path.endswith("/silos") else
                      "/virtualNetwork" if url.path.endswith("/virtualNetworkConnections") else "/default")
            payload = {"value": [_resource(url.path + suffix)]}
            if self.paginate and "page" not in query:
                payload["nextLink"] = request.url + "&page=2"
            return _Response(request, 200, payload)
        if request.method == "GET" and url.path.endswith("/virtualNetworkIntegrations"):
            return _Response(request, 200, _plan_integrations())
        payload = self.reads.pop(0) if self.reads and request.method == "GET" else _resource(url.path)
        if body:
            payload["properties"].update(body.get("properties", {}))
            for key in ("location", "tags"):
                if key in body:
                    payload[key] = body[key]
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
        self.assertEqual(len(actual), 25)
        for command in actual:
            self.assertIsNotNone(table[command].preview_info, command)
            self.assertIn(".appservice.aaz.latest.", type(table[command]).__module__, command)

    def test_appservice_active_backup_all_help_loads(self):
        for entry in COMMANDS:
            with self.subTest(command=entry["command"]):
                output = self.invoke(entry["command"].split() + ["--help"])
                self.assertIn("Examples", output)
        self.assertEqual(self.calls, [])

    def test_appservice_active_backup_examples_parse_and_execute(self):
        table = COMMAND_LOADER_CLS(cli_ctx=get_default_cli()).load_command_table(None)
        for entry in COMMANDS:
            examples = table[entry["command"]].help.get("examples", [])
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
                    if "vnet-integration list" in entry["command"] and "--query" in arguments:
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
        self.assertEqual(len(actual), 21)

    def test_appservice_active_backup_create_uses_root_location_and_tags(self):
        for entry in COMMANDS:
            if not entry["command"].endswith("silo create"):
                continue
            self.calls.clear()
            output = self.invoke(self.arguments(entry) + ["--tags", "environment=preview"])
            body = self.calls[0]["body"]
            self.assertEqual(body["location"], "westus2")
            self.assertEqual(output["location"], "westus2")
            self.assertEqual(body["tags"], {"environment": "preview"})
            self.assertNotIn("siloLocation", body["properties"])
            self.assertEqual(body["properties"]["primaryLocation"], "eastus")
            field = "zoneRedundantOverride" if entry["command"].startswith("appservice") else "followLastKnownGood"
            self.assertIs(body["properties"][field], False)

    def test_appservice_active_backup_nested_location_remains_a_separate_property(self):
        args = self.arguments(next(entry for entry in COMMANDS if entry["command"] == "webapp silo create"))
        self.invoke(args + ["--silo-location", "westus2"])
        self.assertEqual(self.calls[0]["body"]["location"], "westus2")
        self.assertEqual(self.calls[0]["body"]["properties"]["siloLocation"], "westus2")

    def test_appservice_active_backup_create_uses_standard_location_default(self):
        self.invoke([
            "webapp", "silo", "create", "-g", "group", "-n", "primary", "--silo", "backup",
            "--primary-location", "eastus",
        ], location_default="westus2")
        self.assertEqual(self.calls[0]["body"]["location"], "westus2")

    def test_appservice_active_backup_create_requires_primary_location_before_request(self):
        for family in ("appservice plan", "webapp"):
            for properties in ([], ["--number-of-workers", "2"] if family == "appservice plan" else
                               ["--traffic-mode", "Active"]):
                with self.subTest(family=family, properties=properties):
                    self.calls.clear()
                    self.invoke(family.split() + [
                        "silo", "create", "-g", "group", "-n", "primary", "--silo", "backup",
                        "--location", "westus2",
                    ] + properties, expected=2)
                    self.assertEqual(self.calls, [])

    def test_appservice_active_backup_updates_preserve_fields_without_readonly_roundtrip(self):
        for family, flag, value in (
            ("appservice plan", "--number-of-workers", "2"), ("webapp", "--endpoint-status", "Disabled"),
        ):
            self.calls.clear()
            self.invoke(family.split() + [
                "silo", "update", "-g", "group", "-n", "primary", "--silo", "backup", flag, value,
            ], location_default="centralus")
            body = self.calls[-1]["body"]
            self.assertEqual([call["method"] for call in self.calls], ["GET", "PUT"])
            self.assertEqual(body["location"], "westus2")
            self.assertEqual(body["tags"], {"existing": "preserved"})
            self.assertEqual(body["properties"]["primaryLocation"], "eastus")
            self.assertNotIn("provisioningState", body["properties"])
            self.assertNotIn("revisionNumber", body["properties"])
            if family == "webapp":
                self.assertIs(body["properties"]["followLastKnownGood"], False)

    def test_appservice_active_backup_updates_support_tags_and_generic_set(self):
        for family in ("appservice plan", "webapp"):
            self.calls.clear()
            self.invoke(family.split() + [
                "silo", "update", "-g", "group", "-n", "primary", "--silo", "backup",
                "--tags", "environment=preview",
            ])
            self.assertEqual([call["method"] for call in self.calls], ["GET", "PUT"])
            self.assertEqual(self.calls[-1]["body"]["tags"], {"existing": "preserved", "environment": "preview"})
        self.invoke([
            "appservice", "plan", "silo", "update", "-g", "group", "-n", "primary", "--silo", "backup",
            "--set", "properties.instanceNumberOverride=2",
        ])
        self.assertEqual(self.calls[-1]["body"]["properties"]["instanceNumberOverride"], 2)

    def test_appservice_active_backup_update_does_not_expose_create_only_arguments(self):
        for flag, value in (("--location", "eastus"), ("--traffic-mode", "Passive")):
            self.invoke([
                "webapp", "silo", "update", "-g", "group", "-n", "primary", "--silo", "backup", flag, value,
            ], expected=2)
        self.assertEqual(self.calls, [])

    def test_appservice_active_backup_async_and_no_wait(self):
        self.async_operation = True
        for entry in COMMANDS:
            if not entry["command"].endswith(("silo create", "silo update", "silo delete")):
                continue
            for no_wait in (False, True):
                with self.subTest(command=entry["command"], no_wait=no_wait):
                    self.calls.clear()
                    output = self.invoke(self.arguments(entry) + (["--no-wait"] if no_wait else []))
                    delete = entry["command"].endswith("delete")
                    expected = len(entry["methods"]) + (0 if no_wait else 1 if delete else 2)
                    self.assertEqual(len(self.calls), expected)
                    if no_wait or delete:
                        self.assertEqual(output, "")
                    else:
                        self.assertEqual(output["id"], self.calls[0]["path"])
                        self.assertEqual(self.calls[-1]["path"], self.calls[0]["path"])

    def test_appservice_active_backup_async_failure_is_not_success(self):
        self.async_operation = True
        for status in ("Failed", "Canceled"):
            self.calls.clear()
            self.operation_status = status
            self.invoke([
                "webapp", "silo", "create", "-g", "group", "-n", "primary", "--silo", "backup",
                "--location", "westus2", "--primary-location", "eastus",
            ], expected=1)
            self.assertEqual(len(self.calls), 2)

    def test_appservice_active_backup_prefers_standard_azure_async_monitor(self):
        self.async_operation = True
        self.include_location_monitor = True
        self.invoke([
            "webapp", "silo", "create", "-g", "group", "-n", "primary", "--silo", "backup",
            "--location", "westus2", "--primary-location", "eastus",
        ])
        self.assertEqual(len(self.calls), 3)
        self.assertEqual(parse_qs(urlsplit(self.calls[1]["url"]).query)["azureAsyncOperation"], ["1"])

    def test_appservice_active_backup_empty_async_status_is_not_hidden(self):
        self.async_operation = True
        self.include_location_monitor = True
        self.empty_async_status = True
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

    def test_appservice_active_backup_service_errors_are_not_retried_or_rewritten(self):
        for command in (
            ["appservice", "plan", "silo", "delete", "-g", "group", "-n", "primary",
             "--silo", "backup", "--yes"],
            ["webapp", "silo", "vnet-integration", "list", "-g", "group", "-n", "primary", "--silo", "backup"],
        ):
            for payload in (
                {"error": {"code": "Conflict", "message": "Service-provided failure."}},
                {"Code": "Conflict", "Message": "Service-provided failure."},
                None,
            ):
                with self.subTest(command=command, payload=payload):
                    self.calls.clear()
                    self.responses = [(409, payload)]
                    self.invoke(command, expected=1)
                    self.assertEqual(len(self.calls), 1)

    def test_appservice_active_backup_origin_not_found_does_not_fall_back_to_collection(self):
        for status, expected in ((404, 3), (403, 1), (409, 1)):
            self.calls.clear()
            self.responses = [(status, {"error": {"code": "FixtureError", "message": "Original failure."}})]
            self.invoke(["webapp", "silo", "show", "--ids", ORIGIN], expected=expected)
            self.assertEqual([(call["method"], call["path"]) for call in self.calls], [("GET", ORIGIN)])

    def test_appservice_active_backup_failed_update_read_does_not_mutate(self):
        self.responses = [(404, None)]
        self.invoke(["webapp", "silo", "update", "--ids", ORIGIN, "--endpoint-status", "Disabled"], expected=3)
        self.assertEqual([call["method"] for call in self.calls], ["GET"])

    def test_appservice_active_backup_missing_traffic_mode_is_not_fabricated(self):
        resource = _resource(ORIGIN)
        del resource["properties"]["trafficMode"]
        self.responses = [(200, resource)]
        output = self.invoke(["webapp", "silo", "show", "--ids", ORIGIN])
        self.assertNotIn("trafficMode", output["properties"])
        self.assertEqual(len(self.calls), 1)

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

    def test_appservice_active_backup_lists_follow_next_link(self):
        self.paginate = True
        for command in ("webapp silo list", "webapp silo vnet-integration list", "webapp managed-traffic list",
                        "webapp last-known-good list", "appservice plan silo list"):
            self.calls.clear()
            args = command.split() + ["-g", "group", "-n", "primary"]
            if "vnet-integration" in command:
                args += ["--silo", "backup"]
            result = self.invoke(args)
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

    def test_appservice_active_backup_plan_vnet_inspection_preserves_metadata(self):
        output = self.invoke([
            "appservice", "plan", "silo", "vnet-integration", "list",
            "-g", "group", "-n", "primary", "--silo", "backup",
        ])
        expected = _plan_integrations()
        self.assertEqual(output["id"], expected["id"])
        self.assertEqual(output["location"], expected["location"])
        self.assertEqual(output["properties"], expected["properties"])
        self.assertEqual(len(self.calls), 1)

    def test_appservice_active_backup_vnet_lists_accept_empty_contract_results(self):
        for command, payload, expected in (
            ("appservice plan silo vnet-integration list", {"properties": []}, {"properties": []}),
            ("webapp silo vnet-integration list", {"value": []}, []),
        ):
            self.responses = [(200, payload)]
            self.assertEqual(self.invoke(command.split() + [
                "-g", "group", "-n", "primary", "--silo", "backup",
            ]), expected)

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
                self.invoke(args, expected=2 if command.endswith("vnet-integration list") else 1)
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

    def test_appservice_active_backup_read_and_list_preserve_service_location(self):
        for family in ("appservice plan", "webapp"):
            shown = self.invoke(family.split() + ["silo", "show", "-g", "group", "-n", "primary", "--silo", "backup"])
            self.assertEqual(shown["location"], "westus2")
            listed = self.invoke(family.split() + ["silo", "list", "-g", "group", "-n", "primary"])
            self.assertEqual(listed[0]["location"], "westus2")
