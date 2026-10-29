# App Service Active Backup preview

The preview manages plan and site **silos** through public ARM APIs. It does not
configure storage-backed backups, deployment slots, or slot traffic routing.

## Specification and scope

Commands are generated with AAZDev from the `2026-08-01` App Service contract in
[azure-rest-api-specs PR 44330](https://github.com/Azure/azure-rest-api-specs/pull/44330),
using source commit `33ee07b2b3d377b58c4d1a1c5be7e2339f43b879`.
That specification is still under review. Existing ordinary app/plan commands
retain their API versions and support levels.

The first implementation exposes 24 preview commands covering the contract's
20 HTTP operations plus CLI update/wait behavior:

| Group | Commands |
|---|---|
| `appservice plan silo` | create, update, show, list, delete, wait |
| `appservice plan silo vnet-integration` | list |
| `webapp silo` | create, update, show, list, delete, wait, refresh |
| `webapp silo vnet-integration` | show, add, update, remove |
| `webapp managed-traffic` | list, show, update |
| `webapp last-known-good` | list, show, mark |

Configuration, deployments, processes, containers, logs, WebJobs, diagnostics,
metrics, antivirus, extension invocation and other silo pass-through APIs are
deferred. Standalone operation-status commands and managed-traffic metrics are
also deferred because this specification does not define them.

AAZ supplies authentication, cloud selection, error handling, pagination,
serialization and long-running-operation handling. The CLI does not downgrade
the API version or call internal GeoMaster endpoints. Thin subclasses of the
generated silo commands supply a missing top-level location field in the draft
contract; they do not replace its HTTP client or poller. A small identity validator
rejects plan, slot and extension-resource IDs that core ID expansion could
otherwise reinterpret as a different silo.

## Availability

The intended creation preview is Windows/Linux dedicated multitenant plans in
PremiumV3, PremiumMV3, PremiumV4 and PremiumMV4 tier families. P0v3 is excluded.
Subscription, region, flavor, SKU, capacity, placement and origin restrictions
remain service-enforced. Installing the CLI does not enable the feature.

Create a plan silo before a site silo in the same target region. Creating the
first site silo can restart the primary app. Silos allocate billable resources;
there is no automatic plan-plus-app setup, cascading teardown or safe failover
workflow.

## Create and update

Assume an existing eligible primary plan and app in `eastus`:

```azurecli
az appservice plan silo create --resource-group MyGroup --name MyPlan --silo WestPlan --location westus2 --primary-location eastus --number-of-workers 2
az webapp silo create --resource-group MyGroup --name MyApp --silo WestApp --location westus2 --primary-location eastus --traffic-mode Active
az webapp silo show --resource-group MyGroup --name MyApp --silo WestApp
az webapp silo list --resource-group MyGroup --name MyApp
az appservice plan silo update --resource-group MyGroup --name MyPlan --silo WestPlan --zone-redundant false
az webapp silo update --resource-group MyGroup --name MyApp --silo WestApp --follow-last-known-good false
```

`--name` identifies the primary; `--silo` identifies the child. Both create
commands require explicit target `--location` and `--primary-location`.
A configured default location does not select a replica region. The draft
specification maps these values to `properties.siloLocation` and
`properties.primaryLocation`, but the deployed API also requires top-level
`location`. The compatibility layer supplies that root field, retaining the
generated property mappings until the service specification is corrected.

For example, a site create request contains:

```json
{
  "location": "westus2",
  "properties": {
    "siloLocation": "westus2",
    "primaryLocation": "eastus",
    "trafficMode": "Active"
  }
}
```

Resource commands return the modeled ARM resource; collections return item
arrays and follow `nextLink`. Generic GET+PUT updates preserve existing modeled
writable fields, exclude read-only fields, and support `--set`, `--add` and
`--remove`. Generic property paths include the envelope, for example
`--set properties.instanceNumberOverride=2`. Explicit `false` is not omission.
Updates preserve the region returned by the service, even if it is only present
at the root of the response. Missing or conflicting region metadata is an error;
the CLI does not guess from the primary region or a configured default.
An existing silo's location cannot be changed or removed. Service validation
remains authoritative for worker counts and other resource restrictions.

Silo show/update/delete/wait and site networking commands support a complete silo
resource ID through `--ids`. Plan VNet listing uses the named parent/silo arguments.
App-level traffic/LKG/refresh use the primary app's
identity, not an internal replica name. As with standard CLI ID expansion, use
either `--ids` or named identity arguments.

## Async behavior and waits

Create/update/delete use standard AAZ long-running-operation handling.
`--no-wait` submits the initial request without subsequent polling and returns
no custom operation receipt. It does not make the initial HTTP request instant.

```azurecli
az webapp silo create --resource-group MyGroup --name MyApp --silo WestApp --location westus2 --primary-location eastus --traffic-mode Active --no-wait
az webapp silo wait --resource-group MyGroup --name MyApp --silo WestApp --created --interval 10 --timeout 1800
```

The separate `wait` commands poll the **resource**, using standard conditions
such as `--exists`, `--created`, `--updated`, `--deleted` and `--custom`.
They do not accept an operation ID. Provisioning completion does not establish
content/configuration revision, endpoint health or DNS convergence. Observe those
separately. A CLI timeout does not cancel the service operation.

Until the service fixes empty pending Azure async-status responses, silo
create/update/delete use a per-operation response hook to prefer the provided
`Location` monitor. The SDK's standard Location poller keeps waiting on empty
202s; it does not treat acceptance as completion or hide failures. Azure-only
responses without a Location header retain normal Azure async polling.

Plan-silo deletion also supplies AAZ's existing case-insensitive error formatter
for HTTP 409, preserving legacy App Service `Code`/`Message` details that core's
default conflict mapping otherwise loses. The exception remains a conflict and
the command still fails. Empty or unrecognized bodies remain generic failures;
the CLI never invents a dependency-specific reason.

Until the service fixes origin point reads, an origin-only compatibility fallback
handles HTTP 404 by using the generated silo list command and its pagination.
Show, update pre-reads and resource waits accept only a unique matching ARM ID
with the expected resource type and properties, and warn that the collection
response may omit stamp-derived IP fields. Missing origins and unrelated errors
remain errors; no resource metadata is fabricated. This does not change delete
operation polling or treat a failed mutation as success.

## Traffic, Last Known Good and refresh

```azurecli
az webapp managed-traffic show --resource-group MyGroup --name MyApp
az webapp managed-traffic list --resource-group MyGroup --name MyApp --expand endpoints
az webapp managed-traffic update --resource-group MyGroup --name MyApp --traffic-mode Passive
az webapp managed-traffic update --resource-group MyGroup --name MyApp --traffic-mode Active --endpoints "[{region:eastus,weight:700},{region:westus2,weight:300}]"
az webapp last-known-good mark --resource-group MyGroup --name MyApp
az webapp last-known-good show --resource-group MyGroup --name MyApp
az webapp silo refresh --resource-group MyGroup --name MyApp
```

Endpoint collections use typed AAZ shorthand or `@file` input. Weights/priorities
are integers from 1 to 1000, as defined by the specification. `--expand endpoints`
is available on traffic list, not point show.

Active uses weights; Passive uses priorities. Mark selects the latest ready
revision, not an arbitrary revision or a primary rollback. Refresh returns
success with no output on HTTP 204 **acceptance**; revision propagation continues
asynchronously. It does not poll revisions or invent a target revision.

## Networking and teardown

```azurecli
az webapp silo vnet-integration add --resource-group MyGroup --name MyApp --silo WestApp --subnet /subscriptions/SUB/resourceGroups/NetworkGroup/providers/Microsoft.Network/virtualNetworks/WestNet/subnets/integration
az webapp silo vnet-integration show --resource-group MyGroup --name MyApp --silo WestApp
az appservice plan silo vnet-integration list --resource-group MyGroup --name MyPlan --silo WestPlan
az webapp silo vnet-integration update --resource-group MyGroup --name MyApp --silo WestApp --swift-supported false
az webapp silo vnet-integration remove --resource-group MyGroup --name MyApp --silo WestApp --yes
az webapp silo delete --resource-group MyGroup --name MyApp --silo WestApp --yes
az appservice plan silo delete --resource-group MyGroup --name MyPlan --silo WestPlan --yes
```

Site networking uses `virtualNetworkConnections/virtualNetwork`; update sends
PATCH. Plan networking inspection is read-only. Delete site silos before backing
plan silos.

The draft plan VNet-list contract declares an array, but the deployed API returns
an ARM envelope whose `properties` is an array of subnet entries. A handwritten
subclass accepts both shapes and maps the wrapped entries into the generated
model, retaining normal list output without inventing resource IDs. Unexpected
wrapped shapes are errors. Remove this adapter after correcting and regenerating
the service contract; generated Python remains unchanged.

## Validation and regeneration

The independent test-owned command catalog is
`tests\latest\active_backup_command_catalog.json` in the App Service module.
Offline tests exercise actual CLI parsing and generated requests, outputs,
pagination, async failures, resource waits and examples. They do not prove
deployed availability or close service defects.

The opt-in live scenarios cover only this limited surface. Live runs require
explicit authorization, an enabled subscription and the expected regional
capacity. These scenarios are currently live-only; replay recordings and full
command/argument coverage checks remain publication work. Developer-local run
reports, credentials and validation tooling are not committed test assets.

AAZ command models must accompany eventual CLI publication in `Azure/aaz`.
The local generation experiment retains those models under the ignored
`.x\active-backup\aaz-spike\limited-models-v2` directory. Regenerate from command
models; do not hand-edit the generated `aaz\latest` Python files. The generator's
shared `SwiftVirtualNetwork` resource-ID inference warning and the unmerged
service specification remain review dependencies. The location subclasses live
in `operations\active_backup.py` and directly inherit the matching generated
commands/operations. Remove this compatibility code after the service contract
has been corrected and regenerated, with create/update/read regressions passing.
