# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps  # pylint: disable=unused-import
# pylint: disable=line-too-long, too-many-lines

helps['sf'] = """
type: group
short-summary: Manage and administer Azure Service Fabric clusters.
"""

helps['sf application'] = """
type: group
short-summary: Manage applications running on an Azure Service Fabric cluster. Only support ARM deployed applications.
"""

helps['sf application create'] = """
type: command
short-summary: Create a new application on an Azure Service Fabric cluster.
examples:
  - name: Create application "testApp" with parameters. The application type "TestAppType" version "v1" should already exist in the cluster, and the application parameters should be defined in the application manifest.
    text: >
        az sf application create -g testRG -c testCluster --application-name testApp --application-type-name TestAppType \\
          --application-type-version v1 --application-parameters key0=value0
  - name: Create application "testApp" and app type version using the package url provided.
    text: >
        az sf application create -g testRG -c testCluster --application-name testApp --application-type-name TestAppType \\
          --application-type-version v1 --package-url "https://sftestapp.blob.core.windows.net/sftestapp/testApp_1.0.sfpkg" \\
            --application-parameters key0=value0
"""

helps['sf application update'] = """
type: command
short-summary: Update a Azure Service Fabric application. This allows updating the application parameters and/or upgrade the application type version which will trigger an application upgrade.
examples:
  - name: Update application parameters and upgrade policy values and app type version to v2.
    text: >
        az sf application update -g testRG -c testCluster --application-name testApp --application-type-version v2 \\
          --application-parameters key0=value0 --health-check-stable-duration 0 --health-check-wait-duration 0 --health-check-retry-timeout 0 \\
            --upgrade-domain-timeout 5000 --upgrade-timeout 7000 --failure-action Rollback --upgrade-replica-set-check-timeout 300 --force-restart
  - name: Update application minimum and maximum nodes.
    text: >
        az sf application update -g testRG -c testCluster --application-name testApp --minimum-nodes 1 --maximum-nodes 3
"""

helps['sf application certificate'] = """
type: group
short-summary: Manage the certificate of an application.
"""

helps['sf application certificate add'] = """
type: command
short-summary: Add a new certificate to the Virtual Machine Scale Sets that make up the cluster to be used by hosted applications.
examples:
  - name: Add an application certificate.
    text: >
        az sf application certificate add -g group-name -c cluster1  --secret-identifier 'https://{KeyVault}.vault.azure.net/secrets/{Secret}'
"""

helps['sf application show'] = """
type: command
short-summary: Show the properties of an application on an Azure Service Fabric cluster.
examples:
  - name: Get application.
    text: >
        az sf application show -g testRG -c testCluster --application-name testApp
"""

helps['sf application list'] = """
type: command
short-summary: List applications of a given cluster.
examples:
  - name: List applications for a given cluster.
    text: >
        az sf application list -g testRG -c testCluster
"""

helps['sf application delete'] = """
type: command
short-summary: Delete an application.
examples:
  - name: Delete application.
    text: >
        az sf application delete -g testRG -c testCluster --application-name testApp
"""

helps['sf application-type'] = """
type: group
short-summary: Manage applications types and its versions running on an Azure Service Fabric cluster. Only support ARM deployed application types.
"""

helps['sf application-type'] = """
type: group
short-summary: Manage application types on an Azure Service Fabric cluster.
"""

helps['sf application-type create'] = """
type: command
short-summary: Create a new application type on an Azure Service Fabric cluster.
examples:
  - name: Create new application type.
    text: >
        az sf application-type create -g testRG -c testCluster --application-type-name testAppType
"""

helps['sf application-type show'] = """
type: command
short-summary: Show the properties of an application type on an Azure Service Fabric cluster.
examples:
  - name: Get application type.
    text: >
        az sf application-type show -g testRG -c testCluster --application-type-name CalcServiceApp
"""

helps['sf application-type list'] = """
type: command
short-summary: List application types of a given cluster.
examples:
  - name: List application types for a given cluster.
    text: >
        az sf application-type list -g testRG -c testCluster
"""

