# App Service Active Backup preview

The preview commands manage plan and site **silos** through public ARM APIs. They
do not configure storage-backed App Service backups, deployment slots, or slot
traffic routing.

## Availability and API version

New commands use `2026-08-01`, the version registered for the child resources in
the inspected App Service ARM manifest. Ordinary app/plan commands retain their
existing API versions. Direct GeoMaster tests using an older date do not establish
public ARM availability. An unavailable version or feature is reported as a service
error; the CLI does not silently downgrade or call internal GeoMaster endpoints.

The intended creation preview is Windows/Linux dedicated multitenant plans in the
PremiumV3, PremiumMV3, PremiumV4, and PremiumMV4 tier families. **P0v3 is excluded**.
Linux requires service-side flavor enablement. Installing these commands does not
enable a subscription or region, grant quota, or change service eligibility.

Create a plan silo before a site silo in the same target region. Silo names need
not match. Region uniqueness, eligible SKUs, slots, primary deletion restrictions,
and plan placement remain service-enforced. Creating the first site silo can
restart the primary app. Cross-resource-group/subscription source-plan placement
is not established as supported by the current backend.

## Create, inspect, and update

Assume an existing eligible primary plan and app in `eastus`. Creating silos
allocates billable resources; choose a region enabled for your subscription.

```azurecli
az appservice plan silo create -g MyGroup -n MyPlan --silo WestPlan --location westus2 --primary-location eastus --number-of-workers 2
az webapp silo create -g MyGroup -n MyApp --silo WestApp --location westus2 --primary-location eastus --traffic-mode Active
az webapp silo show -g MyGroup -n MyApp --silo WestApp
az webapp silo list -g MyGroup -n MyApp
az appservice plan silo update -g MyGroup -n MyPlan --silo WestPlan --zone-redundant false
az webapp silo update -g MyGroup -n MyApp --silo WestApp --follow-last-known-good false
```

Resource commands return the ARM envelope. This illustrates the shape, not a
captured live response or a promised revision number:

```output
{
  "id": "/subscriptions/SUB/resourceGroups/MyGroup/providers/Microsoft.Web/sites/MyApp/silos/WestApp",
  "name": "WestApp",
  "type": "Microsoft.Web/sites/silos",
  "location": "westus2",
  "properties": {
    "provisioningState": "Succeeded",
    "revisionNumber": 7,
    "followLastKnownGood": false
  }
}
```

`--name` always identifies the primary. `--silo` identifies the child. Supported
non-create commands also accept a complete nested silo ARM ID through `--ids`;
do not combine it with named resource arguments. No internal replica app or plan
name is required.

Create requires an explicit target `--location`; a configured default location
does not choose the silo region. Update preserves the existing silo location when
`--location` is omitted, even if a different CLI default location is configured.

Create/update/delete wait for their API operation, not future content/configuration
revision, probe-health, or DNS convergence. `--no-wait` returns an accepted-operation
receipt when the service starts an asynchronous operation.
After an asynchronous create/update succeeds, the CLI reads and returns the
original target resource, rather than returning the operation-status envelope.

The receipt contains `resourceId`, `operationId`, `operationUrl`, and
`status: Accepted`. It is returned in the selected output format; `--output none`
explicitly suppresses it.

No-wait skips subsequent operation polling; the initial request must still
complete. For restart, use `--synchronous false --no-wait` when you also want
the service to avoid synchronous restart work in that initial request.

```powershell
$operation = az appservice plan silo create -g MyGroup -n MyPlan --silo WestPlan --location westus2 --primary-location eastus --no-wait | ConvertFrom-Json
az appservice plan silo wait -g MyGroup -n MyPlan --silo WestPlan --operation-id $operation.operationId --timeout 7200
```

A synchronous/no-op result is already complete and does not need an operation
wait. A CLI timeout does not cancel the service operation. `silo operation show`
inspects a CRUD operation; `webapp silo runtime-operation show` inspects a runtime
operation instead.

Both plan and site `silo operation show`/`silo wait` request the API's asynchronous
status representation (`azureAsyncOperation=1`). They report operation status
without reading the target resource after success, including after deletion.
Polling errors remain errors; a missing resource alone is not proof of successful
operation completion.

