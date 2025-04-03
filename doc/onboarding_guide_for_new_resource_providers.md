Onboarding Guide for New Resource Providers
=========================

This documentation is for building an easy and clear way to onboard new resource providers to Azure CLI.

## Prerequisite

#### PLR (Product Launch Readiness)

Contact `@Carl Shipley (cashiple@microsoft.com)` for [PLR](http://aka.ms/plrcriteria) process.

#### Azure CLI Dev Contact

Reach out to `azclidev@microsoft.com` to briefly describe your new resource provider, including:
1. Basic information of your resource provider
    1. The name
    2. A concise introduction
2. How/when to release your extension
    1. Release mode
        * GA
        * public preview
        * private preview
    2. Expected release time
3. Swagger information
    1. The link to the Swagger repo
    2. The PR link (if your Swagger specs have not been merged yet)
    
Then Azure CLI team will assign you a dev contact as soon as possible.

## Generate the Code

1. [Do a quick validation](https://github.com/Azure/autorest.az/blob/master/doc/00-onboarding-guide.md#step-2-quick-validation)
2. [Generate code](https://github.com/Azure/autorest.az/blob/master/doc/00-onboarding-guide.md#step-3-generate-code-and-give-it-a-try)
3. [Run test and style check](https://github.com/Azure/autorest.az/blob/master/doc/00-onboarding-guide.md#step-4-run-test-and-style-check)

## CLI Code Review

1. Create a Github PR on [Azure CLI extensions repo](https://github.com/Azure/azure-cli-extensions) with your code changes, select the assigned dev contact as code reviewer.
2. If you don't want to expose your code too early, [Private repo](https://github.com/Azure/azure-cli-extensions-pr) should be your best choice.
