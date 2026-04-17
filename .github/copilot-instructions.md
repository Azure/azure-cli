| description | Guide the user to generate a private `azure-mgmt-appconfiguration` Python SDK from its TypeSpec spec and integrate it into the Azure CLI `appconfig` command module for local development and testing. |
| --- | --- |

# Goal

Help the user generate a private `azure-mgmt-appconfiguration` Python SDK from the App Configuration TypeSpec spec, build it as a wheel, and consume it inside the Azure CLI `appconfig` command module. High-level steps involved:

1. Outline workflow
2. Confirm service information
3. Verify repositories
4. Set up the SDK generation environment
5. Generate the SDK from TypeSpec
6. Build the SDK wheel
7. Install the wheel into the CLI dev environment
8. Update CLI dependency declarations

---

## Generate SDK Locally

### Step 1: Outline workflow

Goal: Ensure the user understands the end-to-end process before starting.

Actions:

- MUST present the high-level steps listed in the Goal section above.
- MUST ask the user to confirm they are ready to proceed before continuing.

---

### Step 2: Confirm service information

Goal: Confirm the fixed service values for App Configuration before proceeding.

Actions:

- Use the following fixed values throughout all steps — do NOT prompt the user for these:
  - **Service name**: `appconfiguration`
  - **Package name**: `azure-mgmt-appconfiguration`
  - **Python namespace**: `azure.mgmt.appconfiguration`
  - **SDK output folder**: `sdk/appconfiguration/azure-mgmt-appconfiguration/`
  - **CLI module**: `appconfig`
- Package version is determined automatically by the generation tooling and does not need to be provided.
- Simply inform the user of these values and ask them to confirm before continuing.

---

### Step 3: Verify repositories

Goal: Ensure both required repositories are cloned locally.

Actions:

- Prompt the user to provide the local path to their clone of **azure-sdk-for-python** (the SDK repo).
- Prompt the user to provide the local path to their clone of **azure-rest-api-specs** (the REST specs repo).
- For each path:
  - Check the path exists on disk.
  - Verify it contains the expected top-level structure (`sdk/` for the SDK repo, `specification/` for the specs repo).
  - If a path is missing or invalid → instruct the user to clone the correct repository:
    ```bash
    git clone https://github.com/Azure/azure-sdk-for-python.git
    git clone https://github.com/Azure/azure-rest-api-specs.git
    ```
- Validate that `tspconfig.yaml` exists at:
  ```
  {specs-repo}/specification/appconfiguration/resource-manager/Microsoft.AppConfiguration/AppConfiguration/tspconfig.yaml
  ```
  If not found, inform the user and ask them to confirm the correct path before continuing.

---

### Step 4: Set up the SDK generation environment

Goal: Install all tooling required to generate a Python SDK from TypeSpec.

Actions:

- MUST check each prerequisite automatically by running the commands below. Do NOT ask the user to run them.
- Check **Python 3.9+** by running:
  ```bash
  python --version
  ```
  If the version is below 3.9 or Python is not found, instruct the user to install it from https://www.python.org/downloads/ and wait for confirmation before continuing.
- Check **Node.js 20 LTS+** by running:
  ```bash
  node --version
  ```
  If the version is below 20 or Node is not found, instruct the user to install it from https://nodejs.org/en/download/ and wait for confirmation before continuing.
- Install the TypeSpec client generator CLI globally by running:
  ```bash
  npm install -g @azure-tools/typespec-client-generator-cli
  ```
  Verify it installed by running `tsp-client --version`. If it fails, inform the user and wait for confirmation before continuing.
- Create and activate a Python virtual environment inside the SDK repo by running:
  ```bash
  cd {sdk-repo-path}
  python -m venv .venv
  ```
  Then activate it:
  ```bash
  # Windows
  .\.venv\Scripts\Activate.ps1
  # Linux / macOS
  source .venv/bin/activate
  ```
- Install Python dependencies by running:
  ```bash
  python scripts/dev_setup.py -p azure-core
  pip install tox setuptools build wheel
  ```
  If any command fails, show the error output and wait for the user to resolve it before continuing.

---

### Step 5: Generate the SDK from TypeSpec

Goal: Run the SDK generator to produce Python source code from the TypeSpec specification.

Actions:

- Retrieve the current HEAD SHA of the REST specs repo:
  ```bash
  git -C {specs-repo-path} rev-parse HEAD
  ```
