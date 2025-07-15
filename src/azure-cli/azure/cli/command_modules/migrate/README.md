# Azure CLI Migration Module

This module provides cross-platform migration capabilities by leveraging PowerShell cmdlets from within Azure CLI. The module works on Windows, Linux, and macOS when PowerShell Core is installed.

## Features

- **Cross-platform PowerShell execution**: Execute PowerShell migration commands on Windows, Linux, and macOS
- **Migration assessment**: Comprehensive assessment tools for various workloads
- **Migration planning**: Create and manage structured migration plans
- **Specialized assessments**: Dedicated commands for SQL Server, Hyper-V, file systems, and network configurations
- **Custom script execution**: Run organization-specific PowerShell migration scripts

## Prerequisites

### Windows
- Windows PowerShell 5.1+ or PowerShell Core 6.0+
- Azure CLI

### Linux/macOS
- PowerShell Core 6.0+ (required)
- Azure CLI

To install PowerShell Core on Linux/macOS, visit: https://github.com/PowerShell/PowerShell

## Commands Overview

### Basic Migration Commands

```bash
# Check migration prerequisites
az migrate check-prerequisites

# Discover migration sources
az migrate discover

# Perform basic migration assessment
az migrate assess
```

### Migration Planning

```bash
# Create a migration plan
az migrate plan create --source-name "MyServer" --target-type azure-vm

# List migration plans
az migrate plan list

# Show plan details
az migrate plan show --plan-name "MyServer-migration-plan"

# Execute a migration step
az migrate plan execute-step --plan-name "MyServer-migration-plan" --step-number 1
```

### Specialized Assessments

```bash
# Assess SQL Server for Azure SQL migration
az migrate assess sql-server --server-name "MyServer"

# Assess Hyper-V VMs for Azure migration
az migrate assess hyperv-vm --vm-name "MyVM"

# Assess file system for Azure Storage migration
az migrate assess filesystem --path "C:\\MyData"

# Assess network configuration
az migrate assess network
```

### Custom PowerShell Execution

```bash
# Execute a custom PowerShell script
az migrate powershell execute --script-path "C:\\Scripts\\MyMigration.ps1"

# Execute script with parameters
az migrate powershell execute --script-path "C:\\Scripts\\MyScript.ps1" --parameters "Server=MyServer,Database=MyDB"
```

## Architecture

The migration module consists of several key components:

1. **PowerShell Executor** (`_powershell_utils.py`): Cross-platform PowerShell command execution
2. **Migration Scripts** (`_powershell_scripts.py`): Pre-built PowerShell scripts for common scenarios
3. **Custom Commands** (`custom.py`): Azure CLI command implementations
4. **Command Registration** (`commands.py`): Command structure and organization
5. **Parameters** (`_params.py`): Command-line argument definitions
6. **Help Documentation** (`_help.py`): Comprehensive help and examples

## PowerShell Scripts

The module includes several pre-built PowerShell scripts for common migration scenarios:

- **SQL Server Assessment**: Analyzes SQL Server instances and databases
- **Hyper-V VM Assessment**: Evaluates virtual machines for Azure compatibility
- **File System Assessment**: Analyzes file structures and storage requirements
- **Network Assessment**: Reviews network configuration and requirements

## Migration Planning

The migration planning feature provides a structured approach to migrations:

1. **Prerequisites Check**: Verify system requirements
2. **Data Assessment**: Analyze data and applications
3. **Migration Preparation**: Prepare environments
4. **Data Migration**: Execute migration
5. **Validation**: Verify migration results
6. **Cutover**: Complete migration

## Error Handling

The module includes comprehensive error handling:

- PowerShell availability checks
- Cross-platform compatibility validation
- Detailed error messages with troubleshooting guidance
- Timeout protection for long-running operations

## Security Considerations

- Scripts execute with current user permissions
- No credential storage or transmission
- PowerShell execution policy bypass for migration scripts only
- Administrative privilege detection and warnings

## Examples

### Complete SQL Server Migration Assessment

```bash
# Check prerequisites
az migrate check-prerequisites

# Assess SQL Server
az migrate assess sql-server --server-name "SQLSERVER01"

# Create migration plan
az migrate plan create --source-name "SQLSERVER01" --target-type azure-sql --plan-name "sql-migration-2025"

# Execute assessment step
az migrate plan execute-step --plan-name "sql-migration-2025" --step-number 2
```

### Hyper-V to Azure VM Migration

```bash
# Discover Hyper-V environment
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
