# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, too-many-statements, super-with-arguments

VnetConfiguration = {
    "infrastructureSubnetId": None,
    "dockerBridgeCidr": None,
    "platformReservedCidr": None,
    "platformReservedDnsIP": None
}

ManagedEnvironment = {
    "location": None,
    "tags": None,
    "properties": {
        "daprAIInstrumentationKey": None,
        "vnetConfiguration": None,  # VnetConfiguration
        "appLogsConfiguration": None,
        "customDomainConfiguration": None,  # CustomDomainConfiguration,
        "workloadProfiles": None
    }
}

CustomDomainConfiguration = {
    "dnsSuffix": None,
    "certificateValue": None,
    "certificatePassword": None
}

AppLogsConfiguration = {
    "destination": None,
    "logAnalyticsConfiguration": None
}

LogAnalyticsConfiguration = {
    "customerId": None,
    "sharedKey": None
}

# Containerapp

Dapr = {
    "enabled": False,
    "appId": None,
    "appProtocol": None,
    "appPort": None,
    "httpReadBufferSize": None,
    "httpMaxRequestSize": None,
    "logLevel": None,
    "enableApiLogging": None
}

EnvironmentVar = {
    "name": None,
    "value": None,
    "secretRef": None
}

ContainerResources = {
    "cpu": None,
    "memory": None
}

VolumeMount = {
    "volumeName": None,
    "mountPath": None,
    "subPath": None
}

Container = {
    "image": None,
    "name": None,
    "command": None,
    "args": None,
    "env": None,  # [EnvironmentVar]
    "resources": None,  # ContainerResources
    "volumeMounts": None,  # [VolumeMount]
}

SecretVolumeItem = {
    "secretRef": None,
    "path": None,
}

Volume = {
    "name": None,
    "storageType": "EmptyDir",  # AzureFile, EmptyDir or Secret
    "storageName": None,   # None for EmptyDir or Secret, otherwise name of storage resource
    "secrets": None,  # [SecretVolumeItem]
    "mountOptions": None,
}

ScaleRuleAuth = {
    "secretRef": None,
    "triggerParameter": None
}

QueueScaleRule = {
    "queueName": None,
    "queueLength": None,
    "auth": None  # ScaleRuleAuth
}

CustomScaleRule = {
    "type": None,
    "metadata": {},
    "auth": None  # ScaleRuleAuth
}

HttpScaleRule = {
    "metadata": {},
    "auth": None  # ScaleRuleAuth
}

ScaleRule = {
    "name": None,
    "azureQueue": None,  # QueueScaleRule
    "custom": None,  # CustomScaleRule
    "http": None,  # HttpScaleRule
}

Secret = {
    "name": None,
    "value": None,
    "keyVaultUrl": None,
    "identity": None
}

Scale = {
    "minReplicas": None,
    "maxReplicas": None,
    "rules": []  # list of ScaleRule
}

ServiceBinding = {
    "serviceId": None,
    "name": None
}

JobScale = {
    "minExecutions": None,
    "maxExecutions": None,
    "pollingInterval": None,
    "rules": []  # list of ScaleRule
}

TrafficWeight = {
    "revisionName": None,
    "weight": None,
    "latestRevision": False
}

BindingType = {

}

CustomDomain = {
    "name": None,
    "bindingType": None,  # BindingType
    "certificateId": None
}

Ingress = {
    "fqdn": None,
    "external": False,
    "targetPort": None,
    "transport": None,  # 'auto', 'http', 'http2', 'tcp'
    "exposedPort": None,
    "allowInsecure": False,
    "traffic": None,  # TrafficWeight
    "customDomains": None,  # [CustomDomain]
    "ipSecurityRestrictions": None,  # [IPSecurityRestrictions]
    "stickySessions": None  # StickySessions
}

RegistryCredentials = {
    "server": None,
    "username": None,
    "passwordSecretRef": None
}

Template = {
    "revisionSuffix": None,
    "containers": None,  # [Container]
    "initContainers": None,  # [Container]
    "scale": Scale,
    "volumes": None,  # [Volume]
    "serviceBinds": None  # [ServiceBinding]
}

Configuration = {
    "secrets": None,  # [Secret]
    "activeRevisionsMode": None,  # 'multiple' or 'single'
    "ingress": None,  # Ingress
    "dapr": Dapr,
    "registries": None  # [RegistryCredentials]
}

JobTemplate = {
    "containers": None,  # [Container]
    "initContainers": None,  # [Container]
    "volumes": None  # [Volume]
}

