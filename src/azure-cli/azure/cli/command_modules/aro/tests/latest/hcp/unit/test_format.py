# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from azure.cli.command_modules.aro.azext_aro_hcp._format import (
    _major_minor,
    _parse_semver,
    cluster_list_table_format,
    cluster_show_table_format,
    get_versions_table_format,
    nodepool_list_table_format,
    nodepool_show_table_format,
)


class FormatTest(unittest.TestCase):

    def test_parse_semver(self):
        self.assertEqual((4, 19, 2), _parse_semver("4.19.2"))
        self.assertEqual((4, 19, 2), _parse_semver("4.19.2-preview"))
        self.assertEqual((0, 0, 0), _parse_semver("4.19"))
        self.assertEqual((0, 0, 0), _parse_semver(None))

    def test_major_minor(self):
        self.assertEqual("4.19", _major_minor("4.19.2"))
        self.assertEqual("4.19", _major_minor("4.19"))
        self.assertEqual("", _major_minor("invalid"))
        self.assertEqual("", _major_minor(None))

    def test_version_table_format(self):
        self.assertEqual(
            [{"Name": "4.19.2", "ChannelGroup": "stable"}, {"Name": "", "ChannelGroup": ""}],
            get_versions_table_format([
                {"name": "4.19.2", "properties": {"channelGroup": "stable"}},
                {},
            ]),
        )

    def test_cluster_table_formats(self):
        cluster = {
            "name": "cluster-one",
            "location": "eastus",
            "resourceGroup": "group-one",
            "properties": {
                "version": {"id": "4.19"},
                "provisioningState": "Succeeded",
                "api": {"url": "https://api.example.invalid"},
            },
        }
        expected = [{
            "Name": "cluster-one",
            "Location": "eastus",
            "ResourceGroup": "group-one",
            "Version": "4.19",
            "ProvisioningState": "Succeeded",
            "ApiServerUrl": "https://api.example.invalid",
        }]

        self.assertEqual(expected, cluster_show_table_format(cluster))
        self.assertEqual(expected, cluster_list_table_format([cluster]))
        self.assertEqual(
            [{
                "Name": "",
                "Location": "",
                "ResourceGroup": "",
                "Version": "",
                "ProvisioningState": "",
                "ApiServerUrl": "",
            }],
            cluster_show_table_format({}),
        )

    def test_nodepool_table_formats(self):
        nodepool = {
            "name": "workers",
            "properties": {
                "version": {"id": "4.19.2"},
                "platform": {"vmSize": "Standard_D4s_v5"},
                "provisioningState": "Succeeded",
            },
        }
        expected = [{
            "Name": "workers",
            "Version": "4.19.2",
            "VmSize": "Standard_D4s_v5",
            "ProvisioningState": "Succeeded",
        }]

        self.assertEqual(expected, nodepool_show_table_format(nodepool))
        self.assertEqual(expected, nodepool_list_table_format([nodepool]))
        self.assertEqual(
            [{"Name": "", "Version": "", "VmSize": "", "ProvisioningState": ""}],
            nodepool_show_table_format({}),
        )


if __name__ == "__main__":
    unittest.main()