# Track2 SDK Migration Roadmap
This document provides the roadmap for track2 SDK migration in Azure CLI. When you migrate your module to track2 SDK, you can go to [Track2 migration guidance](track_2_migration_guidance.md) to check how to migrate to track2 SDK.

## Why do we need migrate track1 SDK to track2 SDK in Azure CLI?
- Track1 SDK will be eventually deprecated sometime in the future. 
- Some new features will only be in track2 SDK in the future.

## Here are criteria to determine the priority of migration:
- On-demand for track2 SDK from CLI customers (such as LinkedIn) has higher priority.
- On-demand for track2 SDK from SDK team has higher priority.
- The smaller the gap between track1 version and track2 version, the higher priority.
- The more frequent release, the higher priority.
- If there is no track2 SDK released, it has lower priority.
- If track1 is in preview (0.x.x or x.x.xrc), the lower priority.
- Extenison has lower priority.

## Here is the proposed roadmap for managment plane migration. (Total ~50 CLI modules and ~50 extensions.)

| Module   | Latest Track2 SDK Status | Latest Track1 SDK status  | Release frequency | CLI Module or Extension |Migration Status | ETA | 
| --------- |:-------------:| :-----:|:-----:|:--:|:--:|:--:|
| Network     | GA (17.0.0) | GA (13.0.0) | High (Once a month)| Module |Completed | N/A |
| NatGateway | Network: GA (8.0.0) | Network: GA (2.2.0) | Use Network package| Module | Completed | N/A |
| Storage     | GA (16.0.0) | GA (11.2.0) | Medium (Once two months) | Module |Completed | N/A |
| Compute     | GA (18.0.0) | GA (14.0.0) | High (Once a month) | Module |Completed | N/A |
| KeyVault    | GA (8.0.0) | GA (2.2.0) | Medium (Once three months) | Module |Completed | N/A |
| Monitor     | Monitor: GA (2.0.0)<br> LogAnalytics: GA (8.0.0) | Monitor: Preview (0.12.0)<br> LogAnalytics: GA (2.0.0) | Medium (Once two months) | Module |In Progress | 01/19/2021 |
| Resource   | GA (15.0.0) | GA (12.0.0) | Medium (Once two months) | Module |Not Started | 03/31/2021 |
| AppService   | GA (1.0.0) | Preview (0.48.0) | Medium (Once three months) | Module |Not Started | 03/31/2021 |
| SQL   | GA (1.0.0) | Preview (0.25.0) | High (Once a month) | Module |Not Started | 03/31/2021 |
| RDBMS | GA (8.0.0) | Preview (3.1.0rc1) | Medium (Once two months) | Module |Not Started | 03/31/2021 |
| ACS   | ContainerService: GA (14.0.0)<br> ContainerInstance: GA (7.0.0) | ContainerService: GA (11.0.0)<br> ContainerInstance: GA (2.0.0) | Medium (Once two months) | Module |Not Started | 03/31/2021 |
| Synapse | Preview (1.0.0b1) | Preview (0.6.0) | Medium (Once two months) | Module |Not Started | 03/31/2021 |
| HDInsight | GA (7.0.0) | GA (2.1.0) | Medium (Once two months) | Module |Not Started | 03/31/2021 |
| ACR   | Preview (8.0.0b1) | Preview (3.0.0rc16) | Medium (Once two months) | Module |Not Started | 03/31/2021 |
| Kusto | Preview (1.0.0b1) | Preview (0.10.0) | Medium (Once two months | Module |Not Started | 03/31/2021  |
| CosmosDB   | GA (6.0.0) | Preview (2.0.0rc1) |  Medium (Once two months) | Module |Not Started | 03/31/2021 |
| NetApp | Preview (1.0.0b1) | Preview (0.15.0) | Medium (Once two months) | Module |Not Started | 03/31/2021 |
| ServiceBus   | GA (6.0.0) | GA (1.0.0) | Medium (Once four months) | Module |Not Started | 03/31/2021 |
| AppConfiguration   | GA (1.0.1) | Preview (0.6.0) | Medium (Once three months) | Module |Not Started | 03/31/2021 |
| EventGrid | GA (8.0.0) | Preview (3.0.0rc8) | Medium (Once three months) | Module |Not Started | 03/31/2021 |
| Security | GA (1.0.0) | Preview (0.6.0) | Medium (Once three months) | Module |Not Started | 03/31/2021 |
| CDN   | Preview (10.0.0b1) | GA (6.0.0) | Low (Once half year) | Module |Not Started | 03/31/2021 |
| Batch   | GA (14.0.0) | GA (9.0.0) | Low (Once half year) | Module |Not Started | 03/31/2021 |
| CognitiveServices | GA (11.0.0) | GA (6.3.0) | Low (Once half year) | Module |Not Started | 04/31/2021 |
| DevTestLabs | GA (9.0.0) | GA (4.0.0) | Low (Once half year) | Module |Not Started | 04/31/2021 |
| SignalR | Preview (1.0.0b1) | Preview (0.4.0) | Low (Once half year) | Module |Not Started | 04/31/2021 |
| PolicyInsights | GA (1.0.0) | Preview (0.6.0) | Low (Once half year) | Module |Not Started | 04/31/2021 |
| Reservations | Preview (1.0.0b1) | Preview (0.8.0) | Low (Once half year) | Module |Not Started | 04/31/2021 |
| Advisor   | GA (9.0.0) | GA (4.0.0) | Low (once eight months) | Module | Not Started | 04/31/2021 |
| EventHub   | GA (8.0.0) | GA (4.2.0) | Low (Once a year) | Module |Not Started | 04/31/2021 |
| Media   | Preview (7.0.0b1) | GA (3.0.0) | Low (Once a year) | Module |Not Started | 04/31/2021 |
| Consumption | GA (8.0.0) | GA (3.0.0) | Low (Once a year) | Module |Not Started | 04/31/2021 |
| ContainerInstance | GA (7.0.0) | GA (2.0.0) | Low (Once a year) | Module |Not Started | 04/31/2021 |
| Search | GA (8.0.0) | GA (3.0.0) | Low (Once a year) | Module |Not Started | 04/31/2021 |
| Billing   | Preview (6.0.0b1) | GA (1.0.0) | Low (Once a year) | Module |Not Started | 04/31/2021 |
| DataMigration | Preview (9.0.0b1) | GA (4.1.0) | Low (Once a year) | Module |Not Started | 04/31/2021 |
| Redis   | GA (12.0.0) | Preview (7.0.0rc2) | Low (Once a year) | Module |Not Started | 04/31/2021 |
| APIManagement   | GA (1.0.0) | Preview (0.2.0) | Low (Once a year) | Module |Not Started | 04/31/2021 |
| RedhatOpenShift   | Preview (1.0.0b1) | Preview (0.1.0) | Low (Once a year) | Module |Not Started | 05/31/2021 |
| DataBoxEdge | Preview (1.0.0b1) | Preview (0.2.0) | Low (Once a year) | Module |Not Started | 05/31/2021 |
| ServiceFabric | Preview (1.0.0b1) | Preview (0.5.0) | Low (Once a year) | Module |Not Started | 05/31/2021 |
| Relay | GA (1.0.0) | Preview (0.2.0) | Low (Once two years) | Module |Not Started | 05/31/2021 |
| DeploymentManager | Preview (1.0.0b1) | Preview (0.2.0) | Low (Once two years) | Module |Not Started | 05/31/2021 |
| BotService   | Preview (1.0.0b1) | Preview (0.2.0) | Low (Once two years) | Module |Not Started | 05/31/2021 |
| ManagedServices | Preview (6.0.0b1) | GA (1.0.0) | Low (Once two years) | Module |Not Started | 05/31/2021 |
| Maps | Preview (1.0.0b1) | Preview (0.1.0) | Low (Once three years) | Module |Not Started | 05/31/2021 |
| Backup   | RecoveryServices: GA (1.0.0)<br> RecoveryServicesBackup: N/A | RecoveryServices: Preview (0.6.0)<br> RecoveryServicesBackup: Preview (0.11.0) | Low (Once half year) | Module |Not Started | 05/31/2021 |
| IoTHub | IoTHub: GA (1.0.0) <br> IoTCentral: N/A <br> IoTHubProvisioningServices: N/A | IoTHub: Preview (0.12.0) <br> IoTCentral: GA (4.0.0) <br> IoTHubProvisioningServices: Preview (0.2.0)| | Module |Not Started | N/A |
| BatchAI   | N/A | GA (2.0.0) | | Module |Not Started | N/A |
| DataLakeAnalytics | N/A | Preview (0.6.0) | | Module |Not Started | N/A |
| DataLakeStore | N/A | Preview (0.5.0) | | Module |Not Started | N/A |
| PrivateDNS | N/A | Preview (0.1.0) | | Module |Not Started | N/A |
| Role | MSI: N/A | MSI: GA (1.0.0) | | Module |Not Started | N/A |

## Here is the proposed roadmap for data plane migration.