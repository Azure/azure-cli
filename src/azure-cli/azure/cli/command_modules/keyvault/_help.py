# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps  # pylint: disable=unused-import
# pylint: disable=line-too-long, too-many-lines

helps['keyvault'] = """
type: group
short-summary: Manage KeyVault keys, secrets, and certificates.
"""

helps['keyvault backup'] = """
type: group
short-summary: Manage full HSM backup.
"""

helps['keyvault backup start'] = """
type: command
short-summary: Begin a full backup of the HSM.
"""

helps['keyvault restore'] = """
type: group
short-summary: Manage full HSM restore.
"""

helps['keyvault restore start'] = """
type: command
short-summary: Restore a full backup of a HSM.
"""

helps['keyvault certificate'] = """
type: group
short-summary: Manage certificates.
"""

helps['keyvault certificate contact'] = """
type: group
short-summary: Manage contacts for certificate management.
"""

helps['keyvault certificate create'] = """
type: command
short-summary: Create a Key Vault certificate.
long-summary: Certificates can be used as a secrets for provisioned virtual machines.
examples:
  - name: Create a self-signed certificate with the default policy and add it to a virtual machine.
    text: |
        az keyvault certificate create --vault-name vaultname -n cert1 \\
          -p "$(az keyvault certificate get-default-policy)"

        secrets=$(az keyvault secret list-versions --vault-name vaultname \\
          -n cert1 --query "[?attributes.enabled].id" -o tsv)

        vm_secrets=$(az vm secret format -s "$secrets")

        az vm create -g group-name -n vm-name --admin-username deploy  \\
          --image debian --secrets "$vm_secrets"
"""

helps['keyvault certificate download'] = """
type: command
short-summary: Download the public portion of a Key Vault certificate.
long-summary: The certificate formatted as either PEM or DER. PEM is the default.
examples:
  - name: Download a certificate as PEM and check its fingerprint in openssl.
    text: |
        az keyvault certificate download --vault-name vault -n cert-name -f cert.pem && \\
        openssl x509 -in cert.pem -inform PEM  -noout -sha1 -fingerprint
  - name: Download a certificate as DER and check its fingerprint in openssl.
    text: |
        az keyvault certificate download --vault-name vault -n cert-name -f cert.crt -e DER && \\
        openssl x509 -in cert.crt -inform DER  -noout -sha1 -fingerprint
"""

helps['keyvault certificate get-default-policy'] = """
type: command
short-summary: Get the default policy for self-signed certificates.
long-summary: |
    This default policy can be used in conjunction with `az keyvault create` to create a self-signed certificate.
    The default policy can also be used as a starting point to create derivative policies.

    For more details, see: https://docs.microsoft.com/azure/key-vault/certificates/about-certificates#certificate-policy
examples:
  - name: Create a self-signed certificate with the default policy
    text: |
        az keyvault certificate create --vault-name vaultname -n cert1 \\
          -p "$(az keyvault certificate get-default-policy)"
"""

helps['keyvault certificate import'] = """
type: command
short-summary: Import a certificate into KeyVault.
long-summary: Certificates can also be used as a secrets in provisioned virtual machines.
examples:
  - name: Create a service principal with a certificate, add the certificate to Key Vault and provision a VM with that certificate.
    text: |
        service_principal=$(az ad sp create-for-rbac --create-cert)

        cert_file=$(echo $service_principal | jq .fileWithCertAndPrivateKey -r)

        az keyvault create -g my-group -n vaultname

        az keyvault certificate import --vault-name vaultname -n cert_name -f cert_file

        secrets=$(az keyvault secret list-versions --vault-name vaultname \\
          -n cert1 --query "[?attributes.enabled].id" -o tsv)

        vm_secrets=$(az vm secret format -s "$secrets")

        az vm create -g group-name -n vm-name --admin-username deploy  \\
          --image debian --secrets "$vm_secrets"
"""

helps['keyvault certificate issuer'] = """
type: group
short-summary: Manage certificate issuer information.
"""

helps['keyvault certificate issuer admin'] = """
type: group
short-summary: Manage admin information for certificate issuers.
"""

helps['keyvault certificate pending'] = """
type: group
short-summary: Manage pending certificate creation operations.
"""

