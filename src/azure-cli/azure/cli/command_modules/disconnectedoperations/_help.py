from knack.help_files import helps

helps['disconnectedoperations'] = """
    type: group
    short-summary: Commands to manage Azure Disconnected Operations.
    long-summary: Manage Azure Disconnected Operations for Edge marketplace offers.
"""

helps['disconnectedoperations edgemarketplace'] = """
    type: group
    short-summary: Manage Edge marketplace offers for disconnected operations.
    long-summary: Commands to list, get details, and package Edge marketplace offers for disconnected operations.
"""

helps['disconnectedoperations edgemarketplace listoffers'] = """
    type: command
    short-summary: List all available Edge marketplace offers.
    long-summary: List all available Edge marketplace offers with their publishers, SKUs, and versions.
    examples:
        - name: List all offers in a resource group
          text: az disconnectedoperations edgemarketplace listoffers -g myResourceGroup
"""

helps['disconnectedoperations edgemarketplace packageoffer'] = """
    type: command
    short-summary: Package an Edge marketplace offer for disconnected operations.
    long-summary: Download and package an Edge marketplace offer including its metadata, logos, and other artifacts.
    parameters:
        - name: --resource-group -g
          type: string
          short-summary: Name of resource group.
          required: true
        - name: --publisher-name
          type: string
          short-summary: Name of the publisher.
          required: true
        - name: --offer-name
          type: string
          short-summary: Name of the offer.
          required: true
        - name: --sku
          type: string
          short-summary: SKU of the offer.
        - name: --version
          type: string
          short-summary: Version of the offer. If not specified, latest version will be used.
        - name: --output-folder
          type: string
          short-summary: Output folder path for downloaded artifacts.
          required: true
    examples:
        - name: Package latest version of an offer
          text: az disconnectedoperations edgemarketplace packageoffer -g myResourceGroup --publisher-name publisherName --offer-name offerName --output-folder ./output
        - name: Package specific version of an offer
          text: az disconnectedoperations edgemarketplace packageoffer -g myResourceGroup --publisher-name publisherName --offer-name offerName --version 1.0.0 --output-folder ./output
"""