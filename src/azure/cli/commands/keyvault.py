from ..commands._auto_command import LongRunningOperation
from ..commands import command, description, option
from ._command_creation import get_mgmt_service_client
from .._locale import L

@command('keyvault create')
@description(L('Create or update a Key Vault'))
@option('--resource-group -g <resourceGroup>', L('the resource group name'), required=True)
@option('--name -n <keyVaultName>', L('the Key Vault name'), required=True)
@option('--location -l <location>', L('the Key Vault location'), required=True)
@option('--tenantId -t <tenantId>', L('the Key Vault tenant'), required=True)
@option('--objectId -o <objectId>',
        L('user object ID, AD user or Service Principal'),
        required=True)
@option('--keysPermissions -kp <value>',
        L('values: all | create | import | update | get | list | delete | backup '
          '| restore | encrypt | decrypt | wrapkey | unwrapkey | sign | verify, default: all'))
@option('--secretsPermissions -sp <value>', L('values: all | get | set | list | delete, '
                                              'default: all'))
@option('--skuName <value>', L('values: standard | premium, default: standard'))
@option('--enableVaultForDeployment -ed', L('enable VM deployment'))
@option('--enableVaultForDiskEncryption -ee', L('enable disk encryption'))
@option('--enabledForTemplateDeployment -et', L('enable template deployment'))
def create_update_keyvault(args, unexpected): #pylint: disable=unused-argument
    from azure.mgmt.resource.resources import (ResourceManagementClientConfiguration,
                                               ResourceManagementClient)
    from azure.mgmt.resource.resources.models import DeploymentProperties, ParametersLink

    parameters = {
        'location': {'value': args.get('location')},
        'tenantId': {'value': args.get('tenantId')},
        'objectId': {'value': args.get('objectId')},
        'keyVaultName': {'value': args.get('name')},
        'keysPermissions': {'value': [args.get('keysPermissions')
                                      if args.get('keysPermissions')
                                      else 'All']},
        'secretsPermissions': {'value': [args.get('secretsPermissions')
                                         if args.get('secretsPermissions')
                                         else 'All']},
        'skuName': {'value': args.get('skuName') if args.get('skuName') else 'Standard'},
        'enableVaultForDeployment': {'value': bool(args.get('enableVaultForDeployment'))},
        'enableVaultForDiskEncryption': {'value': bool(args.get('enableVaultForDiskEncryption'))},
        'enabledForTemplateDeployment': {'value': bool(args.get('enabledForTemplateDeployment'))},
        }

    template_url = ('https://raw.githubusercontent.com/azure/azure-quickstart-templates/'
                    'master/101-key-vault-create/azuredeploy.json')
    properties = DeploymentProperties(template_link=ParametersLink(template_url),
                                      parameters=parameters,
                                      mode='Complete')

    op = LongRunningOperation('Creating Key Vault', 'Key Vault created')
    smc = get_mgmt_service_client(ResourceManagementClient, ResourceManagementClientConfiguration)
    poller = smc.deployments.create_or_update(args.get('resource-group'),
                                              '{}_deployment'.format(args.get('resource-group')),
                                              properties)
    return op(poller)