helps['keyvault create'] = """
type: command
short-summary: Create a Vault or HSM.
long-summary: If `--enable-rbac-authorization` is not specified, then default permissions are created for the current user or service principal unless the `--no-self-perms` flag is specified.
examples:

  - name: Create a key vault with network ACLs specified (use --network-acls to specify IP and VNet rules by using a JSON string).
    text: |
        az keyvault create --location westus2 --name MyKeyVault --resource-group MyResourceGroup --network-acls "{\\"ip\\": [\\"1.2.3.4\\", \\"2.3.4.0/24\\"], \\"vnet\\": [\\"vnet_name_1/subnet_name1\\", \\"vnet_name_2/subnet_name2\\", \\"/subscriptions/000000-0000-0000/resourceGroups/MyResourceGroup/providers/Microsoft.Network/virtualNetworks/MyVNet/subnets/MySubnet\\"]}"

  - name: Create a key vault with network ACLs specified (use --network-acls to specify IP and VNet rules by using a JSON file).
    text: |
        az keyvault create --location westus2 --name MyKeyVault --resource-group MyResourceGroup --network-acls network-acls-example.json

  - name: Create a key vault with network ACLs specified (use --network-acls-ips to specify IP rules).
    text: |
        az keyvault create --location westus2 --name MyKeyVault --resource-group MyResourceGroup --network-acls-ips 3.4.5.0/24 4.5.6.0/24

  - name: Create a key vault with network ACLs specified (use --network-acls-vnets to specify VNet rules).
    text: |
        az keyvault create --location westus2 --name MyKeyVault --resource-group MyResourceGroup --network-acls-vnets vnet_name_2/subnet_name_2 vnet_name_3/subnet_name_3 /subscriptions/000000-0000-0000/resourceGroups/MyResourceGroup/providers/Microsoft.Network/virtualNetworks/vnet_name_4/subnets/subnet_name_4

  - name: Create a key vault with network ACLs specified (use --network-acls, --network-acls-ips and --network-acls-vnets together, redundant rules will be removed, finally there will be 4 IP rules and 3 VNet rules).
    text: |
        az keyvault create --location westus2 --name MyKeyVault --resource-group MyResourceGroup --network-acls "{\\"ip\\": [\\"1.2.3.4\\", \\"2.3.4.0/24\\"], \\"vnet\\": [\\"vnet_name_1/subnet_name1\\", \\"vnet_name_2/subnet_name2\\"]}" --network-acls-ips 3.4.5.0/24 4.5.6.0/24 --network-acls-vnets vnet_name_2/subnet_name_2 vnet_name_3/subnet_name_3 /subscriptions/000000-0000-0000/resourceGroups/MyResourceGroup/providers/Microsoft.Network/virtualNetworks/vnet_name_4/subnets/subnet_name_4
  - name: Create a key vault. (autogenerated)
    text: |
        az keyvault create --location westus2 --name MyKeyVault --resource-group MyResourceGroup
    crafted: true
"""

helps['keyvault delete'] = """
type: command
short-summary: Delete a Vault or HSM.
examples:
  - name: Delete a key vault. (autogenerated)
    text: |
        az keyvault delete --name MyKeyVault --resource-group MyResourceGroup
    crafted: true
"""

helps['keyvault list-deleted'] = """
type: command
short-summary: Get information about the deleted Vaults or HSMs in a subscription.
"""

helps['keyvault purge'] = """
type: command
short-summary: Permanently delete the specified Vault or HSM. Aka Purges the deleted Vault or HSM.
"""

helps['keyvault key'] = """
type: group
short-summary: Manage keys.
"""

helps['keyvault key delete'] = """
type: command
short-summary: Delete a key of any type from storage in Vault or HSM.
long-summary: The delete key operation cannot be used to remove individual versions of a key. This
    operation removes the cryptographic material associated with the key, which means the key is
    not usable for Sign/Verify, Wrap/Unwrap or Encrypt/Decrypt operations. This operation requires
    the keys/delete permission.
"""

