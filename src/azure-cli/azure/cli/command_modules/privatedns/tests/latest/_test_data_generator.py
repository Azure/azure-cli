# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
regexSubscription = '[0-9a-f]{{8}}-[0-9a-f]{{4}}-[0-9a-f]{{4}}-[0-9a-f]{{4}}-[0-9a-f]{{12}}'


def GeneratePrivateZoneName(self):
    self.kwargs['zone'] = self.create_random_name("clitest.privatedns.com", length=35)


def GenerateVirtualNetworkName(self):
    self.kwargs['vnet'] = self.create_random_name("clitestprivatednsvnet", length=35)


def GenerateVirtualNetworkLinkName(self):
    self.kwargs['link'] = self.create_random_name("clitestprivatednslink", length=35)


def GenerateRecordSetName(self):
    self.kwargs['recordset'] = self.create_random_name("clitestprivatednsrecordset", length=35)


def GeneratePrivateZoneArmId(self):
    return "/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.Network/privateDnsZones/{2}".format(
        regexSubscription, self.kwargs['rg'], self.kwargs['zone'])


def GenerateVirtualNetworkLinkArmId(self):
    return "/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.Network/privateDnsZones/{2}/virtualNetworkLinks/{3}".format(
        regexSubscription, self.kwargs['rg'], self.kwargs['zone'], self.kwargs['link'])


def GenerateVirtualNetworkArmId(self):
    return "/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.Network/virtualNetworks/{2}".format(
        regexSubscription, self.kwargs['rg'], self.kwargs['vnet'])


def GenerateRecordSetArmId(self):
    return "/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.Network/privateDnsZones/{2}/{3}/{4}".format(
        regexSubscription, self.kwargs['rg'], self.kwargs['zone'], self.kwargs['recordType'], self.kwargs['recordset'])


def GenerateTags(self):
    tagKey = self.create_random_name("tagKey", length=15)
    tagVal = self.create_random_name("tagVal", length=15)
    self.kwargs['tags'] = "{0}={1}".format(tagKey, tagVal)
    return tagKey, tagVal