Worker overrides are 1-30. Omitted fields preserve service defaults/current values;
explicit `false` is not omission. Location cannot be changed by update. The current
API does not establish resetting existing plan overrides back to inheritance.

## Traffic, origin, Last Known Good, and refresh

For the site `origin` entry only, a point-read HTTP 404 can be worked around using
the exact matching origin resource returned by the paginated silo collection.
The CLI emits a warning when it does this for show, update pre-read, or update
readback. The returned object is the service's collection entry, without invented
fields; stamp-derived IP fields from point reads may be absent. Missing,
duplicate, or malformed origin entries and list/permission failures remain
errors. Ordinary replica, plan-origin and pass-through reads are unchanged.
Origin writes and operation polling still target their original API routes;
the workaround does not prove that the raw ARM point endpoint is working.

```azurecli
az webapp managed-traffic show -g MyGroup -n MyApp
az webapp managed-traffic list -g MyGroup -n MyApp --expand-endpoints
az webapp managed-traffic update -g MyGroup -n MyApp --traffic-mode Passive
az webapp managed-traffic update -g MyGroup -n MyApp --endpoints @endpoints.json
az webapp silo update -g MyGroup -n MyApp --silo WestApp --endpoint-status Enabled
az webapp silo update -g MyGroup -n MyApp --silo origin --endpoint-status Disabled
az webapp last-known-good mark -g MyGroup -n MyApp
az webapp last-known-good show -g MyGroup -n MyApp
az webapp silo refresh -g MyGroup -n MyApp
```

An endpoint file is an array of partial, region-keyed overrides, for example:

```json
[
  {"region": "eastus", "priority": 1},
  {"region": "westus2", "priority": 2}
]
```

The first site silo requires `Active` or `Passive` traffic mode. Change subsequent
mode on the app-wide managed-traffic resource. Active uses weights; Passive uses
priorities. The service validates endpoint membership, readiness, uniqueness, and
the merged state. Explicit weights switch those endpoints to manual weighting;
the API does not currently establish a reset to automatic weighting.

`origin` represents the primary endpoint. Only endpoint status is updatable on
it through the silo update API; it is not a separately creatable/deletable replica.
Verify that the target silo is healthy and enabled before disabling origin.
These commands do not perform a safe failover workflow on the caller's behalf.

LKG mark selects the latest ready revision; it is not arbitrary revision selection
or a primary rollback. Refresh succeeds immediately on HTTP 204 **acceptance** and
prints an asynchronous-propagation notice to stderr. It does not poll revisions,
invent a target revision number, or guarantee completion within a fixed interval.
Use silo show/list to observe revisions, provisioning state, and error details.

## Networking

```azurecli
az webapp silo vnet-integration add -g MyGroup -n MyApp --silo WestApp --subnet /subscriptions/SUB/resourceGroups/NETGROUP/providers/Microsoft.Network/virtualNetworks/WestNet/subnets/integration
az webapp silo vnet-integration show -g MyGroup -n MyApp --silo WestApp
az appservice plan silo vnet-integration list -g MyGroup -n MyPlan --silo WestPlan
az webapp silo vnet-integration remove -g MyGroup -n MyApp --silo WestApp
```

The site API uses the dedicated silo `virtualNetworkConnections/virtualNetwork`
route. `update` uses PATCH. For full connection properties, `--body @request.json`
accepts the API envelope, for example `{"properties":{"subnetResourceId":"..."}}`.
Plan-silo integration inspection is read-only. No normal-primary-region network
validator runs before a silo call.

## Operational pass-through commands

The `webapp silo` subgroups cover configuration reads, configuration snapshots,
deployment history/status, instances/processes, logs, WebJobs, installed extensions,
extension invocation, network checks/traces, metrics, antivirus, and site-container
reads. There is **no CLI-side OS/SKU/flavor/provisioning filter**: the requested silo
route is called directly, and service errors such as 404 are surfaced normally.