helps['keyvault key encrypt'] = """
type: command
short-summary: Encrypt an arbitrary sequence of bytes using an encryption key that
    is stored in a Vault or HSM.
long-summary: The ENCRYPT operation encrypts an arbitrary sequence of bytes using an encryption key that
    is stored in Vault or HSM. Note that the ENCRYPT operation only supports a single block
    of data, the size of which is dependent on the target key and the encryption algorithm to be
    used. The ENCRYPT operation is only strictly necessary for symmetric keys stored in Vault pr HSM
    since protection with an asymmetric key can be performed using public portion of
    the key. This operation is supported for asymmetric keys as a convenience for callers that
    have a key-reference but do not have access to the public key material. This operation
    requires the keys/encrypt permission.
examples:
  - name: Encrypt value(Base64 encoded string) with valut's key using RSA-OAEP.
    text: |
        az keyvault key encrypt --name mykey --vault-name myvault --algorithm RSA-OAEP --value "YWJjZGVm" --data-type base64
  - name: Encrypt value(plaintext) with MHSM's key using AES-GCM.
    text: |
        az keyvault key encrypt --name mykey --hsm-name myhsm --algorithm A256GCM --value "this is plaintext" --data-type plaintext --aad "101112131415161718191a1b1c1d1e1f"
"""

helps['keyvault key decrypt'] = """
type: command
short-summary: Decrypt a single block of encrypted data.
long-summary: The DECRYPT operation decrypts a well-formed block of ciphertext using the target encryption
    key and specified algorithm. This operation is the reverse of the ENCRYPT operation; only a
    single block of data may be decrypted, the size of this block is dependent on the target key
    and the algorithm to be used. The DECRYPT operation applies to asymmetric and symmetric keys
    stored in Vault or HSM since it uses the private portion of the key. This operation
    requires the keys/decrypt permission.
examples:
  - name: Decrypt value(Base64 encoded string returned by encrypt command) with valut's key using RSA-OAEP and get result as base64 encoded.
    text: |
        az keyvault key decrypt --name mykey --vault-name myvault --algorithm RSA-OAEP --data-type base64 --value "CbFcCxHG7WTU+nbpFRrHoqSduwlPy8xpWxf1JxZ2y12BY/qFJirMSYq1i4SO9rvSmvmEMxFV5kw5s9Tc+YoKmv8X6oe+xXx+JytYV8obA5l3OQD9epuuQHWW0kir/mp88lzhcYWxYuF7mKDpPKDV4if+wnAZqQ4woB6t2JEZU5MVK3s+3E/EU4ehb5XrVxAl6xpYy8VYbyF33uJ5s+aUsYIrsVtXgrW99HQ3ic7tJtIOGuWqKhPCdQRezRkOcyxkJcmnDHOLjWA/9strzzx/dyg/t884gT7qrkmIHh8if9SFal/vi1h4XhoDqUleMTnKev2IFHyDNcYVYG3pftJiuA=="
  - name: Decrypt value(Base64 encoded string returned by encrypt command) with MHSM's key using AES-GCM and get result as plaintext.
    text: |
        az keyvault key decrypt --name mykey --hsm-name myhsm --algorithm A256GCM --value "N5w02jS77xg536Ddzv/xPWQ=" --data-type plaintext
        --aad "101112131415161718191a1b1c1d1e1f" --iv "727b26f78e55cf4cd8d34216" --tag "f7207d02cead35a77a1c7e5f8af959e9"
"""

helps['keyvault key backup'] = """
type: command
short-summary: Request that a backup of the specified key be downloaded to the client.
long-summary: The Key Backup operation exports a key from Vault or HSM in a protected form. Note that
    this operation does NOT return key material in a form that can be used outside the Vault or HSM
    system, the returned key material is either protected to a HSM or to Vault itself. The intent
    of this operation is to allow a client to GENERATE a key in one Vault or HSM instance, BACKUP the
    key, and then RESTORE it into another Vault or HSM instance. The BACKUP operation may be used to
    export, in protected form, any key type from Vault or HSM. Individual versions of a key cannot be backed
    up. BACKUP / RESTORE can be performed within geographical boundaries only; meaning that a BACKUP from one
    geographical area cannot be restored to another geographical area. For example, a backup
    from the US geographical area cannot be restored in an EU geographical area. This operation
    requires the key/backup permission.
"""

helps['keyvault key create'] = """
type: command
short-summary: Create a new key, stores it, then returns key parameters and attributes to the client.
long-summary: The create key operation can be used to create any key type in Vault or HSM. If the named
    key already exists, Vault or HSM creates a new version of the key. It requires the keys/create permission.
"""

helps['keyvault key download'] = """
type: command
short-summary: Download the public part of a stored key.
examples:
  - name: Save the key with PEM encoding.
    text: |
        az keyvault key download --vault-name MyKeyVault -n MyKey -e PEM -f mykey.pem
  - name: Save the key with DER encoding.
    text: |
        az keyvault key download --vault-name MyKeyVault -n MyKey -e DER -f mykey.der
"""

