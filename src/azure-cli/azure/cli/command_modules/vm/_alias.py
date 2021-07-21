# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# Alias for image
# https://github.com/Azure/azure-rest-api-specs/blob/master/arm-compute/quickstart-templates/aliases.json

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
          "CentOS": {
            "publisher": "OpenLogic",
            "offer": "CentOS",
            "sku": "7.5",
            "version": "latest"
          },
          "Debian": {
            "publisher": "Debian",
            "offer": "debian-10",
            "sku": "10",
            "version": "latest"
          },
          "Flatcar": {
            "publisher": "kinvolk",
            "offer": "flatcar-container-linux-free",
            "sku": "stable",
            "version": "latest"
          },
          "openSUSE-Leap": {
            "publisher": "SUSE",
            "offer": "openSUSE-Leap",
            "sku": "42.3",
            "version": "latest"
          },
          "RHEL": {
            "publisher": "RedHat",
            "offer": "RHEL",
            "sku": "7-LVM",
            "version": "latest"
          },
          "SLES": {
            "publisher": "SUSE",
            "offer": "SLES",
            "sku": "15",
            "version": "latest"
          },
          "UbuntuLTS": {
            "publisher": "Canonical",
            "offer": "UbuntuServer",
            "sku": "18.04-LTS",
            "version": "latest"
          }
        },
        "Windows": {
          "Win2019Datacenter": {
            "publisher": "MicrosoftWindowsServer",
            "offer": "WindowsServer",
            "sku": "2019-Datacenter",
            "version": "latest"
          },
          "Win2016Datacenter": {
            "publisher": "MicrosoftWindowsServer",
            "offer": "WindowsServer",
            "sku": "2016-Datacenter",
            "version": "latest"
          },
          "Win2012R2Datacenter": {
            "publisher": "MicrosoftWindowsServer",
            "offer": "WindowsServer",
            "sku": "2012-R2-Datacenter",
            "version": "latest"
          },
          "Win2012Datacenter": {
            "publisher": "MicrosoftWindowsServer",
            "offer": "WindowsServer",
            "sku": "2012-Datacenter",
            "version": "latest"
          },
          "Win2008R2SP1": {
            "publisher": "MicrosoftWindowsServer",
            "offer": "WindowsServer",
            "sku": "2008-R2-SP1",
            "version": "latest"
          }
        }
      }
    }
  }
}

"""
