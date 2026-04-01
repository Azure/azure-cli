---
name: cdn-cli
description: "Develop and maintain Azure CDN/AFD CLI commands. Use when: adding new CDN or AFD commands, modifying cdn module code, writing cdn/afd tests, debugging cdn command issues, working with cdn custom domains, endpoints, origins, profiles, routes, rules, secrets, security policies, WAF policies, or migration commands."
argument-hint: "Describe the CDN/AFD CLI task, e.g. 'add a new cdn endpoint command' or 'fix afd origin create'"
---

# Azure CDN/AFD CLI Development

## Overview

The CDN CLI module (`src/azure-cli/azure/cli/command_modules/cdn/`) implements Azure CLI commands for both **Azure CDN** (`az cdn ...`) and **Azure Front Door** (`az afd ...`). Both command groups share the same module codebase and SDK (`azure-mgmt-cdn`).

## Project Structure

```
src/azure-cli/azure/cli/command_modules/cdn/
├── __init__.py              # CdnCommandsLoader - module entry point
├── commands.py              # Command table registration
├── _params.py               # Argument definitions
├── _help.py                 # Help text definitions
├── _validators.py           # Input validators
├── _actions.py              # Custom argparse actions (e.g. OriginType)
├── _client_factory.py       # Service client factories
├── linter_exclusions.yml    # Linter rule exclusions
├── aaz/                     # Auto-generated AAZ (Atomic Azure CLI) commands
│   └── latest/
│       ├── cdn/             # CDN AAZ commands
│       └── afd/             # AFD AAZ commands
├── custom/                  # Custom command implementations
│   ├── custom.py            # Legacy CDN custom commands (SDK-based)
│   ├── custom_cdn.py        # CDN commands extending AAZ base classes
│   ├── custom_afdx.py       # AFD commands extending AAZ base classes
│   ├── custom_rule_util.py  # Shared rule/condition/action utilities
│   └── custom_waf.py        # WAF policy management
└── tests/latest/            # Scenario tests
    ├── scenario_mixin.py        # CDN test helpers
    ├── afdx_scenario_mixin.py   # AFD test helpers
    ├── test_profile_scenarios.py
    ├── test_endpoint_scenarios.py
    ├── test_origin_scenarios.py
    ├── test_custom_domain_scenarios.py
    ├── test_edge_action_scenario.py
    ├── test_nodes_scenarios.py
    ├── test_afd_profile_scenarios.py
    ├── test_afd_endpoint_scenarios.py
    ├── test_afd_origin_scenarios.py
    ├── test_afd_origin_group_scenarios.py
    ├── test_afd_route_scenarios.py
    ├── test_afd_rule_scenarios.py
    ├── test_afd_secret_scenarios.py
    ├── test_afd_security_policy_scenarios.py
    ├── test_afd_custom_domain_scenarios.py
    ├── test_afd_log_analytic_scenarios.py
    └── recordings/              # VCR test recordings
```

## Command Groups

### CDN Commands (`az cdn`)
- `cdn profile` — Create/update/delete/show/list CDN profiles
- `cdn endpoint` — Manage CDN endpoints (create, update, delete, purge, load, start, stop)
- `cdn endpoint rule` — Manage delivery rules on endpoints
- `cdn endpoint rule condition` — Manage rule conditions
- `cdn endpoint rule action` — Manage rule actions
- `cdn origin` — Manage CDN endpoint origins
- `cdn origin-group` — Manage CDN origin groups
- `cdn custom-domain` — Manage custom domains (enable-https, disable-https)
- `cdn name-exists` — Check resource name availability
- `cdn edge-node` — List edge nodes
- `cdn waf policy` — Manage WAF policies
- `cdn profile-migration` — Migrate CDN profiles to AFD

### AFD Commands (`az afd`)
- `afd profile` — Create/update/delete/show/list AFD profiles
- `afd endpoint` — Manage AFD endpoints
- `afd origin` — Manage AFD origins
- `afd origin-group` — Manage AFD origin groups
- `afd route` — Manage AFD routes
- `afd rule` — Manage AFD rules (conditions, actions)
- `afd rule condition` — Add/remove/list rule conditions
- `afd rule action` — Add/remove/list rule actions
- `afd custom-domain` — Manage AFD custom domains
- `afd secret` — Manage AFD secrets (certificates)
- `afd security-policy` — Manage AFD security policies (WAF)
- `afd log-analytic` — Query AFD log analytics
- `afd profile log-scrubbing` — Manage log scrubbing settings

## Code Generation with aaz-dev

The `aaz-dev` tool generates AAZ commands from Azure REST API specs (Swagger/OpenAPI). It supports **two workflows**:

### Quick Path: Pure CLI Generation

```powershell
# Generate code directly from spec — uses default tag (latest stable)
aaz-dev cli generate --spec cdn --module cdn --cli-path C:\Users\jingnanxu\source\repos\cli
```

This converts the spec from `azure-rest-api-specs/specification/cdn/` into AAZ commands using the default tag. If the result isn't ideal, refine with the UI.

### Generate for a Specific API Version (swagger tag)