helps['sf application-type delete'] = """
type: command
short-summary: Delete an application type.
examples:
  - name: Delete application type.
    text: >
        az sf application-type delete -g testRG -c testCluster --application-type-name CalcServiceApp
"""

helps['sf application-type version'] = """
type: group
short-summary: Manage application type versions on an Azure Service Fabric cluster. Only support ARM deployed application type versions.
"""

helps['sf application-type version create'] = """
type: command
short-summary: Create a new application type on an Azure Service Fabric cluster.
examples:
  - name: Create new application type version using the provided package url. The version in the application manifest contained in the package should have the same version as the one specified in --version.
    text: >
        az sf application-type version create -g testRG -c testCluster --application-type-name testAppType \\
          --version 1.0 --package-url "https://sftestapp.blob.core.windows.net/sftestapp/testApp_1.0.sfpkg"
"""

helps['sf application-type version show'] = """
type: command
short-summary: Show the properties of an application type version on an Azure Service Fabric cluster.
examples:
  - name: Show the properties of an application type version on an Azure Service Fabric cluster.
    text: >
        az sf application-type version show -g testRG -c testCluster --application-type-name CalcServiceApp --version 1.0
"""

helps['sf application-type version list'] = """
type: command
short-summary: List version of a given application type.
examples:
  - name: List versions for a particular application type.
    text: >
        az sf application-type version list -g testRG -c testCluster --application-type-name CalcServiceApp
"""

helps['sf application-type version delete'] = """
type: command
short-summary: Delete an application type version.
examples:
  - name: Delete application type version.
    text: >
        az sf application-type version delete -g testRG -c testCluster --application-type-name CalcServiceApp --version 1.0
"""

helps['sf service'] = """
type: group
short-summary: Manage services running on an Azure Service Fabric cluster. Only support ARM deployed services.
"""

helps['sf service create'] = """
type: command
short-summary: Create a new service on an Azure Service Fabric cluster.
examples:
  - name: Create a new stateless service "testApp~testService1" with instance count -1 (on all the nodes).
    text: >
        az sf service create -g testRG -c testCluster --application-name testApp --state stateless --service-name testApp~testService \\
          --service-type testStateless --instance-count -1 --partition-scheme singleton
  - name: Create a new stateful service "testApp~testService2" with a target of 5 nodes.
    text: >
        az sf service create -g testRG -c testCluster --application-name testApp --state stateful --service-name testApp~testService2 \\
          --service-type testStatefulType --min-replica-set-size 3 --target-replica-set-size 5
"""

helps['sf service show'] = """
type: command
short-summary: Get a service.
examples:
  - name: Show the properties of a service on an Azure Service Fabric cluster.
    text: >
        az sf service show -g testRG -c testCluster --application-name testApp --service-name testApp~testService
"""

helps['sf service list'] = """
type: command
short-summary: List services of a given application.
examples:
  - name: List services.
    text: >
        az sf service list -g testRG -c testCluster --application-name testApp
"""

helps['sf service delete'] = """
type: command
short-summary: Delete a service.
examples:
  - name: Delete service.
    text: >
        az sf service delete -g testRG -c testCluster --application-name testApp --service-name testApp~testService
"""

helps['sf cluster'] = """
type: group
short-summary: Manage an Azure Service Fabric cluster.
"""

helps['sf cluster client-certificate'] = """
type: group
short-summary: Manage the client certificate of a cluster.
"""

helps['sf cluster client-certificate add'] = """
type: command
short-summary: Add a common name or certificate thumbprint to the cluster for client authentication.
examples:
  - name: Add client certificate by thumbprint
    text: >
        az sf cluster client-certificate add -g group-name -c cluster1 --thumbprint '5F3660C715EBBDA31DB1FFDCF508302348DE8E7A'

"""

