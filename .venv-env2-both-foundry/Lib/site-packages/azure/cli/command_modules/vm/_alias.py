# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# Alias for image
# https://github.com/Azure/azure-rest-api-specs/blob/main/arm-compute/quickstart-templates/aliases.json

alias_json = """
{
  "$schema": "http://schema.management.azure.com/schemas/2015-01-01/deploymentTemplate.json",
  "contentVersion": "1.0.0.0",
  "parameters": {},
  "variables": {},
  "resources": [],
  "outputs": {
    "aliases": {
      "type": "object",
      "value": {
        "Linux": {
          "CentOS85Gen2":  {
            "publisher":  "OpenLogic",
            "offer":  "CentOS",
            "sku":  "8_5-gen2",
            "version":  "latest",
            "architecture": "x64"
          },
          "Debian11":  {
            "publisher":  "Debian",
            "offer":  "debian-11",
            "sku":  "11-backports-gen2",
            "version":  "latest",
            "architecture": "x64"
          },
          "FlatcarLinuxFreeGen2":  {
            "publisher":  "kinvolk",
            "offer":  "flatcar-container-linux-free",
            "sku":  "stable-gen2",
            "version":  "latest",
            "architecture": "x64"
          },
          "OpenSuseLeap154Gen2":  {
            "publisher":  "SUSE",
            "offer":  "openSUSE-leap-15-4",
            "sku":  "gen2",
            "version":  "latest",
            "architecture": "x64"
          },
          "RHELRaw8LVMGen2":  {
            "publisher":  "RedHat",
            "offer":  "RHEL",
            "sku":  "8-lvm-gen2",
            "version":  "latest",
            "architecture": "x64"
          },
          "SuseSles15SP3": {
            "publisher": "SUSE",
            "offer": "sles-15-sp3",
            "sku": "gen2",
            "version": "latest",
            "architecture": "x64"
          },
          "Ubuntu2204":  {
            "publisher":  "Canonical",
            "offer":  "0001-com-ubuntu-server-jammy",
            "sku":  "22_04-lts-gen2",
            "version":  "latest",
            "architecture": "x64"
          }
        },
        "Windows": {
          "Win2022Datacenter": {
            "publisher": "MicrosoftWindowsServer",
            "offer": "WindowsServer",
            "sku": "2022-datacenter-g2",
            "version": "latest",
            "architecture": "x64"
          },
          "Win2022AzureEditionCore": {
            "publisher": "MicrosoftWindowsServer",
            "offer": "WindowsServer",
            "sku": "2022-datacenter-azure-edition-core",
            "version": "latest",
            "architecture": "x64"
          },
          "Win2019Datacenter": {
            "publisher": "MicrosoftWindowsServer",
            "offer": "WindowsServer",
            "sku": "2019-datacenter-gensecond",
            "version": "latest",
            "architecture": "x64"
          },
          "Win2016Datacenter": {
            "publisher": "MicrosoftWindowsServer",
            "offer": "WindowsServer",
            "sku": "2016-datacenter-gensecond",
            "version": "latest",
            "architecture": "x64"
          },
          "Win2012R2Datacenter": {
            "publisher": "MicrosoftWindowsServer",
            "offer": "WindowsServer",
            "sku": "2012-R2-Datacenter",
            "version": "latest",
            "architecture": "x64"
          },
          "Win2012Datacenter": {
            "publisher": "MicrosoftWindowsServer",
            "offer": "WindowsServer",
            "sku": "2012-Datacenter",
            "version": "latest",
            "architecture": "x64"
          }
        }
      }
    }
  }
}
"""