Use `generate-by-swagger-tag` to target a specific API version. First check available tags:

```powershell
# List available swagger tags in CDN spec
Select-String -Path "C:\Users\jingnanxu\source\repos\swagger\specification\cdn\resource-manager\Microsoft.Cdn\Cdn\readme.md" -Pattern "^### Tag:"
```

Then generate for the desired tag:

```powershell
aaz-dev cli generate-by-swagger-tag `
  --aaz-path C:\Users\jingnanxu\source\repos\aaz `
  --cli-path C:\Users\jingnanxu\source\repos\cli `
  --name cdn `
  --sm "C:\Users\jingnanxu\source\repos\swagger\specification\cdn\resource-manager\Microsoft.Cdn\Cdn" `
  --rp Microsoft.Cdn `
  --tag package-preview-2025-09 `
  --profile latest
```

**Parameters:**
- `--sm` — swagger module path (the folder containing `readme.md` with tag definitions)
- `--rp` — resource provider name (e.g., `Microsoft.Cdn`)
- `--tag` — swagger tag matching a `### Tag:` entry in `readme.md` (e.g., `package-preview-2025-09` for API `2025-09-01-preview`)
- `--profile` — CLI profile, typically `latest`
- `--name` — target CLI module name

**Note:** This command updates both the `aaz` registry (command models) and the `cli` repo (generated code). Check `git status` in both repos after running.

### Interactive Path: Web UI

```powershell
# Launch web UI with all repo paths
aaz-dev run `
  --swagger-path C:\Users\jingnanxu\source\repos\swagger `
  --aaz-path C:\Users\jingnanxu\source\repos\aaz `
  --cli-path C:\Users\jingnanxu\source\repos\cli `
  -e C:\Users\jingnanxu\source\repos\extension
```

Opens at **http://127.0.0.1:5000**. Workflow:
1. Open **Workspace Editor** — select spec, prune/edit the command interface (rename params, flatten, hide args)
2. Click **EXPORT** when done
3. Switch to **CLI Generator** — select target module (e.g., `cdn`), check commands, click **GENERATE**

### Auto-select Resources Script

When creating a workspace with many resources (CDN has 98+), use the [auto_select_resources.py](./scripts/auto_select_resources.py) script to pre-select resources with correct versions. It auto-detects resources that have existing AAZ command models (inheritance).

```powershell
# Requires aaz-dev web UI running on http://127.0.0.1:5000

# Dry run: see what would be selected
python .github\skills\cdn-cli\scripts\auto_select_resources.py --version 2025-09-01-preview --dry-run

# Create workspace and add resources
python .github\skills\cdn-cli\scripts\auto_select_resources.py --workspace cdn-0901 --version 2025-09-01-preview
```

The script:
- Queries swagger spec for all CDN resources
- Checks AAZ registry for existing command models (inheritance)
- Selects target version for resources that have it, falls back to inherited version
- Creates a workspace and adds all selected resources via API