helps['keyvault key list'] = """
type: command
short-summary: List keys in the specified Vault or HSM.
long-summary: Retrieve a list of the keys in the Vault or HSM as JSON Web Key structures that contain the
    public part of a stored key. The LIST operation is applicable to all key types, however only the base
    key identifier, attributes, and tags are provided in the response. Individual versions of a key are not
    listed in the response. This operation requires the keys/list permission.
"""

helps['keyvault key list-deleted'] = """
type: command
short-summary: List the deleted keys in the specified Vault or HSM.
long-summary: Retrieve a list of the keys in the Vault or HSM as JSON Web Key structures that contain the
    public part of a deleted key. This operation includes deletion-specific information. The Get Deleted Keys
    operation is applicable for vaults enabled for soft-delete. While the operation can be invoked on any
    Vault or HSM, it will return an error if invoked on a non soft-delete enabled Vault or HSM. This operation
    requires the keys/list permission.
"""

helps['keyvault key purge'] = """
type: command
short-summary: Permanently delete the specified key.
long-summary: The Purge Deleted Key operation is applicable for soft-delete enabled Vaults or HSMs. While the
    operation can be invoked on any Vault or HSM, it will return an error if invoked on a non soft-delete enabled
    Vault or HSM. This operation requires the keys/purge permission.
"""

helps['keyvault key recover'] = """
type: command
short-summary: Recover the deleted key to its latest version.
long-summary: The Recover Deleted Key operation is applicable for deleted keys in soft-delete enabled
    Vaults or HSMs. It recovers the deleted key back to its latest version under /keys. An attempt to recover
    an non-deleted key will return an error. Consider this the inverse of the delete operation on soft-delete
    enabled Vaults or HSMs. This operation requires the keys/recover permission.
"""

helps['keyvault key restore'] = """
type: command
short-summary: Restore a backed up key to a Vault or HSM.
long-summary: Import a previously backed up key into Vault or HSM, restoring the key, its key identifier, attributes
    and access control policies. The RESTORE operation may be used to import a previously backed up key. Individual
    versions of a key cannot be restored. The key is restored in its entirety with the same key name as it had when
    it was backed up. If the key name is not available in the target Key Vault, the RESTORE operation will be rejected.
    While the key name is retained during restore, the final key identifier will change if the key is restored to a
    different Vault or HSM. Restore will restore all versions and preserve version identifiers. The RESTORE operation
    is subject to security constraints. The target Vault or HSM must be owned by the same Microsoft Azure Subscription
    as the source Vault or HSM. The user must have RESTORE permission in the target Vault or HSM. This operation
    requires the keys/restore permission.
"""

helps['keyvault key set-attributes'] = """
type: command
short-summary: The update key operation changes specified attributes of a stored key and can be applied to any key
    type and key version stored in Vault or HSM.
long-summary: In order to perform this operation, the key must already exist in the Vault or HSM. The cryptographic
    material of a key itself cannot be changed. This operation requires the keys/update permission.
"""

helps['keyvault key show-deleted'] = """
type: command
short-summary: Get the public part of a deleted key.
long-summary: The Get Deleted Key operation is applicable for soft-delete enabled Vaults or HSMs. While the
    operation can be invoked on any Vault or HSM, it will return an error if invoked on a non soft-delete enabled
    Vault or HSM. This operation requires the keys/get permission.
"""

helps['keyvault key get-policy-template'] = """
type: command
short-summary: Return policy template as JSON encoded policy definition.
"""

helps['keyvault key rotate'] = """
type: command
short-summary: Rotate the key based on the key policy by generating a new version of the key.
"""

helps['keyvault key rotation-policy'] = """
type: group
short-summary: Manage key's rotation policy.
"""

helps['keyvault key rotation-policy update'] = """
type: command
short-summary: Update the rotation policy of a Key Vault key.
examples:
  - name: Set rotation policy using json file
    text: |
        az keyvault key rotation-policy update -n mykey --vault-name mykeyvault --value path/to/policy.json
        A valid example for policy.json is:
        {
          "lifetimeActions": [
            {
              "trigger": {
                "timeAfterCreate": "P90D", // ISO 8601 duration. For example: 90 days is "P90D", 3 months is "P3M", and 48 hours is "PT48H".
                "timeBeforeExpiry" : null
              },
              "action": {
                "type": "Rotate"
              }
            },
            {
              "trigger": {
                "timeBeforeExpiry" : "P30D" // ISO 8601 duration.
              },
              "action": {
                "type": "Notify"
              }
            }
          ],
          "attributes": {
            "expiryTime": "P2Y" // ISO 8601 duration.
          }
        }
"""

