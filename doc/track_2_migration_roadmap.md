# Track2 SDK Migration Roadmap
This document provides the roadmap for track2 SDK migration in Azure CLI. When you migrate your module to track2 SDK, you can go to [Track2 migration guidance](track_2_migration_guidance.md) to check how to migrate to track2 SDK.

## Why do we need migrate track1 SDK to track2 SDK in Azure CLI?
- Track1 SDK will be eventually deprecated sometime in the future. 
- Some new features will only be in track2 SDK in the future.

## Here are criteria to determine the priority of migration:
- On-demand for track2 SDK from CLI customers (such as LinkedIn) has higher priority.
- On-demand for track2 SDK from service team has higher priority.
- The smaller the gap between track1 version and track2 version, the higher priority.
- The more frequent release, the higher priority.
- If track1 is in preview (0.x.x or x.x.xrc), the lower priority.
- Extenison has lower priority.

## Here is the proposed roadmap for managment plane migration. (Total ~60 CLI modules: 6 completed and ~60 extensions: 20 completed.)

| Module   | CAE support | Migration Status | ETA | Latest Track2 SDK Status | Latest Track1 SDK status  | Release frequency | CLI Module or Extension |
| --------- |:-------------:| :-----:|:-----:|:--:|:--:|:--:|:--:|
|**Phase 1: Compute, Network, Storage** |  |  | |  | |  |||
| Network     |Yes| **Completed** | 04/31/2021 | GA (17.0.0) | GA (13.0.0) | High (Once a month)| Module |
| Storage     |Yes|**Completed** | 04/31/2021 | GA (16.0.0) | GA (11.2.0) | Medium (Once two months) | Module |
| Compute     | Yes|**Completed** | 04/31/2021 |GA (18.0.0) | GA (14.0.0) | High (Once a month) | Module |
| KeyVault    | Yes|**Completed** | 04/31/2021 |GA (8.0.0) | GA (2.2.0) | Medium (Once three months) | Module |
| Monitor     |Yes |**Completed** | 04/31/2021 |Monitor: GA (2.0.0)<br> LogAnalytics: GA (8.0.0) | Monitor: Preview (0.12.0)<br> LogAnalytics: GA (2.0.0) | Medium (Once two months) | Module |
| Resource   | Yes |Not Started | 04/31/2021 |GA (15.0.0) | GA (12.0.0) | Medium (Once two months) | Module |
| SQL   | No |Not Started | 04/31/2021 |GA (1.0.0) | Preview (0.25.0) | High (Once a month) | Module |
| Role   | No |Not Started | 04/31/2021 |GA (1.0.0) | Preview (0.61.0) | High (Once a month) | Module |
| AppService   |  Yes|Not Started | 04/31/2021 |GA (1.0.0) | Preview (0.48.0) | Medium (Once three months) | Module |
| ACS   |  Yes |Not Started | 04/31/2021 |ContainerService: GA (14.0.0)<br> ContainerInstance: GA (7.0.0) | ContainerService: GA (11.0.0)<br> ContainerInstance: GA (2.0.0) | Medium (Once two months) | Module |
| ACR   | Yes |Not Started | 04/31/2021 |Preview (8.0.0b1) | Preview (3.0.0rc16) | Medium (Once two months) | Module |
| CosmosDB   | Yes |Not Started | 04/31/2021 |GA (6.0.0) | Preview (2.0.0rc1) |  Medium (Once two months) |Module|
| ServiceBus   | Yes |Not Started | 04/31/2021 |GA (6.0.0) | GA (1.0.0) | Medium (Once four months) | Module |
| CDN   | Yes |Not Started | 04/31/2021 |Preview (10.0.0b1) | GA (6.0.0) | Low (Once half year) | Module |
| NetAppFiles |  Yes |Not Started | 04/31/2021 |Preview (1.0.0b1) | Preview (0.15.0) | Medium (Once two months) | Module|
| PrivateDNS | Yes | Not Started | 04/31/2021 |N/A | Preview (0.1.0) | | Module |
| ApplicationInsights   |Yes | Not Started | 04/31/2021 |N/A | Vendored_Preview (0.2.0) | N/A | Extension |
| Firewall   |Yes| Not Started | 04/31/2021 | N/A | Vendored_GA (13.0.0) | N/A | Extension |
| Frontdoor   | Yes | Not Started | 04/31/2021 |N/A | Vendored_Preview (0.3.1) | N/A | Extension |
|**Phase 2: Management&Governance&others** |  |  | |  | |  |||
| CostManagement   | Yes | **Completed** | 06/31/2021 |Vendored_GA (1.2.0) | N/A | N/A | Extension |
| DataFactory   | Yes | **Completed** | 06/31/2021 |Vendored_SDK | N/A | N/A | Extension |
| RDBMS |  Yes|Not Started | 06/31/2021 |GA (8.0.0) | Preview (3.1.0rc1) | Medium (Once two months) | Module |
| EventGrid | Yes |Not Started | 06/31/2021 | GA (8.0.0) | Preview (3.0.0rc8) | Medium (Once three months) | Module |
| HDInsight | Yes |Not Started | 06/31/2021 | GA (7.0.0) | GA (2.1.0) | Medium (Once two months) | Module |
| Kusto |  Yes |Not Started | 06/31/2021 |Preview (1.0.0b1) | Preview (0.10.0) | Medium (Once two months | Module |
|**Phase 3** |  |  | |  | |  |||
| NatGateway || **Completed** | N/A | Network: GA (8.0.0) | Network: GA (2.2.0) | Use Network package| Module |
| Synapse |  |Not Started | N/A |Preview (1.0.0b1) | Preview (0.6.0) | Medium (Once two months) | Module |
| AppConfiguration  |  |N/A | N/A |GA (1.0.1) | Preview (0.6.0) | Medium (Once three months) | Module |
| Security |  |Not Started | N/A |GA (1.0.0) | Preview (0.6.0) | Medium (Once three months) | Module |
| Batch   |  |Not Started | N/A |GA (14.0.0) | GA (9.0.0) | Low (Once half year) | Module |
| CognitiveServices | |Not Started | N/A | GA (11.0.0) | GA (6.3.0) | Low (Once half year) | Module |
| DevTestLabs | |Not Started | N/A |GA (9.0.0) | GA (4.0.0) | Low (Once half year) | Module |
| SignalR | |Not Started | N/A | Preview (1.0.0b1) | Preview (0.4.0) | Low (Once half year) | Module |
| PolicyInsights | |Not Started | N/A | GA (1.0.0) | Preview (0.6.0) | Low (Once half year) | Module |
| Reservations |  |Not Started | N/A |Preview (1.0.0b1) | Preview (0.8.0) | Low (Once half year) | Module |
| Advisor   |  |Not Started | N/A |GA (9.0.0) | GA (4.0.0) | Low (once eight months) | Module |
| EventHub   |  |Not Started | N/A |GA (8.0.0) | GA (4.2.0) | Low (Once a year) | Module |
| Media   |  |Not Started | N/A |Preview (7.0.0b1) | GA (3.0.0) | Low (Once a year) | Module |
| Consumption |  |Not Started | N/A |GA (8.0.0) | GA (3.0.0) | Low (Once a year) | Module |
| ContainerInstance |  |Not Started | N/A |GA (7.0.0) | GA (2.0.0) | Low (Once a year) | Module |
| Search |  |Not Started | N/A |GA (8.0.0) | GA (3.0.0) | Low (Once a year) | Module |
| Billing   |  |Not Started | N/A |Preview (6.0.0b1) | GA (1.0.0) | Low (Once a year) | Module |
| DataMigration |  |Not Started | N/A |Preview (9.0.0b1) | GA (4.1.0) | Low (Once a year) | Module |
| Redis   | |Not Started | N/A |GA (12.0.0) | Preview (7.0.0rc2) | Low (Once a year) | Module |
| APIManagement   | |Not Started | N/A |GA (1.0.0) | Preview (0.2.0) | Low (Once a year) | Module |
| RedhatOpenShift   |  |Not Started | N/A|Preview (1.0.0b1) | Preview (0.1.0) | Low (Once a year) | Module |
| DataBoxEdge |  |Not Started | N/A|Preview (1.0.0b1) | Preview (0.2.0) | Low (Once a year) | Module |
| ServiceFabric |  |Not Started | N/A|Preview (1.0.0b1) | Preview (0.5.0) | Low (Once a year) | Module |
| Relay |  |Not Started | N/A|GA (1.0.0) | Preview (0.2.0) | Low (Once two years) | Module |
| DeploymentManager |  |Not Started | N/A|Preview (1.0.0b1) | Preview (0.2.0) | Low (Once two years) | Module |
| BotService   |  |Not Started | N/A|Preview (1.0.0b1) | Preview (0.2.0) | Low (Once two years) | Module |
| ManagedServices | |Not Started | N/A| Preview (6.0.0b1) | GA (1.0.0) | Low (Once two years) | Module |
| Maps |  |Not Started | N/A|Preview (1.0.0b1) | Preview (0.1.0) | Low (Once three years) | Module |
| Backup   | |Not Started | N/A| RecoveryServices: GA (1.0.0)<br> RecoveryServicesBackup: N/A | RecoveryServices: Preview (0.6.0)<br> RecoveryServicesBackup: Preview (0.11.0) | Low (Once half year) | Module |
| IoTHub | | Not Started | N/A |IoTHub: GA (1.0.0) <br> IoTCentral: N/A <br> IoTHubProvisioningServices: N/A | IoTHub: Preview (0.12.0) <br> IoTCentral: GA (4.0.0) <br> IoTHubProvisioningServices: Preview (0.2.0)| | Module |
| BatchAI   | | Not Started | N/A | N/A | GA (2.0.0) | | Module |
| DataLakeAnalytics |  | Not Started | N/A |N/A | Preview (0.6.0) | | Module |
| DataLakeStore |  | Not Started | N/A |N/A | Preview (0.5.0) | | Module |
| Role |  | Not Started | N/A |MSI: N/A | MSI: GA (1.0.0) | | Module |
| |  |  | |  | |  |||
| Account   | | **Completed** | N/A |Subscription: Vendored_Preview (0.5.0) | N/A | N/A | Extension |
| Attestation   |  | **Completed** | N/A |Vendored_SDK | N/A | N/A | Extension |
| Automation   |  | **Completed** | N/A |Vendored_SDK | N/A | N/A | Extension |
| Communication   |  | **Completed** | N/A |Vendored_SDK | N/A | N/A | Extension |
| ConnectedMachine   |  | **Completed** | N/A |Vendored_SDK | N/A | N/A | Extension |
| DataDog   |  | **Completed** | N/A |Vendored_SDK | N/A | N/A | Extension |
| DataShare   |  | **Completed** | N/A |Vendored_SDK | N/A | N/A | Extension |
| DesktopVirtualization   |  | **Completed** | N/A |Vendored_Preview (0.2.0) | N/A | N/A | Extension |
| Footprint   |  | **Completed** | N/A |Vendored_SDK | N/A | N/A | Extension |
| GuestConfig   |  | **Completed** | N/A |Vendored_SDK | N/A | N/A | Extension |
| HardwareSecutiryModules   |  | **Completed** | N/A |Vendored_SDK | N/A | N/A | Extension |
| HealthCareAPIs   |  | **Completed** | N/A |Vendored_Preview (0.3.0) | N/A | N/A | Extension |
| Import-Export   |  | **Completed** | N/A |Vendored_SDK | N/A | N/A | Extension |
| Footprint   |  | **Completed** | N/A |Vendored_SDK | N/A | N/A | Extension |
| Logic   | | **Completed** | N/A |N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| Maintenance   | | **Completed** | N/A |N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| Peering   | | **Completed** | N/A |N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| Portal  | | **Completed** | N/A |N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| StackHCI   | | **Completed** | N/A |N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| AKS-Preview  | | Not Started | N/A |N/A | ContainerService: Vendored_GA (0.2.0) | N/A | Extension |
| AlertsManagement   | | Not Started | N/A |N/A | Vendored_Preview (0.2.0rc2) | N/A | Extension |
| BlockChain   | | Not Started | N/A |N/A | Vendored_GA (2.0.0) | N/A | Extension |
| BluePrint   | | Not Started | N/A |N/A | Vendored_Preview (2018-11-01-preview) | N/A | Extension |
| CodeSpaces   | | Not Started | N/A |N/A | Vendored_SDK | N/A | Extension |
| ConnectedK8S   | | Not Started | N/A |N/A | Vendored_Preview (0.1.1) | N/A | Extension |
| CustomProviders   | | Not Started | N/A |N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| DataBox   | | Not Started | N/A |N/A | Vendored_Preview (0.2.0) | N/A | Extension |
| DataBricks   | | Not Started | N/A |N/A | Vendored_Preview (0.1.0 | N/A | Extension |
| DB-Up   | | Not Started | N/A |N/A | RDBMS: Vendored_GA (1.5.0) <br> SQL: Vendored_Preview (0.11.0) | N/A | Extension |
| DMS-Preview   | | Not Started | N/A |N/A | Vendored_GA (4.0.0) | N/A | Extension |
| ExpressRouteCrossConnection   || Not Started | N/A | N/A | Network: Vendored_SDK | N/A | Extension |
| Hack   | | Not Started | N/A |N/A | Call AppService, CosmosDB, RDBMS, CognitiveServices | N/A | Extension |
| HPC-Cache   || Not Started | N/A | N/A | Vendored_Preview (0.2.0 | N/A | Extension |
| InternetAnalyzer   || Not Started | N/A | N/A | Frontdoor: Vendored_Preview (0.3.0) | N/A | Extension |
| Ip-Group   | | Not Started | N/A |N/A | Network: Vendored_SDK | N/A | Extension |
| K8SConfiguration   | | Not Started | N/A |N/A | Vendored_SDK) | N/A | Extension |
| Log-Analytics   | | Not Started | N/A |N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| ManagementPartner   | | Not Started | N/A |N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| Mesh   | | Not Started | N/A |N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| Mixed-Reality   | | Not Started | N/A |N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| NotificationHub   | | Not Started | N/A |N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| PowerbiDedicated   | | Not Started | N/A |N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| ResourceGraph   | | Not Started | N/A |N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| SecurityInsight   | | Not Started | N/A |N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| SpringCloud   | | Not Started | N/A |N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| StorageSync   | | Not Started | N/A |N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| Stream-Analytics   | | Not Started | N/A |N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| Support   | | Not Started | N/A |N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| TimeSeriesInsights   | | Not Started | N/A |N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| VMWare   | | Not Started | N/A |N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| VirtualWan   | | Not Started | N/A |N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| Swiftlet   | | Not Started | N/A |N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| ScheduledQuery   | | Not Started | N/A |N/A | Vendored_Preview (0.1.0) | N/A | Extension |
| *Below services are not supported in CLI repo*|  |  | |  | |  |||
| Azure Security Center |  Yes | | 06/31/2021 | |  |  |  |
| Sentinel|  Yes | | 06/31/2021 | |  |  |  |
| Azure Data Explorer|  Yes | | 06/31/2021 | |  |  |  |
| Azure DevOps|  Yes | | 06/31/2021 | |  |  |  |
| Azure Machine Learning|  Yes | | 06/31/2021 | |  |  |  |