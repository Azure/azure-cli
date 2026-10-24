# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import contextlib
import unittest
from unittest import mock

from azure.cli.command_modules.aro.azext_aro_hcp.commands import load_command_table


class _Loader:
    def __init__(self):
        self.command_table = {}
        self.command_groups = []

    def command_group(self, name):
        self.command_groups.append(name)
        return contextlib.nullcontext()


class CommandTableTest(unittest.TestCase):

    @mock.patch("azure.cli.command_modules.aro.azext_aro_hcp.custom.GetVersions", autospec=True)
    @mock.patch("azure.cli.command_modules.aro.aaz.latest.aro.hcp.cluster.nodepool._show.Show", autospec=True)
    @mock.patch("azure.cli.command_modules.aro.aaz.latest.aro.hcp.cluster.nodepool._list.List", autospec=True)
    @mock.patch("azure.cli.command_modules.aro.aaz.latest.aro.hcp.cluster._show.Show", autospec=True)
    @mock.patch("azure.cli.command_modules.aro.aaz.latest.aro.hcp.cluster._list.List", autospec=True)
    @mock.patch("azure.cli.command_modules.aro.azext_aro_hcp.custom.RequestCredential", autospec=True)
    @mock.patch("azure.cli.command_modules.aro.azext_aro_hcp.custom.ClusterUpdate", autospec=True)
    @mock.patch("azure.cli.command_modules.aro.azext_aro_hcp.custom.ClusterCreate", autospec=True)
    def test_load_command_table_registers_custom_commands_and_transformers(
            self, cluster_create, cluster_update, request_credential, cluster_list, cluster_show,
            nodepool_list, nodepool_show, get_versions):
        loader = _Loader()

        load_command_table(loader, None)

        self.assertEqual(
            ["aro hcp cluster", "aro hcp cluster nodepool", "aro hcp"],
            loader.command_groups,
        )
        self.assertEqual(
            {
                "aro hcp cluster create",
                "aro hcp cluster update",
                "aro hcp cluster request-credential",
                "aro hcp cluster list",
                "aro hcp cluster show",
                "aro hcp cluster nodepool list",
                "aro hcp cluster nodepool show",
                "aro hcp get-versions",
            },
            set(loader.command_table),
        )
        cluster_create.assert_called_once_with(loader=loader)
        cluster_update.assert_called_once_with(loader=loader)
        request_credential.assert_called_once_with(loader=loader)
        cluster_list.assert_called_once()
        cluster_show.assert_called_once()
        nodepool_list.assert_called_once()
        nodepool_show.assert_called_once()
        get_versions.assert_called_once_with(loader=loader)

        from azure.cli.command_modules.aro.azext_aro_hcp._format import (
            cluster_list_table_format,
            cluster_show_table_format,
            nodepool_list_table_format,
            nodepool_show_table_format,
        )
        self.assertIs(cluster_list.call_args.kwargs["table_transformer"], cluster_list_table_format)
        self.assertIs(cluster_show.call_args.kwargs["table_transformer"], cluster_show_table_format)
        self.assertIs(nodepool_list.call_args.kwargs["table_transformer"], nodepool_list_table_format)
        self.assertIs(nodepool_show.call_args.kwargs["table_transformer"], nodepool_show_table_format)


if __name__ == "__main__":
    unittest.main()