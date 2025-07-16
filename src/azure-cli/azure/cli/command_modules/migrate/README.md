# Azure CLI Migration Module

This module provides migration capabilities for Azure resources and workloads through Azure CLI commands.

## Features

- **Migration assessment**: Assessment tools for various Azure migration scenarios
- **Resource migration**: Commands for migrating different types of resources
- **Migration project management**: Create and manage Azure Migrate projects
- **Appliance management**: Configure and manage Azure Migrate appliances

## Prerequisites

- Azure CLI 2.0+
- Valid Azure subscription
- Appropriate permissions for migration operations

## Commands Overview

### Project Management Commands

```bash
# Create a migration project
az migrate project create --name "MyMigrationProject" --resource-group "MyRG" --location "East US"

# List migration projects
az migrate project list

# Show project details
az migrate project show --name "MyMigrationProject" --resource-group "MyRG"

# Delete migration project
az migrate project delete --name "MyMigrationProject" --resource-group "MyRG"
```

### Assessment Commands

```bash
# List assessments in a project
az migrate assessment list --project-name "MyMigrationProject" --resource-group "MyRG"

# Show assessment details
az migrate assessment show --assessment-name "MyAssessment" --project-name "MyMigrationProject" --resource-group "MyRG"
```

### Machine Discovery and Management

```bash
# List discovered machines
az migrate machine list --project-name "MyMigrationProject" --resource-group "MyRG"

# Show machine details
az migrate machine show --machine-name "MyMachine" --project-name "MyMigrationProject" --resource-group "MyRG"
```

### Solution Management

```bash
# Add solution to project
az migrate solution create --solution-type "Servers" --project-name "MyMigrationProject" --resource-group "MyRG"

# List solutions in project
az migrate solution list --project-name "MyMigrationProject" --resource-group "MyRG"

# Delete solution
az migrate solution delete --solution-type "Servers" --project-name "MyMigrationProject" --resource-group "MyRG"
```

## Architecture

The migration module consists of several key components:

1. **Project Management**: Core project operations and lifecycle management
2. **Assessment Operations**: Resource assessment and evaluation capabilities  
3. **Machine Discovery**: Discovery and inventory of source machines
4. **Solution Management**: Integration with Azure Migrate solutions

## Common Workflows

### Setting up a Migration Project

```bash
# Create resource group if needed
az group create --name "migration-rg" --location "East US"

# Create migration project
az migrate project create --name "server-migration-2025" --resource-group "migration-rg" --location "East US"

# Add server assessment solution
az migrate solution create --solution-type "Servers" --project-name "server-migration-2025" --resource-group "migration-rg"

# List project contents
az migrate project show --name "server-migration-2025" --resource-group "migration-rg"
```

### Viewing Migration Data

```bash
# List all discovered machines
az migrate machine list --project-name "server-migration-2025" --resource-group "migration-rg"

# View assessments
az migrate assessment list --project-name "server-migration-2025" --resource-group "migration-rg"

# Get detailed assessment information
az migrate assessment show --assessment-name "ServerAssessment" --project-name "server-migration-2025" --resource-group "migration-rg"
```

## Error Handling

The module includes comprehensive error handling for:

- Invalid project configurations
- Permission and authentication issues
- Resource not found scenarios
- Azure service connectivity problems

## Troubleshooting

### Common Issues

**Project Creation Fails**
- Verify you have Contributor permissions on the subscription
- Ensure the location supports Azure Migrate
- Check resource naming conventions

**Assessment Data Not Visible**
- Confirm the appliance is properly configured
- Verify network connectivity from appliance to Azure
- Check that discovery is running on the appliance

**Permission Errors**
- Ensure Azure Migrate Contributor role is assigned
- Verify subscription-level permissions for creating resources

## Contributing

When extending the migration module:

1. Follow Azure CLI command naming conventions
2. Implement proper error handling and validation
3. Add comprehensive help documentation
4. Include usage examples in help text
5. Update this README with new command examples

For more information on Azure Migrate, visit: https://docs.microsoft.com/azure/migrate/

## License

This project is licensed under the MIT License - see the LICENSE file for details.
az migrate discover --source-type vm

# Assess specific VM
az migrate assess hyperv-vm --vm-name "WebServer01"

# Create migration plan
az migrate plan create --source-name "WebServer01" --target-type azure-vm
```

### File Share Migration to Azure Files

```bash
# Assess file system
az migrate assess filesystem --path "\\\\FileServer\\Share"

# Create migration plan
az migrate plan create --source-name "FileShare" --target-type azure-files
```

## Troubleshooting

### PowerShell Not Found
- On Windows: Install PowerShell Core or ensure Windows PowerShell is available
- On Linux/macOS: Install PowerShell Core from https://github.com/PowerShell/PowerShell

### Permission Errors
- Ensure appropriate permissions for the operations being performed
- Some operations may require administrative privileges

### Script Execution Errors
- Check PowerShell execution policy
- Verify script syntax and compatibility
- Review error messages for specific guidance

## Contributing

When adding new migration scenarios:

1. Add PowerShell scripts to `_powershell_scripts.py`
2. Implement custom commands in `custom.py`
3. Register commands in `commands.py`
4. Add parameters in `_params.py`
5. Document commands in `_help.py`
6. Update this README with examples

## License

This project is licensed under the MIT License - see the LICENSE file for details.
