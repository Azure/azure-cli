# VM Create scenarios before merge #

## P0: BASIC ##
Execute P0s before any change to VM Create is merged

**plain windows VM from Windows with Storage Redundancy Standard_RAGRS**

 - create
 - get puclic IP
 - login with RDP
 - verify NSG
 - verify storage type

**plain UbuntuLTS from Linux (no extra params)**

 - create
 - get public IP
 - login with SSH
 - verify NSG

**Linux with existing availability set, existing NSG, existing public IP
Size Standard_A3, existing storage account, existing storage container name, existing VNET/Subnet**

 - verify VM is in availability set
 - verify NSG
 - verify private and public IP are static
 - verify VHD storage path
 - verify in correct VNet/Subnet
 - verify existing IP used
 - login with SSH

**Linux, path for SSH key, static private IP, static public IP, DNS name**

 - create
 - login with SSH
 - verify private/public IPs are static
 - verify DNS name

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

## P2: ERROR CASES ##
Be aware of the P2 behavior, execute P2s occassionally or before an important event/ship cycle

**windows VM with SSH**

**linux VM, no public key generated**