helps['keyvault key rotation-policy show'] = """
type: command
short-summary: Get the rotation policy of a Key Vault key.
"""

helps['keyvault list'] = """
type: command
short-summary: List Vaults and/or HSMs.
"""

helps['keyvault network-rule'] = """
type: group
short-summary: Manage vault network ACLs.
"""

helps['keyvault network-rule wait'] = """
type: command
short-summary: Place the CLI in a waiting state until a condition of the vault is met.
examples:
  - name: Pause CLI until the network ACLs are updated.
    text: |
        az keyvault network-rule wait --name MyVault --updated
"""

helps['keyvault private-endpoint-connection'] = """
type: group
short-summary: Manage vault/HSM private endpoint connections.
"""

helps['keyvault private-endpoint-connection approve'] = """
type: command
short-summary: Approve a private endpoint connection request for a Key Vault/HSM.
examples:
  - name: Approve a private endpoint connection request for a Key Vault by ID.
    text: |
        az keyvault private-endpoint-connection approve --id "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/myrg/providers/Microsoft.KeyVault/vaults/mykv/privateEndpointConnections/mykv.00000000-0000-0000-0000-000000000000"
  - name: Approve a private endpoint connection request for a Key Vault by ID.
    text: |
        id = (az keyvault show -n mykv --query "privateEndpointConnections[0].id")
        az keyvault private-endpoint-connection approve --id $id
  - name: Approve a private endpoint connection request for a Key Vault using vault name and connection name.
    text: |
        az keyvault private-endpoint-connection approve -g myrg --vault-name mykv --name myconnection
  - name: Approve a private endpoint connection request for a Key Vault using vault name and connection name.
    text: |
        name = (az keyvault show -n mykv --query "privateEndpointConnections[0].name")
        az keyvault private-endpoint-connection approve -g myrg --vault-name mykv --name $name
  - name: Approve a private endpoint connection request for a HSM using hsm name and connection name.
    text: |
        az keyvault private-endpoint-connection approve -g myrg --hsm-name myhsm --name myconnection
"""

helps['keyvault private-endpoint-connection reject'] = """
type: command
short-summary: Reject a private endpoint connection request for a Key Vault/HSM.
examples:
  - name: Reject a private endpoint connection request for a Key Vault by ID.
    text: |
        az keyvault private-endpoint-connection reject --id "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/myrg/providers/Microsoft.KeyVault/vaults/mykv/privateEndpointConnections/mykv.00000000-0000-0000-0000-000000000000"
  - name: Reject a private endpoint connection request for a Key Vault by ID.
    text: |
        id = (az keyvault show -n mykv --query "privateEndpointConnections[0].id")
        az keyvault private-endpoint-connection reject --id $id
  - name: Reject a private endpoint connection request for a Key Vault using vault name and connection name.
    text: |
        az keyvault private-endpoint-connection reject -g myrg --vault-name mykv --name myconnection
  - name: Reject a private endpoint connection request for a Key Vault using vault name and connection name.
    text: |
        name = (az keyvault show -n mykv --query "privateEndpointConnections[0].name")
        az keyvault private-endpoint-connection reject -g myrg --vault-name mystorageaccount --name $name
  - name: Reject a private endpoint connection request for a HSM using hsm name and connection name.
    text: |
        az keyvault private-endpoint-connection reject -g myrg --hsm-name myhsm --name myconnection
"""

helps['keyvault private-endpoint-connection delete'] = """
type: command
short-summary: Delete the specified private endpoint connection associated with a Key Vault/HSM.
examples:
  - name: Delete a private endpoint connection request for a Key Vault by ID.
    text: |
        az keyvault private-endpoint-connection delete --id "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/myrg/providers/Microsoft.KeyVault/vaults/mykv/privateEndpointConnections/mykv.00000000-0000-0000-0000-000000000000"
  - name: Delete a private endpoint connection request for a Key Vault by ID.
    text: |
        id = (az keyvault show -n mykv --query "privateEndpointConnections[0].id")
        az keyvault private-endpoint-connection delete --id $id
  - name: Delete a private endpoint connection request for a Key Vault using vault name and connection name.
    text: |
        az keyvault private-endpoint-connection delete -g myrg --vault-name mykv --name myconnection
  - name: Delete a private endpoint connection request for a Key Vault using vault name and connection name.
    text: |
        name = (az keyvault show -n mykv --query "privateEndpointConnections[0].name")
        az keyvault private-endpoint-connection delete -g myrg --vault-name mykv --name $name
  - name: Delete a private endpoint connection request for a HSM using hsm name and connection name.
    text: |
        az keyvault private-endpoint-connection delete -g myrg --hsm-name myhsm --name myconnection
"""

