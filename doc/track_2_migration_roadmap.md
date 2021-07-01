# Track 2 SDK Migration Roadmap
This document provides the roadmap for Track 2 SDK migration in Azure CLI. When you migrate your module to Track 2 SDK, you can go to [Track 2 migration guidance](track_2_migration_guidance.md) to check how to migrate to Track 2 SDK.

## Why do we need migrate Track 1 SDK to Track 2 SDK in Azure CLI?
- Track 1 SDK will be eventually deprecated sometime in the future. 
- Some new features will only be in track2 SDK in the future.

## Here are criteria to determine the priority of migration:
- On-demand for Track 2 SDK from CLI customers (such as CAE support from LinkedIn) has higher priority.
- On-demand for Track 2 SDK from service team has higher priority.
- The smaller the gap between Track 1 SDK version and Track 2 SDK version, the higher priority.
- The more frequent release, the higher priority.
- If Track 1 SDK is in preview (0.x.x or x.x.xrc), the lower priority.
- Extenison has lower priority.

## Here is the proposed roadmap for managment plane migration. (Total ~60 CLI modules: 6 completed and ~60 extensions: 20 completed.)

- To meet CAE requirements (`CAE support` column is `Yes` in the table below), 
  - 12 services need to be migrated by the end of 0/30/2021.
  - 4 services need to be migrated by the end of 06/30/2021.
- Totally 18 services need to be migrated by the end of 06/30/2021.
- To achieve this goal:
  - We need notify service teams ahead of time so that they have sufficient time to migrate.
  - If there is no Track 2 SDK for those services, we'll release stable Track 2 SDK version for them before 03/11/2021.
  - If the Track 2 SDK for those services is in preview, we'll release stable Track 2 SDK version for them before 02/11/2021.

