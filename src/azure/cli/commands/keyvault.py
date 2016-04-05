from ..commands._auto_command import LongRunningOperation
from ..commands import command, description, option
from ._command_creation import get_mgmt_service_client
from .._locale import L

@command('keyvault create')
@description(L('Create or update a Key Vault'))
@option('--resource-group -g <resourceGroup>', L('the resource group name'), required=True)
@option('--name -n <keyVaultName>', L('the Key Vault name'), required=True)
@option('--location -l <location>', L('the Key Vault location'), required=True)
@option('--tenant-id -t <tenantId>', L('the Key Vault tenant'), required=True)
@option('--object-id -o <objectId>',
        L('user object ID from an AD user or Service Principal'),
        required=True)
@option('--keys-permissions -kp <value>',
        L('values (quoted, space-seperated): all | create | import | update | get | list | delete'
          ' | backup | restore | encrypt | decrypt | wrapkey | unwrapkey | sign | verify, '
          'default: all'))
@option('--secrets-permissions -sp <value>', L('values (quoted, space-seperated): all | get | set'
                                               ' | list | delete, default: all'))
@option('--sku-name <value>', L('values: standard | premium, default: standard'))
@option('--enable-vault-for-deployment -ed', L('enable VM deployment'))
@option('--enable-vault-for-disk-encryption -ee', L('enable disk encryption'))
@option('--enabled-for-template-deployment -et', L('enable template deployment'))
@option('--deployment-mode -dp <value>', L('values: Complete | Incremental, default: Incremental'))
def create_update_keyvault(args, unexpected): #pylint: disable=unused-argument
    from azure.mgmt.resource.resources import (ResourceManagementClientConfiguration,
                                               ResourceManagementClient)
    from azure.mgmt.resource.resources.models import DeploymentProperties, ParametersLink

    parameters = {
        'location': {'value': args.get('location')},
        'tenantId': {'value': args.get('tenant-id')},
        'objectId': {'value': args.get('object-id')},
        'keyVaultName': {'value': args.get('name')},
        }

    if 'keys-permissions' in args:
        parameters['keysPermissions'] = {'value': args['keys-permissions'].split()}

    if 'secrets-permissions' in args:
        parameters['secretsPermissions'] = {'value': args['secrets-permissions'].split()}

    if 'sku-name' in args:
        parameters['skuName'] = {'value': args['sku-name']}

    if 'enable-vault-for-deployment' in args:
        parameters['enableVaultForDeployment'] = {'value': args['enable-vault-for-deployment']}

    if 'enable-vault-for-disk-encryption' in args:
        parameters['enableVaultForDiskEncryption'] = {'value':
                                                      args['enable-vault-for-disk-encryption']}

    if 'enabled-for-template-deployment' in args:
        parameters['enabledForTemplateDeployment'] = {'value':
                                                      args['enabled-for-template-deployment']}

    template_url = ('https://raw.githubusercontent.com/azure/azure-quickstart-templates/'
                    'master/101-key-vault-create/azuredeploy.json')

    properties = DeploymentProperties(template_link=ParametersLink(template_url),
                                      parameters=parameters,
                                      mode=args.get('deployment-mode', 'Incremental'))

    op = LongRunningOperation('Creating Key Vault', 'Key Vault created')
    smc = get_mgmt_service_client(ResourceManagementClient, ResourceManagementClientConfiguration)
    poller = smc.deployments.create_or_update(args.get('resource-group'),
                                              '{}_deployment'.format(args.get('resource-group')),
                                              properties)
    return op(poller)
