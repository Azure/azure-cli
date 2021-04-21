## AZ

These settings apply only when `--az` is specified on the command line.

``` yaml $(az) && $(cloudservice)
tag: package-2020-10-01-preview-only
az:
  extensions: cloud-service
  namespace: azure.mgmt.compute
  package-name: azure-mgmt-compute
az-output-folder: $(azure-cli-extension-folder)/src/cloudservice
python-sdk-output-folder: $(az-output-folder)/azext_cloudservice/vendored_sdks/cloudservice
cli:
    cli-directive:
        - where:
            group: "*"
            op: "*"
          hidden: true
        - where:
            group: "CloudServiceRoleInstances"
            op: "*"
          hidden: false
        - where:
            group: "CloudServiceRoles"
            op: "*"
          hidden: false
        - where:
            group: "CloudServices"
            op: "*"
          hidden: false
        - where:
            group: "CloudServicesUpdateDomain"
            op: "*"
          hidden: false
directive:
  - where:
      group: cloud-service cloud-service-role-instance
    set:
      group: cloud-service role-instance
  - where:
      group: cloud-service cloud-service-role
    set:
      group: cloud-service role
  - where:
      group: cloud-service cloud-service-update-domain
    set:
      group: cloud-service update-domain
```

``` yaml $(az) && $(target-mode) == "core"
tag: package-2020-12-01-only
az:
  extensions: vm
  namespace: azure.mgmt.compute
  package-name: azure-mgmt-compute
az-output-folder: $(azure-cli-folder)/src/azure-cli/azure/cli/command_modules/vm
python-sdk-output-folder: "$(az-output-folder)/vendored_sdks/vm"
extension-mode: stable
compatible-level: track2
cli:
    cli-directive:
        - where:
            group: "*"
            op: "*"
          hidden: true
        - where:
            group: "SshPublicKeys"
            op: "*"
          hidden: false
        - where:
            group: "SshPublicKeys"
            op: "GenerateKeyPair"
          hidden: true
        - where:
            group: "*"
            op: "*"
            param: vmName
          alias: name
directive: 
  - where: 
      group: vm ssh-public-key
    set:
      group: sshkey
  - where:
      group: ^vm virtual-machine-scale-set$
    set:
      group: vmss
  - where:
      group: vm virtual-machine-scale-set-vm-extension
    set:
      group: vmss vm-extension
  - where:
      group: vm virtual-machine-scale-set-v-ms
    set:
      group: vmss v-ms
  - where:
      group: vm virtual-machine-scale-set-vm-run-command
    set:
      group: vmss vm-run
  - where:
      group: ^vm virtual-machine$
    set:
      group: vm
```


### -----start of auto generated cli-directive----- ###
``` yaml $(az) && $(target-mode) == "core"
cli:
  cli-directive:
    - where:
        group: 'DiskAccesses'
        op: ListPrivateEndpointConnections|DeleteAPrivateEndpointConnection
        apiVersion: '2020-09-30'
      hidden: false
    - where:
        group: 'DiskAccesses'
        op: GetPrivateLinkResources
        apiVersion: '2020-05-01'
      hidden: false
    - where:
        group: 'DiskRestorePoint'
        op: Get
        apiVersion: '2020-12-01'
      hidden: false
    - where:
        group: 'VirtualMachines'
        op: InstallPatches
        apiVersion: '2020-12-01'
      hidden: false
    - where:
        group: 'VirtualMachines'
        op: Reimage
        apiVersion: '2018-06-01'
      hidden: false
    - where:
        group: 'VirtualMachineScaleSets'
        op: ConvertToSinglePlacementGroup
        apiVersion: '2020-12-01'
      hidden: false
    - where:
        group: 'VirtualMachineScaleSets'
        op: ForceRecoveryServiceFabricPlatformUpdateDomainWalk|ReimageAll
        apiVersion: '2018-10-01'
      hidden: false
    - where:
        group: 'VirtualMachineScaleSets'
        op: Redeploy
        apiVersion: '2019-12-01'
      hidden: false
    - where:
        group: 'VirtualMachineScaleSetVMExtensions'
        op: List|Get|CreateOrUpdate
        apiVersion: '2019-07-01'
      hidden: false
    - where:
        group: 'VirtualMachineScaleSetVMs'
        op: Redeploy
        apiVersion: '2019-03-01'
      hidden: false
    - where:
        group: 'VirtualMachineScaleSetVMs'
        op: ReimageAll
        apiVersion: '2018-04-01'
      hidden: false
    - where:
        group: 'VirtualMachineScaleSetVMs'
        op: RetrieveBootDiagnosticsData
        apiVersion: '2020-06-01'
      hidden: false
    - where:
        group: 'VirtualMachineScaleSetVMRunCommands'
        op: List
        apiVersion: '2020-12-01'
      hidden: false
    - where:
        group: 'ContainerServices'
        op: CreateOrUpdate
        apiVersion: '2016-09-30'
      hidden: false
```
### -----end of auto generated cli-directive----- ###
