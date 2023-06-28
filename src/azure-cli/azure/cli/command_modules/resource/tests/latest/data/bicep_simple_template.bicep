param location string = 'centralus'

@minLength(3)
@maxLength(24)
param storageAccountName string = 'uniquestorage001' // must be globally unique

resource stg 'Providers.Test/statefulResources@2014-04-01' = {
    name: storageAccountName
    location: location
}

output storageId string = stg.id // output resourceId of storage account
