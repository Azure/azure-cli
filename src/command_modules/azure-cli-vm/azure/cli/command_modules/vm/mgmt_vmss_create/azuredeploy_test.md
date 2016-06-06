# VM Create scenarios before merge #

## P0: BASIC ##
Execute P0s before any change to VMSS Create **OR VM CREATE** is merged

**simple Windows VMSS**

 - create
 - verify LB and public IP
 - verify storage type
 - RDP into instance 1

**Windows VMSS with no overprovisioning, instance count 4, ReadWrite caching and Automatic upgrades, static private and static Public IP Addresses**

 - create
 - verify LB public/private IP is static
 - verify overprovisioning, instance count (capacity), caching and upgrade policy
 - RDP into instance 1

**Linux VMSS with custom OS Disk name and storage container name, existing VNet/subnet, existing IP for LB**

 - verify existing IP is used by LB
 - verify OS Disk name
 - verify in correct VNet/Subnet
 - verify existing IP used
 - SSH into instance 1

**Linux VMSS with existing LB and DNS name**

 - verify existing LB is used
 - verify DNS name
 - SSH into instance 1

**custom Linux image**

 - create VM1, add a customization such as "sudo apt-get install emacs23"
 - generalize, capture and deallocate VM1's vhd (https://azure.microsoft.com/en-us/documentation/articles/virtual-machines-linux-capture-image/)
 - create VMSS with OS Disk URI pointing to VM1's vhd
 - SSH into instance 1
 - verify emacs is still installed

 **custom Windows image**

 - create VM1, add a customization such as installing an application
 - generalize, capture and deallocate VM1's vhd (https://azure.microsoft.com/en-us/documentation/articles/virtual-machines-windows-classic-capture-image/ + https://azure.microsoft.com/en-us/documentation/articles/virtual-machines-linux-capture-image/)
 - create VMSS with OS Disk URI pointing to VM1's vhd
 - RDP into instance 1
 - verify application is still installed


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

**windows VM with SSH**

**linux VM, no public key generated**