Azure CLI Version Management
============================

## History
Azure CLI 2 was used for branding as compared to Azure classic CLI. A regular release only updates the PATCH version, which was confusing.

## Current Norm
Starting from version 2.1.0, Azure CLI updates:  
* MAJOR version for core changes that break commands behavior globally;  
* MINOR version for general backwards compatible feature changes and service commands breaking changes;  
* PATCH verison for bug fixes.

## Backward Compatability
Considering Azure CLI is a command line tool for Azure Services, we tend to just bump the MINOR verison for breaking changes in a service module command. All breaking changes for a command will be marked as **BREAKING CHANGE** in [release notes](https://docs.microsoft.com/cli/azure/release-notes-azure-cli?view=azure-cli-latest).

From command level, packages only upgrading PATCH version guanrantees backwards compatibilty.


