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
          long-summary: Uses brazilus.management.azure.com for test environment, management.azure.com for production.
          default: management.azure.com
        - name: --provider-namespace
          type: string
          short-summary: Provider namespace.
          long-summary: Use "Private.EdgeInternal" for test environment or "Microsoft.Edge" for production.
          default: Microsoft.Edge
        - name: --sub-provider
          type: string
          short-summary: Sub-provider namespace.
          default: Microsoft.EdgeMarketPlace
        - name: --api-version
          type: string
          short-summary: API version to use.
          default: 2023-08-01-preview
    examples:
        - name: List offers using production environment
          text: az disconnectedoperations edgemarketplace listoffers -g myResourceGroup
        - name: List offers using test environment
          text: az disconnectedoperations edgemarketplace listoffers -g myResourceGroup --provider-namespace Private.EdgeInternal
        - name: List offers in table format
          text: az disconnectedoperations edgemarketplace listoffers -g myResourceGroup --output table
"""

helps['disconnectedoperations edgemarketplace get-offer'] = """
    type: command
    short-summary: Get details of a specific marketplace offer.
    long-summary: Retrieve detailed information about a marketplace offer and optionally download its logos.
    parameters:
        - name: --resource-group -g
          type: string
          required: true
          short-summary: Name of resource group.
        - name: --offer-name
          type: string
          required: true
          short-summary: Name of the offer to retrieve.
        - name: --output-folder
          type: string
          short-summary: Local folder path to save logos and metadata.
        - name: --management-endpoint
          type: string
          short-summary: Management endpoint URL.
          long-summary: Uses brazilus.management.azure.com for test environment, management.azure.com for production.
          default: management.azure.com
        - name: --provider-namespace
          type: string
          short-summary: Provider namespace.
          long-summary: Use "Private.EdgeInternal" for test environment or "Microsoft.Edge" for production.
          default: Microsoft.Edge
        - name: --sub-provider
          type: string
          short-summary: Sub-provider namespace.
          default: Microsoft.EdgeMarketPlace
        - name: --api-version
          type: string
          short-summary: API version to use.
          default: 2023-08-01-preview
    examples:
        - name: Get offer details using production environment
          text: az disconnectedoperations edgemarketplace get-offer -g myResourceGroup --offer-name myOffer
        - name: Get offer details and save logos using test environment
          text: az disconnectedoperations edgemarketplace get-offer -g myResourceGroup --offer-name myOffer --output-folder ./artifacts --provider-namespace Private.EdgeInternal
"""

helps['disconnectedoperations edgemarketplace get-image-download-url'] = """
    type: command
    short-summary: Get download URL for a marketplace image.
    long-summary: Get the download URL for a specific marketplace image version.
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
          short-summary: SKU identifier.
        - name: --version
          type: string
          required: true
          short-summary: Version of the marketplace image.
        - name: --management-endpoint
          type: string
          short-summary: Management endpoint URL.
          long-summary: Uses brazilus.management.azure.com for test environment, management.azure.com for production.
          default: management.azure.com
        - name: --provider-namespace
          type: string
          short-summary: Provider namespace.
          long-summary: Use "Private.EdgeInternal" for test environment or "Microsoft.Edge" for production.
          default: Microsoft.Edge
        - name: --api-version
          type: string
          short-summary: API version to use.
          default: 2024-11-01-preview
    examples:
        - name: Get image download URL using production environment
          text: az disconnectedoperations edgemarketplace get-image-download-url -g myResourceGroup --publisher MicrosoftWindowsServer --offer WindowsServer --sku 2019-Datacenter --version latest
        - name: Get image download URL using test environment
          text: az disconnectedoperations edgemarketplace get-image-download-url -g myResourceGroup --publisher MicrosoftWindowsServer --offer WindowsServer --sku 2019-Datacenter --version latest --provider-namespace Private.EdgeInternal
"""