helps['sf cluster client-certificate remove'] = """
type: command
short-summary: Remove client certificates or subject names used for authentication.
examples:
  - name: Remove a client certificate by thumbprint.
    text: >
        az sf cluster client-certificate remove -g group-name -c cluster1 --thumbprint '5F3660C715EBBDA31DB1FFDCF508302348DE8E7A'

"""

helps['sf cluster create'] = """
type: command
short-summary: Create a new Azure Service Fabric cluster.
examples:
  - name: Create a cluster with a given size and self-signed certificate that is downloaded locally.
    text: >
        az sf cluster create -g group-name -c cluster1 -l westus --cluster-size 4 --vm-password Password#1234 --certificate-output-folder MyCertificates --certificate-subject-name cluster1
  - name: Use a keyvault certificate and custom template to deploy a cluster.
    text: >
        az sf cluster create -g group-name -c cluster1 -l westus --template-file template.json \\
            --parameter-file parameter.json --secret-identifier https://{KeyVault}.vault.azure.net:443/secrets/{MyCertificate}

"""

helps['sf cluster durability'] = """
type: group
short-summary: Manage the durability of a cluster.
"""

helps['sf cluster durability update'] = """
type: command
short-summary: Update the durability tier or VM SKU of a node type in the cluster.
examples:
  - name: Change the cluster durability level to 'Silver'.
    text: >
        az sf cluster durability update -g group-name -c cluster1 --durability-level Silver --node-type nt1

"""

helps['sf cluster list'] = """
type: command
short-summary: List cluster resources.
"""

helps['sf cluster node'] = """
type: group
short-summary: Manage the node instance of a cluster.
"""

helps['sf cluster node add'] = """
type: command
short-summary: Add nodes to a node type in a cluster.
examples:
  - name: Add 2 'nt1' nodes to a cluster.
    text: >
        az sf cluster node add -g group-name -c cluster1 --number-of-nodes-to-add 2 --node-type 'nt1'

"""

helps['sf cluster node remove'] = """
type: command
short-summary: Remove nodes from a node type in a cluster.
examples:
  - name: Remove 2 'nt1' nodes from a cluster.
    text: >
        az sf cluster node remove -g group-name -c cluster1 --node-type 'nt1' --number-of-nodes-to-remove 2

"""

helps['sf cluster node-type'] = """
type: group
short-summary: Manage the node-type of a cluster.
"""

helps['sf cluster node-type add'] = """
type: command
short-summary: Add a new node type to a cluster.
examples:
  - name: Add a new node type to a cluster.
    text: >
        az sf cluster node-type add -g group-name -c cluster1 --node-type 'n2' --capacity 5 --vm-user-name 'adminName' --vm-password testPassword0

"""

helps['sf cluster reliability'] = """
type: group
short-summary: Manage the reliability of a cluster.
"""

helps['sf cluster reliability update'] = """
type: command
short-summary: Update the reliability tier for the primary node in a cluster.
examples:
  - name: Change the cluster reliability level to 'Silver'.
    text: >
        az sf cluster reliability update -g group-name -c cluster1 --reliability-level Silver

"""

helps['sf cluster setting'] = """
type: group
short-summary: Manage a cluster's settings.
"""

helps['sf cluster setting remove'] = """
type: command
short-summary: Remove settings from a cluster.
examples:
  - name: Remove the `MaxFileOperationTimeout` setting from a cluster.
    text: >
        az sf cluster setting remove -g group-name -c cluster1 --section 'NamingService' --parameter 'MaxFileOperationTimeout'

"""

helps['sf cluster setting set'] = """
type: command
short-summary: Update the settings of a cluster.
examples:
  - name: Set the `MaxFileOperationTimeout` setting for a cluster to 5 seconds.
    text: >
        az sf cluster setting set -g group-name -c cluster1 --section 'NamingService' --parameter 'MaxFileOperationTimeout' --value 5000

"""

helps['sf cluster upgrade-type'] = """
type: group
short-summary: Manage the upgrade type of a cluster.
"""

