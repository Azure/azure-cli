# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Unit tests for the Compose → Sitecontainers conversion helpers in custom.py.

These tests validate the parsing functions without requiring Azure connectivity.
Run with: python -m pytest <this_file> -v
"""

import os
import unittest
from base64 import b64encode
from unittest.mock import MagicMock, patch, call

import yaml


# Import the helpers under test
from azure.cli.command_modules.appservice.custom import (
    _parse_compose_entrypoint_or_command,
    _merge_entrypoint_command,
    _parse_compose_environment,
    _parse_compose_ports,
    _parse_compose_volumes,
    _make_bind_mount,
    _make_named_volume_mount,
    _sanitize_container_name,
    _convert_compose_to_sitecontainers,
    _COMPOSE_WEBAPP_STORAGE_HOME,
)

SAMPLES_DIR = os.path.dirname(__file__)


def _load_sample(filename):
    """Load and parse a sample compose YAML from the test directory."""
    path = os.path.join(SAMPLES_DIR, filename)
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def _b64_encode_file(filename):
    """Return the base64-encoded contents of a sample file (simulating linuxFxVersion)."""
    path = os.path.join(SAMPLES_DIR, filename)
    with open(path, 'rb') as f:
        return b64encode(f.read()).decode('utf-8')


# ---------------------------------------------------------------------------
# _sanitize_container_name
# ---------------------------------------------------------------------------
class TestSanitizeContainerName(unittest.TestCase):
    def test_simple_name(self):
        self.assertEqual(_sanitize_container_name("web"), "web")

    def test_underscores_replaced(self):
        self.assertEqual(_sanitize_container_name("my_web_app"), "my-web-app")

    def test_dots_replaced(self):
        self.assertEqual(_sanitize_container_name("background.worker"), "background-worker")

    def test_uppercase_lowered(self):
        self.assertEqual(_sanitize_container_name("UPPERCASE_SVC"), "uppercase-svc")

    def test_already_valid(self):
        self.assertEqual(_sanitize_container_name("data-processor"), "data-processor")

    def test_consecutive_specials_collapsed(self):
        self.assertEqual(_sanitize_container_name("a__b..c"), "a-b-c")

    def test_empty_string(self):
        self.assertEqual(_sanitize_container_name(""), "container")

    def test_leading_trailing_hyphens_stripped(self):
        self.assertEqual(_sanitize_container_name("_leading_"), "leading")


# ---------------------------------------------------------------------------
# _parse_compose_entrypoint_or_command
# ---------------------------------------------------------------------------
class TestParseEntrypointOrCommand(unittest.TestCase):
    def test_none_returns_empty(self):
        self.assertEqual(_parse_compose_entrypoint_or_command(None), [])

    def test_string_split_on_whitespace(self):
        result = _parse_compose_entrypoint_or_command("gunicorn --bind 0.0.0.0:5000 app:app")
        self.assertEqual(result, ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"])

    def test_list_preserved(self):
        result = _parse_compose_entrypoint_or_command(["celery", "-A", "tasks"])
        self.assertEqual(result, ["celery", "-A", "tasks"])

    def test_single_word_string(self):
        result = _parse_compose_entrypoint_or_command("python")
        self.assertEqual(result, ["python"])

    def test_entrypoint_empty_string(self):
        result = _parse_compose_entrypoint_or_command("")
        self.assertEqual(result, [])


# ---------------------------------------------------------------------------
# _merge_entrypoint_command
# ---------------------------------------------------------------------------
class TestMergeEntrypointCommand(unittest.TestCase):
    def test_both_empty_returns_none(self):
        self.assertIsNone(_merge_entrypoint_command([], []))

    def test_only_entrypoint(self):
        result = _merge_entrypoint_command(["python", "app.py"], [])
        self.assertEqual(result, "python app.py")

    def test_only_command(self):
        result = _merge_entrypoint_command([], ["--workers", "4"])
        self.assertEqual(result, "--workers 4")

    def test_both_merged(self):
        result = _merge_entrypoint_command(["gunicorn"], ["--bind", "0.0.0.0:5000", "app:app"])
        self.assertEqual(result, "gunicorn --bind 0.0.0.0:5000 app:app")


# ---------------------------------------------------------------------------
# _parse_compose_environment
# ---------------------------------------------------------------------------
class TestParseComposeEnvironment(unittest.TestCase):
    def test_env_none_returns_empty(self):
        self.assertEqual(_parse_compose_environment(None), {})

    def test_mapping_format(self):
        env = {"NODE_ENV": "production", "PORT": 3000, "EMPTY": None}
        result = _parse_compose_environment(env)
        self.assertEqual(result, {"NODE_ENV": "production", "PORT": "3000", "EMPTY": ""})

    def test_sequence_with_values(self):
        env = ["KEY1=value1", "KEY2=value2"]
        result = _parse_compose_environment(env)
        self.assertEqual(result, {"KEY1": "value1", "KEY2": "value2"})

    def test_sequence_value_with_equals(self):
        """Value itself contains '=' characters."""
        env = ["CONNECTION=Server=localhost;Database=mydb"]
        result = _parse_compose_environment(env)
        self.assertEqual(result, {"CONNECTION": "Server=localhost;Database=mydb"})

    def test_sequence_name_only(self):
        """No '=' means value-less reference to an app setting."""
        env = ["EXISTING_SETTING"]
        result = _parse_compose_environment(env)
        self.assertEqual(result, {"EXISTING_SETTING": ""})

    def test_sequence_empty_value(self):
        """Trailing '=' means empty value."""
        env = ["KEY="]
        result = _parse_compose_environment(env)
        self.assertEqual(result, {"KEY": ""})


# ---------------------------------------------------------------------------
# _parse_compose_ports
# ---------------------------------------------------------------------------
class TestParseComposePorts(unittest.TestCase):
    def test_ports_none_returns_empty(self):
        self.assertEqual(_parse_compose_ports(None), [])

    def test_host_container_mapping(self):
        result = _parse_compose_ports(["8080:80", "3306:3306"])
        self.assertEqual(result, [(8080, 80), (3306, 3306)])

    def test_single_port_no_host(self):
        result = _parse_compose_ports(["80"])
        self.assertEqual(result, [(None, 80)])

    def test_invalid_port_skipped(self):
        result = _parse_compose_ports(["abc:xyz", "8080:80"])
        self.assertEqual(result, [(8080, 80)])


# ---------------------------------------------------------------------------
# _parse_compose_volumes
# ---------------------------------------------------------------------------
class TestParseComposeVolumes(unittest.TestCase):
    def test_volumes_none_returns_empty(self):
        mounts, warnings = _parse_compose_volumes(None, {})
        self.assertEqual(mounts, [])
        self.assertEqual(warnings, [])

    def test_bind_mount_short_syntax(self):
        volumes = ["${WEBAPP_STORAGE_HOME}/site/wwwroot:/var/www/html"]
        mounts, warnings = _parse_compose_volumes(volumes, {})
        self.assertEqual(len(mounts), 1)
        self.assertEqual(mounts[0]["volume_sub_path"], "/home/site/wwwroot")
        self.assertEqual(mounts[0]["container_mount_path"], "/var/www/html")
        self.assertFalse(mounts[0]["read_only"])

    def test_bind_mount_root_home(self):
        """${WEBAPP_STORAGE_HOME} alone (no subpath) maps to /home."""
        volumes = ["${WEBAPP_STORAGE_HOME}:/mnt/home"]
        mounts, warnings = _parse_compose_volumes(volumes, {})
        self.assertEqual(len(mounts), 1)
        self.assertEqual(mounts[0]["volume_sub_path"], "/home")
        self.assertEqual(mounts[0]["container_mount_path"], "/mnt/home")

    def test_bind_mount_with_ro(self):
        volumes = ["${WEBAPP_STORAGE_HOME}/config:/etc/config:ro"]
        mounts, warnings = _parse_compose_volumes(volumes, {})
        self.assertEqual(len(mounts), 1)
        self.assertTrue(mounts[0]["read_only"])

    def test_unsupported_host_path(self):
        volumes = ["/var/data:/app/data"]
        mounts, warnings = _parse_compose_volumes(volumes, {})
        self.assertEqual(len(mounts), 0)
        self.assertTrue(any("UNSUPPORTED" in w for w in warnings))

    def test_relative_path_unsupported(self):
        volumes = ["./config:/app/config"]
        mounts, warnings = _parse_compose_volumes(volumes, {})
        self.assertEqual(len(mounts), 0)
        self.assertTrue(any("UNSUPPORTED" in w for w in warnings))

    def test_named_volume(self):
        volumes = ["mydata:/app/data"]
        mounts, warnings = _parse_compose_volumes(volumes, {"mydata": None})
        self.assertEqual(len(mounts), 1)
        self.assertEqual(mounts[0]["volume_sub_path"], "/compose/volumes/mydata")
        self.assertEqual(mounts[0]["container_mount_path"], "/app/data")
        self.assertTrue(any("Named volume" in w for w in warnings))

    def test_long_syntax_bind(self):
        volumes = [{"type": "bind", "source": "${WEBAPP_STORAGE_HOME}/site/wwwroot", "target": "/app"}]
        mounts, warnings = _parse_compose_volumes(volumes, {})
        self.assertEqual(len(mounts), 1)
        self.assertEqual(mounts[0]["volume_sub_path"], "/home/site/wwwroot")
        self.assertEqual(mounts[0]["container_mount_path"], "/app")

    def test_long_syntax_bind_read_only(self):
        volumes = [{
            "type": "bind",
            "source": "${WEBAPP_STORAGE_HOME}/conf",
            "target": "/etc/conf",
            "read_only": True,
        }]
        mounts, warnings = _parse_compose_volumes(volumes, {})
        self.assertEqual(len(mounts), 1)
        self.assertTrue(mounts[0]["read_only"])

    def test_long_syntax_volume(self):
        volumes = [{"type": "volume", "source": "cache-vol", "target": "/tmp/cache"}]
        mounts, warnings = _parse_compose_volumes(volumes, {"cache-vol": None})
        self.assertEqual(len(mounts), 1)
        self.assertEqual(mounts[0]["volume_sub_path"], "/compose/volumes/cache-vol")

    def test_mixed_supported_and_unsupported(self):
        """Mix of valid bind mount, invalid host path, and named volume."""
        volumes = [
            "${WEBAPP_STORAGE_HOME}/site/wwwroot:/app/public",
            "/var/data:/app/data",
            "${WEBAPP_STORAGE_HOME}/logs:/app/logs",
        ]
        mounts, warnings = _parse_compose_volumes(volumes, {})
        self.assertEqual(len(mounts), 2)  # Two valid bind mounts
        self.assertTrue(any("UNSUPPORTED" in w for w in warnings))


# ---------------------------------------------------------------------------
# _make_bind_mount
# ---------------------------------------------------------------------------
class TestMakeBindMount(unittest.TestCase):
    def test_standard_path(self):
        warnings = []
        result = _make_bind_mount("${WEBAPP_STORAGE_HOME}/site/wwwroot", "/var/www/html", False, warnings)
        self.assertIsNotNone(result)
        self.assertEqual(result["volume_sub_path"], "/home/site/wwwroot")
        self.assertEqual(result["container_mount_path"], "/var/www/html")
        self.assertEqual(len(warnings), 0)

    def test_root_only(self):
        warnings = []
        result = _make_bind_mount("${WEBAPP_STORAGE_HOME}", "/mnt", False, warnings)
        self.assertEqual(result["volume_sub_path"], "/home")

    def test_non_matching_source_returns_none(self):
        warnings = []
        result = _make_bind_mount("/some/host/path", "/app", False, warnings)
        self.assertIsNone(result)
        self.assertEqual(len(warnings), 1)

    def test_nested_path(self):
        warnings = []
        result = _make_bind_mount(
            "${WEBAPP_STORAGE_HOME}/deep/nested/path/here", "/container/path", False, warnings
        )
        self.assertEqual(result["volume_sub_path"], "/home/deep/nested/path/here")


# ---------------------------------------------------------------------------
# Integration-style: load sample YAML and validate structure
# ---------------------------------------------------------------------------
class TestSampleYamlParsing(unittest.TestCase):
    """Validate that sample compose YAMLs parse correctly with yaml.safe_load."""

    def _load(self, filename):
        return _load_sample(filename)

    def test_basic_has_two_services(self):
        compose = self._load("compose-convert-basic.yml")
        self.assertIn("services", compose)
        self.assertEqual(len(compose["services"]), 2)
        self.assertIn("web", compose["services"])
        self.assertIn("redis", compose["services"])

    def test_env_mapping_format(self):
        compose = self._load("compose-convert-env-mapping.yml")
        api_env = compose["services"]["api"]["environment"]
        self.assertIsInstance(api_env, dict)
        self.assertEqual(api_env["NODE_ENV"], "production")

    def test_env_sequence_format(self):
        compose = self._load("compose-convert-env-sequence.yml")
        app_env = compose["services"]["app"]["environment"]
        self.assertIsInstance(app_env, list)
        self.assertIn("REDIS_URL=redis://localhost:6379", app_env)

    def test_volumes_bind_mount(self):
        compose = self._load("compose-convert-volumes-bind.yml")
        wp_vols = compose["services"]["wordpress"]["volumes"]
        self.assertEqual(len(wp_vols), 2)
        self.assertTrue(wp_vols[0].startswith("${WEBAPP_STORAGE_HOME}"))

    def test_volumes_named(self):
        compose = self._load("compose-convert-volumes-named.yml")
        self.assertIn("volumes", compose)
        self.assertIn("app-data", compose["volumes"])

    def test_volumes_long_syntax(self):
        compose = self._load("compose-convert-volumes-long.yml")
        web_vols = compose["services"]["web"]["volumes"]
        self.assertIsInstance(web_vols[0], dict)
        self.assertEqual(web_vols[0]["type"], "bind")

    def test_entrypoint_command(self):
        compose = self._load("compose-convert-entrypoint-command.yml")
        web = compose["services"]["web"]
        self.assertEqual(web["entrypoint"], "gunicorn")
        self.assertEqual(web["command"], "--bind 0.0.0.0:5000 app:app --workers 4")
        worker = compose["services"]["worker"]
        self.assertIsInstance(worker["entrypoint"], list)
        self.assertIsInstance(worker["command"], list)

    def test_port_conflict_file_parses(self):
        compose = self._load("compose-convert-port-conflict.yml")
        # Both services have port 8080 as container port
        fe_ports = compose["services"]["frontend"]["ports"]
        be_ports = compose["services"]["backend"]["ports"]
        self.assertEqual(fe_ports, ["80:8080"])
        self.assertEqual(be_ports, ["8080:8080"])

    def test_full_scenario_service_count(self):
        compose = self._load("compose-convert-full.yml")
        self.assertEqual(len(compose["services"]), 4)

    def test_underscore_names_parse(self):
        compose = self._load("compose-convert-underscore-names.yml")
        services = list(compose["services"].keys())
        self.assertIn("my_web_app", services)
        self.assertIn("background.worker", services)
        self.assertIn("UPPERCASE_SVC", services)

    def test_no_ports_file_parses(self):
        compose = self._load("compose-convert-no-ports.yml")
        # Neither service has ports
        for svc in compose["services"].values():
            self.assertNotIn("ports", svc)

    def test_b64_encode_roundtrip(self):
        """Verify base64 encode/decode preserves the YAML."""
        from base64 import b64decode
        b64 = _b64_encode_file("compose-convert-basic.yml")
        decoded = b64decode(b64.encode('utf-8')).decode('utf-8')
        compose = yaml.safe_load(decoded)
        self.assertIn("services", compose)
        self.assertEqual(len(compose["services"]), 2)


# ---------------------------------------------------------------------------
# End-to-end parsing of volumes from sample files
# ---------------------------------------------------------------------------
class TestSampleVolumeParsing(unittest.TestCase):
    """Parse volumes from sample YAMLs through the actual helper functions."""

    def test_bind_mount_file(self):
        compose = _load_sample("compose-convert-volumes-bind.yml")
        wp_vols = compose["services"]["wordpress"]["volumes"]
        mounts, warnings = _parse_compose_volumes(wp_vols, {})
        self.assertEqual(len(mounts), 2)
        self.assertEqual(mounts[0]["volume_sub_path"], "/home/site/wwwroot")
        self.assertEqual(mounts[0]["container_mount_path"], "/var/www/html")
        self.assertEqual(mounts[1]["volume_sub_path"], "/home/wordpress/uploads")

    def test_named_volume_file(self):
        compose = _load_sample("compose-convert-volumes-named.yml")
        top_vols = compose.get("volumes", {})
        app_vols = compose["services"]["app"]["volumes"]
        mounts, warnings = _parse_compose_volumes(app_vols, top_vols)
        self.assertEqual(len(mounts), 2)
        self.assertEqual(mounts[0]["volume_sub_path"], "/compose/volumes/app-data")
        self.assertTrue(any("Named volume" in w for w in warnings))

    def test_long_syntax_file(self):
        compose = _load_sample("compose-convert-volumes-long.yml")
        web_vols = compose["services"]["web"]["volumes"]
        mounts, warnings = _parse_compose_volumes(web_vols, {})
        self.assertEqual(len(mounts), 2)
        self.assertEqual(mounts[0]["volume_sub_path"], "/home/site/wwwroot")
        self.assertEqual(mounts[0]["container_mount_path"], "/usr/share/nginx/html")
        self.assertTrue(mounts[1]["read_only"])  # second mount has read_only: true

    def test_unsupported_bind_file(self):
        compose = _load_sample("compose-convert-unsupported-bind.yml")
        app_vols = compose["services"]["app"]["volumes"]
        mounts, warnings = _parse_compose_volumes(app_vols, {})
        # 2 valid ${WEBAPP_STORAGE_HOME} mounts, 2 unsupported
        self.assertEqual(len(mounts), 2)
        unsupported_warnings = [w for w in warnings if "UNSUPPORTED" in w]
        self.assertEqual(len(unsupported_warnings), 2)

    def test_full_scenario_volumes(self):
        compose = _load_sample("compose-convert-full.yml")
        # WordPress has short + long syntax volumes
        wp_vols = compose["services"]["wordpress"]["volumes"]
        mounts, warnings = _parse_compose_volumes(wp_vols, {})
        self.assertEqual(len(mounts), 2)
        paths = [m["volume_sub_path"] for m in mounts]
        self.assertIn("/home/site/wwwroot", paths)
        self.assertIn("/home/wordpress/uploads", paths)


# ---------------------------------------------------------------------------
# End-to-end parsing of entrypoint/command from sample files
# ---------------------------------------------------------------------------
class TestSampleEntrypointParsing(unittest.TestCase):
    def test_string_entrypoint_and_command(self):
        compose = _load_sample("compose-convert-entrypoint-command.yml")
        web = compose["services"]["web"]
        ep = _parse_compose_entrypoint_or_command(web.get("entrypoint"))
        cmd = _parse_compose_entrypoint_or_command(web.get("command"))
        merged = _merge_entrypoint_command(ep, cmd)
        self.assertEqual(merged, "gunicorn --bind 0.0.0.0:5000 app:app --workers 4")

    def test_list_entrypoint_and_command(self):
        compose = _load_sample("compose-convert-entrypoint-command.yml")
        worker = compose["services"]["worker"]
        ep = _parse_compose_entrypoint_or_command(worker.get("entrypoint"))
        cmd = _parse_compose_entrypoint_or_command(worker.get("command"))
        merged = _merge_entrypoint_command(ep, cmd)
        self.assertEqual(merged, "celery -A tasks worker --loglevel=info --concurrency=2")

    def test_command_only(self):
        compose = _load_sample("compose-convert-entrypoint-command.yml")
        scheduler = compose["services"]["scheduler"]
        ep = _parse_compose_entrypoint_or_command(scheduler.get("entrypoint"))
        cmd = _parse_compose_entrypoint_or_command(scheduler.get("command"))
        merged = _merge_entrypoint_command(ep, cmd)
        self.assertEqual(merged, "celery -A tasks beat --loglevel=info")

    def test_entrypoint_only(self):
        compose = _load_sample("compose-convert-entrypoint-command.yml")
        sidecar = compose["services"]["sidecar"]
        ep = _parse_compose_entrypoint_or_command(sidecar.get("entrypoint"))
        cmd = _parse_compose_entrypoint_or_command(sidecar.get("command"))
        merged = _merge_entrypoint_command(ep, cmd)
        self.assertEqual(merged, "/usr/local/bin/monitor --port 9090")


# ---------------------------------------------------------------------------
# End-to-end parsing of environment variables from sample files
# ---------------------------------------------------------------------------
class TestSampleEnvParsing(unittest.TestCase):
    def test_env_mapping_format_from_file(self):
        compose = _load_sample("compose-convert-env-mapping.yml")
        env = _parse_compose_environment(compose["services"]["api"]["environment"])
        self.assertEqual(env["NODE_ENV"], "production")
        self.assertEqual(env["DB_HOST"], "localhost")
        self.assertEqual(env["DB_PORT"], "5432")

    def test_sequence_format(self):
        compose = _load_sample("compose-convert-env-sequence.yml")
        env = _parse_compose_environment(compose["services"]["app"]["environment"])
        self.assertEqual(env["REDIS_URL"], "redis://localhost:6379")
        self.assertEqual(env["EXISTING_SETTING"], "")  # name-only reference

    def test_multiline_value(self):
        compose = _load_sample("compose-convert-full.yml")
        env = _parse_compose_environment(compose["services"]["wordpress"]["environment"])
        # WORDPRESS_CONFIG_EXTRA has multiline YAML value
        self.assertIn("WP_REDIS_HOST", env["WORDPRESS_CONFIG_EXTRA"])


# ---------------------------------------------------------------------------
# Port parsing from sample files
# ---------------------------------------------------------------------------
class TestSamplePortParsing(unittest.TestCase):
    def test_basic_ports(self):
        compose = _load_sample("compose-convert-basic.yml")
        ports = _parse_compose_ports(compose["services"]["web"].get("ports"))
        self.assertEqual(ports, [(8080, 8080)])

    def test_port_conflict_different_host_same_container(self):
        compose = _load_sample("compose-convert-port-conflict.yml")
        fe_ports = _parse_compose_ports(compose["services"]["frontend"].get("ports"))
        be_ports = _parse_compose_ports(compose["services"]["backend"].get("ports"))
        # Both have container port 8080
        self.assertEqual(fe_ports[0][1], 8080)
        self.assertEqual(be_ports[0][1], 8080)

    def test_multi_port(self):
        compose = _load_sample("compose-convert-multi-port.yml")
        ports = _parse_compose_ports(compose["services"]["app"].get("ports"))
        self.assertEqual(len(ports), 3)
        self.assertEqual(ports[0], (80, 80))
        self.assertEqual(ports[1], (443, 443))
        self.assertEqual(ports[2], (8080, 8080))

    def test_no_ports(self):
        compose = _load_sample("compose-convert-no-ports.yml")
        ports = _parse_compose_ports(compose["services"]["processor"].get("ports"))
        self.assertEqual(ports, [])


# ---------------------------------------------------------------------------
# _make_named_volume_mount (direct tests)
# ---------------------------------------------------------------------------
class TestMakeNamedVolumeMount(unittest.TestCase):
    def test_basic_named_volume(self):
        warnings = []
        result = _make_named_volume_mount("mydata", "/app/data", False, {}, warnings)
        self.assertIsNotNone(result)
        self.assertEqual(result["volume_sub_path"], "/compose/volumes/mydata")
        self.assertEqual(result["container_mount_path"], "/app/data")
        self.assertFalse(result["read_only"])
        self.assertTrue(any("Named volume" in w for w in warnings))
        self.assertTrue(any("ephemeral" in w.lower() or "LOCAL" in w for w in warnings))

    def test_named_volume_read_only(self):
        warnings = []
        result = _make_named_volume_mount("cache", "/tmp/cache", True, {}, warnings)
        self.assertTrue(result["read_only"])

    def test_named_volume_with_top_level(self):
        warnings = []
        result = _make_named_volume_mount("pgdata", "/var/lib/pg", False, {"pgdata": None}, warnings)
        self.assertEqual(result["volume_sub_path"], "/compose/volumes/pgdata")

    def test_named_volume_persistence_warning(self):
        warnings = []
        _make_named_volume_mount("data", "/data", False, {}, warnings)
        self.assertTrue(any("persist" in w.lower() or "restart" in w.lower() for w in warnings))


# ---------------------------------------------------------------------------
# Helpers to build mocked objects for orchestration tests
# ---------------------------------------------------------------------------
def _make_compose_b64(compose_dict):
    """Encode a compose dict as COMPOSE|<base64> linuxFxVersion."""
    yaml_str = yaml.dump(compose_dict, default_flow_style=False)
    b64 = b64encode(yaml_str.encode('utf-8')).decode('utf-8')
    return f"COMPOSE|{b64}"


def _make_mock_site_config(**kwargs):
    """Create a mock site_config object."""
    config = MagicMock()
    config.acr_use_managed_identity_creds = kwargs.get("acr_use_managed_identity_creds", None)
    config.acr_user_managed_identity_id = kwargs.get("acr_user_managed_identity_id", None)
    return config


def _make_mock_cmd(existing_app_settings=None):
    """Create a mock cmd object with CLI context for ARM calls."""
    cmd = MagicMock()
    cmd.cli_ctx = MagicMock()
    cmd.cli_ctx.cloud.endpoints.resource_manager = "https://management.azure.com"

    # Mock send_raw_request to return existing app settings
    settings = existing_app_settings or {}
    response = MagicMock()
    response.json.return_value = {"properties": settings}
    return cmd, response


# Patch targets in the module under test
_CUSTOM_MOD = "azure.cli.command_modules.appservice.custom"
_GET_SUB_ID = "azure.cli.core.commands.client_factory.get_subscription_id"


# ---------------------------------------------------------------------------
# Orchestration: Main container detection
# ---------------------------------------------------------------------------
class TestMainContainerDetection(unittest.TestCase):
    """Test main container auto-detection logic in _convert_compose_to_sitecontainers."""

    def _run_conversion(self, compose_dict, main_container_name=None, existing_settings=None):
        """Run the conversion with mocked ARM calls and return created sitecontainers."""
        cmd, raw_response = _make_mock_cmd(existing_settings)
        site_config = _make_mock_site_config()
        linux_fx = _make_compose_b64(compose_dict)
        created = []

        def track_create(cmd, name, rg, container_name, sitecontainer, slot):
            created.append({
                "container_name": container_name,
                "is_main": sitecontainer.is_main,
                "image": sitecontainer.image,
                "target_port": sitecontainer.target_port,
            })
            return MagicMock()

        with patch(f"{_CUSTOM_MOD}.send_raw_request", return_value=raw_response), \
             patch(_GET_SUB_ID, return_value="00000000-0000-0000-0000-000000000000"), \
             patch(f"{_CUSTOM_MOD}._create_or_update_webapp_sitecontainer_internal", side_effect=track_create), \
             patch(f"{_CUSTOM_MOD}.update_app_settings"), \
             patch(f"{_CUSTOM_MOD}.update_site_configs"), \
             patch(f"{_CUSTOM_MOD}.prompt_y_n", return_value=True):
            _convert_compose_to_sitecontainers(
                cmd, "testapp", "testrg", None, site_config, linux_fx, main_container_name
            )
        return created

    def test_single_service_with_port_is_main(self):
        compose = {
            "version": "3",
            "services": {
                "web": {"image": "nginx:alpine", "ports": ["80:80"]},
                "redis": {"image": "redis:alpine"},
            }
        }
        created = self._run_conversion(compose)
        self.assertEqual(len(created), 2)
        web = next(c for c in created if c["container_name"] == "web")
        redis = next(c for c in created if c["container_name"] == "redis")
        self.assertTrue(web["is_main"])
        self.assertFalse(redis["is_main"])

    def test_multiple_ports_first_is_main(self):
        # yaml.dump sorts keys alphabetically, so 'api' < 'web' means 'api' is first
        compose = {
            "version": "3",
            "services": {
                "api": {"image": "nginx:alpine", "ports": ["80:80"]},
                "web": {"image": "node:20", "ports": ["8080:8080"]},
            }
        }
        created = self._run_conversion(compose)
        api = next(c for c in created if c["container_name"] == "api")
        web = next(c for c in created if c["container_name"] == "web")
        self.assertTrue(api["is_main"])
        self.assertFalse(web["is_main"])

    def test_no_ports_first_service_is_main(self):
        # yaml.dump sorts keys alphabetically, so 'alpha' < 'beta' means 'alpha' is first
        compose = {
            "version": "3",
            "services": {
                "alpha": {"image": "busybox:latest"},
                "beta": {"image": "busybox:latest"},
            }
        }
        created = self._run_conversion(compose)
        alpha = next(c for c in created if c["container_name"] == "alpha")
        beta = next(c for c in created if c["container_name"] == "beta")
        self.assertTrue(alpha["is_main"])
        self.assertFalse(beta["is_main"])

    def test_explicit_main_container_name_by_service(self):
        compose = {
            "version": "3",
            "services": {
                "frontend": {"image": "nginx:alpine", "ports": ["80:80"]},
                "backend": {"image": "node:20", "ports": ["8080:8080"]},
            }
        }
        created = self._run_conversion(compose, main_container_name="backend")
        frontend = next(c for c in created if c["container_name"] == "frontend")
        backend = next(c for c in created if c["container_name"] == "backend")
        self.assertFalse(frontend["is_main"])
        self.assertTrue(backend["is_main"])

    def test_explicit_main_container_name_not_found_raises(self):
        compose = {
            "version": "3",
            "services": {
                "web": {"image": "nginx:alpine", "ports": ["80:80"]},
            }
        }
        from azure.cli.core.azclierror import ValidationError
        with self.assertRaises(ValidationError):
            self._run_conversion(compose, main_container_name="nonexistent")


# ---------------------------------------------------------------------------
# Orchestration: Container name collision
# ---------------------------------------------------------------------------
class TestContainerNameCollision(unittest.TestCase):

    def test_collision_raises_validation_error(self):
        """Services 'my_web_app' and 'my.web.app' both sanitize to 'my-web-app'."""
        compose = {
            "version": "3",
            "services": {
                "my_web_app": {"image": "nginx:alpine", "ports": ["80:80"]},
                "my.web.app": {"image": "httpd:alpine"},
            }
        }
        cmd, raw_response = _make_mock_cmd()
        site_config = _make_mock_site_config()
        linux_fx = _make_compose_b64(compose)

        from azure.cli.core.azclierror import ValidationError
        with patch(f"{_CUSTOM_MOD}.send_raw_request", return_value=raw_response), \
             patch(_GET_SUB_ID, return_value="sub-id"), \
             patch(f"{_CUSTOM_MOD}.prompt_y_n", return_value=True):
            with self.assertRaises(ValidationError) as ctx:
                _convert_compose_to_sitecontainers(
                    cmd, "testapp", "testrg", None, site_config, linux_fx
                )
            self.assertIn("collision", str(ctx.exception).lower())


# ---------------------------------------------------------------------------
# Orchestration: Environment variable app setting naming
# ---------------------------------------------------------------------------
class TestEnvVarAppSettingNaming(unittest.TestCase):

    def _run_and_capture_settings(self, compose_dict, existing_settings=None):
        """Run conversion and capture the app settings that would be created."""
        cmd, raw_response = _make_mock_cmd(existing_settings)
        site_config = _make_mock_site_config()
        linux_fx = _make_compose_b64(compose_dict)
        captured_settings = {}

        def capture_update_settings(cmd, rg, name, settings_list, slot=None):
            for s in settings_list:
                key, val = s.split("=", 1)
                captured_settings[key] = val

        with patch(f"{_CUSTOM_MOD}.send_raw_request", return_value=raw_response), \
             patch(_GET_SUB_ID, return_value="sub-id"), \
             patch(f"{_CUSTOM_MOD}._create_or_update_webapp_sitecontainer_internal", return_value=MagicMock()), \
             patch(f"{_CUSTOM_MOD}.update_app_settings", side_effect=capture_update_settings), \
             patch(f"{_CUSTOM_MOD}.update_site_configs"), \
             patch(f"{_CUSTOM_MOD}.prompt_y_n", return_value=True):
            _convert_compose_to_sitecontainers(
                cmd, "testapp", "testrg", None, site_config, linux_fx
            )
        return captured_settings

    def test_env_vars_create_compose_prefixed_settings(self):
        compose = {
            "version": "3",
            "services": {
                "web": {
                    "image": "nginx:alpine",
                    "ports": ["80:80"],
                    "environment": {"MY_VAR": "hello", "OTHER": "world"},
                }
            }
        }
        settings = self._run_and_capture_settings(compose)
        self.assertIn("COMPOSE_WEB_MY_VAR", settings)
        self.assertEqual(settings["COMPOSE_WEB_MY_VAR"], "hello")
        self.assertIn("COMPOSE_WEB_OTHER", settings)
        self.assertEqual(settings["COMPOSE_WEB_OTHER"], "world")

    def test_env_var_service_name_sanitized_in_key(self):
        """Service with underscores should have underscores in setting key (not hyphens)."""
        compose = {
            "version": "3",
            "services": {
                "my-api": {
                    "image": "node:20",
                    "ports": ["8080:8080"],
                    "environment": {"PORT": "8080"},
                }
            }
        }
        settings = self._run_and_capture_settings(compose)
        # _sanitize_container_name("my-api") -> "my-api", then upper + replace - with _
        self.assertIn("COMPOSE_MY_API_PORT", settings)

    def test_valueless_env_var_references_existing_setting(self):
        """Env var with no value should reference existing app setting directly."""
        compose = {
            "version": "3",
            "services": {
                "web": {
                    "image": "nginx:alpine",
                    "ports": ["80:80"],
                    "environment": ["EXISTING_KEY"],
                }
            }
        }
        # EXISTING_KEY already exists as an app setting
        settings = self._run_and_capture_settings(compose, existing_settings={"EXISTING_KEY": "some-value"})
        # Should NOT create a COMPOSE_ prefixed setting for it
        self.assertNotIn("COMPOSE_WEB_EXISTING_KEY", settings)

    def test_valueless_env_var_no_existing_creates_empty(self):
        """Env var with no value and no existing setting creates empty COMPOSE_ key."""
        compose = {
            "version": "3",
            "services": {
                "web": {
                    "image": "nginx:alpine",
                    "ports": ["80:80"],
                    "environment": ["MISSING_KEY"],
                }
            }
        }
        settings = self._run_and_capture_settings(compose, existing_settings={})
        self.assertIn("COMPOSE_WEB_MISSING_KEY", settings)
        self.assertEqual(settings["COMPOSE_WEB_MISSING_KEY"], "")


# ---------------------------------------------------------------------------
# Orchestration: Port conflict warnings
# ---------------------------------------------------------------------------
class TestPortConflictWarnings(unittest.TestCase):

    def _run_and_capture_warnings(self, compose_dict):
        """Run conversion and capture logger warnings."""
        cmd, raw_response = _make_mock_cmd()
        site_config = _make_mock_site_config()
        linux_fx = _make_compose_b64(compose_dict)
        warnings = []

        def capture_warning(msg, *args):
            warnings.append(msg % args if args else msg)

        with patch(f"{_CUSTOM_MOD}.send_raw_request", return_value=raw_response), \
             patch(_GET_SUB_ID, return_value="sub-id"), \
             patch(f"{_CUSTOM_MOD}._create_or_update_webapp_sitecontainer_internal", return_value=MagicMock()), \
             patch(f"{_CUSTOM_MOD}.update_app_settings"), \
             patch(f"{_CUSTOM_MOD}.update_site_configs"), \
             patch(f"{_CUSTOM_MOD}.logger") as mock_logger, \
             patch(f"{_CUSTOM_MOD}.prompt_y_n", return_value=True):
            mock_logger.warning = capture_warning
            _convert_compose_to_sitecontainers(
                cmd, "testapp", "testrg", None, site_config, linux_fx
            )
        return warnings

    def test_port_conflict_critical_warning(self):
        compose = {
            "version": "3",
            "services": {
                "frontend": {"image": "nginx:alpine", "ports": ["80:80"]},
                "backend": {"image": "httpd:alpine", "ports": ["8080:80"]},
            }
        }
        warnings = self._run_and_capture_warnings(compose)
        critical = [w for w in warnings if "CRITICAL" in w and "80" in w]
        self.assertTrue(len(critical) > 0, "Expected a CRITICAL port conflict warning for port 80")

    def test_host_container_port_mismatch_warning(self):
        compose = {
            "version": "3",
            "services": {
                "web": {"image": "nginx:alpine", "ports": ["8080:3000"]},
            }
        }
        warnings = self._run_and_capture_warnings(compose)
        mismatch = [w for w in warnings if "Host port" in w and "8080" in w and "3000" in w]
        self.assertTrue(len(mismatch) > 0, "Expected host/container port mismatch warning")

    def test_multiple_ports_warning(self):
        compose = {
            "version": "3",
            "services": {
                "web": {"image": "nginx:alpine", "ports": ["80:80", "443:443"]},
            }
        }
        warnings = self._run_and_capture_warnings(compose)
        multi = [w for w in warnings if "Multiple port mappings" in w]
        self.assertTrue(len(multi) > 0, "Expected multiple port mappings warning")

    def test_unsupported_keys_warning(self):
        compose = {
            "version": "3",
            "services": {
                "web": {
                    "image": "nginx:alpine",
                    "ports": ["80:80"],
                    "depends_on": ["redis"],
                    "healthcheck": {"test": "curl http://localhost"},
                },
                "redis": {"image": "redis:alpine"},
            }
        }
        warnings = self._run_and_capture_warnings(compose)
        dep_warnings = [w for w in warnings if "depends_on" in w]
        hc_warnings = [w for w in warnings if "healthcheck" in w]
        self.assertTrue(len(dep_warnings) > 0, "Expected depends_on warning")
        self.assertTrue(len(hc_warnings) > 0, "Expected healthcheck warning")

    def test_networking_notice_always_shown(self):
        compose = {
            "version": "3",
            "services": {
                "web": {"image": "nginx:alpine", "ports": ["80:80"]},
            }
        }
        warnings = self._run_and_capture_warnings(compose)
        net = [w for w in warnings if "localhost" in w and "network namespace" in w]
        self.assertTrue(len(net) > 0, "Expected networking change notice")


# ---------------------------------------------------------------------------
# Orchestration: Rollback on failure
# ---------------------------------------------------------------------------
class TestRollbackOnFailure(unittest.TestCase):

    def test_rollback_deletes_created_containers(self):
        """If creating the 2nd container fails, the 1st should be rolled back."""
        compose = {
            "version": "3",
            "services": {
                "web": {"image": "nginx:alpine", "ports": ["80:80"]},
                "sidecar": {"image": "redis:alpine"},
            }
        }
        cmd, raw_response = _make_mock_cmd()
        site_config = _make_mock_site_config()
        linux_fx = _make_compose_b64(compose)
        call_count = [0]

        def fail_on_second(cmd, name, rg, container_name, sitecontainer, slot):
            call_count[0] += 1
            if call_count[0] == 2:
                raise Exception("Simulated ARM failure")
            return MagicMock()

        from azure.cli.core.azclierror import AzureInternalError
        with patch(f"{_CUSTOM_MOD}.send_raw_request", return_value=raw_response), \
             patch(_GET_SUB_ID, return_value="sub-id"), \
             patch(f"{_CUSTOM_MOD}._create_or_update_webapp_sitecontainer_internal", side_effect=fail_on_second), \
             patch(f"{_CUSTOM_MOD}.update_app_settings"), \
             patch(f"{_CUSTOM_MOD}.update_site_configs"), \
             patch(f"{_CUSTOM_MOD}.delete_webapp_sitecontainer") as mock_delete, \
             patch(f"{_CUSTOM_MOD}.prompt_y_n", return_value=True):
            with self.assertRaises(AzureInternalError):
                _convert_compose_to_sitecontainers(
                    cmd, "testapp", "testrg", None, site_config, linux_fx
                )
            # 'sidecar' < 'web' alphabetically, so sidecar is created first (succeeds),
            # then web fails. Rollback deletes the already-created 'sidecar'.
            mock_delete.assert_called_once()
            delete_args = mock_delete.call_args
            self.assertEqual(delete_args[0][1], "testapp")
            self.assertEqual(delete_args[0][3], "sidecar")

    def test_linuxfxversion_not_set_on_failure(self):
        """If container creation fails, linuxFxVersion should NOT be changed."""
        compose = {
            "version": "3",
            "services": {
                "web": {"image": "nginx:alpine", "ports": ["80:80"]},
            }
        }
        cmd, raw_response = _make_mock_cmd()
        site_config = _make_mock_site_config()
        linux_fx = _make_compose_b64(compose)

        from azure.cli.core.azclierror import AzureInternalError
        with patch(f"{_CUSTOM_MOD}.send_raw_request", return_value=raw_response), \
             patch(_GET_SUB_ID, return_value="sub-id"), \
             patch(f"{_CUSTOM_MOD}._create_or_update_webapp_sitecontainer_internal",
                   side_effect=Exception("ARM failure")), \
             patch(f"{_CUSTOM_MOD}.update_app_settings"), \
             patch(f"{_CUSTOM_MOD}.update_site_configs") as mock_update_config, \
             patch(f"{_CUSTOM_MOD}.delete_webapp_sitecontainer"), \
             patch(f"{_CUSTOM_MOD}.prompt_y_n", return_value=True):
            with self.assertRaises(AzureInternalError):
                _convert_compose_to_sitecontainers(
                    cmd, "testapp", "testrg", None, site_config, linux_fx
                )
            mock_update_config.assert_not_called()


# ---------------------------------------------------------------------------
# Orchestration: Auth type detection
# ---------------------------------------------------------------------------
class TestAuthTypeDetection(unittest.TestCase):

    def _run_and_capture_auth(self, compose_dict, site_config_kwargs=None, existing_settings=None):
        """Run conversion and capture the auth_type used for each container."""
        cmd, raw_response = _make_mock_cmd(existing_settings)
        site_config = _make_mock_site_config(**(site_config_kwargs or {}))
        linux_fx = _make_compose_b64(compose_dict)
        created = []

        def track_create(cmd, name, rg, container_name, sitecontainer, slot):
            created.append({
                "container_name": container_name,
                "auth_type": sitecontainer.auth_type,
                "user_name": sitecontainer.user_name,
                "user_managed_identity_client_id": sitecontainer.user_managed_identity_client_id,
            })
            return MagicMock()

        with patch(f"{_CUSTOM_MOD}.send_raw_request", return_value=raw_response), \
             patch(_GET_SUB_ID, return_value="sub-id"), \
             patch(f"{_CUSTOM_MOD}._create_or_update_webapp_sitecontainer_internal", side_effect=track_create), \
             patch(f"{_CUSTOM_MOD}.update_app_settings"), \
             patch(f"{_CUSTOM_MOD}.update_site_configs"), \
             patch(f"{_CUSTOM_MOD}.prompt_y_n", return_value=True):
            _convert_compose_to_sitecontainers(
                cmd, "testapp", "testrg", None, site_config, linux_fx
            )
        return created

    def test_anonymous_when_no_credentials(self):
        compose = {"version": "3", "services": {"web": {"image": "nginx:alpine", "ports": ["80:80"]}}}
        created = self._run_and_capture_auth(compose)
        self.assertEqual(created[0]["auth_type"], "Anonymous")

    def test_user_credentials_from_app_settings(self):
        compose = {"version": "3", "services": {"web": {"image": "myacr.azurecr.io/app:v1", "ports": ["80:80"]}}}
        created = self._run_and_capture_auth(compose, existing_settings={
            "DOCKER_REGISTRY_SERVER_USERNAME": "myuser",
            "DOCKER_REGISTRY_SERVER_PASSWORD": "mypass",
        })
        self.assertEqual(created[0]["auth_type"], "UserCredentials")
        self.assertEqual(created[0]["user_name"], "myuser")

    def test_system_identity(self):
        compose = {"version": "3", "services": {"web": {"image": "myacr.azurecr.io/app:v1", "ports": ["80:80"]}}}
        created = self._run_and_capture_auth(compose, site_config_kwargs={
            "acr_use_managed_identity_creds": True,
        })
        self.assertEqual(created[0]["auth_type"], "SystemIdentity")

    def test_user_assigned_managed_identity(self):
        compose = {"version": "3", "services": {"web": {"image": "myacr.azurecr.io/app:v1", "ports": ["80:80"]}}}
        created = self._run_and_capture_auth(compose, site_config_kwargs={
            "acr_use_managed_identity_creds": True,
            "acr_user_managed_identity_id": "client-id-123",
        })
        self.assertEqual(created[0]["auth_type"], "UserAssigned")
        self.assertEqual(created[0]["user_managed_identity_client_id"], "client-id-123")

    def test_auth_shared_across_all_containers(self):
        compose = {
            "version": "3",
            "services": {
                "web": {"image": "myacr.azurecr.io/web:v1", "ports": ["80:80"]},
                "worker": {"image": "myacr.azurecr.io/worker:v1"},
            }
        }
        created = self._run_and_capture_auth(compose, existing_settings={
            "DOCKER_REGISTRY_SERVER_USERNAME": "user",
            "DOCKER_REGISTRY_SERVER_PASSWORD": "pass",
        })
        self.assertEqual(len(created), 2)
        for c in created:
            self.assertEqual(c["auth_type"], "UserCredentials")


# ---------------------------------------------------------------------------
# Orchestration: Invalid compose input
# ---------------------------------------------------------------------------
class TestInvalidComposeInput(unittest.TestCase):

    def _run(self, linux_fx):
        cmd, raw_response = _make_mock_cmd()
        site_config = _make_mock_site_config()
        with patch(f"{_CUSTOM_MOD}.send_raw_request", return_value=raw_response), \
             patch(_GET_SUB_ID, return_value="sub-id"):
            _convert_compose_to_sitecontainers(
                cmd, "testapp", "testrg", None, site_config, linux_fx
            )

    def test_invalid_base64_raises(self):
        from azure.cli.core.azclierror import ValidationError
        with self.assertRaises(ValidationError) as ctx:
            self._run("COMPOSE|!!!not-base64!!!")
        self.assertIn("base64", str(ctx.exception).lower())

    def test_missing_services_raises(self):
        from azure.cli.core.azclierror import ValidationError
        compose = {"version": "3"}  # no services key
        linux_fx = _make_compose_b64(compose)
        with self.assertRaises(ValidationError) as ctx:
            self._run(linux_fx)
        self.assertIn("services", str(ctx.exception).lower())

    def test_empty_services_raises(self):
        from azure.cli.core.azclierror import ValidationError
        compose = {"version": "3", "services": {}}
        linux_fx = _make_compose_b64(compose)
        with self.assertRaises(ValidationError) as ctx:
            self._run(linux_fx)
        self.assertIn("no services", str(ctx.exception).lower())

    def test_service_without_image_raises(self):
        from azure.cli.core.azclierror import ValidationError
        compose = {"version": "3", "services": {"web": {"ports": ["80:80"]}}}
        linux_fx = _make_compose_b64(compose)
        with self.assertRaises(ValidationError) as ctx:
            self._run(linux_fx)
        self.assertIn("image", str(ctx.exception).lower())


# ---------------------------------------------------------------------------
# Orchestration: linuxFxVersion set to SITECONTAINERS on success
# ---------------------------------------------------------------------------
class TestLinuxFxVersionSet(unittest.TestCase):

    def test_sitecontainers_fx_version_set_on_success(self):
        compose = {
            "version": "3",
            "services": {"web": {"image": "nginx:alpine", "ports": ["80:80"]}}
        }
        cmd, raw_response = _make_mock_cmd()
        site_config = _make_mock_site_config()
        linux_fx = _make_compose_b64(compose)

        with patch(f"{_CUSTOM_MOD}.send_raw_request", return_value=raw_response), \
             patch(_GET_SUB_ID, return_value="sub-id"), \
             patch(f"{_CUSTOM_MOD}._create_or_update_webapp_sitecontainer_internal", return_value=MagicMock()), \
             patch(f"{_CUSTOM_MOD}.update_app_settings"), \
             patch(f"{_CUSTOM_MOD}.update_site_configs") as mock_update_config, \
             patch(f"{_CUSTOM_MOD}.prompt_y_n", return_value=True):
            _convert_compose_to_sitecontainers(
                cmd, "testapp", "testrg", None, site_config, linux_fx
            )
            mock_update_config.assert_called_once_with(
                cmd, "testrg", "testapp", slot=None, linux_fx_version="SITECONTAINERS"
            )


if __name__ == '__main__':
    unittest.main()
