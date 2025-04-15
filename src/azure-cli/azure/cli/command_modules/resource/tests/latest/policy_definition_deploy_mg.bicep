targetScope = 'managementGroup'

resource policyDef 'Microsoft.Authorization/policyDefinitions@2018-05-01' = {
  name: 'policy-for-bicep-test'
  properties: {
    policyType: 'Custom'
    policyRule: {
      if: {
        field: 'location'
        equals: 'westus2'
      }
      then: {
        effect: 'deny'
      }
    }
  }
}
