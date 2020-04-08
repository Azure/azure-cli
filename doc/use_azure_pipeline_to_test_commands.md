# Use Azure Pipelines to Test Commands

This tutorial shows how to use Azure Pipelines to test Azure CLI commands.

Azure CLI has large number of commands and test cases. Running test cases has high cost. Especially when running test cases in local machine, it may block normal work for a long time.
Azure Pipelines is a cloud service that you can use to automatically build and test your code project and make it available to other users. It works with just about any language or project type.
We have created a pipeline to enable running test cases in Azure platform. By using this pipeline, users can test their code easily and get a visualized test report.

Here are steps:
1. Open the [pipeline](https://dev.azure.com/azure-sdk/public/_build?definitionId=1369). In the 
