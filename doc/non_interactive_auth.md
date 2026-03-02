# Non-interactive authentication for Azure CLI

This document explains recommended non-interactive authentication modes for automation (CI/CD, scripts, headless servers) and provides safe examples and a small helper script.

Supported modes

- Service Principal (client secret) — recommended for CI systems where a secret can be stored securely.
- Managed Identity (MSI) — recommended when running inside Azure (VM, VMSS, App Service, Function) and you can assign a managed identity.
- Device Code — useful for ad-hoc non-browser sign-ins when interactive approval is acceptable.
- Workload Identity — recommended for Kubernetes-based workloads using federated credentials.

Environment variables

The helper scripts and CI examples below use the following environment variables (common conventions):

- AZURE_AUTH_MODE: one of `service-principal`, `managed-identity`, `device-code`, `workload-identity` (optional; script will try to auto-detect)
- AZURE_CLIENT_ID
- AZURE_CLIENT_SECRET
- AZURE_TENANT_ID
- AZURE_FEDERATED_TOKEN_FILE (for workload identity / token file)

Security guidance

- Store secrets in your CI secret store (GitHub Secrets, Azure DevOps variable groups, etc.).
- Prefer managed identities or workload identity federation where possible to avoid long-lived secrets.
- Limit permissions using least-privilege service principals.

Examples

Service principal (GitHub Actions)

```yaml
# GitHub Actions snippet
env:
  AZURE_CLIENT_ID: ${{ secrets.AZURE_CLIENT_ID }}
  AZURE_CLIENT_SECRET: ${{ secrets.AZURE_CLIENT_SECRET }}
  AZURE_TENANT_ID: ${{ secrets.AZURE_TENANT_ID }}

steps:
- name: Install Azure CLI
  uses: azure/CLI@v1

- name: Login with service principal
  run: az login --service-principal -u "$AZURE_CLIENT_ID" -p "$AZURE_CLIENT_SECRET" --tenant "$AZURE_TENANT_ID"
```

Managed Identity (Azure VM / App Service)

On an Azure VM with a system-assigned or user-assigned managed identity you can run:

```bash
az login --identity
```

Device code (interactive)

```bash
az login --use-device-code
```

Workload identity (Kubernetes with federated credentials)

Use Azure AD Workload Identity or federated credential to obtain a token and then use `az account get-access-token` or configure the environment according to your runtime. For CI that provides a token file, a short helper can run `az login --federated-token` style workflows; see the example helper script in `scripts/non_interactive_login.py`.

Helper script

A small helper script `scripts/non_interactive_login.py` is included that demonstrates safe detection of environment variables and returns the recommended `az login` command for common automation scenarios. The script is intentionally conservative and does not run `az` by default in unit tests.

Further reading

- https://docs.microsoft.com/azure/active-directory/develop/howto-create-service-principal-portal
- https://docs.microsoft.com/azure/active-directory/managed-identities-azure-resources/overview
- https://learn.microsoft.com/azure/aks/workload-identity-overview
