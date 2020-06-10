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
short-summary: Manage applications running on an Azure Service Fabric cluster.
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
  - name: Update application parameters and upgreade policy values and app type version to v2.
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
short-summary: Manage applications types and its versions running on an Azure Service Fabric cluster.
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
short-summary: Manage application type versions on an Azure Service Fabric cluster.
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
short-summary: Manage services running on an Azure Service Fabric cluster.
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

helps['sf cluster certificate'] = """
type: group
short-summary: Manage a cluster certificate.
"""

helps['sf cluster certificate add'] = """
type: command
short-summary: Add a secondary cluster certificate to the cluster.
examples:
  - name: Add a certificate to a  cluster using a keyvault secret identifier.
    text: |
        az sf cluster certificate add -g group-name -c cluster1 \\
            --secret-identifier 'https://{KeyVault}.vault.azure.net/secrets/{Secret}'
  - name: Add a self-signed certificate to a cluster.
    text: >
        az sf cluster certificate add -g group-name -c cluster1 --certificate-subject-name test.com

  - name: Add a secondary cluster certificate to the cluster. (autogenerated)
    text: az sf cluster certificate add --cluster-name cluster1 --resource-group group-name --secret-identifier 'https://{KeyVault}.vault.azure.net/secrets/{Secret}' --vault-name MyVault
    crafted: true
"""

helps['sf cluster certificate remove'] = """
type: command
short-summary: Remove a certificate from a cluster.
examples:
  - name: Remove a certificate by thumbprint.
    text: >
        az sf cluster certificate remove -g group-name -c cluster1 --thumbprint '5F3660C715EBBDA31DB1FFDCF508302348DE8E7A'

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
