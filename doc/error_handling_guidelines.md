# Azure CLI Error Handling Guidelines

This document aims to provide the guidelines for command group authors to onboard the error handling method and the new error output format.

Previously in Azure CLI, `CLIError` was widely used to wrap error messages after different kinds of error types are being caught. Now, `CLIError` is deprecated and replaced by a set of newly designed error types, which will provide clearer structures for error categorizing and also more actionable error outputs for better user experience.

For the new commands or features authoring in CLI modules, here are what need to be done to get onboard. __Any PRs not following these rules here will be rejected.__ For the existing `CLIError` in command groups, command group owners should schedule to replace them with the new error types.
1. [__Mandatory__] Use the newly designed error types instead of `CLIError`. See section [Error Type](#Error-Type)
2. [__Mandatory__] Follow the error message authoring guidelines. See section [Error Message](#Error-Message)
3. [__Recommended__] Provide recommendations for users to take action. See section [Error Recommendation](#Error-Recommendation)

__For CLI extensions, it's optional to adopt the new error types. If applying the new error types,  `azext.minCliCoreVersion` should be set to `2.15.0` or higher versions.__

## Error Type

### Available Error Types

The newly designed error types are provided in [azure/cli/core/azclierror.py](https://github.com/Azure/azure-cli/blob/dev/src/azure-cli-core/azure/cli/core/azclierror.py), where the error types are defined in three layers with their structures shown below. `AzCLIError` is the base layer for all the newly defined error types. The second layer includes the main categories (`UserFault`, `ClientError`, `ServiceError`), which can be shown to users and also can be used for Telemetry analysis. __The third layer includes the specific error types, which are the ones command group authors can use when raising errors.__

```
| -- AzCLIError                             # [Base Layer]: DO NOT use it in command groups
|    | -- UserFault                         # [Second Layer]: DO NOT use it in command groups
|    |    | -- CommandNotFoundError         # [Third Layer]: Can be used in command groups
|    |    | -- UnrecognizedArgumentError
|    |    | -- RequiredArgumentMissingError
|    |    | -- MutuallyExclusiveArgumentError
|    |    | -- InvalidArgumentValueError
|    |    | -- ArgumentUsageError               # fallback of argument related errors
|    |    | -- BadRequestError
|    |    | -- UnauthorizedError
|    |    | -- ForbiddenError
|    |    | -- ResourceNotFoundError
|    |    | -- AzureResponseError               # fallback of response related errors
|    |    | -- AzureConnectionError
|    |    | -- ClientRequestError               # fallback of request related errors
|    |    | -- ValidationError                  # fallback of validation related errors
|    |    | -- FileOperationError
|    |    | -- ManualInterrupt
|    |    | -- UnclassifiedUserFault            # fallback of UserFault related errors
|    |    | -- InvalidTemplateError
|    |    | -- DeploymentError
|    | -- ClientError
|    |    | -- CLIInternalError
|    | -- ServiceError
|    |    | -- AzureInternalError
```

To summarize, here is a list of rules for command group authors to select a proper error type.
- __DO NOT__ use the error types defined in the base layer and the second layer
- Avoid using the fallback error types unless you can not find a specific one for your case
- Consider defining a new error type if you can not find a proper one when it is a general error

### Apply the Error Type

Applying the new error types is just as easy as using `CLIError`. Wherever an `CLIError` could appear, you can use the new error types to replace it.

For example, previously, you may raise `CLIError` in this way.
```Python
err_msg = 'the specified resource group ... not exist'
raise CLIError(err_msg)
```

Now, you could use the new error type in this way.
```Python
from azure.cli.core.azclierror import ResourceNotFoundError

err_msg = 'the specified resource group ... not exist'
raise ResourceNotFoundError(err_msg)
```

The new error types all have the same signature for `__init__` function shown below. When an error is raised, you are highly recommended to provide some recommendations for users to take action if the error message is not clear enough for users to know what to do next.
```Python
__init__(self, error_msg, recommendation=None):
```
- `error_msg`: _string_, _required_. A clear message shown to users what the error is.
- `recommendation`: _string_ or _list_, _optional_. Recommendations telling users what action to take.

### Add a New Error Type

If there is not a proper error type for your case and the error is general enough, consider defining a new error type in [azure/cli/core/azclierror.py](https://github.com/Azure/azure-cli/blob/dev/src/azure-cli-core/azure/cli/core/azclierror.py). The defined error type should inherit from one of the errors defined in the second layer (`UserFault`, `ClientError`, `ServiceError`). Please reach out to AzCLIDev@microsoft.com for more details before adding a new error type.

For example, a new error type can be defined in this way.
```Python
class NewErrorTypeName(UserFault):
    """ A description of new error type. """
    pass
```


## Error Message

A clear and actionable error message is very important when raising an error, so make sure your error message describes clearly what the error is and tells users what they need to do if possible.

A general pattern is provided here, keep it in mind when you write an error message.

1. __What the error is.__
2. __Why it happens.__
3. __What users need to do to fix it.__

Below are the specific DOs and DON'Ts when writing the error messages. PRs violate rules here will be rejected.

__DOs__
- Use the capital letter ahead of an error message.
- Provide actionable message with argument suggestion. (e.g, Instead of using `resource group is missing, please provide a resource group name`, use `resource group is missing, please provide a resource group name by --resource-group`)

__DON'Ts__
- Do not control the style of an error message. (e.g, the unnecessary `'\n'` and the colorization.)
- Do not include the error type info in an error message. (e.g, `usage error: --ids | --name [--resource-group]`)
- Do not use a formula-like or a programming expression in the error message. (e.g, `Parameter 'resource_group_name' must conform to the following pattern: '^[-\\w\\._\\(\\)]+$'`)
- Do not use ambiguous expressions which mean nothing to users. (e.g, `Something unexpected happens.`)


## Error Recommendation

When necessary, it is highly suggested for command group authors to provide recommendations for users to resolve the errors they encountered. It is also suggested that we split the error message itself from the recommendations, which can be done either by specifying the `recommendation` parameter when initiating an error type or using the `set_recommendation` function after an error is initiated. In both cases, you can either provide a single recommendation with a string or multiple recommendations with a string list. The recommendations you provide will be printed right below the error message, one recommendation in a new line.


```Python
from azure.cli.core.azclierror import MutuallyExclusiveArgumentError

error_msg = 'Please specify all of (--publisher, --offer, --sku, --version), or --urn'
recommendation = 'Try to use --urn publisher:offer:sku:version only'
raise MutuallyExclusiveArgumentError(err_msg, recommendation)
```

```Python
from azure.cli.core.azclierror import MutuallyExclusiveArgumentError

error_msg = 'Please specify all of (--publisher, --offer, --sku, --version), or --urn'
recommendation = 'Try to use --urn publisher:offer:sku:version only'

az_error = MutuallyExclusiveArgumentError(err_msg)
az_error.set_recommendation(recommendation)
raise az_error
```