helps['keyvault private-endpoint-connection list'] = """
type: command
short-summary: List all private endpoint connections associated with a HSM.
examples:
  - name: List all private endpoint connections associated with a HSM using hsm name.
    text: |
        az keyvault private-endpoint-connection list -g myrg --hsm-name myhsm
"""

helps['keyvault private-endpoint-connection show'] = """
type: command
short-summary: Show details of a private endpoint connection associated with a Key Vault/HSM.
examples:
  - name: Show details of a private endpoint connection request for a Key Vault by ID.
    text: |
        az keyvault private-endpoint-connection show --id "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/myrg/providers/Microsoft.KeyVault/vaults/mykv/privateEndpointConnections/mykv.00000000-0000-0000-0000-000000000000"
  - name: Show details of a private endpoint connection request for a Key Vault by ID.
    text: |
        id = (az keyvault show -n mykv --query "privateEndpointConnections[0].id")
        az keyvault private-endpoint-connection show --id $id
  - name: Show details of a private endpoint connection request for a Key Vault using vault name and connection name.
    text: |
        az keyvault private-endpoint-connection show -g myrg --vault-name mykv --name myconnection
  - name: Show details of a private endpoint connection request for a Key Vault using vault name and connection name.
    text: |
        name = (az keyvault show -n mykv --query "privateEndpointConnections[0].name")
        az keyvault private-endpoint-connection show -g myrg --vault-name mykv --name $name
"""

helps['keyvault private-endpoint-connection wait'] = """
type: command
short-summary: Place the CLI in a waiting state until a condition of the private endpoint connection is met.
examples:
  - name: Pause CLI until the private endpoint connection is approved/rejected by ID.
    text: |
        az keyvault private-endpoint-connection wait --id "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/myrg/providers/Microsoft.KeyVault/vaults/mykv/privateEndpointConnections/mykv.00000000-0000-0000-0000-000000000000" --created
  - name: Pause CLI until the private endpoint connection is approved/rejected using vault name and connection name.
    text: |
        az keyvault private-endpoint-connection wait -g myrg --vault-name mykv --name myconnection --created
"""

helps['keyvault private-link-resource'] = """
type: group
short-summary: Manage vault/HSM private link resources.
"""

helps['keyvault private-link-resource list'] = """
type: command
short-summary: List the private link resources supported for a Key Vault/HSM.
examples:
  - name: Get the private link resources that need to be created for a Key Vault.
    text: |
        az keyvault private-link-resource list --vault-name mykv
  - name: Get the private link resources that need to be created for a HSM.
    text: |
        az keyvault private-link-resource list --hsm-name myhsm
"""

helps['keyvault recover'] = """
type: command
short-summary: Recover a Vault or HSM.
long-summary: Recover a previously deleted Vault or HSM for which soft delete was enabled.
examples:
  - name: Recover a key vault. (autogenerated)
    text: |
        az keyvault recover --location westus2 --name MyKeyVault --resource-group MyResourceGroup
    crafted: true
"""

helps['keyvault role'] = """
type: group
short-summary: Manage user roles for access control.
"""

helps['keyvault role assignment'] = """
type: group
short-summary: Manage role assignments.
"""

helps['keyvault role definition'] = """
type: group
short-summary: Manage role definitions.
"""

helps['keyvault role definition create'] = """
type: command
short-summary: Create a custom role definition.
examples:
  - name: Create a role by a JSON string.
    text: |
        az keyvault role definition create --hsm-name MyHSM --role-definition '{
            "roleName": "My Custom Role",
            "description": "The description of the custom rule.",
            "actions": [],
            "notActions": [],
            "dataActions": [
                "Microsoft.KeyVault/managedHsm/keys/read/action"
            ],
            "notDataActions": []
        }'
  - name: Create a role from a file containing a JSON description.
    text: >
        az keyvault role definition create --hsm-name MyHSM --role-definition @keyvault-role.json
"""