helps['sf cluster upgrade-type set'] = """
type: command
short-summary: Change the  upgrade type for a cluster.
examples:
  - name: Set a cluster to use the 'Automatic' upgrade mode.
    text: >
        az sf cluster upgrade-type set -g group-name -c cluster1 --upgrade-mode Automatic
"""

helps['sf managed-cluster'] = """
type: group
short-summary: Manage an Azure Service Fabric managed cluster.
"""

helps['sf managed-cluster show'] = """
type: command
short-summary: Show the properties of an Azure Service Fabric managed cluster.
examples:
  - name: Get cluster.
    text: >
        az sf managed-cluster show -g testRG -c testCluster
"""

helps['sf managed-cluster list'] = """
type: command
short-summary: List managed clusters.
examples:
  - name: List clusters by resource group.
    text: >
        az sf managed-cluster list -g testRG
  - name: List clusters by subscription.
    text: >
        az sf managed-cluster list
"""

helps['sf managed-cluster create'] = """
type: command
short-summary: Delete a managed cluster.
examples:
  - name: Create cluster with standard sku and client cert by thumbprint.
    text: >
        az sf managed-cluster create -g testRG -c testCluster -l eastus2 --cert-thumbprint XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX --cert-is-admin --admin-password PassTest123@ --sku Standard
  - name: Create cluster with standard sku and client cert by common name.
    text: >
        az sf managed-cluster create -g testRG -c testCluster -l eastus2 --cert-common-name Contoso.com --cert-issuer-thumbprint XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX --cert-is-admin --admin-password PassTest123@ --sku Standard
"""

helps['sf managed-cluster update'] = """
type: command
short-summary: Update a managed cluster.
examples:
  - name: Update cluster client port and dns name.
    text: >
        az sf managed-cluster update -g testRG -c testCluster --client-port 50000 --dns-name testnewdns
"""

helps['sf managed-cluster delete'] = """
type: command
short-summary: Delete a managed cluster.
examples:
  - name: Delete cluster.
    text: >
        az sf managed-cluster delete -g testRG -c testCluster
"""

helps['sf managed-cluster client-certificate'] = """
type: group
short-summary: Manage client certificates of a manged cluster.
"""

helps['sf managed-cluster client-certificate add'] = """
type: command
short-summary: Add a new client certificate to the managed cluster.
examples:
  - name: Add admin client certificate by thumbprint.
    text: >
        az sf managed-cluster client-certificate add -g testRG -c testCluster --thumbprint XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX --is-admin
  - name: Add non admin client certificate by common name.
    text: >
        az sf managed-cluster client-certificate add -g testRG -c testCluster --common-name Contoso.com --issuer-thumbprint XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
"""

helps['sf managed-cluster client-certificate delete'] = """
type: command
short-summary: Delete a client certificate from the managed cluster.
examples:
  - name: Delete client certificate by thumbprint.
    text: >
        az sf managed-cluster client-certificate delete -g testRG -c testCluster --thumbprint XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
  - name: Delete client certificate by common name.
    text: >
        az sf managed-cluster client-certificate delete -g testRG -c testCluster --common-name Contoso.com
"""

helps['sf managed-node-type'] = """
type: group
short-summary: Manage a node type of an Azure Service Fabric managed cluster.
"""

helps['sf managed-node-type show'] = """
type: command
short-summary: Show the properties of a node type.
examples:
  - name: Get node type.
    text: >
        az sf managed-node-type show -g testRG -c testCluster -n pnt
"""

helps['sf managed-node-type list'] = """
type: command
short-summary: List node types of a managed cluster.
examples:
  - name: List node types by cluster.
    text: >
        az sf managed-node-type list -g testRG -c testCluster
"""

