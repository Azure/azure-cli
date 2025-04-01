# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

helps['edge'] = """
type: group
short-summary: Manage Azure Edge services and operations for edge computing scenarios.
"""

# Remove the duplicate entry and improve the remaining one
helps['edge disconnected-operation'] = """
type: group
short-summary: Manage Azure Edge Marketplace services for disconnected (offline) environments.
long-summary: Enables downloading and packaging of marketplace offerings for deployment in environments with limited or no internet connectivity.
"""

helps['edge disconnected-operation offer'] = """
type: group
short-summary: Manage marketplace offers for disconnected Edge environments.
long-summary: View, download, and package marketplace VM images and solutions for deployment to disconnected edge environments.
"""

helps['edge disconnected-operation offer list'] = """
type: command
short-summary: List all available marketplace offers for disconnected operations.
long-summary: Retrieves a list of all VM images and solutions available in the marketplace that can be packaged for disconnected environments, including publisher, offer, SKU, and version information.
examples:
  - name: List all marketplace offers for a specific resource
    text: >
      az edge disconnected-operation offer list --resource-group myResourceGroup --resource-name myResource
  - name: List offers and format output as table
    text: >
      az edge disconnected-operation offer list -g myResourceGroup --resource-name myResource --output table
  - name: List offers and filter output using JMESPath query
    text: >
      az edge disconnected-operation offer list -g myResourceGroup --resource-name myResource --query "[?OS_Type=='Linux']"
parameters:
  - name: --resource-group -g
    type: string
    short-summary: Name of resource group containing the disconnected operations resource
  - name: --resource-name
    type: string
    short-summary: Name of the disconnected operations resource
"""

helps['edge disconnected-operation offer get'] = """
type: command
short-summary: Get detailed information about a specific marketplace offer.
long-summary: Retrieves comprehensive details for a marketplace offer, including available SKUs, versions, OS type, and size information to help with disconnected environment planning.
examples:
  - name: Get details of a specific marketplace offer
    text: >
      az edge disconnected-operation offer get --resource-group myResourceGroup --resource-name myResource --publisher-name publisherName --offer-id offerName
  - name: Get offer details and output as JSON
    text: >
      az edge disconnected-operation offer get -g myResourceGroup --resource-name myResource --publisher-name publisherName --offer-id offerName --output json
  - name: Get offer details with custom query
    text: >
      az edge disconnected-operation offer get -g myResourceGroup --resource-name myResource --publisher-name publisherName --offer-id offerName --query "[].{SKU:SKU,Version:Versions}"
parameters:
  - name: --resource-group -g
    type: string
    short-summary: Name of resource group containing the disconnected operations resource
  - name: --resource-name
    type: string
    short-summary: Name of the disconnected operations resource
  - name: --publisher-name
    type: string
    short-summary: Publisher name of the marketplace offer (e.g., 'MicrosoftWindowsServer')
  - name: --offer-id
    type: string
    short-summary: Offer identifier in the marketplace (e.g., 'WindowsServer')
"""

helps['edge disconnected-operation offer package'] = """
type: command
short-summary: Download and package a marketplace VM image with its metadata for offline use.
long-summary: Creates a complete package containing the VM image (VHD), metadata, and icons for deployment in disconnected environments. The package can be transported to an air-gapped environment and used for VM deployment without internet connectivity.
examples:
  - name: Package a marketplace offer with specific version
    text: >
      az edge disconnected-operation offer package --resource-group myResourceGroup --resource-name myResource --publisher-name publisherName --offer-id offerName --sku skuName --version versionNumber --output-folder "D:\\MarketplacePackages"
  - name: Package a marketplace offer with specific region
    text: >
      az edge disconnected-operation offer package --resource-group myResourceGroup --resource-name myResource --publisher-name publisherName --offer-id offerName --sku skuName --version versionNumber --output-folder "D:\\MarketplacePackages" --region eastus
parameters:
  - name: --resource-group -g
    type: string
    short-summary: Name of resource group containing the disconnected operations resource
  - name: --resource-name
    type: string
    short-summary: Name of the disconnected operations resource
  - name: --publisher-name
    type: string
    short-summary: Publisher name of the marketplace offer (e.g., 'MicrosoftWindowsServer')
  - name: --offer-id
    type: string
    short-summary: Offer identifier in the marketplace (e.g., 'WindowsServer')
  - name: --sku
    type: string
    short-summary: SKU identifier for the specific offer variant (e.g., '2019-Datacenter')
  - name: --version
    type: string
    short-summary: Version of the marketplace offer to download (e.g., '17763.3287.2210110541')
  - name: --output-folder
    type: string
    short-summary: Local folder path where the package contents will be downloaded and organized
  - name: --region
    type: string
    short-summary: Azure region to use for marketplace access (e.g., 'eastus', 'westeurope')
"""