| Module   | CAE support | Migration Status | ETA | Coordinator Team |Latest Track 2 SDK Status | Latest Track 1 SDK status  | Release frequency | CLI Module or Extension |
| --------- |:-------------:| :-----:|:-----:|:--:|:--:|:--:|:--:|:--:|
|**Phase 1: Compute, Network, Storage**  |  |  | |  | |  ||||
| Network     |Yes| **Completed** | 04/30/2021 | Yong |GA (17.0.0) | GA (13.0.0) | High (Once a month)| Module |
| Storage     |Yes|**Completed** | 04/30/2021 | Yong |GA (16.0.0) | GA (11.2.0) | Medium (Once two months) | Module |
| Monitor     |Yes |**Completed** | 04/30/2021 |Yong|Monitor: GA (2.0.0)<br> LogAnalytics: GA (8.0.0) | Monitor: Preview (0.12.0)<br> LogAnalytics: GA (2.0.0) | Medium (Once two months) | Module |
| CosmosDB   | Yes |**Completed** | 04/30/2021 |Yong|GA (6.0.0) | Preview (2.0.0rc1) |  Medium (Once two months) |Module|
| CDN   | Yes |**Completed** | 04/30/2021 |Yong|GA (10.0.0) | GA (6.0.0) | Low (Once half year) | Module |
| NetAppFiles |  Yes |**Completed** | 04/30/2021 |Yong|GA (1.0.0) | Preview (0.15.0) | Medium (Once two months) | Module|
| Resource   | Yes |**Completed** | 04/30/2021 |Yong |GA (15.0.0) | GA (12.0.0) | Medium (Once two months) | Module |
| DNS |  Yes |**Completed** | 04/30/2021 |Yong|Preview (8.0.0b1) | GA (3.0.0) | Medium (Once two months) | Module|
| PrivateDNS | Yes | **Completed** | 04/30/2021 |Yong|Preview (1.0.0b1) | Preview (0.1.0) |N/A | Module |
| Application-Insights   |Yes | **Completed** | 04/30/2021 |Yong|GA (1.0.0) | Vendored_Preview (0.2.0) | N/A | Extension |
| Firewall   |Yes| **Completed** | 04/30/2021 |Yong| Network: GA (17.0.0) | Network: Vendored_GA (13.0.0) | N/A | Extension |
| Front-door   | Yes | **Completed** | 04/30/2021 |Yong|Preview (1.0.0b1) | Vendored_Preview (0.3.1) | N/A | Extension |
| VirtualWan   | Yes| **Completed** | 04/30/2021 |Yong|N/A |Vendored_Preview (0.1.0) | N/A | Extension |
| Compute     | Yes|**Completed** | 04/30/2021 |Catherine|GA (18.0.0) | GA (14.0.0) | High (Once a month) | Module |
| KeyVault    | Yes|**Completed** | 04/30/2021 |Catherine|GA (8.0.0) | GA (2.2.0) | Medium (Once three months) | Module |
| AppService   |  Yes | **Completed** | 04/30/2021 |Catherine|GA (1.0.0) | Preview (0.48.0) | Medium (Once three months) | Module |
|**Phase 2: Management&Governance&others** |  |  | |  | |  ||||
| CostManagement   | Yes | **Completed** | 06/30/2021 |Yong|Vendored_GA (1.2.0) | N/A | N/A | Extension |
| RDBMS |  Yes|**Completed** | 06/30/2021 |Yong|GA (8.0.0) | Preview (3.1.0rc1) | Medium (Once two months) | Module |
| DataFactory   | Yes | **Completed** | 06/30/2021 |Catherine|Vendored_SDK | N/A | N/A | Extension |
| SQL   | No |**In progress** | 06/30/2021 |Yong|GA (1.0.0) | Preview (0.25.0) | Medium (Once two months) | Module |
| ACS   |  Yes |Not Started | 06/30/2021 |Catherine|ContainerService: GA (14.0.0)<br> ContainerInstance: GA (7.0.0) | ContainerService: GA (11.0.0)<br> ContainerInstance: GA (2.0.0) | Medium (Once two months) | Module |
| ACR   | Yes |Not Started | 06/30/2021 |Catherine|Preview (8.0.0b1) | Preview (3.0.0rc16) | Medium (Once two months) | Module |
| ServiceBus   | Yes |**Completed** | 06/30/2021 |Catherine|GA (6.0.0) | GA (1.0.0) | Medium (Once four months) | Module |
| EventGrid | Yes |Not Started | 06/30/2021 |Catherine| GA (8.0.0) | Preview (3.0.0rc8) | Medium (Once three months) | Module |
| HDInsight | Yes |Not Started | 06/30/2021 |Catherine| GA (7.0.0) | GA (2.1.0) | Medium (Once two months) | Module |
| Kusto |  Yes |Not Started | 06/30/2021 |Catherine|Preview (1.0.0b1) | Preview (0.10.0) | Medium (Once two months | Module |
|**Phase 3** |  | 33 modules (Yong: 17, Catherie: 16), 51 extensions (Yong: 26, Catherie: 25)  | | | |  |||
| NatGateway || **Completed** | N/A |Yong|Network: GA (8.0.0) | Network: GA (2.2.0) | Use Network package| Module |
| Search |  |**Completed** | N/A |Yong|GA (8.0.0) | GA (3.0.0) | Low (Once a year) | Module |
| Billing (CLI own)  |  |Not Started | N/A|Yong|Preview (6.0.0b1) | GA (1.0.0) | Low (Once a year) | Module |
| DataBoxEdge (CLI own) |  |Not Started | N/A|Yong|Preview (1.0.0b1) | Preview (0.2.0) | Low (Once a year) | Module |
| DLA (CLI own)|  | Not Started | N/A |Yong|N/A | DataLakeAnalytics: Preview (0.6.0) | | Module |
| DLS (CLI own)|  | Not Started | N/A (Will incorporate into storage SDK) |Yong|N/A | DataLakeStore: Preview (0.5.0) | | Module |
| Role (CLI own)  | |Not Started | N/A |Yong| Authorization: GA (1.0.0)<br>MSI: N/A | Authorization: Preview (0.61.0)<br>MSI: GA (1.0.0) | Low (Once a year) | Module |
| Synapse |  |Not Started | N/A |Yong|Preview (1.0.0b1) | Preview (0.6.0) | Medium (Once two months) | Module |
| SQLVM |  |Not Started | N/A |Yong|N/A| SQLVirtualMachine: Preview (0.5.0) | N/A | Module |
| Security |  |Not Started | N/A |Yong|GA (1.0.0) | Preview (0.6.0) | Medium (Once three months) | Module |
| EventHub   |  |Not Started | N/A |Yong|GA (8.0.0) | GA (4.2.0) | Low (Once a year) | Module |
| SignalR | |Not Started | N/A |Yong |Preview (1.0.0b1) | Preview (0.4.0) | Low (Once half year) | Module |
| PolicyInsights | |Not Started | N/A |Yong| GA (1.0.0) | Preview (0.6.0) | Low (Once half year) | Module |
| DMS |  |Not Started | N/A |Yong|DataMigration: Preview (9.0.0b1) | DataMigration: GA (4.1.0) | Low (Once a year) | Module |
| Redis   | |Not Started | N/A |Yong|GA (12.0.0) | Preview (7.0.0rc2) | Low (Once a year) | Module |
| DeploymentManager |  |Not Started | N/A|Yong|Preview (1.0.0b1) | Preview (0.2.0) | Low (Once two years) | Module |
| ManagedServices | |Not Started | N/A|Yong| Preview (6.0.0b1) | GA (1.0.0) | Low (Once two years) | Module |
| IoT | | Not Started | N/A |Yong|IoTHub: GA (1.0.0) <br> IoTCentral: N/A <br> IoTHubProvisioningServices: N/A | IoTHub: Preview (0.12.0) <br> IoTCentral: GA (4.0.0) <br> IoTHubProvisioningServices: Preview (0.2.0)| | Module |
| Relay |  |Not Started | N/A|Yong|GA (1.0.0) | Preview (0.2.0) | Low (Once two years) | Module |
| AppConfiguration  |  |**Completed** | N/A |Catherine|GA (1.0.1) | Preview (0.6.0) | Medium (Once three months) | Module |
| Container   |   |Not Started | N/A |Catherine| ContainerInstance: GA (7.0.0) |  ContainerInstance: GA (2.0.0) | Medium (Once two months) | Module |
| Batch   |  |**In progress** | N/A |Catherine|GA (15.0.0) | GA (9.0.0) | Low (Once half year) | Module |
| ServiceFabric |  |**Completed** | N/A|Catherine|Preview (1.0.0) | Preview (0.5.0) | Low (Once a year) | Module |
| ContainerInstance |  |Not Started | N/A |Catherine|GA (7.0.0) | GA (2.0.0) | Low (Once a year) | Module |
| BotService   |  |Not Started | N/A|Catherine|Preview (1.0.0b1) | Preview (0.2.0) | Low (Once two years) | Module |
| Maps |  |Not Started | N/A|Catherine|Preview (1.0.0b1) | Preview (0.1.0) | Low (Once three years) | Module |
| Backup   | |**In progress** | N/A|Catherine|RecoveryServices: GA (1.0.0)<br> RecoveryServicesBackup: N/A | RecoveryServices: Preview (0.6.0)<br> RecoveryServicesBackup: Preview (0.11.0) | Low (Once half year) | Module |
| BatchAI   | | Not Started | N/A |Catherine |N/A | GA (2.0.0) | | Module |
| Lab  | |Not Started | N/A |Catherine|DevTestLabs: GA (9.0.0) | DevTestLabs: GA (4.0.0) | Low (Once half year) | Module |
| Reservations |  |Not Started | N/A |Catherine|Preview (1.0.0b1) | Preview (0.8.0) | Low (Once half year) | Module |
| CognitiveServices | |Not Started | N/A |Catherine| GA (11.0.0) | GA (6.3.0) | Low (Once half year) | Module |
| Advisor   |  |Not Started | N/A |Catherine|GA (9.0.0) | GA (4.0.0) | Low (once eight months) | Module |
| AMS   |  |Not Started | N/A |Catherine|Media: Preview (7.0.0b1) |Media: GA (3.0.0) | Low (Once a year) | Module |
| Consumption |  |Not Started | N/A |Catherine|GA (8.0.0) | GA (3.0.0) | Low (Once a year) | Module |
| APIM   | |Not Started | N/A |Catherine|APIManagement: GA (1.0.0) | APIManagement: Preview (0.2.0) | Low (Once a year) | Module |
| ARO   |  |Not Started | N/A|Catherine|RedhatOpenShift: Preview (1.0.0b1) | RedhatOpenShift: Preview (0.1.0) | Low (Once a year) | Module |
| HealthCareAPIs   |  | **Completed** | N/A |Yong|Vendored_Preview (0.3.0) | N/A | N/A | Extension |
| Communication   |  | **Completed** | N/A |Yong|Vendored_SDK | N/A | N/A | Extension |
| Footprint   |  | **Completed** | N/A |Yong|Vendored_SDK | N/A | N/A | Extension |
| Logic   | | **Completed** | N/A |Yong|N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| Maintenance   | | **Completed** | N/A|Yong|N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| Peering   | | **Completed** | N/A| Yong|N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| Portal  | | **Completed** | N/A |Yong|N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| Stack-HCI   | | **Completed** | N/A |Yong|N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| RedisEnterprise   | | **Completed** | N/A |Yong|N/A | Vendored_SDK | N/A | Extension |
| Monitor-Control-Service   | | **Completed** | N/A |Yong|N/A | Vendored_SDK | N/A | Extension |
| AD | | **Completed** | N/A |Yong|N/A | Vendored_SDK | N/A | Extension |
| Custom-Providers (CLI own) | | Not Started | N/A |Yong|N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| Mixed-Reality (CLI own)  | | Not Started | N/A|Yong|N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| Resource-Graph (CLI own)  | | Not Started | N/A |Yong|N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| DataBox (CLI own)  | | Not Started | N/A |Yong|N/A | Vendored_Preview (0.2.0) | N/A | Extension |
| HPC-Cache (CLI own)  || Not Started | N/A |Yong |N/A | Vendored_Preview (0.2.0 | N/A | Extension |
| Log-Analytics (CLI own)  | | Not Started | N/A|Yong|N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| PowerbiDedicated (CLI own)  | | Not Started | N/A |Yong|N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| StorageSync (CLI own)  | | Not Started | N/A |Yong|N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| Storage-Preview (CLI own)  | | Not Started | N/A |Yong|N/A | Vendored_SDK | N/A | Extension |
| Storage-Blob-Preview (CLI own)  | | Not Started | N/A |Yong|N/A | Vendored_SDK | N/A | Extension |
| DB-Up (CLI own)  | | Not Started | N/A |Yong|N/A | RDBMS: Vendored_GA (1.5.0) <br> SQL: Vendored_Preview (0.11.0) | N/A | Extension |
| TimeSeriesInsights (CLI own)  | | Not Started | N/A |Yong|N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| Scheduled-Query (CLI own)  | | Not Started | N/A|Yong |N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| Log-Analytics-Solution (CLI own)  | | Not Started | N/A|Yong |N/A | Vendored_SDK | N/A | Extension |
| Connection-Monitor-Preview (CLI own)  | | Not Started | N/A|Yong |N/A | Vendored_SDK | N/A | Extension |
| BlockChain (CLI own)   | | Not Started | N/A| Yong|N/A | Vendored_GA (2.0.0) | N/A | Extension |
| Express-Route-Cross-Connection (CLI own)  || Not Started | N/A|Yong | N/A | Network: Vendored_SDK | N/A | Extension |
| Ip-Group (CLI own) | | Not Started | N/A |Yong|N/A | Network: Vendored_SDK | N/A | Extension |
| Virtual-Network-Tap (CLI own)  | | Not Started | N/A|Yong |N/A | Network: Vendored_SDK | N/A | Extension |
| Internet-Analyzer (CLI own)  || Not Started | N/A |Yong| N/A | Frontdoor: Vendored_Preview (0.3.0) | N/A | Extension |
| DMS-Preview   | | Not Started | N/A |Yong|N/A | Vendored_GA (4.0.0) | N/A | Extension |
| CosmosDB-Preview   | | Not Started | N/A |Yong|N/A | Vendored_SDK | N/A | Extension |
| Hack   | | Not Started | N/A |Yong|N/A | Call AppService, CosmosDB, RDBMS, CognitiveServices | N/A | Extension |
| ManagementPartner   | | Not Started | N/A| Yong|N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| RDBMS-Connect   | | Not Started | N/A|Yong |N/A | Vendored_SDK | N/A | Extension |
| NetAppFiles-Preview (Replace by NetApp in core?)   | | Not Started | N/A|Yong |N/A | Vendored_SDK | N/A | Extension |
| Account   | | **Completed** | N/A |Catherine|Subscription: Vendored_Preview (0.5.0) | N/A | N/A | Extension |
| Attestation   |  | **Completed** | N/A |Catherine|Vendored_SDK | N/A | N/A | Extension |
| Automation   |  | **Completed** | N/A |Catherine|Vendored_SDK | N/A | N/A | Extension |
| ConnectedMachine   |  | **Completed** | N/A|Catherine|Vendored_SDK | N/A | N/A | Extension |
| DataDog   |  | **Completed** | N/A |Catherine|Vendored_SDK | N/A | N/A | Extension |
| DataShare   |  | **Completed** | N/A |Catherine|Vendored_SDK | N/A | N/A | Extension |
| DesktopVirtualization   |  | **Completed** | N/A |Catherine|Vendored_Preview (0.2.0) | N/A | N/A | Extension |
| GuestConfig   |  | **Completed** | N/A |Catherine|Vendored_SDK | N/A | N/A | Extension |
| Hardware-Secutiry-Modules   |  | **Completed** | N/A| Catherine|Vendored_SDK | N/A | N/A | Extension |
| Import-Export   |  | **Completed** | N/A |Catherine|Vendored_SDK | N/A | N/A | Extension |
| Resource-Mover   |  | **Completed** | N/A |Catherine|Vendored_SDK | N/A | N/A | Extension |
| ProviderHub   |  | **Completed** | N/A |Catherine|Vendored_SDK | N/A | N/A | Extension |
| OffAzure   |  | **Completed** | N/A |Catherine|Vendored_SDK | N/A | N/A | Extension |
| HealthBot   |  | **Completed** | N/A |Catherine|Vendored_SDK | N/A | N/A | Extension |
| Confluent   |  | **Completed** | N/A |Catherine|Vendored_SDK | N/A | N/A | Extension |
| ACRTransfer   |  | **Completed** | N/A |Catherine|Vendored_SDK | N/A | N/A | Extension |
| AlertsManagement (CLI own)  | | Not Started | N/A| Catherine|N/A | Vendored_Preview (0.2.0rc2) | N/A | Extension |
| BluePrint (CLI own)  | | Not Started | N/A| Catherine|N/A | Vendored_Preview (2018-11-01-preview) | N/A | Extension |
| CloudService (CLI own)  | | Not Started | N/A|Catherine |N/A | N/A | N/A | Extension |
| Notification-Hub (CLI own)  | | Not Started | N/A| Catherine|N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| SecurityInsight (CLI own)  | | Not Started | N/A |Catherine|N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| DataBricks (CLI own)  | | Not Started | N/A|Catherine|N/A | Vendored_Preview (0.1.0 | N/A | Extension |
| Stream-Analytics (CLI own)  | | Not Started | N/A |Catherine|N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| Swiftlet (CLI own)  | | Not Started | N/A |Catherine|N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| Image-Copy (CLI own)  | | Not Started | N/A|Catherine |N/A | Vendored_SDK | N/A | Extension |
| AKS-Preview  | | Not Started | N/A |Catherine|N/A | ContainerService: Vendored_GA (0.2.0) | N/A | Extension |
| ConnectedK8S   | | Not Started | N/A |Catherine|N/A | Vendored_Preview (0.1.1) | N/A | Extension |
| K8S-Configuration (Deprecate K8SConfiguration)  | | Not Started | N/A|Catherine|N/A | Vendored_SDK) | N/A | Extension |
| K8S-Extension  | | Not Started | N/A|Catherine|N/A | Vendored_SDK) | N/A | Extension |
| Mesh   | | Not Started | N/A |Catherine|N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| SpringCloud   | | Not Started | N/A |Catherine|N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| Support   | | Not Started | N/A |Catherine|N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| VM-Repair   | | Not Started | N/A |Catherine|N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| VMWare   | | Not Started | N/A |Catherine|N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| WebApp   | | Not Started | N/A|Catherine |N/A | N/A | N/A | Extension |
| SSH   | | Not Started | N/A|Catherine |N/A | N/A | N/A | Extension |
| Quantum   | | Not Started | N/A|Catherine |N/A | Vendored_SDK | N/A | Extension |
| CodeSpaces   | | Not Started | N/A|Catherine |N/A | Vendored_SDK | N/A | Extension |
| Dev-Spaces   | | Not Started | N/A|Catherine |N/A | N/A | N/A | Extension |
| Cli-Translator   | | Not Started | N/A|Catherine |N/A | N/A | N/A | Extension |
| AEM   | | Not Started | N/A|Catherine |N/A | N/A | N/A | Extension |
| *Below services don't exist in CLI repo*|  |  | |  | |  ||||
| Azure Security Center |  Yes | | 06/30/2021 | |  |  |  ||
| Sentinel|  Yes | | 06/30/2021 | |  |  |  ||
| Azure Data Explorer|  Yes | | 06/30/2021 | |  |  |  ||
| Azure DevOps|  Yes | | 06/30/2021 | |  |  |  ||
| Azure Machine Learning|  Yes | | 06/30/2021 | |  |  |  ||