helps['sf managed-node-type create'] = """
type: command
short-summary: Delete a managed cluster.
examples:
  - name: Create primary node type with 5 nodes.
    text: >
        az sf managed-node-type create -g testRG -c testCluster -n pnt --instance-count 5 --primary
  - name: Create non primary node type with placement properities, capacities and ports.
    text: >
        az sf managed-node-type create -g testRG -c testCluster -n snt --instance-count 5 --placement-property NodeColor=Green SomeProperty=5 --capacity ClientConnections=65536 --app-start-port 20575 --app-end-port 20605 --ephemeral-start-port 20606 --ephemeral-end-port 20861
"""

helps['sf managed-node-type update'] = """
type: command
short-summary: Update a managed cluster.
examples:
  - name: Update the instance count of the node type.
    text: >
        az sf managed-node-type update -g testRG -c testCluster -n snt --instance-count 7
  - name: Update placement properties of the node type. This will overwrite older placement properties if any.
    text: >
        az sf managed-node-type update -g testRG -c testCluster -n snt --placement-property NodeColor=Red SomeProperty=6
"""

helps['sf managed-node-type delete'] = """
type: command
short-summary: Delete node type from a cluster.
examples:
  - name: Delete cluster.
    text: >
        az sf managed-node-type delete -g testRG -c testCluster -n snt
"""

helps['sf managed-node-type node'] = """
type: group
short-summary: Perform operations on nodes of a node type on managed clusters.
"""

helps['sf managed-node-type node restart'] = """
type: command
short-summary: Restart nodes of a node type.
examples:
  - name: Restart 2 nodes.
    text: >
        az sf managed-node-type node restart -g testRG -c testCluster -n snt --node-name snt_0 snt_1
"""

helps['sf managed-node-type node reimage'] = """
type: command
short-summary: Reimage nodes of a node type.
examples:
  - name: Reimage 2 nodes.
    text: >
        az sf managed-node-type node reimage -g testRG -c testCluster -n snt --node-name snt_0 snt_1
"""

helps['sf managed-node-type node delete'] = """
type: command
short-summary: Delete nodes of a node type.
examples:
  - name: Delete 2 nodes.
    text: >
        az sf managed-node-type node delete -g testRG -c testCluster -n snt --node-name snt_0 snt_1
"""

helps['sf managed-node-type vm-extension'] = """
type: group
short-summary: Managed vm extension on a node type on managed clusters.
"""

helps['sf managed-node-type vm-extension add'] = """
type: command
short-summary: Add an extension to the node type.
examples:
  - name: Add bg extension.
    text: >
        az sf managed-node-type vm-extension add -g testRG -c testCluster -n snt --extension-name csetest --publisher Microsoft.Compute --extension-type BGInfo --type-handler-version 2.1 --auto-upgrade-minor-version
"""

helps['sf managed-node-type vm-extension delete'] = """
type: command
short-summary: Delete an extension to the node type.
examples:
  - name: Delete extension by name.
    text: >
        az sf managed-node-type vm-extension delete -g testRG -c testCluster -n snt --extension-name csetest
"""

helps['sf managed-node-type vm-secret'] = """
type: group
short-summary: Managed vm secrets on a node type on managed clusters.
"""

helps['sf managed-node-type vm-secret add'] = """
type: command
short-summary: Add a secret to the node type.
examples:
  - name: Add certificate to the node type as a secret.
    text: >
        az sf managed-node-type vm-secret add -g testRG -c testCluster -n snt --source-vault-id /subscriptions/XXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX/resourceGroups/testRG/providers/Microsoft.KeyVault/vaults/testkv --certificate-url https://testskv.vault.azure.net:443/secrets/TestCert/xxxxxxxxxxxxxxxxxxxxxxxx --certificate-store my
"""

helps['sf managed-application'] = """
type: group
short-summary: Manage applications running on an Azure Service Fabric managed cluster. Only support ARM deployed applications.
"""

