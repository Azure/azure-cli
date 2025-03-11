# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

helps['disconnectedoperations'] = """
type: group
short-summary: Manage disconnected operations.
"""

helps['disconnectedoperations edge-marketplace'] = """
type: group
short-summary: Manage Edge Marketplace for disconnected operations.
"""

helps['disconnectedoperations edge-marketplace offer'] = """
type: group
short-summary: Manage Edge Marketplace offers for disconnected operations.
"""

helps['disconnectedoperations edge-marketplace offer list'] = """
type: command
short-summary: List all available marketplace offers.
examples:
  - name: List all marketplace offers for a specific resource
    text: >
      az disconnectedoperations edge-marketplace offer list --resource-group myResourceGroup --resource-name myResource
  - name: List offers and format output as table
    text: >
      az disconnectedoperations edge-marketplace offer list -g myResourceGroup --resource-name myResource --output table
  - name: List offers and filter output using JMESPath query
    text: >
      az disconnectedoperations edge-marketplace offer list -g myResourceGroup --resource-name myResource --query "[?OS_Type=='Linux']"
parameters:
  - name: --resource-group -g
    type: string
    short-summary: Name of resource group
  - name: --resource-name
    type: string
    short-summary: The resource name
"""

helps['disconnectedoperations edge-marketplace offer get'] = """
type: command
short-summary: Get details of a specific marketplace offer.
examples:
  - name: Get details of a specific marketplace offer
    text: >
      az disconnectedoperations edge-marketplace offer get --resource-group myResourceGroup --resource-name myResource --publisher-name publisherName --offer-name offerName
  - name: Get offer details and output as JSON
    text: >
      az disconnectedoperations edge-marketplace offer get -g myResourceGroup --resource-name myResource --publisher-name publisherName --offer-name offerName --output json
  - name: Get offer details with custom query
    text: >
      az disconnectedoperations edge-marketplace offer get -g myResourceGroup --resource-name myResource --publisher-name publisherName --offer-name offerName --query "[].{SKU:SKU,Version:Versions}"
parameters:
  - name: --resource-group -g
    type: string
    short-summary: Name of resource group
  - name: --resource-name
    type: string
    short-summary: The resource name
  - name: --publisher-name
    type: string
    short-summary: The publisher name of the offer
  - name: --offer-name
    type: string
    short-summary: The name of the offer
"""

helps['disconnectedoperations edge-marketplace offer package'] = """
type: command
short-summary: Download and package a marketplace offer with its metadata and icons.
long-summary: Downloads the marketplace offer metadata, icons, and creates a package in the specified output folder.
examples:
  - name: Package a marketplace offer with specific version
    text: >
      az disconnectedoperations edge-marketplace offer package --resource-group myResourceGroup --resource-name myResource --publisher-name publisherName --offer-name offerName --sku skuName --version versionNumber --output-folder "D:\\MarketplacePackages"
parameters:
  - name: --resource-group -g
    type: string
    short-summary: Name of resource group
  - name: --resource-name
    type: string
    short-summary: The resource name
  - name: --publisher-name
    type: string
    short-summary: The publisher name of the offer
  - name: --offer-name
    type: string
    short-summary: The name of the offer
  - name: --sku
    type: string
    short-summary: The SKU of the offer
  - name: --version
    type: string
    short-summary: The version of the offer (optional, latest version will be used if not specified)
  - name: --output-folder
    type: string
    short-summary: The folder path where the package will be downloaded
"""
