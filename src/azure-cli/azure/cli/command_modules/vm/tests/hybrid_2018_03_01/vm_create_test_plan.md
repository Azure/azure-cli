# VM Create scenarios before merge #

## P0: BASIC ##
Execute P0s before any change to VM Create ***OR VMSS CREATE*** is merged

**simple VM**

 - delete vm_create_ubuntu.yaml
 - delete vm_create_state_modifications.yaml
 - re-record tests

**Linux with existing availability set, existing NSG, existing public IP
Size Standard_A3, existing storage account, existing storage container name, existing VNET/Subnet**

 - verify VM is in availability set
 - verify NSG
 - verify private and public IP are static
 - verify VHD storage path
 - verify in correct VNet/Subnet
 - verify existing IP used
 - login with SSH

 OR

 - delete test_vm_create_existing_options.yaml
 - re-record test

**Linux, static private IP, static public IP, DNS name**

 - create
 - verify private/public IPs are static
 - verify DNS name

 OR 

 - delete test_vm_create_custom_ip.yaml
 - re-record test

 **Multi-NIC VM**

 - create vm with multiple nics
 - verify create succeeds and that nics are added in the correct order

 OR

 - delete test_vm_create_multinic.yaml
 - re-record test

 **Minimum VM**

 - create vm with no availability set, NSG, public ip or tags
 - verify create succeeds and that the other resources aren't created

 OR

 - delete test_vm_create_none_options.yaml
 - re-record test

 **custom Linux image**

 - create VM, add a customization such as "sudo apt-get install emacs23"
 - generalize, capture and deallocate VM's vhd (https://azure.microsoft.com/documentation/articles/virtual-machines-linux-capture-image/)
 - create VM with OS Disk URI pointing to VM's vhd.  Create in a different resource group than
   the storage account the VHD is in.
 - SSH into instance
 - verify emacs is still installed

Commands to verify (Linux):
 vmname=cusvm0101z
 rg=myvms2
 ./az vm create -n $vmname -g $rg --image https://genlinuximg001100.blob.core.windows.net/vhds/linuximage.vhd --authentication-type ssh --custom-disk-os-type linux --storage-account <ID ending in genlinuximg001100> --storage-container-name ${vmname}vhdcopy --os-disk-name osdiskimage
 then 
 ssh <IPAddress> (don't specify username or password)
 verify emacs/application is installed

 **custom Windows image**

 - create VM, add a customization such as installing an application
 - generalize, capture and deallocate VM's vhd (https://azure.microsoft.com/documentation/articles/virtual-machines-windows-classic-capture-image/ + https://azure.microsoft.com/documentation/articles/virtual-machines-linux-capture-image/)
 - create VM with OS Disk URI pointing to VM's vhd.  Create in a different resource group than
   the storage account the VHD is in.
 - RDP into instance
 - verify application is still installed

Commands to verify (Windows):
 set vmname=cusvm05123
 set rg=myvms
 call az vm create -n %vmname% -g %rg% --image http://genwinimg001100.blob.core.windows.net/vhds/osdiskimage.vhd --authentication-type password --admin-password Test1234@! --storage-account <ID ending in genwinimg001100> --storage-container-name %vmname%mygenimg
 then
 RDP <IPAddress>
 verify WinMerge/application is installed

## P1: LESS COMMON ##
Execute P1 scenarios if a change is made in these areas

**password Linux**

 - create
 - login with password

**custom ssh key path**
 - create
 - login with SSH
 - verify SSH key path

## P2: ERROR CASES ##
Be aware of the P2 behavior, execute P2s occassionally or before an important event/ship cycle

**Windows VM with SSH**

**Linux VM, no public key generated**