helps['sf managed-application create'] = """
type: command
short-summary: Create a new managed application on an Azure Service Fabric managed cluster.
examples:
  - name: Create managed application "testApp" with parameters. The application type "TestAppType" version "v1" should already exist in the cluster, and the application parameters should be defined in the application manifest.
    text: >
        az sf managed-application create -g testRG -c testCluster --application-name testApp --application-type-name TestAppType \\
          --application-type-version v1 --application-parameters key0=value0 --tags key1=value1
  - name: Create application "testApp" and app type version using the package url provided.
    text: >
        az sf managed-application create -g testRG -c testCluster --application-name testApp --application-type-name TestAppType \\
          --application-type-version v1 --package-url "https://sftestapp.blob.core.windows.net/sftestapp/testApp_1.0.sfpkg" \\
            --application-parameters key0=value0
"""

helps['sf managed-application update'] = """
type: command
short-summary: Update a Azure Service Fabric managed application.
long-summary: This allows for updating the tags, the application parameters, value is the application UpgradePolicy and/or upgrade the application type version which will trigger an application upgrade.
examples:
  - name: Update application parameters and upgreade policy values and app type version to v2.
    text: >
        az sf managed-application update -g testRG -c testCluster --application-name testApp --application-type-version v2 \\
          --application-parameters key0=value0 --health-check-stable-duration 0 --health-check-wait-duration 0 --health-check-retry-timeout 0 \\
            --upgrade-domain-timeout 5000 --upgrade-timeout 7000 --failure-action Rollback --upgrade-replica-set-check-timeout 300 --force-restart
  - name: Update managed application service type health policy map.
    text: >
        az sf managed-application update -g testRG -c testCluster --application-name testApp --service-type-health-policy-map  \"ServiceTypeName01\"=\"5,10,5\" \"ServiceTypeName02\"=\"5,5,5\"
"""

helps['sf managed-application show'] = """
type: command
short-summary: Show the properties of a managed application on an Azure Service Fabric managed cluster.
examples:
  - name: Get managed application.
    text: >
        az sf managed-application show -g testRG -c testCluster --application-name testApp
"""

helps['sf managed-application list'] = """
type: command
short-summary: List managed applications of a given managed cluster.
examples:
  - name: List managed applications for a given managed cluster.
    text: >
        az sf managed-application list -g testRG -c testCluster
"""

helps['sf managed-application delete'] = """
type: command
short-summary: Delete a managed application.
examples:
  - name: Delete managed application.
    text: >
        az sf managed-application delete -g testRG -c testCluster --application-name testApp
"""

helps['sf managed-application-type'] = """
type: group
short-summary: Manage applications types and its versions running on an Azure Service Fabric managed cluster. Only support ARM deployed application types.
"""

helps['sf managed-application-type'] = """
type: group
short-summary: Manage application types on an Azure Service Fabric cluster.
"""

helps['sf managed-application-type create'] = """
type: command
short-summary: Create a new managed application type on an Azure Service Fabric managed cluster.
examples:
  - name: Create new managed application type.
    text: >
        az sf managed-application-type create -g testRG -c testCluster --application-type-name testAppType
"""

helps['sf managed-application-type show'] = """
type: command
short-summary: Show the properties of a managed application type on an Azure Service Fabric managed cluster.
examples:
  - name: Get managed application type.
    text: >
        az sf managed-application-type show -g testRG -c testCluster --application-type-name CalcServiceApp
"""

helps['sf managed-application-type list'] = """
type: command
short-summary: List managed application types of a given managed cluster.
examples:
  - name: List managed application types for a given managed cluster.
    text: >
        az sf managed-application-type list -g testRG -c testCluster
"""

helps['sf managed-application-type update'] = """
type: command
short-summary: Update an managed application type.
long-summary: This allows for updating of application type tags.
examples:
  - name: Update application type tags.
    text: >
        az sf managed-application-type update -g testRG -c testCluster --application-type-name CalcServiceApp --tags new=tags are=nice
"""

helps['sf managed-application-type delete'] = """
type: command
short-summary: Delete a managed application type.
examples:
  - name: Delete managed application type.
    text: >
        az sf managed-application-type delete -g testRG -c testCluster --application-type-name CalcServiceApp
"""