helps['keyvault role definition update'] = """
type: command
short-summary: Update a role definition.
examples:
  - name: Update a role by a JSON string.
    text: |
        az keyvault role definition update --hsm-name MyHSM --role-definition '{
            "roleName": "My Custom Role",
            "name": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
            "id": "Microsoft.KeyVault/providers/Microsoft.Authorization/roleDefinitions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
            "description": "The description of the custom rule.",
            "actions": [],
            "notActions": [],
            "dataActions": [
                "Microsoft.KeyVault/managedHsm/keys/read/action",
                "Microsoft.KeyVault/managedHsm/keys/write/action",
                "Microsoft.KeyVault/managedHsm/keys/backup/action",
                "Microsoft.KeyVault/managedHsm/keys/create"
            ],
            "notDataActions": []
        }'
  - name: Update a role from a file containing a JSON description.
    text: >
        az keyvault role definition update --hsm-name MyHSM --role-definition @keyvault-role.json
"""

helps['keyvault role definition delete'] = """
type: command
short-summary: Delete a role definition.
"""

helps['keyvault role definition show'] = """
type: command
short-summary: Show the details of a role definition.
"""

helps['keyvault secret'] = """
type: group
short-summary: Manage secrets.
"""

helps['keyvault secret set'] = """
type: command
short-summary: Create a secret (if one doesn't exist) or update a secret in a KeyVault.
examples:
  - name: Create a secret (if one doesn't exist) or update a secret in a KeyVault.
    text: |
        az keyvault secret set --name MySecretName --vault-name MyKeyVault --value MyVault
  - name: Create a secret (if one doesn't exist) or update a secret in a KeyVault through a file.
    text: |
        az keyvault secret set --name MySecretName --vault-name MyKeyVault --file /path/to/file --encoding MyEncoding
"""

helps['keyvault show'] = """
type: command
short-summary: Show details of a Vault or HSM.
examples:
  - name: Show details of a key vault. (autogenerated)
    text: |
        az keyvault show --name MyKeyVault
    crafted: true
"""

helps['keyvault show-deleted'] = """
type: command
short-summary: Show details of a deleted Vault or HSM.
examples:
  - name: Show details of a deleted key vault.
    text: |
        az keyvault show-deleted --name MyKeyVault
"""

helps['keyvault storage'] = """
type: group
short-summary: Manage storage accounts.
"""

helps['keyvault storage add'] = """
type: command
examples:
  - name: Create a storage account and setup a vault to manage its keys
    text: |
        $id = az storage account create -g resourcegroup -n storageacct --query id

        # assign the Azure Key Vault service the "Storage Account Key Operator Service Role" role.
        az role assignment create --role "Storage Account Key Operator Service Role" --scope $id \\
        --assignee cfa8b339-82a2-471a-a3c9-0fc0be7a4093

        az keyvault storage add --vault-name vault -n storageacct --active-key-name key1    \\
        --auto-regenerate-key --regeneration-period P90D  --resource-id $id
"""

helps['keyvault storage remove'] = """
type: command
short-summary: Remove a Key Vault managed Azure Storage Account and all associated SAS definitions. This operation requires the storage/delete permission.
examples:
  - name: Remove a Key Vault managed Azure Storage Account and all associated SAS definitions (autogenerated)
    text: |
        az keyvault storage remove --id "/subscriptions/00000000-0000-0000-0000-00000000000000000/resourceGroups/myrg/providers/Microsoft.KeyVault/vaults/mykv/privateEndpointConnections/mykv.00000000-0000-0000-0000-00000000000000000"
    crafted: true
  - name: Remove a Key Vault managed Azure Storage Account and all associated SAS definitions (autogenerated)
    text: |
        az keyvault storage remove --name MyStorageAccount --vault-name MyVault
    crafted: true
"""

helps['keyvault storage sas-definition'] = """
type: group
short-summary: Manage storage account SAS definitions.
"""

