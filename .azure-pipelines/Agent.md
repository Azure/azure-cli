# Pipeline and packaging handoff

Use this reference when changing CLI build-tool versions or packaging. It supplements the [repository safety rules](../.github/instructions/agent-safety.instructions.md); it does not authorize changes to other repositories or pipeline definitions.

Keep repository edits local unless explicitly authorized otherwise. Pipeline owners handle external definitions, issue and PR creation, pushes, and releases.

## In-repository pins

Keep `azdev==0.2.15` and `azure-cli-diff-tool==0.1.2` aligned in:

- [Shared setup](templates/azdev_setup.yml): main and breaking-change CI setup.
- [Automation tests](templates/automation_test.yml): full and incremental tests; forwards both package parameters to shared setup.
- [GitHub environment setup](../.github/actions/env-setup/action.yml): shared action used by CLI checks.
- [Live-test setup](../scripts/live_test/CLITest.yml): common variables used by the Linux, Windows, and macOS jobs.

Use released package requirements, not personal-fork URLs or commit pins. Before merging a pin update, confirm the version is installable from the package index used by each job. A Git tag, GitHub release, or successful artifact build is not proof of PyPI publication. Preserve parameter overrides and the single pip install transaction for both packages.

Keep [pytest constraints](pytest-constraints.txt) available when breaking-change tests switch branches. Validate YAML parsing, embedded shell syntax, dependency resolution, `pip check`, and the affected setup/test/reporting paths. Do not equate local smoke tests with a successful full pipeline.

## Verified pipeline references

These are **YAML-backed definitions**, not the classic pipelines that still need inventory. Definitions were checked on 2026-11-09 in the `azclitools` organization, project `5147fa83-336e-44ef-bbe0-c86b8ae86cbb`.