ARM collection list commands follow `nextLink` and return the item array, so
`--query "[].name"` and table output include all pages. Property-bag responses,
such as app settings, connection strings, storage accounts and metadata, retain
their service shape. The startup-log response also retains its file/latest-log
wrapper rather than being flattened into an ARM collection.

```azurecli
az webapp silo config show -g MyGroup -n MyApp --silo WestApp
az webapp silo config appsettings list -g MyGroup -n MyApp --silo WestApp
az webapp silo instance list -g MyGroup -n MyApp --silo WestApp
az webapp silo restart -g MyGroup -n MyApp --silo WestApp
az webapp silo log startup list -g MyGroup -n MyApp --silo WestApp --latest true
az webapp silo log container download -g MyGroup -n MyApp --silo WestApp --format zip --file logs.zip
```

Instance-qualified process/container operations accept `--instance`. Binary
downloads require `--file`; an existing destination requires `--overwrite`.
`log tail` streams text, or exact bytes with `--file`. Configuration/connection
string/auth/private-snapshot reads intentionally return sensitive values: protect
their output and do not put it in source control.

Use named options for DNS checks, TCP checks and antivirus configuration:

```azurecli
az webapp silo network-check dns -g MyGroup -n MyApp --silo WestApp --dns-name example.com
az webapp silo network-check tcp-ping -g MyGroup -n MyApp --silo WestApp --host example.com --port 443
az webapp silo antivirus config update -g MyGroup -n MyApp --silo WestApp --delete-infected-files false
```

For those commands, `--body` remains an advanced alternative and cannot be
combined with the named request fields. TCP ports are integers from 1 to 65535;
the CLI serializes the port using the service's string-valued field.

Other request-body operations accept JSON or `@file` containing the API envelope.
The advanced-body forms of the commands above use the same envelopes:

| Operation | Example body |
|---|---|
| `network-check dns` | `{"properties":{"dnsName":"example.com"}}` |
| `network-check tcp-ping` | `{"properties":{"host":"example.com","port":"443"}}` |
| `network-check connectivity` | `{"properties":{"providerType":"Web","credentials":{"credentialType":"AppSetting","appSetting":"MY_ENDPOINT"},"resourceMetadata":{"entityName":"example.com"}}}` |
| `antivirus config update` | `{"properties":{"deleteInfectedFiles":false}}` |

`extension invoke` requires an instance, relative `--path`, and supports
GET/POST/PUT/PATCH/DELETE/HEAD with an optional body/content type/file. The service's
extension-path restrictions still apply. Use `--uri-parameters KEY=VALUE` for
extension query parameters; repeated keys are preserved and cannot override the
ARM API version. It is not a general arbitrary-host REST client.

The API has point process reads but no reviewed silo process-list route. No
primary process-list fallback is used. Configuration snapshot reads do not imply
snapshot restore. General configuration writes, direct deployment, identity
assignment, and site-container writes are not invented where the service has no
silo route. The publishing-profile silo route needs backend target-rewrite
verification before it can be exposed safely.

## Teardown

Delete site silos before their backing plan silos; then use ordinary commands to
delete the primary resources if desired. There is no automatic cascade.

```azurecli
az webapp silo delete -g MyGroup -n MyApp --silo WestApp --yes
az appservice plan silo delete -g MyGroup -n MyPlan --silo WestPlan --yes
```

## Validation and release prerequisites

Offline mock coverage exercises all 84 pass-through methods, management bodies,
operation protocols, identity handling, file/stream behavior, and runtime help.
It is not evidence that an API version/feature is deployed in a particular cloud
or that a service-specific operation works for every silo.

The opt-in scenario tests require an enabled preview subscription and explicit
authorization to allocate resources. Set `AZURE_ACTIVE_BACKUP_LIVE=1` only for that
purpose, along with `AZURE_ACTIVE_BACKUP_PRIMARY_LOCATION` and
`AZURE_ACTIVE_BACKUP_SILO_LOCATION`. Linux also needs service-side enablement.
No live recording or public ARM availability claim should be inferred from a
passing mock suite.

Use the repository's live runner only after enabling that opt-in:

```powershell
azdev test test_appservice_active_backup_windows test_appservice_active_backup_linux --live
```
