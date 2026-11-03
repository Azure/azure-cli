# App Service Active Backup preview

The preview manages plan and site **silos** through public ARM APIs. It does not
configure storage-backed backups, deployment slots, or slot traffic routing.

## Specification and scope

Commands are generated with AAZDev from the `2026-08-01` App Service contract in
[azure-rest-api-specs PR 44330](https://github.com/Azure/azure-rest-api-specs/pull/44330),
using merged source commit `2d07da92bcad212fdd5e2bffebf96563081ec250`.
Existing ordinary app/plan commands retain their API versions and support levels.

The implementation exposes 25 preview commands covering 21 HTTP operations
plus CLI update/wait behavior:

| Group | Commands |
|---|---|
| `appservice plan silo` | create, update, show, list, delete, wait |
| `appservice plan silo vnet-integration` | list |
| `webapp silo` | create, update, show, list, delete, wait, refresh |
| `webapp silo vnet-integration` | list, show, add, update, remove |
| `webapp managed-traffic` | list, show, update |
| `webapp last-known-good` | list, show, mark |

Configuration, deployments, processes, containers, logs, WebJobs, diagnostics,
metrics, antivirus, extension invocation and other silo pass-through APIs are
deferred. Standalone operation-status commands and managed-traffic metrics are
also deferred because this specification does not define them.

AAZ supplies authentication, cloud selection, error handling, pagination,
serialization and long-running-operation handling. The CLI does not downgrade
the API version or call internal GeoMaster endpoints. Commands use generated AAZ
implementations directly, without custom transport, response adapters or polling
overrides. A small identity validator rejects plan, slot and extension-resource IDs that core ID expansion could
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

`--name` identifies the primary; `--silo` identifies the child. Create commands use
standard AAZ location resolution, including configured
defaults and resource-group location. Specify `--location` explicitly to select
the replica region rather than accidentally using the primary region.
`--primary-location` is required on both silo create commands and maps to
`properties.primaryLocation`. Missing input is rejected before sending a request. The optional
`--silo-location` maps to the legacy `properties.siloLocation` field; when supplied,
it must match the root location. The CLI does not synthesize that compatibility
property.

For example, a site create request contains:

```json
{
  "location": "westus2",
  "properties": {
    "primaryLocation": "eastus",
    "trafficMode": "Active"
  }
}
```

Resource commands return the modeled ARM resource; collections return item
arrays and follow `nextLink`. Generic GET+PUT updates preserve existing modeled
writable fields, exclude read-only fields, and support `--set`, `--add` and
`--remove`. Tags are supported on create and update through `--tags`, for example
`--tags environment=preview`. Generic property paths include the envelope, for example
`--set properties.instanceNumberOverride=2`. Explicit `false` is not omission.
Updates preserve root location from the GET response rather than substituting a
configured default or inferring it from a nested field. There is no `--location`
or `--traffic-mode` argument on silo update. Service validation remains authoritative
for immutable fields, worker counts and other resource restrictions.

The specification also declares tags-only PATCH operations for plan/site silos.
The CLI retains the generator's standard GET+PUT update behavior so that a single
update command supports both configuration and tags. It does not expose a separate
tags-only PATCH command.

Silo show/update/delete/wait and site networking mutations/point reads support a
complete silo resource ID through `--ids`. Plan and site VNet listing use the named
parent/silo arguments.
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

The accepted App Service PUT contract returns 200 or 202, including a resource
body on 202. The CLI uses the standard Azure async poller and does not remove
`Azure-AsyncOperation` headers to force Location polling. Empty or malformed
async-status responses can therefore fail while the service operation continues.
Use `--no-wait` to submit without operation polling, then observe resource state
with the separate wait/show commands when appropriate.

Origin point-read failures are returned directly, without a collection fallback.
Conflict messages use standard AAZ/core error formatting; legacy App Service
errors may have less detail. No service failure is converted into success.

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
az webapp silo vnet-integration list --resource-group MyGroup --name MyApp --silo WestApp
az appservice plan silo vnet-integration list --resource-group MyGroup --name MyPlan --silo WestPlan
az webapp silo vnet-integration update --resource-group MyGroup --name MyApp --silo WestApp --swift-supported false
az webapp silo vnet-integration remove --resource-group MyGroup --name MyApp --silo WestApp --yes
az webapp silo delete --resource-group MyGroup --name MyApp --silo WestApp --yes
az appservice plan silo delete --resource-group MyGroup --name MyPlan --silo WestPlan --yes
```

Site networking uses `virtualNetworkConnections/virtualNetwork`; update sends
PATCH. Plan networking inspection is read-only. Delete site silos before backing
plan silos.

Plan VNet inspection returns its modeled ARM envelope, including `id`, `location`
and the `properties` array of subnet entries with allocation metadata. To select
subnet IDs, use `--query "properties[].subnetResourceId"`. Site VNet listing returns
the items from the standard `value` collection and follows `nextLink`.

## Accepted backend rollout gaps

The CLI targets the merged contract even where backend implementation is still
rolling out. ARM review accepted temporary gaps for tags-only PATCH
([40399839](https://dev.azure.com/msazure/Antares/_workitems/edit/40399839)),
site-silo VNet collection GET
([40409856](https://dev.azure.com/msazure/Antares/_workitems/edit/40409856)) and
`trafficMode` read-back
([40409857](https://dev.azure.com/msazure/Antares/_workitems/edit/40409857)).
The CLI neither feature-detects these capabilities nor supplies fallback values
or substitute requests. Calls can fail or read-back fields can be absent until
the backend changes deploy. Track rollout and interim failures through the
service team's agreed IcM process; these accepted gaps are not additional
Swagger approval gates.

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
The local generation workspace retains those models under the ignored
`.x\active-backup\aaz-spike\merged-models` directory, with its source pin and hash
in `merged-generation-result.json`. The locally prepared companion change is
`.x\active-backup\aaz-spike\aaz-companion\active-backup-models.patch`; its manifest
records the upstream `Azure/aaz` baseline and file hashes. It preserves existing
command indexes and excludes unused intermediate command groups. Regenerate from command
models; do not hand-edit the generated `aaz\latest` Python files. The generator's
shared `SwiftVirtualNetwork` resource-ID inference warning remains a generation
limitation; command routing is covered by the offline regressions. There are no
Active Backup compatibility subclasses.