helps['sf managed-application-type version'] = """
type: group
short-summary: Manage application type versions on an Azure Service Fabric managed cluster. Only support ARM deployed application type versions.
"""

helps['sf managed-application-type version create'] = """
type: command
short-summary: Create a new managed application type on an Azure Service Fabric managed cluster.
examples:
  - name: Create new managed application type version using the provided package url. The version in the application manifest contained in the package should have the same version as the one specified in --version.
    text: >
        az sf managed-application-type version create -g testRG -c testCluster --application-type-name testAppType \\
          --version 1.0 --package-url "https://sftestapp.blob.core.windows.net/sftestapp/testApp_1.0.sfpkg"
"""

helps['sf managed-application-type version show'] = """
type: command
short-summary: Show the properties of a managed application type version on an Azure Service Fabric managed cluster.
examples:
  - name: Show the properties of a managed application type version on an Azure Service Fabric managed cluster.
    text: >
        az sf managed-application-type version show -g testRG -c testCluster --application-type-name CalcServiceApp --version 1.0
"""

helps['sf managed-application-type version list'] = """
type: command
short-summary: List versions of a given managed application type.
examples:
  - name: List versions for a particular managed application type.
    text: >
        az sf managed-application-type version list -g testRG -c testCluster --application-type-name CalcServiceApp
"""

helps['sf managed-application-type version update'] = """
type: command
short-summary: Update a managed application type version.
long-summary: This allows for updating of application type version tags and the package url.
examples:
  - name: Update managed application type version.
    text: >
        az sf managed-application-type version update -g testRG -c testCluster --application-type-name CalcServiceApp --version 1.0 --tags new=tags
"""

helps['sf managed-application-type version delete'] = """
type: command
short-summary: Delete a managed application type version.
examples:
  - name: Delete managed application type version.
    text: >
        az sf managed-application-type version delete -g testRG -c testCluster --application-type-name CalcServiceApp --version 1.0
"""

helps['sf managed-service'] = """
type: group
short-summary: Manage services running on an Azure Service Fabric managed cluster. Only support ARM deployed services.
"""

helps['sf managed-service create'] = """
type: command
short-summary: Create a new managed service on an Azure Service Fabric managed cluster.
examples:
  - name: Create a new stateless managed service "testService1" with instance count -1 (on all the nodes).
    text: >
        az sf managed-service create -g testRG -c testCluster --application-name testApp --state stateless --service-name testService \\
          --service-type testStateless --instance-count -1 --partition-scheme singleton
  - name: Create a new stateful service "testService2" with a target of 5 nodes.
    text: >
        az sf managed-service create -g testRG -c testCluster --application-name testApp --state stateful --service-name testService2 --has-persisted-state \\
          --service-type testStatefulType --min-replica-set-size 3 --target-replica-set-size 5 --partition-scheme uniformint64range --partition-count 1 --low-key 0 --high-key 25
"""

helps['sf managed-service show'] = """
type: command
short-summary: Get a service.
examples:
  - name: Show the properties of a managed service on an Azure Service Fabric managed cluster.
    text: >
        az sf managed-service show -g testRG -c testCluster --application-name testApp --service-name testService
"""

helps['sf managed-service list'] = """
type: command
short-summary: List managed services of a given managed application.
examples:
  - name: List managed services.
    text: >
        az sf managed-service list -g testRG -c testCluster --application-name testApp
"""

helps['sf managed-service update'] = """
type: command
short-summary: Update a managed service.
examples:
  - name: Update managed stateless service.
    text: >
        az sf managed-service update -g testRG -c testCluster --application-name testApp --service-name testService --min-instance-count 2 \\
          --min-instance-percentage 20
  - name: Update managed stateful service.
    text: >
        az sf managed-service update -g testRG -c testCluster --application-name testApp --service-name testService2 --service-placement-time-limit '00:11:00' \\
          --stand-by-replica-keep-duration '00:11:00' --replica-restart-wait-duration '00:11:00' --quorum-loss-wait-duration '00:11:00'
"""

