## AZ

These settings apply only when `--az` is specified on the command line.

``` yaml $(az) && $(target-mode) == "core"
az:
  extensions: vm
  namespace: azure.mgmt.compute
  package-name: azure-mgmt-compute
az-output-folder: $(azure-cli-folder)/src/azure-cli/azure/cli/command_modules/vm
python-sdk-output-folder: "$(az-output-folder)/vendored_sdks/vm"
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
directive: 
  - where: 
      command: vm ssh-public-key
    set:
      command: sshkey
```

### -----start of auto generated cli-directive----- ###
``` yaml $(az)
cli:
  cli-directive:
    - where:
        group: '*'
        op: '*'
      hidden: true
    - where:
        group: 'CloudServices'
        op: ListAll|List|Delete|Get|CreateOrUpdate|GetInstanceView|PowerOff|Restart|Start
        apiVersion: '2020-10-01-preview'
      hidden: false
    - where:
        group: 'CloudServiceRoleInstances'
        op: List|Get|GetInstanceView|Reimage|GetRemoteDesktopFile|Restart
        apiVersion: '2020-10-01-preview'
      hidden: false
    - where:
        group: 'CloudServiceRoles'
        op: List|Get
        apiVersion: '2020-10-01-preview'
      hidden: false
    - where:
        group: 'CloudServicesUpdateDomain'
        op: ListUpdateDomains
        apiVersion: '2020-10-01-preview'
      hidden: false
    - where:
        group: 'DiskAccesses'
        op: DeleteAPrivateEndpointConnection
        apiVersion: '2020-09-30'
      hidden: false
    - where:
        group: 'DiskAccesses'
        op: GetPrivateLinkResources
        apiVersion: '2020-05-01'
      hidden: false
    - where:
        group: 'GalleryApplications'
        op: ListByGallery|Delete|CreateOrUpdate
        apiVersion: '2019-03-01'
      hidden: false
    - where:
        group: 'GalleryApplications'
        op: Get
        apiVersion: '2019-07-01'
      hidden: false
    - where:
        group: 'GalleryApplicationVersions'
        op: ListByGalleryApplication
        apiVersion: '2019-03-01'
      hidden: false
    - where:
        group: 'SshPublicKeys'
        op: Delete
        apiVersion: '2019-12-01'
      hidden: false
    - where:
        group: 'VirtualMachines'
        op: Reimage
        apiVersion: '2019-07-01'
      hidden: false
    - where:
        group: 'VirtualMachineScaleSets'
        op: ForceRecoveryServiceFabricPlatformUpdateDomainWalk|ReimageAll
        apiVersion: '2018-10-01'
      hidden: false
    - where:
        group: 'VirtualMachineScaleSets'
        op: Redeploy
        apiVersion: '2020-06-01'
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