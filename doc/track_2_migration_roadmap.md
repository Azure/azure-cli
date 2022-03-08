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

## Here is the proposed roadmap for managment plane migration. (Total 60 CLI modules and 78 extensions)

- To meet CAE requirements (`CAE support` column is `Yes` in the table below), 
  - 12 services need to be migrated by the end of 0/30/2021.
  - 4 services need to be migrated by the end of 06/30/2021.
- Totally 18 services need to be migrated by the end of 06/30/2021.
- To achieve this goal:
  - We need notify service teams ahead of time so that they have sufficient time to migrate.

| Module   | CAE support | Migration Status | ETA |Latest Track 2 SDK Status | Latest Track 1 SDK status  | Release frequency | CLI Module or Extension |
| --------- |:-------------:| :-----:|:-----:|:--:|:--:|:--:|:--:|
|**Phase 1: Compute, Network, Storage**  |  |  | |  | |  ||||
| Network     |Yes| **Completed** | 04/30/2021 |GA (17.0.0) | GA (13.0.0) | High (Once a month)| Module |
| Storage     |Yes|**Completed** | 04/30/2021 |GA (16.0.0) | GA (11.2.0) | Medium (Once two months) | Module |
| Monitor     |Yes |**Completed** | 04/30/2021 |Monitor: GA (2.0.0)<br> LogAnalytics: GA (8.0.0) | Monitor: Preview (0.12.0)<br> LogAnalytics: GA (2.0.0) | Medium (Once two months) | Module |
| CosmosDB   | Yes |**Completed** | 04/30/2021 |GA (6.0.0) | Preview (2.0.0rc1) |  Medium (Once two months) |Module|
| CDN   | Yes |**Completed** | 04/30/2021 |GA (10.0.0) | GA (6.0.0) | Low (Once half year) | Module |
| NetAppFiles |  Yes |**Completed** | 04/30/2021 |GA (1.0.0) | Preview (0.15.0) | Medium (Once two months) | Module|
| Resource   | Yes |**Completed** | 04/30/2021  |GA (15.0.0) | GA (12.0.0) | Medium (Once two months) | Module |
| DNS |  Yes |**Completed** | 04/30/2021 |Preview (8.0.0b1) | GA (3.0.0) | Medium (Once two months) | Module|
| PrivateDNS | Yes | **Completed** | 04/30/2021 |Preview (1.0.0b1) | Preview (0.1.0) |N/A | Module |
| Application-Insights   |Yes | **Completed** | 04/30/2021 |GA (1.0.0) | Vendored_Preview (0.2.0) | N/A | Extension |
| Firewall   |Yes| **Completed** | 04/30/2021 | Network: GA (17.0.0) | Network: Vendored_GA (13.0.0) | N/A | Extension |
| Front-door   | Yes | **Completed** | 04/30/2021 |Preview (1.0.0b1) | Vendored_Preview (0.3.1) | N/A | Extension |
| VirtualWan   | Yes| **Completed** | 04/30/2021 |N/A |Vendored_Preview (0.1.0) | N/A | Extension |
| Compute     | Yes|**Completed** | 04/30/2021 |GA (18.0.0) | GA (14.0.0) | High (Once a month) | Module |
| KeyVault    | Yes|**Completed** | 04/30/2021 |GA (8.0.0) | GA (2.2.0) | Medium (Once three months) | Module |
| AppService   |  Yes | **Completed** | 04/30/2021 |GA (1.0.0) | Preview (0.48.0) | Medium (Once three months) | Module |
|**Phase 2: Management&Governance&others** |  |  | |  | |  ||||
| CostManagement   | Yes | **Completed** | 06/30/2021 |Vendored_GA (1.2.0) | N/A | N/A | Extension |
| RDBMS |  Yes|**Completed** | 06/30/2021 |GA (8.0.0) | Preview (3.1.0rc1) | Medium (Once two months) | Module |
| DataFactory   | Yes | **Completed** | 06/30/2021 |Vendored_SDK | N/A | N/A | Extension |
| ServiceBus   | Yes |**Completed** | 06/30/2021 |GA (6.0.0) | GA (1.0.0) | Medium (Once four months) | Module |
| EventGrid | Yes |**Completed** | 06/30/2021 | GA (8.0.0) | Preview (3.0.0rc8) | Medium (Once three months) | Module |
| HDInsight | Yes |**Completed** | 06/30/2021 | GA (7.0.0) | GA (2.1.0) | Medium (Once two months) | Module |
| Kusto |  Yes |**Completed** | 06/30/2021 |Preview (1.0.0b1) | Preview (0.10.0) | Medium (Once two months | Module |
| ACS   |  Yes |**Completed** | 06/30/2021 |ContainerService: GA (14.0.0)<br> ContainerInstance: GA (7.0.0) | ContainerService: GA (11.0.0)<br> ContainerInstance: GA (2.0.0) | Medium (Once two months) | Module |
| SQL   | No |**Completed** | 06/30/2021 |GA (1.0.0) | Preview (0.25.0) | Medium (Once two months) | Module |
| ACR   | Yes |**Completed** | 06/30/2021 |Preview (8.0.0b1) | Preview (3.0.0rc16) | Medium (Once two months) | Module |
|**Phase 3** |  |  | | | |  |||
| NatGateway || **Completed** | N/A |Network: GA (8.0.0) | Network: GA (2.2.0) | Use Network package| Module |
| Search |  |**Completed** | N/A |GA (8.0.0) | GA (3.0.0) | Low (Once a year) | Module |
| Synapse |  |**Completed** | N/A |Preview (1.0.0b1) | Preview (0.6.0) | Medium (Once two months) | Module |
| AppConfiguration  |  |**Completed** | N/A |GA (1.0.1) | Preview (0.6.0) | Medium (Once three months) | Module |
| SignalR | |**Completed** | N/A  |Preview (1.0.0b1) | Preview (0.4.0) | Low (Once half year) | Module |
| Batch   |  |**Completed** | N/A |GA (15.0.0) | GA (9.0.0) | Low (Once half year) | Module |
| Backup   | |**Completed** | N/A|RecoveryServices: GA (1.0.0)<br> RecoveryServicesBackup: N/A | RecoveryServices: Preview (0.6.0)<br> RecoveryServicesBackup: Preview (0.11.0) | Low (Once half year) | Module |
| Advisor   |  |**Completed** | N/A |GA (9.0.0) | GA (4.0.0) | Low (once eight months) | Module |
| Maps |  |**Completed** | N/A|Preview (1.0.0b1) | Preview (0.1.0) | Low (Once three years) | Module |
| BatchAI (CLI own)  | | **Completed** | N/A  |N/A | GA (2.0.0) | | Module |
| Billing (CLI own)  |  |**Completed** | N/A|Preview (6.0.0b1) | GA (1.0.0) | Low (Once a year) | Module |
| PolicyInsights | |**Completed** | N/A | GA (1.0.0) | Preview (0.6.0) | Low (Once half year) | Module |
| DMS |  |**Completed** | N/A |DataMigration: Preview (9.0.0b1) | DataMigration: GA (4.1.0) | Low (Once a year) | Module |
| Redis   | |**Completed** | N/A |GA (12.0.0) | Preview (7.0.0rc2) | Low (Once a year) | Module |
| CognitiveServices | |**Completed** | N/A | GA (11.0.0) | GA (6.3.0) | Low (Once half year) | Module |
| SQLVM |  |**Completed** | N/A |N/A| SQLVirtualMachine: Preview (0.5.0) | N/A | Module |
| IoT | | **Completed** | N/A |IoTHub: GA (1.0.0) <br> IoTCentral: N/A <br> IoTHubProvisioningServices: N/A | IoTHub: Preview (0.12.0) <br> IoTCentral: GA (4.0.0) <br> IoTHubProvisioningServices: Preview (0.2.0)| | Module |
| Security |  |**Completed** | N/A |GA (1.0.0) | Preview (0.6.0) | Medium (Once three months) | Module |
| Container   |   |**Completed** | N/A | ContainerInstance: GA (7.0.0) |  ContainerInstance: GA (2.0.0) | Medium (Once two months) | Module |
| DataBoxEdge (CLI own) |  |**Completed** | N/A|Preview (1.0.0b1) | Preview (0.2.0) | Low (Once a year) | Module |
| AMS   |  |**Completed** | N/A |Media: Preview (7.0.0b1) |Media: GA (3.0.0) | Low (Once a year) | Module |
| IoT | | **Completed** | N/A |IoTHub: GA (1.0.0) <br> IoTCentral: N/A <br> IoTHubProvisioningServices: N/A | IoTHub: Preview (0.12.0) <br> IoTCentral: GA (4.0.0) <br> IoTHubProvisioningServices: Preview (0.2.0)| | Module |
| ARO   |  |**Completed** | N/A|RedhatOpenShift: Preview (1.0.0b1) | RedhatOpenShift: Preview (0.1.0) | Low (Once a year) | Module |
| DeploymentManager |  |**Completed (deprecated)**  | N/A|Preview (1.0.0b1) | Preview (0.2.0) | Low (Once two years) | Module |
| Reservations |  |**Completed (too old)** | N/A |Preview (1.0.0b1) | Preview (0.8.0) | Low (Once half year) | Module |
| Consumption |  |**Completed (too old)** | N/A |GA (8.0.0) | GA (3.0.0) | Low (Once a year) | Module |
| DLA (CLI own)|  | **Completed (too old)** | N/A |N/A | DataLakeAnalytics: Preview (0.6.0) | | Module |
| DLS (CLI own)|  | **Completed (too old)** | N/A (Will incorporate into storage SDK) |N/A | DataLakeStore: Preview (0.5.0) | | Module |
| ManagedServices | |**Completed (too old)**| N/A| Preview (6.0.0b1) | GA (1.0.0) | Low (Once two years) | Module |
| BotService   |  |**Block by service team** | N/A|Preview (1.0.0b1) | Preview (0.2.0) | Low (Once two years) | Module |
| APIM   | |**Completed**  | N/A |APIManagement: GA (1.0.0) | APIManagement: Preview (0.2.0) | Low (Once a year) | Module |
| ServiceFabric |  |***Completed** | N/A|Preview (1.0.0) | Preview (0.5.0) | Low (Once a year) | Module |
| EventHub   |  |**Completed**  | N/A |GA (8.0.0) | GA (4.2.0) | Low (Once a year) | Module |
| Relay |  |**On demand (no new feature)** | N/A|GA (1.0.0) | Preview (0.2.0) | Low (Once two years) | Module |
| Role (CLI own)  | |**On demand (no new feature)** | N/A | Authorization: GA (1.0.0)<br>MSI: N/A | Authorization: Preview (0.61.0)<br>MSI: GA (1.0.0) | Low (Once a year) | Module |
| Lab  | |**On demand (no new feature)** | N/A |DevTestLabs: GA (9.0.0) | DevTestLabs: GA (4.0.0) | Low (Once half year) | Module |
| HealthCareAPIs   |  | **Completed** | N/A |Vendored_Preview (0.3.0) | N/A | N/A | Extension |
| Communication   |  | **Completed** | N/A |Vendored_SDK | N/A | N/A | Extension |
| Footprint   |  | **Completed** | N/A |Vendored_SDK | N/A | N/A | Extension |
| Logic   | | **Completed** | N/A |N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| Maintenance   | | **Completed** | N/A|N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| Peering   | | **Completed** | N/A|N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| Portal  | | **Completed** | N/A |N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| Stack-HCI   | | **Completed** | N/A |N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| RedisEnterprise   | | **Completed** | N/A |N/A | Vendored_SDK | N/A | Extension |
| Monitor-Control-Service   | | **Completed** | N/A |N/A | Vendored_SDK | N/A | Extension |
| AD | | **Completed** | N/A |N/A | Vendored_SDK | N/A | Extension |
| Account   | | **Completed** | N/A |Subscription: Vendored_Preview (0.5.0) | N/A | N/A | Extension |
| Attestation   |  | **Completed** | N/A |Vendored_SDK | N/A | N/A | Extension |
| Automation   |  | **Completed** | N/A |Vendored_SDK | N/A | N/A | Extension |
| ConnectedMachine   |  | **Completed** | N/A|Vendored_SDK | N/A | N/A | Extension |
| DataDog   |  | **Completed** | N/A |Vendored_SDK | N/A | N/A | Extension |
| DataShare   |  | **Completed** | N/A |Vendored_SDK | N/A | N/A | Extension |
| DesktopVirtualization   |  | **Completed** | N/A |Vendored_Preview (0.2.0) | N/A | N/A | Extension |
| GuestConfig   |  | **Completed** | N/A |Vendored_SDK | N/A | N/A | Extension |
| Hardware-Secutiry-Modules   |  | **Completed** | N/A|Vendored_SDK | N/A | N/A | Extension |
| Import-Export   |  | **Completed** | N/A |Vendored_SDK | N/A | N/A | Extension |
| Resource-Mover   |  | **Completed** | N/A |Vendored_SDK | N/A | N/A | Extension |
| ProviderHub   |  | **Completed** | N/A |Vendored_SDK | N/A | N/A | Extension |
| OffAzure   |  | **Completed** | N/A |Vendored_SDK | N/A | N/A | Extension |
| HealthBot   |  | **Completed** | N/A |Vendored_SDK | N/A | N/A | Extension |
| Confluent   |  | **Completed** | N/A |Vendored_SDK | N/A | N/A | Extension |
| ACRTransfer   |  | **Completed** | N/A |Vendored_SDK | N/A | N/A | Extension |
| Custom-Providers (CLI own) | | **Completed** | N/A |N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| Mixed-Reality (CLI own)  | | **Completed** | N/A|N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| Resource-Graph (CLI own)  | | **Completed** | N/A |N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| DataBox (CLI own)  | | **Completed** | N/A |N/A | Vendored_Preview (0.2.0) | N/A | Extension |
| HPC-Cache (CLI own)  || **Completed** | N/A  |N/A | Vendored_Preview (0.2.0 | N/A | Extension |
| TimeSeriesInsights (CLI own)  | | **Completed** | N/A |N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| BlockChain (CLI own)   | | **Completed** | N/A|N/A | Vendored_GA (2.0.0) | N/A | Extension |
| Internet-Analyzer (CLI own)  || **Completed** | N/A | N/A | Frontdoor: Vendored_Preview (0.3.0) | N/A | Extension |
| CosmosDB-Preview   | | **Completed** | N/A |N/A | Vendored_SDK | N/A | Extension |
| CloudService (CLI own)  | | **Completed**| N/A |N/A | N/A | N/A | Extension |
| SecurityInsight (CLI own)  | | **Completed** | N/A |N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| Swiftlet (CLI own)  | | **Completed** | N/A |N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| Storage-Preview (CLI own)  | | **Completed** | N/A |N/A | Vendored_SDK | N/A | Extension |
| Storage-Blob-Preview (CLI own)  | | **Completed** | N/A |N/A | Vendored_SDK | N/A | Extension |
| Scheduled-Query (CLI own)  | | **Completed** | N/A |N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| PowerbiDedicated (CLI own)  | | **Completed** | N/A |N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| RDBMS-Connect   | | **Completed** | N/A |N/A | Vendored_SDK | N/A | Extension |
| AKS-Preview  | | **Completed** | N/A |N/A | ContainerService: Vendored_GA (0.2.0) | N/A | Extension |
| AEM   | | **Completed** | N/A |N/A | N/A | N/A | Extension |
| Quantum   | | **Completed** | N/A |N/A | Vendored_SDK | N/A | Extension |
| StorageSync (CLI own)  | | **Completed** | N/A |N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| SpringCloud   | | **Completed** | N/A |N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| VMWare   | | **Completed** | N/A |N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| ConnectedK8S   | | **Completed** | N/A |N/A | Vendored_Preview (0.1.1) | N/A | Extension |
| BluePrint (CLI own)  | | **Completed** | N/A|N/A | Vendored_Preview (2018-11-01-preview) | N/A | Extension |
| K8S-Configuration  | | **Completed**| N/A|N/A | Vendored_SDK) | N/A | Extension |
| K8S-Extension  | | **Completed** | N/A|N/A | Vendored_SDK) | N/A | Extension |
| DMS-Preview   | | **Completed** | N/A |N/A | Vendored_GA (4.0.0) | N/A | Extension |
| Connection-Monitor-Preview (CLI own)  | | **Completed (already moved to CLI module)** | N/A |N/A | Vendored_SDK | N/A | Extension |
| Dev-Spaces   | | **Completed (No SDK)** | N/A |N/A | N/A | N/A | Extension |
| Cli-Translator   | | **Completed (No SDK)** | N/A |N/A | N/A | N/A |
| Image-Copy (CLI own)  | | **Completed (No SDK)** | N/A |N/A | Vendored_SDK | N/A | Extension |
| SSH   | | **Completed (no SDK)** | N/A |N/A | N/A | N/A | Extension |
| VM-Repair  | | **Completed (No SDK)**| N/A |N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| NetAppFiles-Preview   | | **Completed (deprecated)** | N/A |N/A | Vendored_SDK | N/A | Extension |
| DB-Up (CLI own)  | | **Completed (deprecated)** | N/A |N/A | RDBMS: Vendored_GA (1.5.0) <br> SQL: Vendored_Preview (0.11.0) | N/A | Extension |
| Mesh   | | **Completed (deprecated)** | N/A |N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| Hack   | | **Completed (deprecated)** | N/A |N/A | Call AppService, CosmosDB, RDBMS, CognitiveServices | N/A | Extension |
| Log-Analytics-Solution (CLI own)  | | **Completed (too old)** | N/A |N/A | Vendored_SDK | N/A | Extension |
| Express-Route-Cross-Connection (CLI own)  || **Completed (too old)** | N/A | N/A | Network: Vendored_SDK | N/A | Extension |
| Ip-Group (CLI own) | | **Completed (too old)** | N/A |N/A | Network: Vendored_SDK | N/A | Extension |
| Virtual-Network-Tap (CLI own)  | | **Completed (too old)**| N/A |N/A | Network: Vendored_SDK | N/A | Extension |
| AlertsManagement (CLI own)  | | **Completed (too old)** | N/A|N/A | Vendored_Preview (0.2.0rc2) | N/A | Extension |
| Notification-Hub (CLI own)  | | **Completed (too old)** | N/A|N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| DataBricks (CLI own)  | | **Completed (too old)** | N/A|N/A | Vendored_Preview (0.1.0 | N/A | Extension |
| Stream-Analytics (CLI own)  | | **Completed (too old)** | N/A |N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| CodeSpaces   | | **Completed (too old)** | N/A |N/A | Vendored_SDK | N/A | Extension |
| Support   | | **Completed (no new features)** | N/A |N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| ManagementPartner   | | **Completed (no new features)** | N/A|N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| Log-Analytics (CLI own)  | | **Completed (data plane)** | N/A|N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| WebApp   | | **On demand (no new feature)** | N/A |N/A | N/A | N/A | Extension |