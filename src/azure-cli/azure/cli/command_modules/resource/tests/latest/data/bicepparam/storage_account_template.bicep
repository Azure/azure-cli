var storageAccountName = 'store${uniqueString(resourceGroup().id)}'

param location string

param kind string

resource sa 'Microsoft.Storage/storageAccounts@2019-04-01' = {
  name: storageAccountName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: kind
  properties: {}
}
