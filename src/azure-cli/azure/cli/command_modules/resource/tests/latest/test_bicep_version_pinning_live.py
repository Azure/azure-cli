# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Opt-in real-compiler tests; Azure resource creation additionally requires AZURE_BICEP_PINNING_RUN_AZURE=1."""

import contextlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import requests

from azure.cli.testsdk import LiveScenarioTest, ResourceGroupPreparer, live_only


_PINNED_VERSION = "0.31.92"
_NEWER_VERSION = "0.41.2"
_TEMPLATE = "param name string = 'original'\noutput name string = name\n"


def _run_live_request(request):
    """Run repository code in a fresh process, observing rather than replacing real compiler execution."""
    from azure.cli.core import get_default_cli
    from azure.cli.core.azclierror import CLIError
    from azure.cli.command_modules.resource import _bicep, custom

    cli = get_default_cli()
    cli.config.set_value("bicep", "check_version", "false")
    preference = request.get("path_preference", "false")
    cli.config.set_value("bicep", "use_binary_from_path", preference)
    calls = []
    urls = []
    stdout = io.StringIO()
    stderr = io.StringIO()
    run_command = _bicep._run_command
    get = _bicep.requests.get
    urlopen = _bicep.urlopen

    def observe_command(executable, args, custom_env=None):
        calls.append({"executable": executable, "args": args})
        return run_command(executable, args, custom_env)

    def observe_get(url, *args, **kwargs):
        urls.append(url)
        if request.get("offline"):
            raise requests.ConnectionError("Bicep acquisition deliberately blocked by the live test")
        return get(url, *args, **kwargs)

    def observe_urlopen(url, *args, **kwargs):
        urls.append(url)
        if request.get("offline"):
            raise AssertionError("Unexpected default compiler download")
        return urlopen(url, *args, **kwargs)

    code = 0
    result = None
    with contextlib.ExitStack() as stack:
        stack.enter_context(contextlib.redirect_stdout(stdout))
        stack.enter_context(contextlib.redirect_stderr(stderr))
        stack.enter_context(mock.patch.object(_bicep, "_run_command", side_effect=observe_command))
        stack.enter_context(mock.patch.object(_bicep.requests, "get", side_effect=observe_get))
        stack.enter_context(mock.patch.object(_bicep, "urlopen", side_effect=observe_urlopen))
        try:
            if request.get("acquire"):
                installation = _bicep.ensure_bicep_version_installation(
                    _bicep.parse_bicep_version_constraint(request["acquire"])
                )
                result = {"path": installation.executable_path}
            elif request.get("prepare"):
                cmd = SimpleNamespace(
                    cli_ctx=cli,
                    get_models=lambda *names: (SimpleNamespace,) * len(names),
                )
                parameters = request.get("parameters")
                template = request.get("template")
                if request.get("stack"):
                    properties = custom._prepare_stacks_templates_and_parameters(
                        cmd, "resourceGroup", SimpleNamespace(template=None, template_link=None),
                        template, None, None, parameters, None,
                    )
                else:
                    properties = custom._prepare_deployment_properties_unmodified(
                        cmd, "resourceGroup", template_file=template, parameters=parameters, no_prompt=True,
                    )
                result = {
                    "template": properties.template if request.get("stack") else json.loads(properties.template),
                    "parameters": properties.parameters,
                }
            else:
                code = cli.invoke(request["args"], out_file=stdout)
        except CLIError as err:
            code = 1
            stderr.write(str(err))
    report = {
        "code": code, "stdout": stdout.getvalue(), "stderr": stderr.getvalue(),
        "calls": calls, "urls": urls, "result": result,
        "path_preference": cli.config.get("bicep", "use_binary_from_path", None),
    }
    Path(request["report"]).write_text(json.dumps(report), encoding="utf-8")


