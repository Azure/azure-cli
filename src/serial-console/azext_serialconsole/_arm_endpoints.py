# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


class ArmEndpoints:  # pylint: disable=too-few-public-methods
    region_prefix_pairings = {'australiacentral': 'australiaeast',
                              'australiaeast': 'australiacentral',
                              'brazilsouth': 'brazilsoutheast',
                              'brazilsoutheast': 'brazilsouth',
                              'canadacentral': 'canadaeast',
                              'canadaeast': 'canadacentral',
                              'centralindia': 'southindia',
                              'centralus': 'westcentralus',
                              'centraluseuap': 'eastus2euap',
                              'eastasia': 'southeastasia',
                              'eastus': 'westus',
                              'eastus2': 'westus2',  # pairing eastus2 + westus2 ensure that INT works as expected
                              'eastus2euap': 'centraluseuap',
                              'francecentral': 'francesouth',
                              'francesouth': 'francecentral',
                              'germanynorth': 'germanywestcentral',
                              'germanywestcentral': 'germanynorth',
                              'japaneast': 'japanwest',
                              'japanwest': 'japaneast',
                              'koreacentral': 'koreasouth',
                              'koreasouth': 'koreacentral',
                              'northeurope': 'westeurope',
                              'norwayeast': 'norwaywest',
                              'norwaywest': 'norwayeast',
                              # 'southafricanorth': 'southafricawest' is not yet deployed
                              'southeastasia': 'eastasia',
                              'southindia': 'centralindia',
                              'swedencentral': 'swedensouth',
                              'swedensouth': 'swedencentral',
                              'switzerlandnorth': 'switzerlandwest',
                              'switzerlandwest': 'switzerlandnorth',
                              'uaecentral': 'uaenorth',
                              'uaenorth': 'uaecentral',
                              'uksouth': 'ukwest',
                              'ukwest': 'uksouth',
                              'westcentralus': 'centralus',
                              'westeurope': 'northeurope',
                              'westus': 'eastus',
                              'westus2': 'eastus2',
                              'usgovarizona': 'usgoveast',  # usgoveast == usgovvirginia
                              'usgovvirginia': 'usgovsw',  # usgovsw == usgovarizona
                              }