- Create a file named `generatedInput.json` **outside both repos** with the following content. Substitute all placeholder values:
  ```json
  {
    "specFolder": "{absolute-path-to-azure-rest-api-specs}",
    "headSha": "{output-of-git-rev-parse-HEAD}",
    "repoHttpsUrl": "https://github.com/Azure/azure-rest-api-specs",
    "relatedTypeSpecProjectFolder": [
      "specification/appconfiguration/resource-manager/Microsoft.AppConfiguration/AppConfiguration/"
    ]
  }
  ```
- Confirm the `tspconfig.yaml` at `specification/appconfiguration/resource-manager/Microsoft.AppConfiguration/AppConfiguration/tspconfig.yaml` contains a Python emitter block like:
  ```yaml
  parameters:
    "service-dir":
      default: "sdk/appconfiguration"
  options:
    "@azure-tools/typespec-python":
      emitter-output-dir: "{output-dir}/{service-dir}/azure-mgmt-appconfiguration"
      namespace: "azure.mgmt.appconfiguration"
      generate-test: true
      generate-sample: true
      flavor: "azure"
  ```
- Run the generator (from the SDK repo root, with the venv activated):
  ```bash
  python -m packaging_tools.sdk_generator ..\generatedInput.json ..\generatedOutput.json
  ```
- After generation completes, show the user the contents of `generatedOutput.json` and confirm the output was placed at:
  ```
  {sdk-repo}/sdk/appconfiguration/azure-mgmt-appconfiguration/
  ```

---

## Build SDK Wheel Locally

### Step 6: Build the SDK wheel

Goal: Package the generated Python SDK as a `.whl` file for local installation.

Actions:

- Navigate to the generated SDK project directory:
  ```bash
  cd {sdk-repo}/sdk/appconfiguration/azure-mgmt-appconfiguration
  ```
- Build the wheel:
  ```bash
  python -m build --wheel --outdir dist/
  ```
- Confirm that a file matching `azure_mgmt_appconfiguration-{version}-py3-none-any.whl` was created in `dist/`.
- Record the **absolute path** to the wheel; it will be used in later steps.

---

## Integrate the Private SDK into Azure CLI

### Step 7: Install the wheel into the CLI dev environment

Goal: Make the private SDK available to the Azure CLI source installation.

Actions:

- Prompt the user to confirm the Azure CLI repo root path (this repository).
- Activate the CLI development virtual environment:
  ```bash
  # Windows
  .\env\Scripts\Activate.ps1
  # Linux / macOS
  source env/bin/activate
  ```
- Install the wheel built in Step 6:
  ```bash
  pip install {absolute-path-to-wheel} --force-reinstall
  ```
- If the wheel is hosted at a remote URL (e.g. an Azure Pipelines artifact), use:
  ```bash
  pip install {wheel-url} --force-reinstall
  ```
- Confirm installation succeeded:
  ```bash
  pip show azure-mgmt-appconfiguration
  ```

---

### Step 8: Update CLI dependency declarations

Goal: Record the new SDK version in all CLI dependency files so that builds and installs are reproducible.

Actions:

- Open `src/azure-cli/setup.py` and locate the `install_requires` list.
  - If an entry for `azure-mgmt-appconfiguration` already exists, update its pinned version.
  - If no entry exists, add one:
    ```python
    'azure-mgmt-appconfiguration=={version}',
    ```
- Apply the same version update to each platform requirements file that references this package (only update files where the package already appears):
  - `src/azure-cli/requirements.py3.windows.txt`
  - `src/azure-cli/requirements.py3.Linux.txt`
  - `src/azure-cli/requirements.py3.Darwin.txt`
- MUST show the user a diff of every file changed in this step and ask for confirmation before saving.

---

## Naming Conventions

| Concept | Value |
|---|---|
| Service name | `appconfiguration` |
| Package name | `azure-mgmt-appconfiguration` |
| Python namespace | `azure.mgmt.appconfiguration` |
| SDK folder (SDK repo) | `sdk/appconfiguration/azure-mgmt-appconfiguration/` |
| CLI module | `appconfig` |
| Wheel filename | `azure_mgmt_appconfiguration-{version}-py3-none-any.whl` |

---

## References

- [SDK Generation from TypeSpec](https://github.com/Azure/azure-sdk-for-python/blob/main/doc/dev/mgmt/generation.md)
- [Local SDK Workflow (azure-sdk-for-python)](https://github.com/Azure/azure-sdk-for-python/blob/main/eng/common/instructions/azsdk-tools/local-sdk-workflow.instructions.md)