# Added template for starting job executions
JobExecutionTemplate = {
    "containers": None,  # [Container]
    "initContainers": None  # [Container]
}

JobConfiguration = {
    "secrets": None,  # [Secret]
    "triggerType": None,  # 'manual' or 'schedule' or 'event'
    "replicaTimeout": None,
    "replicaRetryLimit": None,
    "manualTriggerConfig": None,  # ManualTriggerConfig
    "scheduleTriggerConfig": None,  # ScheduleTriggerConfig
    "eventTriggerConfig": None,  # EventTriggerConfig
    "registries": None,  # [RegistryCredentials]
    "dapr": None
}

ManualTriggerConfig = {
    "replicaCompletionCount": None,
    "parallelism": None
}

ScheduleTriggerConfig = {
    "replicaCompletionCount": None,
    "parallelism": None,
    "cronExpression": None
}

EventTriggerConfig = {
    "replicaCompletionCount": None,
    "parallelism": None,
    "scale": None,  # [JobScale]
}

UserAssignedIdentity = {

}

ManagedServiceIdentity = {
    "type": None,  # 'None', 'SystemAssigned', 'UserAssigned', 'SystemAssigned,UserAssigned'
    "userAssignedIdentities": None  # {string: UserAssignedIdentity}
}

ServiceConnector = {
    "properties": {
        "targetService": {
            "id": None,
            "type": "AzureResource"
        },
        "authInfo": {
            "authType": None,
        },
        "scope": None,
    }
}

Service = {
    "type": None
}

ContainerApp = {
    "location": None,
    "identity": None,  # ManagedServiceIdentity
    "properties": {
        "environmentId": None,
        "configuration": None,  # Configuration
        "template": None,  # Template
        "workloadProfileName": None
    },
    "tags": None
}

ContainerAppsJob = {
    "location": None,
    "identity": None,  # ManagedServiceIdentity
    "properties": {
        "environmentId": None,
        "configuration": None,  # JobConfiguration
        "template": None,  # JobTemplate
        "workloadProfileName": None
    },
    "tags": None
}

ContainerAppCertificateEnvelope = {
    "location": None,
    "properties": {
        "password": None,
        "value": None
    }
}

DaprComponent = {
    "properties": {
        "componentType": None,  # String
        "version": None,
        "ignoreErrors": None,
        "initTimeout": None,
        "secrets": None,
        "metadata": None,
        "scopes": None
    }
}

DaprMetadata = {
    "key": None,  # str
    "value": None,  # str
    "secret_ref": None  # str
}

SourceControl = {
    "properties": {
        "repoUrl": None,
        "branch": None,
        "githubActionConfiguration": None  # [GitHubActionConfiguration]
    }

}

GitHubActionConfiguration = {
    "registryInfo": None,  # [RegistryInfo]
    "azureCredentials": None,  # [AzureCredentials]
    "image": None,  # str
    "contextPath": None,  # str
    "publishType": None,  # str
    "os": None,  # str
    "runtimeStack": None,  # str
    "runtimeVersion": None  # str
}

RegistryInfo = {
    "registryUrl": None,  # str
    "registryUserName": None,  # str
    "registryPassword": None  # str
}

AzureCredentials = {
    "clientId": None,  # str
    "clientSecret": None,  # str
    "tenantId": None,  # str
    "subscriptionId": None  # str
}

ContainerAppCustomDomainEnvelope = {
    "properties": {
        "configuration": {
            "ingress": {
                "customDomains": None
            }
        }
    }
}

ContainerAppCustomDomain = {
    "name": None,
    "bindingType": "SniEnabled",
    "certificateId": None
}

AzureFileProperties = {
    "accountName": None,
    "accountKey": None,
    "accessMode": None,
    "shareName": None
}

ManagedCertificateEnvelop = {
    "location": None,  # str
    "properties": {
        "subjectName": None,  # str
        "validationMethod": None  # str
    }
}

# ContainerApp Patch
ImageProperties = {
    "imageName": None,
    "targetContainerName": None,
    "targetContainerAppName": None,
    "revisionMode": None,
}

ImagePatchableCheck = {
    "targetContainerAppName": None,
    "targetContainerName": None,
    "revisionMode": None,
    "targetImageName": None,
    "oldRunImage": None,
    "newRunImage": None,
    "id": None,
    "reason": None,
}

OryxMarinerRunImgTagProperty = {
    "fullTag": None,
    "framework": None,
    "version": None,
    "marinerVersion": None,
    "architectures": None,
    "support": None,
}
