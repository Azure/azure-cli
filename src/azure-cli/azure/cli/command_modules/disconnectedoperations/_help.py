from knack.help_files import helps  # pylint: disable=unused-import

helps['disconnectedoperations'] = """
    type: group
    short-summary: Commands to manage disconnected operations.
    long-summary: Manage Azure Edge marketplace operations in disconnected environments.
"""

helps['disconnectedoperations edgemarketplace'] = """
    type: group
    short-summary: Manage Edge Marketplace operations.
    long-summary: Commands to manage Edge Marketplace images and offers.
"""

helps['disconnectedoperations edgemarketplace listoffers'] = """
    type: command
    short-summary: List available marketplace offers.
    long-summary: List all available marketplace offers with their SKUs and versions.
    parameters:
        - name: --resource-group -g
          type: string
          required: true
          short-summary: Name of resource group.
        - name: --management-endpoint
          type: string
          short-summary: Management endpoint URL.
          default: brazilus.management.azure.com
        - name: --provider-namespace
          type: string
          short-summary: Provider namespace.
          default: Private.EdgeInternal
        - name: --api-version
          type: string
          short-summary: API version to use.
          default: 2023-08-01-preview
    examples:
        - name: List offers in default format
          text: az disconnectedoperations edgemarketplace listoffers -g myResourceGroup
        - name: List offers in table format
          text: az disconnectedoperations edgemarketplace listoffers -g myResourceGroup --output table
        - name: List offers with custom endpoint
          text: az disconnectedoperations edgemarketplace listoffers -g myResourceGroup --management-endpoint customendpoint.azure.com
"""

helps['disconnectedoperations edgemarketplace packageimage'] = """
    type: command
    short-summary: Package a marketplace image.
    long-summary: Download and package a marketplace image for use in disconnected environments.
    parameters:
        - name: --resource-group -g
          type: string
          required: true
          short-summary: Name of resource group.
        - name: --publisher
          type: string
          required: true
          short-summary: Publisher of the marketplace image.
        - name: --offer
          type: string
          required: true
          short-summary: Offer name of the marketplace image.
        - name: --sku
          type: string
          required: true
          short-summary: SKU of the marketplace image.
        - name: --location -l
          type: string
          required: true
          short-summary: Location for the packaged image.
    examples:
        - name: Package a Windows Server image
          text: az disconnectedoperations edgemarketplace packageimage -g myResourceGroup --publisher MicrosoftWindowsServer --offer WindowsServer --sku 2019-Datacenter --location eastus
"""