helps['keyvault storage sas-definition create'] = """
type: command
examples:
  - name: Add a sas-definition for an account sas-token
    text: |4
        $sastoken = az storage account generate-sas --expiry 2020-01-01 --permissions rw --resource-types sco --services bfqt --https-only --account-name storageacct --account-key 00000000

        az keyvault storage sas-definition create --vault-name vault --account-name storageacct -n rwallserviceaccess --validity-period P2D --sas-type account --template-uri $sastoken
  - name: Add a sas-definition for a blob sas-token
    text: >4
        $sastoken = az storage blob generate-sas --account-name storageacct --account-key 00000000 -c container1 -n blob1 --https-only --permissions rw

        $url = az storage blob url --account-name storageacct -c container1 -n blob1

        az keyvault storage sas-definition create --vault-name vault --account-name storageacct -n rwblobaccess --validity-period P2D --sas-type service --template-uri $url?$sastoken
  - name: Add a sas-definition for a container sas-token
    text: >4
        $sastoken = az storage container generate-sas --account-name storageacct --account-key 00000000 -n container1 --https-only --permissions rw

        $url = "https://{storage-account-name}.blob.core.windows.net/{container-name}"  # The prefix of your blob url

        az keyvault storage sas-definition create --vault-name vault --account-name storageacct -n rwcontaineraccess --validity-period P2D --sas-type service --template-uri $url?$sastoken
"""

helps['keyvault update'] = """
type: command
short-summary: Update the properties of a Vault.
examples:
  - name: Update the properties of a Vault. (autogenerated)
    text: |
        az keyvault update --enabled-for-disk-encryption true --name MyKeyVault --resource-group MyResourceGroup
    crafted: true
"""

helps['keyvault update-hsm'] = """
type: command
short-summary: Update the properties of a HSM.
examples:
  - name: Update the properties of a HSM.
    text: |
        az keyvault update-hsm --enable-purge-protection true --hsm-name MyHSM --resource-group MyResourceGroup
    crafted: true
"""

helps['keyvault wait'] = """
type: command
short-summary: Place the CLI in a waiting state until a condition of the Vault is met.
examples:
  - name: Pause CLI until the vault is created.
    text: |
        az keyvault wait --name MyVault --created
"""

helps['keyvault wait-hsm'] = """
type: command
short-summary: Place the CLI in a waiting state until a condition of the HSM is met.
examples:
  - name: Pause CLI until the HSM is created.
    text: |
        az keyvault wait-hsm --hsm-name MyHSM --created
"""

helps['keyvault security-domain'] = """
type: group
short-summary: Manage security domain operations.
"""

helps['keyvault security-domain init-recovery'] = """
type: command
short-summary: Retrieve the exchange key of the HSM.
examples:
  - name: Retrieve the exchange key and store it.
    text: |
        az keyvault security-domain init-recovery --hsm-name MyHSM --sd-exchange-key "{PATH_TO_RESTORE}"
"""

helps['keyvault security-domain upload'] = """
type: command
short-summary: Start to restore the HSM.
examples:
  - name: Security domain upload (M=2).
    text: |
        az keyvault security-domain upload --hsm-name MyHSM --sd-file "{SD_TRANSFER_FILE}" --sd-exchange-key "{PEM_FILE_NAME}" --sd-wrapping-keys "{PEM_PRIVATE_KEY1_FILE_NAME}" "{PEM_PRIVATE_KEY2_FILE_NAME}"
"""

helps['keyvault security-domain download'] = """
type: command
short-summary: Download the security domain file from the HSM.
examples:
  - name: Security domain download (N=3, M=2).
    text: |
        az keyvault security-domain download --hsm-name MyHSM --security-domain-file "{SD_FILE_NAME}" --sd-quorum 2 --sd-wrapping-keys "{PEM_PUBLIC_KEY1_FILE_NAME}" "{PEM_PUBLIC_KEY2_FILE_NAME}" "{PEM_PUBLIC_KEY3_FILE_NAME}"
"""

helps['keyvault security-domain wait'] = """
type: command
short-summary: Place the CLI in a waiting state until HSM security domain operation is finished.
examples:
  - name: Pause CLI until the security domain operation is finished.
    text: |
        az keyvault security-domain wait --hsm-name MyHSM
"""

helps['keyvault set-policy'] = """
type: command
short-summary: Update security policy settings for a Key Vault.
examples:
  - name: Assign key permissions `get`, `list`, `import` and secret permissions `backup`, `restore` to an object id.
    text: |
        az keyvault set-policy -n MyVault --key-permissions get list import --secret-permissions backup restore --object-id {GUID}
  - name: Assign key permissions `get`, `list` to a UPN (User Principal Name).
    text: |
        az keyvault set-policy -n MyVault --key-permissions get list --upn {UPN}
  - name: Assign key permissions `get`, `list` to a SPN (Service Principal Name).
    text: |
        az keyvault set-policy -n MyVault --key-permissions get list --spn {SPN}
"""
