targetScope = 'tenant'

resource roleDef 'Microsoft.Authorization/roleDefinitions@2018-01-01-preview' = {
  name: '0cb07228-4614-4814-ac1a-c4e39793ce58'
  properties: {
    roleName: 'Test Role'
    type: 'CustomRole'
    permissions: [
      {
        'actions': [
          'Microsoft.Storage/*/read'
        ]
        'notActions': []
      }
    ]
    assignableScopes: [
      '/providers/Microsoft.Management/managementGroups/cli_tenant_level_deployment_mg'
    ]
  }
}
