# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest import mock

from azure.cli.command_modules.containerapp import _up_utils
from azure.cli.core.azclierror import RequiredArgumentMissingError


class ContainerAppImageRegistryTest(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch.multiple(
            _up_utils,
            _get_acr_cred=mock.DEFAULT,
            _get_acr_rg=mock.DEFAULT,
            ResourceGroup=mock.DEFAULT,
            AzureContainerRegistry=mock.DEFAULT,
        )
        self.mocks = patcher.start()
        self.addCleanup(patcher.stop)
        self.mocks["_get_acr_cred"].return_value = ("registry-user", "registry-password", "registry-rg")
        self.mocks["_get_acr_rg"].return_value = "registry-rg"
        self.cmd = mock.Mock()

    def test_containerapp_image_non_acr_does_not_infer_registry_or_credentials(self):
        for image in (
            None,
            "",
            "nginx:latest",
            "docker.io/library/nginx:latest",
            "sample.example.com/azurecr.io/app:v1",
            "sample.example.com/repository.azurecr.io",
            "sample.azurecr.io.example.com/app:v1",
            "sample.azurecr.cn.example.com/app:v1",
            "sample.azurecr.us.example.com/app:v1",
        ):
            for username, password in ((None, None), ("user", "password")):
                with self.subTest(image=image, username=username):
                    for patched in self.mocks.values():
                        patched.reset_mock()
                    app = mock.Mock(
                        image=image, registry_server=None, registry_user=username, registry_pass=password, acr=None
                    )

                    _up_utils._get_acr_from_image(self.cmd, app)

                    self.mocks["_get_acr_cred"].assert_not_called()
                    self.mocks["_get_acr_rg"].assert_not_called()
                    self.mocks["AzureContainerRegistry"].assert_not_called()
                    self.assertIsNone(app.registry_server)
                    self.assertIsNone(app.acr)
                    self.assertEqual(app.registry_user, username)
                    self.assertEqual(app.registry_pass, password)

    def test_containerapp_image_invalid_acr_authorities_do_not_infer_credentials(self):
        for server in (
            ".azurecr.io",
            "a.b.azurecr.io",
            "user@sample.azurecr.io",
            "sample.azurecr.io:443",
            "sample:443.azurecr.io",
            "sample_name.azurecr.io",
            "sample-name.azurecr.io",
            "\u00e9sample.azurecr.io",
            "https:",
        ):
            with self.subTest(server=server):
                for patched in self.mocks.values():
                    patched.reset_mock()
                app = mock.Mock(
                    image=server + "/app:v1", registry_server=None, registry_user=None, registry_pass=None, acr=None
                )

                _up_utils._get_acr_from_image(self.cmd, app)

                self.mocks["_get_acr_cred"].assert_not_called()
                self.mocks["_get_acr_rg"].assert_not_called()
                self.assertIsNone(app.registry_server)
                self.assertIsNone(app.acr)

    def test_containerapp_image_uses_credentials_for_its_acr_authority(self):
        for server in ("sample.azurecr.io", "Sample.AzureCR.io", "sample.azurecr.cn", "sample.azurecr.us"):
            for reference in ("/team/app:v1", "/team/app@sha256:" + "0" * 64):
                for username, password in ((None, None), ("user", None), (None, "password")):
                    with self.subTest(server=server, reference=reference, username=username):
                        self.mocks["_get_acr_cred"].reset_mock()
                        self.mocks["AzureContainerRegistry"].reset_mock()
                        self.mocks["ResourceGroup"].reset_mock()
                        app = mock.Mock(
                            image=server + reference, registry_server=None,
                            registry_user=username, registry_pass=password
                        )

                        _up_utils._get_acr_from_image(self.cmd, app)

                        self.mocks["_get_acr_cred"].assert_called_once_with(self.cmd.cli_ctx, "sample")
                        self.mocks["ResourceGroup"].assert_called_once_with(self.cmd, "registry-rg", None, None)
                        self.mocks["AzureContainerRegistry"].assert_called_once_with(
                            "sample", self.mocks["ResourceGroup"].return_value
                        )
                        self.assertEqual(app.registry_server, server)
                        self.assertEqual(app.registry_user, "registry-user")
                        self.assertEqual(app.registry_pass, "registry-password")
        self.mocks["_get_acr_rg"].assert_not_called()

    def test_containerapp_image_preserves_explicit_credentials(self):
        for server in ("sample.azurecr.io", "Sample.AzureCR.io", "sample.azurecr.cn", "sample.azurecr.us"):
            with self.subTest(server=server):
                self.mocks["_get_acr_rg"].reset_mock()
                self.mocks["AzureContainerRegistry"].reset_mock()
                app = mock.Mock(
                    image=server + "/app:v1", registry_server=None,
                    registry_user="user", registry_pass="password"
                )

                _up_utils._get_acr_from_image(self.cmd, app)

                self.mocks["_get_acr_cred"].assert_not_called()
                self.mocks["_get_acr_rg"].assert_called_once_with(app)
                self.mocks["AzureContainerRegistry"].assert_called_once_with(
                    name="sample", resource_group=self.mocks["ResourceGroup"].return_value
                )
                self.assertEqual(app.registry_server, server)
                self.assertEqual(app.registry_user, "user")
                self.assertEqual(app.registry_pass, "password")

    def test_containerapp_image_acr_lookup_failure_preserves_argument_error(self):
        cause = ValueError("lookup failed")
        self.mocks["_get_acr_cred"].side_effect = cause
        app = mock.Mock(image="sample.azurecr.io/app:v1", registry_user=None, registry_pass=None)

        with self.assertRaises(RequiredArgumentMissingError) as error:
            _up_utils._get_acr_from_image(self.cmd, app)

        self.assertIs(error.exception.__cause__, cause)
        self.mocks["AzureContainerRegistry"].assert_not_called()

    def test_containerapp_image_defaults_do_not_infer_credentials_from_a_path(self):
        app = mock.Mock(
            image="sample.example.com/azurecr.io/app:v1",
            registry_server=None, registry_user=None, registry_pass=None, acr=None
        )
        env = mock.Mock()
        env.name = None
        resource_group = mock.Mock()
        resource_group.name = "group"
        with mock.patch.object(_up_utils, "_get_app_env_and_group"), \
                mock.patch.object(_up_utils, "_get_env_and_group_from_log_analytics"):
            _up_utils._set_up_defaults(
                self.cmd, "app", "group", None, "eastus", resource_group, env, app, False
            )

        self.mocks["_get_acr_cred"].assert_not_called()
        self.assertIsNone(app.registry_server)
        self.assertIsNone(app.registry_pass)