| Pipeline | Definition | Source |
| --- | --- | --- |
| Azure.azure-cli | [32](https://dev.azure.com/azclitools/5147fa83-336e-44ef-bbe0-c86b8ae86cbb/_build?definitionId=32) | [azure-pipelines.yml](../azure-pipelines.yml) |
| Azure.azure-cli Full Test | [62](https://dev.azure.com/azclitools/5147fa83-336e-44ef-bbe0-c86b8ae86cbb/_build?definitionId=62) | [azure-pipelines-full-tests.yml](../azure-pipelines-full-tests.yml) |
| Azure.azure-cli Breaking Change Test | [308](https://dev.azure.com/azclitools/5147fa83-336e-44ef-bbe0-c86b8ae86cbb/_build?definitionId=308) | [.azure-pipelines/breaking-change-tests.yml](breaking-change-tests.yml) |
| Azure.azdev | [60](https://dev.azure.com/azclitools/5147fa83-336e-44ef-bbe0-c86b8ae86cbb/_build?definitionId=60) | [azure-cli-dev-tools build](https://github.com/Azure/azure-cli-dev-tools/blob/dev/azure-pipelines.yml) |
| Azure.azdev-cli | [61](https://dev.azure.com/azclitools/5147fa83-336e-44ef-bbe0-c86b8ae86cbb/_build?definitionId=61) | [azure-cli-dev-tools integration tests](https://github.com/Azure/azure-cli-dev-tools/blob/dev/azure-pipelines-cli.yml) |

For azdev 0.2.15, [build 372242](https://dev.azure.com/azclitools/5147fa83-336e-44ef-bbe0-c86b8ae86cbb/_build/results?buildId=372242) produced `metadata` and `pypi` artifacts from commit `441d577696b6e6d892f42c9fa049a36c899b8333`, tagged [v0.2.15](https://github.com/Azure/azure-cli-dev-tools/releases/tag/v0.2.15). Run number `20261109.4` is not unique across pipelines; verify definition, commit, version, and artifact name before releasing.

## External consumers requiring follow-up

- **Classic build/release definitions and shared task groups:** these can contain inline install commands, script references, agent-image dependencies, variable-group overrides, and environment-specific toolchains outside this Git repository. The public release-definition query returned no visible definitions; this is not a complete inventory. Owners must supply authenticated definition links, revisions, environments, and script locations. Do not invent IDs or change production definitions as part of a source-only PR.
- **Reference-documentation pipelines:** [TriggerReferenceDocsCI.yml](../.github/workflows/TriggerReferenceDocsCI.yml) queues external latest/LTS definitions selected by `ADO_DocsReference_Latest_Pipeline_ID` and `ADO_DocsReference_LTS_Pipeline_ID`. Organization and project are also configured outside this repository. Resolve them with the docs owners; do not copy credentials or secret values into issues.
- **Extension release detection:** the reported external script `find_extension_upgraded.py` imports `parse_version` from `pkg_resources`. Its owning repository, pipeline definition, and exact path have not been identified here. The reported failing run used azdev 0.2.14/setuptools 84.2.1; the preceding successful run used 0.2.13/79.0.1. These package versions are reported observations; use pipeline definition and build IDs to identify the affected runs.
- **Extensions repository installers:** at [azure-cli-extensions commit 1c11485](https://github.com/Azure/azure-cli-extensions/tree/1c11485d529a92fc4088f5c00eb746b854574208), azdev 0.2.13 remains pinned in [shared setup](https://github.com/Azure/azure-cli-extensions/blob/1c11485d529a92fc4088f5c00eb746b854574208/.azure-pipelines/templates/azdev_setup.yml), [GitHub setup](https://github.com/Azure/azure-cli-extensions/blob/1c11485d529a92fc4088f5c00eb746b854574208/.github/actions/env-setup/action.yml), [version calculation](https://github.com/Azure/azure-cli-extensions/blob/1c11485d529a92fc4088f5c00eb746b854574208/.github/workflows/VersionCalPRComment.yml), and the [main pipeline](https://github.com/Azure/azure-cli-extensions/blob/1c11485d529a92fc4088f5c00eb746b854574208/azure-pipelines.yml). Update and validate them in that repository; this CLI pin change does not migrate all extension packages.
- **Legacy documentation path:** [test_ref_doc.sh](../scripts/ci/test_ref_doc.sh) explicitly installs Sphinx 1.6.7 and Jinja2 3.0.3. Confirm whether external classic definitions still invoke it. Do not install that stack into the same environment as azdev 0.2.15, which requires Sphinx 7 or newer.

## Environment isolation and removal criteria

Mutually incompatible toolchains need separate virtual environments or jobs, not sequential pip overrides in a shared interpreter. This requirement concerns dependency isolation; it does not assert that a deployment exclusive-lock check is configured.

- Use explicit interpreter paths and independent package directories, constraints, and configuration directories. Do not reuse a globally installed or cached environment across incompatible toolchains.
- Record Python, pip, azdev, setuptools, Sphinx, and diff-tool versions before each affected step; run `pip check` after installation. Keep credentials and sensitive configuration out of logs.
- Azdev 0.2.15 temporarily requires runtime `setuptools>=78.1.1,<80` for downstream `pkg_resources` imports. Its isolated PEP 517 build requirement remains `setuptools>=78.1.1` with no ceiling. A later upgrade of runtime setuptools can undo the workaround.
- Migrate external version comparisons to `packaging.version.parse`, declare `packaging` directly, and test prereleases, equivalent version forms, and nonstandard input handling. Remove the runtime cap only after all identified consumers pass with current setuptools.
- Validate classic-pipeline changes in non-production runs, including documentation generation, extension detection, packaging, and job-to-job isolation. Track certificate/TLS failures separately; the dependency changes do not fix certificates.

## Follow-up tracking

Suggested owner-filed Azure CLI issue: **Audit external classic pipelines and isolate incompatible packaging environments**. Record each definition link, revision, owner, environment, source script, declared dependencies, installed versions, and validation run. Completion requires an owner-confirmed inventory, tested environment isolation, migration of the legacy imports, and evidence supporting removal of temporary constraints.
