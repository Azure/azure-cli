Azure CLI Version Management
============================

## History
Azure CLI 2 was used for branding as compared to Azure classic CLI. We intended to keep the MAJOR version fixed at 2 for a while. A regular release only updated the PATCH version, which was a little confusing.

## Current Norm
Starting from version 2.1.0, Azure CLI updates:  
* MAJOR version for core changes that break commands' behavior globally;  
* MINOR version for general backward compatible feature changes and service command breaking changes;  
* PATCH version for bug fixes.

## Backward Compatibility
Considering Azure CLI is a command line tool for Azure Services, we tend to just bump the MINOR version for breaking changes in a service command module. All breaking changes for commands will be marked as **BREAKING CHANGE** in [release notes](https://docs.microsoft.com/cli/azure/release-notes-azure-cli).

At command level, packages only upgrading the PATCH version guarantee backward compatibility.