helps['sf managed-service delete'] = """
type: command
short-summary: Delete a managed service.
examples:
  - name: Delete managed service.
    text: >
        az sf managed-service delete -g testRG -c testCluster --application-name testApp --service-name testService
"""

helps['sf managed-service correlation-scheme'] = """
type: group
short-summary: Manage correlation schemes of services running on an Azure Service Fabric managed cluster. Only support ARM deployed services.
"""

helps['sf managed-service correlation-scheme create'] = """
type: command
short-summary: Create a new managed service correlation scheme on an Azure Service Fabric managed cluster.
long-summary: Create a new managed service correlation scheme on an Azure Service Fabric managed cluster. NOTE You can only have one service correlation per service.
examples:
  - name: Create a new managed service correlation scheme.
    text: >
        az sf managed-service correlation-scheme create -g testRG -c testCluster --application-name testApp --service-name testService \\
          --correlated-service-name "/subscriptions/00000000-0000-0000-0000-000000000000/resourcegroups/testRg/providers/Microsoft.ServiceFabric/managedclusters/testCluster/applications/testApp/services/testService2" \\
            --scheme AlignedAffinity
"""

helps['sf managed-service correlation-scheme update'] = """
type: command
short-summary: Update a managed service correlation scheme.
examples:
  - name: Update managed service correlation scheme.
    text: >
        az sf managed-service correlation-scheme update -g testRG -c testCluster --application-name testApp --service-name testService \\
          --correlated-service-name "/subscriptions/00000000-0000-0000-0000-000000000000/resourcegroups/testRg/providers/Microsoft.ServiceFabric/managedclusters/testCluster/applications/testApp/services/testService2" \\
            --scheme NonAlignedAffinity
"""

helps['sf managed-service correlation-scheme delete'] = """
type: command
short-summary: Delete a managed service correlation scheme.
examples:
  - name: Delete managed service correlation scheme.
    text: >
        az sf managed-service correlation-scheme delete -g testRG -c testCluster --application-name testApp --service-name testService \\
          --correlated-service-name "/subscriptions/00000000-0000-0000-0000-000000000000/resourcegroups/testRg/providers/Microsoft.ServiceFabric/managedclusters/testCluster/applications/testApp/services/testService2"
"""

helps['sf managed-service load-metrics'] = """
type: group
short-summary: Manage service load metrics running on an Azure Service Fabric managed cluster. Only support ARM deployed services.
"""

helps['sf managed-service load-metrics create'] = """
type: command
short-summary: Create a new managed service load metric on an Azure Service Fabric managed cluster.
examples:
  - name: Create a new stateless managed service load metric.
    text: >
        az sf managed-service load-metrics create -g testRG -c testCluster --application-name testApp --service-name testService \\
          --metric-name Metric1 --weight Low --default-load 3
  - name: Create a new stateful service load metric.
    text: >
        az sf managed-service load-metrics create -g testRG -c testCluster --application-name testApp --service-name testService2 \\
          --metric-name Metric2 --weight High --primary-default-load 3 --secondary-default-load 2
"""

helps['sf managed-service load-metrics update'] = """
type: command
short-summary: Update a managed service.
examples:
  - name: Update a new stateless managed service load metric.
    text: >
        az sf managed-service load-metrics update -g testRG -c testCluster --application-name testApp --service-name testService \\
          --metric-name Metric1 --weight Medium --default-load 5
  - name: Update a new stateful service load metric.
    text: >
        az sf managed-service load-metrics update -g testRG -c testCluster --application-name testApp --service-name testService2 \\
          --metric-name Metric2 --weight Low --primary-default-load 2 --secondary-default-load 1
"""

helps['sf managed-service load-metrics delete'] = """
type: command
short-summary: Delete a managed service.
examples:
  - name: Delete managed service.
    text: >
        az sf managed-service load-metrics delete -g testRG -c testCluster --application-name testApp --service-name testService2 \\
          --metric-name Metric1
"""
