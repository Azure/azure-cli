# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

def build_deployment_resource(name, template, dependencies=None):
    dependencies = dependencies or []
    deployment = {
        'name': name,
        'type': 'Microsoft.Resources/deployments',
        'apiVersion': '2015-01-01',
        'dependsOn': dependencies,
        'properties': {
            'mode': 'Incremental',
            'template': template,
        }
    }
    return deployment


def build_dce_resource(name, location):
    # TO DO:

    dce_properties = {
        "networkAcls":
        {
            "publicNetworkAccess": "Enabled"
        }
    }

    dce_resource = {
        "type": "Microsoft.Insights/dataCollectionEndpoints",
        "name": name,
        "location": location,
        "apiVersion": "2021-04-01",
        "properties": dce_properties
    }

    return dce_resource


def build_ama_install_resource(vmname, vm_location):

    name = vmname + "/AzureMonitorWindowsAgent"
    ama_install_resource = {
        "type": "Microsoft.Compute/virtualMachines/extensions",
        "apiVersion": "2021-11-01",
        "name": name,
        "location": vm_location,
        "properties": {
            "publisher": "Microsoft.Azure.Monitor",
            "type": "AzureMonitorWindowsAgent",
            "typeHandlerVersion": "1.0",
            "autoUpgradeMinorVersion": True,
            "enableAutomaticUpgrade": True
        }
    }

    return ama_install_resource


def build_dcr_resource(
        dcr_name,
        location,
        workspace_name,
        workspace_res_id,
        dce_resource_id,
        dce_name):

    dcr = {
        "type": "Microsoft.Insights/dataCollectionRules",
        "name": dcr_name,
        "location": location,
        "apiVersion": "2021-09-01-preview",
        "dependsOn": [
                f"[resourceId('Microsoft.Insights/dataCollectionEndpoints', '{dce_name}')]"
        ],
        "properties": {
            "dataCollectionEndpointId": dce_resource_id,
            "streamDeclarations": {
                "Custom-MyLogFileFormat": {
                    "columns": [
                        {
                            "name": "TimeGenerated",
                            "type": "datetime"
                        },
                        {
                            "name": "RawData",
                            "type": "string"
                        }
                    ]
                }
            },
            "dataSources": {
                "logFiles": [
                    {
                        "streams": [
                            "Custom-MyLogFileFormat"
                        ],
                        "filePatterns": [
                            "C:\\Windows\\System32\\config\\systemprofile\\AppData\\"
                            "Local\\Microsoft SQL Server IaaS Agent\\Assessment\\*.csv"
                        ],
                        "format": "text",
                        "settings": {
                            "text": {
                                "recordStartTimestampFormat": "ISO 8601"
                            }
                        },
                        "name": "myLogFileFormat-Windows"
                    }
                ]
            },
            "destinations": {
                "logAnalytics": [
                    {
                        "workspaceResourceId": workspace_res_id,
                        "name": workspace_name
                    }
                ]
            },
            "dataFlows": [
                {
                    "streams": [
                        "Custom-MyLogFileFormat"
                    ],
                    "destinations": [
                        workspace_name
                    ],
                    "transformKql": "source",
                    "outputStream": "Custom-SqlAssessment_CL"
                }
            ]
        }
    }

    return dcr


def build_dcr_vm_linkage_resource(
        vmname,
        association_name,
        dcr_resource_id):

    scope = "Microsoft.Compute/virtualMachines/" + vmname
    link_resources = {
        "type": "Microsoft.Insights/dataCollectionRuleAssociations",
        "apiVersion": "2022-06-01",
        "scope": scope,
        "name": association_name,
        "properties": {
            "description": "Association of data collection rule."
            "Deleting this association will break the data collection for this virtual machine.",
            "dataCollectionRuleId": dcr_resource_id
        }
    }

    return link_resources
