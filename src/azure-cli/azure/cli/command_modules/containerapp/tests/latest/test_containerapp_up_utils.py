# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest.mock import Mock, patch

from azure.cli.command_modules.containerapp import _up_utils
from azure.cli.core.azclierror import ValidationError


class ContainerAppRegistryDetailsTest(unittest.TestCase):
    def test_containerapp_registry_acr_lookup(self):
        for server, suffix, sources in (
            ("myacr.azurecr.io", ".azurecr.io", (None, ".")),
            ("MyAcr.AzureCR.io", ".azurecr.io", (None, ".")),
            ("myacr.azurecr.cn", ".azurecr.cn", (None, ".")),
            ("https://myacr.azurecr.io", ".azurecr.io", (None, ".")),
            ("https://myacr.azurecr.io/", ".azurecr.io", (None,)),
            ("https://MyAcr.AzureCR.io", ".azurecr.io", (None, ".")),
            ("https://myacr.azurecr.cn/", ".azurecr.cn", (None,)),
        ):
            for source in sources:
                for username, password in ((None, None), ("user", None), (None, "password")):
                    with self.subTest(server=server, source=source, username=username, password=password):
                        cmd = Mock()
                        cmd.cli_ctx.cloud.suffixes.acr_login_server_endpoint = suffix
                        app = Mock(registry_server=server, registry_user=username, registry_pass=password)
                        with patch.object(_up_utils, "_set_acr_creds", return_value="registry-rg") as lookup, \
                                patch.object(_up_utils, "ResourceGroup") as resource_group:
                            _up_utils._get_registry_details(cmd, app, source)
                        lookup.assert_called_once_with(cmd, app, "myacr")
                        resource_group.assert_called_once_with(cmd, "registry-rg", None, None)
                        self.assertEqual(app.acr.name, "myacr")
                        self.assertEqual(app.registry_server, server)

    def test_containerapp_registry_lookup_requires_acr_server(self):
        for server in (
            "myacr.example.com",
            "myacr.azurecr.io.example.com",
            "a.b.azurecr.io",
            "docker.io",
            "https://myacr.example.com",
            "https://myacr.azurecr.io.example.com/",
            "https://a.b.azurecr.io/",
        ):
            for source in (None, "."):
                for username, password in ((None, None), ("user", None), (None, "password")):
                    with self.subTest(server=server, source=source, username=username, password=password):
                        cmd = Mock()
                        cmd.cli_ctx.cloud.suffixes.acr_login_server_endpoint = ".azurecr.io"
                        app = Mock(registry_server=server, registry_user=username, registry_pass=password)
                        with patch.object(_up_utils, "_set_acr_creds") as lookup:
                            with self.assertRaises(ValidationError) as error:
                                _up_utils._get_registry_details(cmd, app, source)
                        lookup.assert_not_called()
                        if source is None or server == "a.b.azurecr.io":
                            self.assertEqual(
                                str(error.exception),
                                f"Registry server '{server}' is not an Azure Container Registry. Use "
                                "--registry-server, or pass --registry-username and --registry-password.",
                            )

    def test_containerapp_registry_explicit_credentials(self):
        for server in ("docker.io", "ghcr.io", "myacr.azurecr.io"):
            with self.subTest(server=server):
                cmd = Mock()
                app = Mock(registry_server=server, registry_user="user", registry_pass="password")
                with patch.object(_up_utils, "_set_acr_creds") as lookup, \
                        patch.object(_up_utils, "_get_acr_rg", return_value="registry-rg") as get_rg, \
                        patch.object(_up_utils, "ResourceGroup"):
                    _up_utils._get_registry_details(cmd, app, None)
                lookup.assert_not_called()
                get_rg.assert_called_once_with(app)
                self.assertEqual(app.acr.name, server.split(".")[0])
                self.assertEqual(app.registry_server, server)