Docs:
- [Workspace Editor](https://azure.github.io/aaz-dev-tools/pages/usage/workspace-editor/)
- [CLI Generator](https://azure.github.io/aaz-dev-tools/pages/usage/cli-generator/)
- [Customization](https://azure.github.io/aaz-dev-tools/pages/usage/customization/)

### AAZ Flow MCP Server

The project includes an MCP server at `tools/aaz-flow/` that wraps aaz-dev as Copilot tools. In Codespace, it's pre-configured. Use cases:
- "generate code for azure cli" — generate models and code
- "generate test for cdn module" — generate test cases

### Local Environment Setup

The following paths are specific to the current dev machine. aaz-dev reads them from **environment variables**:

| Env Var | Value | Purpose |
|---------|-------|---------|
| `AAZ_SWAGGER_PATH` | `C:\Users\jingnanxu\source\repos\swagger` | azure-rest-api-specs repo |
| `AAZ_PATH` | `C:\Users\jingnanxu\source\repos\aaz` | AAZ command model registry |
| `AAZ_CLI_PATH` | `C:\Users\jingnanxu\source\repos\cli` | azure-cli repo |
| `AAZ_CLI_EXTENSION_PATH` | `C:\Users\jingnanxu\source\repos\extension` | azure-cli-extensions repo |

**Full setup commands (PowerShell):**

```powershell
# Step 1: Activate virtual environment
& C:\Users\jingnanxu\source\repos\azdev\Scripts\Activate.ps1

# Step 2: Set environment variables (required for aaz-dev)
$env:AAZ_SWAGGER_PATH = "C:\Users\jingnanxu\source\repos\swagger"
$env:AAZ_PATH = "C:\Users\jingnanxu\source\repos\aaz"
$env:AAZ_CLI_PATH = "C:\Users\jingnanxu\source\repos\cli"
$env:AAZ_CLI_EXTENSION_PATH = "C:\Users\jingnanxu\source\repos\extension"

# Step 3: Verify
aaz-dev --version
```

**Generate CDN module code:**

```powershell
# Generate from spec (CDN swagger spec at specification/cdn)
aaz-dev cli generate --spec cdn --module cdn --cli-path C:\Users\jingnanxu\source\repos\cli

# For Front Door spec
aaz-dev cli generate --spec frontdoor --module cdn --cli-path C:\Users\jingnanxu\source\repos\cli
```

Key paths in the workspace:
- Swagger specs: `swagger\specification\cdn` (CDN), `swagger\specification\frontdoor` (Front Door)
- AAZ registry: `aaz`
- Virtual env: `azdev\Scripts\Activate.ps1`

Other related repos:
- `extension` — azure-cli-extensions
- `cdnrp` — CDN RP source
- `Networking-Frontdoor-ControlPlane` / `Networking-Frontdoor-Delaware` — Front Door control plane
- `Azure-CdnLogAnalysis` — CDN log analysis
- `AFDBillingPipeline` — AFD billing pipeline

### Setup from scratch (if not already configured)

```bash
# Install aaz-dev
uv pip install aaz-dev

# Clone companion repos (needed for specs and command model registry)
git clone https://github.com/Azure/aaz.git
git clone https://github.com/Azure/azure-rest-api-specs.git
```

## Development Patterns

### Adding a New Command

1. **Generate AAZ base command**: Use `aaz-dev cli generate` or the Web UI to create the base command in `aaz/latest/cdn/` or `aaz/latest/afd/`
2. **Customize (optional)**: Subclass the AAZ base class in `custom/custom_cdn.py` or `custom/custom_afdx.py` to add custom logic
3. **Register in `commands.py`**: Import and assign to `self.command_table['command name']`
4. **Add help text in `_help.py`**: Use the `helps['command name']` pattern
5. **Add parameters in `_params.py`** if needed for non-AAZ commands

### AAZ Command Customization Pattern

```python
from azure.cli.command_modules.cdn.aaz.latest.afd.profile import Create as _AFDProfileCreate
from azure.cli.core.aaz import AAZStrArg, AAZBoolArg

class AFDProfileCreate(_AFDProfileCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        # Add or modify arguments here
        args_schema.location._registered = False  # Hide argument
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        args.location = 'global'  # Set defaults
```

### Command Registration Pattern

```python
# In commands.py
from .custom.custom_cdn import CDNProfileCreate
self.command_table['cdn profile create'] = CDNProfileCreate(loader=self)
```

### Help Text Pattern

```python
# In _help.py
helps['cdn profile create'] = """
type: command
short-summary: Create a new CDN profile.
parameters:
  - name: --sku
    type: string
    short-summary: The pricing tier.
examples:
  - name: Create a CDN profile.
    text: az cdn profile create -g group -n profile --sku Standard_Microsoft
"""
```

## Testing

### Test Structure

Tests use `ScenarioTest` from `azure.cli.testsdk` with mixin classes:
- `CdnScenarioMixin` — Helper methods for CDN commands
- `CdnAfdScenarioMixin` — Helper methods for AFD commands

### Running Tests

```bash
# Run all CDN tests
azdev test cdn

# Run a specific test file
azdev test test_endpoint_scenarios

# Run a specific test
azdev test test_endpoint_scenarios::CdnEndpointScenarioTest::test_endpoint_crud

# Run in live mode (against real Azure)
azdev test cdn --live

# Re-record tests
azdev test cdn --live
```

### Writing a Test

```python
from azure.cli.testsdk import ResourceGroupPreparer, JMESPathCheck, ScenarioTest
from .scenario_mixin import CdnScenarioMixin

class CdnMyFeatureTest(CdnScenarioMixin, ScenarioTest):
    @ResourceGroupPreparer(additional_tags={'owner': 'jingnanxu'})
    def test_my_feature(self, resource_group):
        profile_name = 'profile123'
        self.profile_create_cmd(resource_group, profile_name)

        checks = [JMESPathCheck('name', profile_name)]
        self.profile_show_cmd(resource_group, profile_name, checks=checks)
```

### Test Helpers

Use `CdnScenarioMixin` methods like `profile_create_cmd`, `endpoint_create_cmd`, `origin_show_cmd`, etc. Use `CdnAfdScenarioMixin` for AFD commands like `afd_profile_create_cmd`, `afd_endpoint_create_cmd`, etc.

## Key SDK and Dependencies

- **SDK**: `azure-mgmt-cdn` (CdnManagementClient)
- **Client factory**: `_client_factory.py` — provides `cf_cdn`, `cf_endpoints`, `cf_custom_domain`, etc.
- **AAZ framework**: `azure.cli.core.aaz` — the new atomic command framework
- **Resource type**: `ResourceType.MGMT_CDN`

## Linting

- Run `azdev linter cdn` to check for CLI linting issues
- Exclusions are defined in `linter_exclusions.yml` (e.g., `option_length_too_long`)

## Common Pitfalls

- CDN profile location is always `'global'` — set it in `pre_operations` and hide the `--location` argument
- AFD commands use `--profile-name` while CDN uses both `--profile-name` and `-n` patterns
- Rule conditions/actions have complex nested structures — see `custom_rule_util.py` for the mapping
- Test recordings are stored in `tests/latest/recordings/` and can be large
