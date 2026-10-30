# Azure CLI Storage Module #
This is a main module for storage features.

### Included Features

#### Management Policy:	
Manage data policy rules associated with a storage account: [more info](https://learn.microsoft.com/azure/storage/common/storage-lifecycle-managment-concepts)\	
*Examples:*	
```	
az storage account management-policy create \	
    --account-name accountName \	
    --resource-group groupName \	
    --policy @{path}	
```	

#### Static Website:	
Manage static website configurations: [more info](https://learn.microsoft.com/azure/storage/blobs/storage-blob-static-website)\	
*Examples:*	
```	
az storage blob service-properties update \	
    --account-name accountName \	
    --static-website \	
    --404-document error.html \	
    --index-document index.html	
```	

#### Hierarchical Namespace:	
Enable the blob service to exhibit filesystem semantics: [more info](https://learn.microsoft.com/azure/storage/data-lake-storage/namespace)\	
*Examples:*	
```	
az storage account create \	
    --name accountName \	
    --resource-group groupName \	
    --kind StorageV2 \	
    --enable-hierarchical-namespace	
```	

#### File AAD Integration:	
Enable AAD integration for Azure files, which will support SMB access: [more info](https://learn.microsoft.com/azure/storage/files/storage-files-active-directory-enable)\	
*Examples:*	
```	
az storage account create \	
    --name accountName \	
    --resource-group groupName \	
    --kind StorageV2	
az storage account update \	
    --name accountName \	
    --resource-group groupName	
```	

#### Premium Blobs/Files:	
Create premium blob/file storage accounts.\	
More info:[premium blobs](https://azure.microsoft.com/blog/introducing-azure-premium-blob-storage-limited-public-preview/) [premium files](https://learn.microsoft.com/azure/storage/files/storage-files-introduction)\	
*Examples:*	
```	
az storage account create \	
    --name accountName \	
    --resource-group groupName \	
    --sku Premium_LRS \	
    --kind BlockBlobStorage	
az storage account create \	
    --name accountName \	
    --resource-group groupName \	
    --sku Premium_LRS \	
    --kind FileStorage	
```	

#### Customer-Controlled Failover:	
Failover GRS/RA-GRS storage accounts from the primary cluster to the secondary cluster: [more info](https://learn.microsoft.com/azure/storage/common/storage-disaster-recovery-guidance)\	
*Examples:*	
```	
az storage account show \	
    --name accountName \	
    --expand geoReplicationStats	
az storage account failover \	
    --name accountName	
```

#### Storage Management Resource Groups

The following built-in command groups use Storage Management API `2026-09-01`:

| Command group | Operations |
| --- | --- |
| `az storage account blob-access-point-configuration` | Create, update, delete, show, list, test existing/proposed connections, wait |
| `az storage context-cache` | Create, update, delete, show, list, check name availability, wait |
| `az storage context-cache container` | Create, update, delete, show, list, wait |
| `az storage context-cache identity` | Assign, remove, show managed identities |

Use each command's `--help` for its required arguments and examples. Long-running
connection tests support `--no-wait`; they do not have a separate test-result wait
command. Storage task assignments, including `az storage account task-assignment stop`,
remain in the `storage-preview` extension.

Blob Access Point configuration updates use PATCH without resending create-only
properties or injecting argument defaults.

##### Polymorphic connection inputs

The `--source` argument uses nested CLI discriminator names rather than the
service's raw discriminator fields. For example, a Blob Access Point configuration
can use the following source object:

```json
{
  "s3-compatible": {
    "connection": {
      "endpoint": {
        "endpoint": "https://s3.example.com"
      }
    },
    "auth": {
      "access-key": {
        "access-key-id": "<access-key-id>",
        "secret-access-key": "<secret-access-key>"
      }
    }
  }
}
```

Other source variants are `net-app-ontap`, `azure-net-app-files`, `dell-one-fs`,
`qumulo`, `commvault` and `nasuni`. Connections support `endpoint` and `private-link`.
Use the nested argument help to see required Private Link fields. Remote access
keys are write-only: show/list responses do not include `secretAccessKey`.
Keep input files containing credentials out of version control and shell history.

##### Context cache updates and identities

Context caches support both system-assigned and user-assigned managed identities.
Use `az storage context-cache identity assign/remove/show` to manage identities.
These helpers preserve unrelated cache properties and identities not selected
for removal.

Cache and cache-container updates, including cache identity assignment/removal,
poll until completion, then retrieve the updated resource from its original URI,
matching the .NET SDK behavior. The operation-status endpoint does not return the
resource. `--no-wait` continues to return without polling or retrieving the final
resource.

Cache and cache-container updates use PATCH. Cache `account-kind` and container
`model-name`/`provider` are create-only. Container `--time-to-live` accepts 1 through
30 inclusive. `az storage context-cache list` works across the subscription or
within a specified resource group. `az storage context-cache check-name --name NAME`
checks availability with the resource type defaulted to `Microsoft.Storage/contextCaches`.

#### Recording Storage Management Scenarios

The management scenarios use `ScenarioTest` and `ResourceGroupPreparer`, following
the [CLI test authoring workflow](https://github.com/Azure/azure-cli/blob/dev/doc/authoring_tests.md).
They create their own Storage accounts, cache containers, caches and managed
identities rather than depending on persistent resources. For test-owned resource
groups, teardown cleans up the fixtures, including when a scenario fails.

- [Account scenarios](tests/latest/test_storage_account_scenarios.py) exercise
  service-specific Shared Key and Blob Access Point policies, user-bound SAS policies,
  and Turbo Tier.
- [Context cache scenarios](tests/latest/test_storage_context_cache_scenarios.py)
  exercise cache/container lifecycles, both list scopes, name availability, TTL
  boundaries and managed identity preservation.

Scenarios without a committed recording require initial live recording before
playback is available.
**A missing recording makes the framework run live**, even without `--live`.
Do not run them against Azure until the subscription, region, permissions and
potential charges have been approved. Policy, SAS and context cache fixtures use
East US. Turbo Tier uses the Canary region `eastus2euap`; confirm that the selected
subscription supports this feature.
Turbo Tier is created enabled at 10 percent, then disabled.
Extended-group testing is omitted, as in the .NET tests.
Disabling Turbo Tier omits an inherited target percentage, matching the .NET
request; the service rejects a disabled tier with the previous target included.
Collecting tests with `pytest --collect-only` does not provision resources.
When recording with pytest 9, use Python 3.11 or later: the test framework's
Python 3.10 outcome handling can discard recordings even when the tests pass.
Verify that each expected recording file exists after the live run.

From the configured CLI development environment, record the new selectors:

```powershell
azdev test `
    test_storage_account_service_keys_and_collaboration_policy `
    test_storage_account_user_bound_sas_policy `
    test_storage_account_turbo_tier `
    test_storage_context_cache_lifecycle `
    test_storage_context_cache_managed_identities --live
```

Inspect the resulting recordings for credentials and other sensitive values,
including real subscription/tenant IDs and the actor-identifying
`x-ms-operation-identifier` response header. Sanitize those values, then rerun the
same selectors without `--live` and verify offline playback before submitting
them. Blob Access Point connection/attachment scenarios additionally
need a real supported backing endpoint and credential-sanitization fixtures.