def _invoke_child(root, config, request, cwd=None, path=None):
    report = os.path.join(root, "report.json")
    Path(report).unlink(missing_ok=True)
    request = dict(request, report=report)
    environment = os.environ.copy()
    environment["AZURE_CONFIG_DIR"] = config
    environment["AZURE_EXTENSION_DIR"] = os.path.join(root, "extensions")
    if path:
        environment["PATH"] = path + os.pathsep + environment.get("PATH", "")
    bootstrap = (
        f"import sys; sys.path[:0] = {sys.path!r}; "
        "from test_bicep_version_pinning_live import _run_live_request; "
        f"_run_live_request({request!r})"
    )
    process = subprocess.run(
        [sys.executable, "-B", "-c", bootstrap], env=environment, cwd=cwd or root,
        capture_output=True, text=True, encoding="utf-8", timeout=300, check=False,
    )
    if process.returncode:
        raise AssertionError(f"Live test subprocess failed:\n{process.stdout}\n{process.stderr}")
    return json.loads(Path(report).read_text(encoding="utf-8"))


@live_only()
class TestBicepVersionPinningLive(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        directory = tempfile.TemporaryDirectory(dir=os.path.dirname(__file__))
        cls.addClassCleanup(directory.cleanup)
        cls.seed_root = directory.name
        cls.seed_config = os.path.join(cls.seed_root, "config")
        for version in (_PINNED_VERSION, _NEWER_VERSION):
            report = _invoke_child(cls.seed_root, cls.seed_config, {
                "acquire": version,
            })
            if report["code"]:
                raise AssertionError(f"Unable to install live-test compiler {version}: {report}")

    def setUp(self):
        directory = tempfile.TemporaryDirectory(dir=os.path.dirname(__file__))
        self.addCleanup(directory.cleanup)
        self.root = directory.name
        self.config_dir = os.path.join(self.root, "cli-config")
        self.entrypoint = self.write("project/main.bicep", _TEMPLATE)
        self.parameters = self.write("project/main.bicepparam", "using './main.bicep'\nparam name = 'provided'\n")
        self.project_config = os.path.join(self.root, "project", "bicepconfig.json")
        self.pin(_PINNED_VERSION)

    def write(self, relative_path, text):
        path = Path(self.root, relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return str(path)

    def pin(self, version):
        self.write("project/bicepconfig.json", json.dumps({"bicep": {"version": version}}))

    def seed(self, version=_PINNED_VERSION):
        source = Path(self.seed_config, "bin", "bicep-versions", version)
        destination = Path(self.config_dir, "bin", "bicep-versions", version)
        shutil.copytree(source, destination, dirs_exist_ok=True)
        return str(next(path for path in destination.rglob("bicep*") if path.is_file()))

    def invoke(self, args=None, success=True, **kwargs):
        cwd = kwargs.pop("cwd", None)
        path = kwargs.pop("path", None)
        report = _invoke_child(self.root, self.config_dir, dict(kwargs, args=args), cwd=cwd, path=path)
        if success:
            self.assertEqual(0, report["code"], report)
        else:
            self.assertNotEqual(0, report["code"], report)
        return report

    def assert_compiler(self, report, executable, command=None):
        calls = [call for call in report["calls"] if call["args"] != ["--version"]]
        self.assertTrue(calls, report)
        for call in calls:
            self.assertEqual(os.path.normcase(executable), os.path.normcase(call["executable"]), report)
        if command:
            self.assertTrue(any(call["args"][0] == command for call in calls), report)

    def assert_generated_by(self, template, version):
        reported = template["metadata"]["_generator"]["version"]
        self.assertEqual(version, ".".join(reported.split(".")[:3]))

    def test_bicep_exact_pin_downloads_and_reuses_real_compiler_offline(self):
        report = self.invoke(["bicep", "build", "--file", self.entrypoint, "--stdout"])
        template = json.loads(report["stdout"])
        self.assert_generated_by(template, _PINNED_VERSION)
        self.assertEqual("[parameters('name')]", template["outputs"]["name"]["value"])
        self.assertTrue(any(_PINNED_VERSION in url and "bicep-" in url for url in report["urls"]), report)
        executable = next(
            call["executable"] for call in report["calls"] if call["args"][0] == "build"
        )
        self.assertTrue(Path(executable).is_file())
        self.assertTrue(Path(executable).is_relative_to(Path(self.config_dir, "bin", "bicep-versions")))
        repeated = self.invoke(
            ["bicep", "build", "--file", self.entrypoint, "--stdout"], offline=True,
        )
        self.assert_compiler(repeated, executable, "build")
        self.assertEqual([], repeated["urls"])
        self.assertEqual(template, json.loads(repeated["stdout"]))

    def test_bicep_inherited_range_uses_entrypoint_and_highest_compatible_cache(self):
        self.seed()
        selected = self.seed(_NEWER_VERSION)
        self.write("bicepconfig.json", json.dumps({"bicep": {"version": "0.1.0"}}))
        self.write("shared/base.json", json.dumps({"bicep": {"version": ">=0.31, <0.42"}}))
        self.write("project/bicepconfig.json", json.dumps({"extends": "../shared/base.json"}))
        report = self.invoke(
            ["bicep", "build", "--file", self.entrypoint, "--stdout"], offline=True, cwd=self.root,
        )
        self.assert_compiler(report, selected, "build")
        self.assert_generated_by(json.loads(report["stdout"]), _NEWER_VERSION)
        self.pin(">=0.31, <0.32")
        report = self.invoke(["bicep", "build", "--file", self.entrypoint, "--stdout"], offline=True)
        self.assert_generated_by(json.loads(report["stdout"]), _PINNED_VERSION)
        self.assertEqual([], report["urls"])

    def test_bicep_pin_overrides_real_default_and_path_without_changing_preference(self):
        selected = self.seed()
        other = self.seed(_NEWER_VERSION)
        default = Path(self.config_dir, "bin", Path(other).name)
        shutil.copy2(other, default)
        for preference in ("true", "false", "if_found_in_ci"):
            with self.subTest(preference=preference):
                report = self.invoke(
                    ["bicep", "build", "--file", self.entrypoint, "--stdout"], offline=True,
                    path=str(default.parent), path_preference=preference,
                )
                self.assert_compiler(report, selected, "build")
                self.assertEqual(preference, report["path_preference"])
        self.assertEqual(Path(other).read_bytes(), default.read_bytes())

    def test_bicep_unpinned_commands_keep_real_default_and_path_behavior(self):
        source = self.seed(_NEWER_VERSION)
        default = Path(self.config_dir, "bin", Path(source).name)
        shutil.copy2(source, default)
        self.write("project/bicepconfig.json", "{}")
        for preference, executable in (("false", str(default)), ("true", "bicep")):
            with self.subTest(preference=preference):
                report = self.invoke(
                    ["bicep", "build", "--file", self.entrypoint, "--stdout"], offline=True,
                    path=str(default.parent), path_preference=preference,
                )
                self.assert_compiler(report, executable, "build")
                self.assert_generated_by(json.loads(report["stdout"]), _NEWER_VERSION)

    def test_bicep_invalid_or_unavailable_pin_never_falls_back(self):
        source = self.seed(_NEWER_VERSION)
        shutil.copy2(source, Path(self.config_dir, "bin", Path(source).name))
        for config, message in (
            ({"bicep": {"version": "^0.31"}}, "version"),
            ({"bicep": {"version": ">=2, <1"}}, "satisfied"),
            ({"extends": "missing.json"}, "missing.json"),
            ({"extends": "bicepconfig.json"}, "cycl"),
            ({"bicep": {"version": _PINNED_VERSION}}, "deliberately blocked"),
        ):
            with self.subTest(config=config):
                self.write("project/bicepconfig.json", json.dumps(config))
                report = self.invoke(
                    ["bicep", "build", "--file", self.entrypoint, "--stdout"],
                    offline=True, success=False, path_preference="true",
                )
                self.assertIn(message, report["stderr"].lower(), report)
                self.assertEqual([], report["calls"], report)
                self.assertEqual("", report["stdout"], report)
                self.assertFalse(Path(self.entrypoint).with_suffix(".json").exists())

    def test_bicep_real_file_commands_preserve_options_and_outputs(self):
        selected = self.seed()
        report = self.invoke(
            ["bicep", "build-params", "--file", self.parameters, "--stdout", "--no-restore"], offline=True,
        )
        self.assert_compiler(report, selected, "build-params")
        parameters_json = json.loads(json.loads(report["stdout"])["parametersJson"])
        self.assertEqual("provided", parameters_json["parameters"]["name"]["value"])
        output = os.path.join(self.root, "generated.bicepparam")
        report = self.invoke([
            "bicep", "generate-params", "--file", self.entrypoint, "--outfile", output,
            "--output-format", "bicepparam", "--include-params", "all", "--no-restore",
        ], offline=True)
        self.assert_compiler(report, selected, "generate-params")
        self.assertIn("param name", Path(output).read_text(encoding="utf-8"))
        unformatted = self.write("project/format.bicep", "param name string='original'\noutput name string=name")
        report = self.invoke([
            "bicep", "format", "--file", unformatted, "--stdout",
            "--indent-kind", "Space", "--indent-size", "2", "--insert-final-newline",
        ], offline=True)
        self.assert_compiler(report, selected, "format")
        self.assertIn("param name string = 'original'", report["stdout"])
        self.assertTrue(report["stdout"].endswith("\n"))
        lint_file = self.write("project/lint.bicep", "param unused string = 'value'\n")
        report = self.invoke([
            "bicep", "lint", "--file", lint_file, "--no-restore",
        ], offline=True)
        self.assert_compiler(report, selected, "lint")
        self.assertIn("no-unused-params", report["stdout"] + report["stderr"])
        report = self.invoke(["bicep", "restore", "--file", self.entrypoint, "--force"], offline=True)
        self.assert_compiler(report, selected, "restore")

    def test_bicep_snapshot_capture_validate_and_detect_change(self):
        self.pin(_NEWER_VERSION)
        selected = self.seed(_NEWER_VERSION)
        self.write("project/main.bicep",
                   "param name string\n"
                   "resource account 'Microsoft.Storage/storageAccounts@2023-05-01' = {\n"
                   "  name: name\n  location: 'westus'\n  kind: 'StorageV2'\n"
                   "  sku: {\n    name: 'Standard_LRS'\n  }\n  properties: {}\n}\n")
        args = [
            "bicep", "snapshot", "--file", self.parameters,
            "--subscription-id", "00000000-0000-0000-0000-000000000000",
            "--resource-group", "pinning-test", "--deployment-name", "pinning-test",
        ]
        report = self.invoke(args + ["--mode", "Overwrite"], offline=True)
        self.assert_compiler(report, selected, "snapshot")
        snapshot = Path(self.parameters).with_suffix(".snapshot.json")
        self.assertTrue(snapshot.is_file(), report)
        self.assertEqual(
            "provided", json.loads(snapshot.read_text(encoding="utf-8"))["predictedResources"][0]["name"],
        )
        report = self.invoke(args + ["--mode", "Validate"], offline=True)
        self.assert_compiler(report, selected, "snapshot")
        self.write("project/main.bicepparam", "using './main.bicep'\nparam name = 'changed'\n")
        report = self.invoke(args + ["--mode", "Validate"], offline=True, success=False)
        self.assert_compiler(report, selected, "snapshot")
        self.assertIn("changed", report["stdout"] + report["stderr"])

    def test_bicep_unsupported_pinned_command_does_not_run_newer_default(self):
        selected = self.seed()
        newer = self.seed(_NEWER_VERSION)
        shutil.copy2(newer, Path(self.config_dir, "bin", Path(newer).name))
        report = self.invoke(
            ["bicep", "snapshot", "--file", self.parameters], offline=True, success=False,
        )
        self.assertIn("bicep.version", report["stderr"])
        self.assertIn(_NEWER_VERSION, report["stderr"])
        self.assertEqual([{"executable": selected, "args": ["--version"]}], report["calls"])

    def test_bicep_real_deployment_preparation_and_using_none_overrides(self):
        selected = self.seed()
        self.seed(_NEWER_VERSION)
        self.write("bicepconfig.json", json.dumps({"bicep": {"version": _NEWER_VERSION}}))
        template = self.write("templates/main.bicep", _TEMPLATE)
        for stack in (False, True):
            report = self.invoke(prepare=True, stack=stack, template=self.entrypoint, offline=True)
            self.assert_compiler(report, selected, "build")
            self.assert_generated_by(report["result"]["template"], _PINNED_VERSION)
            for using_none in (False, True):
                for supplemental in (False, True):
                    with self.subTest(stack=stack, using_none=using_none, supplemental=supplemental):
                        using = "none" if using_none else "'../templates/main.bicep'"
                        self.write("project/main.bicepparam", f"using {using}\nparam name = 'provided'\n")
                        parameters = [[self.parameters, "name=changed"]] if supplemental else [[self.parameters]]
                        report = self.invoke(
                            prepare=True, stack=stack, template=template, parameters=parameters, offline=True,
                        )
                        self.assert_compiler(report, selected, "build-params")
                        self.assertEqual(
                            "changed" if supplemental else "provided",
                            report["result"]["parameters"]["name"]["value"],
                        )
                        self.assert_generated_by(report["result"]["template"], _PINNED_VERSION)
                        builds = [call for call in report["calls"] if call["args"][0] == "build-params"]
                        self.assertEqual(2 if supplemental else 1, len(builds))
                        if using_none:
                            self.assertTrue(all("--bicep-file" not in call["args"] for call in builds))

    def test_bicep_install_version_and_uninstall_preserve_project_cache(self):
        selected = self.seed()
        before = Path(selected).read_bytes()
        report = self.invoke(["bicep", "install", "--version", "v" + _NEWER_VERSION])
        self.assertTrue(any("v" + _NEWER_VERSION in url for url in report["urls"]), report)
        self.assertFalse(Path(self.config_dir, "bin", "bicep-versions", _NEWER_VERSION).exists())
        self.invoke(["bicep", "install", "--version", "v" + _NEWER_VERSION], offline=True)
        report = self.invoke(["bicep", "version"], offline=True)
        self.assertIn("Bicep CLI version " + _NEWER_VERSION, report["stdout"])
        self.assertEqual(before, Path(selected).read_bytes())
        default = Path(self.config_dir, "bin", Path(selected).name)
        self.assertTrue(default.is_file())
        self.assertEqual([{"executable": str(default), "args": ["--version"]}], report["calls"])
        sibling = Path(self.config_dir, "bin", "other-tool")
        sibling.write_text("preserve", encoding="utf-8")
        report = self.invoke(["bicep", "uninstall"], offline=True)
        self.assertIsNone(report["path_preference"])
        self.assertFalse(default.exists())
        self.assertEqual(before, Path(selected).read_bytes())
        self.assertEqual("preserve", sibling.read_text(encoding="utf-8"))
        self.assertEqual(_PINNED_VERSION, json.loads(Path(self.project_config).read_text())["bicep"]["version"])
        report = self.invoke(["bicep", "version"], success=False, offline=True)
        self.assertIn("Bicep CLI not found", report["stderr"])
        report = self.invoke(["bicep", "build", "--file", self.entrypoint, "--stdout"], offline=True)
        self.assert_compiler(report, selected, "build")
        self.assert_generated_by(json.loads(report["stdout"]), _PINNED_VERSION)
        self.assertFalse(default.exists())

    def test_bicep_latest_install_and_upgrade_only_manage_default_compiler(self):
        selected = self.seed()
        pinned_bytes = Path(selected).read_bytes()
        default = Path(self.config_dir, "bin", Path(selected).name)
        for command in ("install", "upgrade"):
            with self.subTest(command=command):
                if command == "upgrade":
                    shutil.copy2(selected, default)
                report = self.invoke(["bicep", command])
                self.assertIn("https://aka.ms/BicepLatestRelease", report["urls"])
                self.assertTrue(any("bicep-" in url for url in report["urls"]), report)
                self.assertEqual([_PINNED_VERSION], os.listdir(default.parent / "bicep-versions"))
                version = self.invoke(["bicep", "version"], offline=True)["stdout"].split()[3]
                unpinned = self.write("unpinned/main.bicep", _TEMPLATE)
                self.write("unpinned/bicepconfig.json", "{}")
                built = self.invoke(["bicep", "build", "--file", unpinned, "--stdout"], offline=True)
                self.assert_compiler(built, str(default), "build")
                self.assert_generated_by(json.loads(built["stdout"]), version)
                built = self.invoke(["bicep", "build", "--file", self.entrypoint, "--stdout"], offline=True)
                self.assert_compiler(built, selected, "build")
                self.assert_generated_by(json.loads(built["stdout"]), _PINNED_VERSION)
                self.assertEqual(pinned_bytes, Path(selected).read_bytes())
                if command == "install":
                    before = default.read_bytes()
                    repeated = self.invoke(["bicep", "install"], offline=True)
                    self.assertEqual([], repeated["urls"])
                    self.assertEqual(before, default.read_bytes())


@unittest.skipUnless(
    os.environ.get("AZURE_BICEP_PINNING_RUN_AZURE") == "1" and
    os.environ.get("AZURE_BICEP_PINNING_SUBSCRIPTION_ID"),
    "Requires AZURE_BICEP_PINNING_RUN_AZURE=1 and AZURE_BICEP_PINNING_SUBSCRIPTION_ID; creates Azure resources.",
)
class BicepVersionPinningAzureTest(LiveScenarioTest):
    def setUp(self):
        super().setUp()
        from azure.cli.command_modules.resource import _bicep

        self.assertFalse(
            os.environ.get("AZURE_CLI_TEST_DEV_RESOURCE_GROUP_NAME"),
            "These tests require dedicated resource groups, not an existing development resource group.",
        )
        self.kwargs["pinning_subscription"] = os.environ["AZURE_BICEP_PINNING_SUBSCRIPTION_ID"]
        directory = tempfile.TemporaryDirectory(dir=os.path.dirname(__file__))
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        stack = contextlib.ExitStack()
        self.addCleanup(stack.close)
        # Preserve SDK authentication, but redirect every managed compiler path to test-owned storage.
        stack.enter_context(mock.patch.object(_bicep, "_bicep_installation_dir", str(self.root / "bin")))
        stack.enter_context(mock.patch.object(
            _bicep, "_bicep_version_check_file_path", str(self.root / "bicepVersionCheck.json"),
        ))
        self.run_command = stack.enter_context(mock.patch.object(_bicep, "_run_command", wraps=_bicep._run_command))
        self.template = self.root / "main.bicep"
        self.template.write_text(_TEMPLATE, encoding="utf-8")
        (self.root / "bicepconfig.json").write_text(json.dumps({
            "bicep": {"version": _PINNED_VERSION},
            "cacheRootDirectory": str(self.root / "modules"),
        }), encoding="utf-8")

    def assert_selected_compiler(self, command):
        calls = [call for call in self.run_command.call_args_list if call.args[1][0] == command]
        self.assertTrue(calls)
        for call in calls:
            path = Path(call.args[0])
            self.assertTrue(path.is_relative_to(self.root / "bin" / "bicep-versions"))
            self.assertEqual(_PINNED_VERSION, path.parent.parent.name)

    @ResourceGroupPreparer(
        name_prefix="cli_bicep_pin_registry",
        subscription=os.environ.get("AZURE_BICEP_PINNING_SUBSCRIPTION_ID"),
        location=os.environ.get("AZURE_BICEP_PINNING_LOCATION", "eastus"),
    )
    def test_bicep_publish_and_restore_with_pinned_compiler(self, resource_group):
        registry = self.create_random_name("clipinning", 24)
        registry_info = self.cmd(
            f"az acr create --resource-group {resource_group} --name {registry} --sku Basic "
            "--subscription {pinning_subscription}"
        ).get_output_in_json()
        server = registry_info["loginServer"]
        target = f"br:{server}/modules/pinning:v1"
        documentation = "https://example.com/bicep-pinning"
        self.cmd(
            f'az bicep publish --file "{self.template}" --target "{target}" '
            f'--documentation-uri "{documentation}" --with-source'
        )
        self.assert_selected_compiler("publish")
        manifest = self.cmd(
            f"az acr manifest show --registry {registry} --name modules/pinning:v1 "
            "--subscription {pinning_subscription}"
        ).get_output_in_json()
        self.assertEqual(documentation, manifest["annotations"]["org.opencontainers.image.documentation"])
        self.assertIn(
            "application/vnd.ms.bicep.module.source.v1.tar+gzip",
            [layer["mediaType"] for layer in manifest["layers"]],
        )
        self.template.write_text("output updated string = 'updated'\n", encoding="utf-8")
        self.cmd(f'az bicep publish --file "{self.template}" --target "{target}" --with-source --force')
        consumer = self.root / "consumer.bicep"
        consumer.write_text(
            f"module example '{target}' = {{\n  name: 'example'\n}}\n"
            "output value string = example.outputs.updated\n", encoding="utf-8",
        )
        self.cmd(f'az bicep restore --file "{consumer}" --force')
        self.assert_selected_compiler("restore")
        self.assertTrue(any((self.root / "modules").rglob("main.json")))
        compiled_path = self.root / "consumer.json"
        self.cmd(f'az bicep build --file "{consumer}" --outfile "{compiled_path}" --no-restore')
        compiled = json.loads(compiled_path.read_text(encoding="utf-8"))
        nested = compiled["resources"][0]["properties"]["template"]
        self.assertEqual("updated", nested["outputs"]["updated"]["value"])
        self.assert_selected_compiler("build")

    @ResourceGroupPreparer(
        name_prefix="cli_bicep_pin_deploy",
        subscription=os.environ.get("AZURE_BICEP_PINNING_SUBSCRIPTION_ID"),
        location=os.environ.get("AZURE_BICEP_PINNING_LOCATION", "eastus"),
    )
    def test_bicep_deployment_and_what_if_with_pinned_parameters(self, resource_group):
        self.kwargs["deployment"] = self.create_random_name("pinning", 20)
        self.template.write_text(
            "param name string\nparam location string = resourceGroup().location\n"
            "resource account 'Microsoft.Storage/storageAccounts@2023-05-01' = {\n"
            "  name: name\n  location: location\n  kind: 'StorageV2'\n"
            "  sku: {\n    name: 'Standard_LRS'\n  }\n"
            "  properties: {\n"
            "    allowSharedKeyAccess: false\n    allowBlobPublicAccess: false\n"
            "    supportsHttpsTrafficOnly: true\n    minimumTlsVersion: 'TLS1_2'\n"
            "  }\n}\n"
            "output accountId string = account.id\n", encoding="utf-8",
        )
        account = self.create_random_name("clipinning", 24)
        parameters = self.root / "main.bicepparam"
        parameters.write_text(
            f"using './main.bicep'\nparam name = '{account}'\n", encoding="utf-8",
        )
        self.cmd(
            f'az deployment group create --resource-group {resource_group} --name {{deployment}} '
            f'--parameters "{parameters}" --subscription {{pinning_subscription}}',
            checks=self.check("properties.provisioningState", "Succeeded"),
        )
        self.assert_selected_compiler("build-params")
        self.cmd(
            f"az storage account show --resource-group {resource_group} --name {account} "
            "--subscription {pinning_subscription}",
            checks=self.check("name", account),
        )
        self.run_command.reset_mock()
        what_if = self.cmd(
            f'az deployment group what-if --resource-group {resource_group} --name {{deployment}} '
            f'--parameters "{parameters}" --no-pretty-print --subscription {{pinning_subscription}}'
        ).get_output_in_json()
        self.assert_selected_compiler("build-params")
        self.assertEqual("Succeeded", what_if["status"])
        self.assertTrue(what_if["changes"])
        self.assertTrue(all(change["changeType"] in ("NoChange", "Ignore") for change in what_if["changes"]))
