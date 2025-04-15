# VMSS Create scenarios before merge #

## P0: BASIC ##
Execute P0s before any change to VMSS Create **OR VM CREATE** is merged

**simple Windows VMSS**

 - create
 - verify LB and public IP

OR

 - Delete test_vm_scaleset_create_simple.yaml
 - Re-record the tests

**Windows VMSS with no overprovisioning, instance count 4, ReadWrite caching and Automatic upgrades, static private and static Public IP Addresses**

 - create
 - verify LB public/private IP is static
 - verify overprovisioning, instance count (capacity), caching and upgrade policy

 OR

 - Delete test_vm_scaleset_create_options.yaml
 - Re-record tests

**Linux VMSS with custom OS Disk name and storage container name, existing VNet/subnet, existing IP for LB**

 - verify existing IP is used by LB
 - verify OS Disk name
 - verify in correct VNet/Subnet
 - verify existing IP used

OR

 - Delete test_vm_scaleset_create_existing_options.yaml
 - Re-record tests

 **Minimum VMSS**

 - create vmss with no load balancer, public ip or tags
 - verify create succeeds and that the other resources aren't created

 OR

 - delete test_vmss_create_none_options.yaml
 - re-record test

**custom Linux image**

 - create VM1, add a customization such as "sudo apt-get install emacs23"
 - generalize, capture and deallocate VM1's vhd (https://azure.microsoft.com/documentation/articles/virtual-machines-linux-capture-image/)
 - create VMSS with OS Disk URI pointing to VM1's vhd. Create in a different resource group than
   the storage account the VHD is in.
 - SSH into instance 1
 - verify emacs is still installed

Commands to verify (Linux):
 vmssname=myvmss16e
 rg=myvmsss
 ./az vmss create --image https://genlinuximg001100.blob.core.windows.net/vhds/linuximage.vhd --custom-os-disk-type linux -g $rg --name $vmssname --authentication-type ssh
 ./az vmss show -n $vmssname -g $rg
 ./az network public-ip show -n ${vmssname}PublicIP -g $rg --query ipAddress 
 SSH into the VM, Ssh format for instance 0: ssh <ipAddress> -p 50000
 Type 'emacs', it should start (exit with Ctrl-X Ctrl-C)

 **custom Windows image**

 - create VM1, add a customization such as installing an application (e.g WinMerge)
 - generalize, capture and deallocate VM1's vhd (https://azure.microsoft.com/documentation/articles/virtual-machines-windows-classic-capture-image/ + https://azure.microsoft.com/documentation/articles/virtual-machines-linux-capture-image/)
 - create VMSS with OS Disk URI pointing to VM1's vhd. Create in a different resource group than
   the storage account the VHD is in.
 - RDP into instance 1
 - verify application is still installed (e.g. launch WinMerge)

Commands to verify (windows):
 set vmssname=myvmss16g
 set rg=myvmsss
 call az vmss create --image http://genwinimg001100.blob.core.windows.net/vhds/osdiskimage.vhd --custom-os-disk-type windows -g %rg% --name %vmssname% --admin-password Test@1234!
 call az vmss show -n %vmssname% -g %rg%
 call az network public-ip show -n %vmssname%PublicIP -g %rg% --query ipAddress 
 Then RDP in and look for app being installed already
 mstsc /v:<vmname>:50000, launch application

## P1: LESS COMMON ##
Execute P1 scenarios if a change is made in these areas

**password Linux**

 - create
 - login with password
 - verify SSH key path

**custom ssh key path**
 - create
 - login with SSH
 - verify SSH key path

**no load balancer**
 - create without LB
 - verify no LB

## P2: ERROR CASES ##
Be aware of the P2 behavior, execute P2s occassionally or before an important event/ship cycle

**Windows VM with SSH**

**Linux VM, no public key generated**