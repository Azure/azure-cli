# Azure CLI Error Handling Guidelines

This document aims to provide the guidelines for command group authors to onboard the error handling method and the new error output format.

Previously in Azure CLI, `CLIError` is widely used to wrap the error messages after the different kinds of error types being caught. Now, `CLIError` is deprecated and it is replaced by a set of new designed error types, which will provide more clear structures for error categorizing and also more actionable error outputs for user experience.

For the new commands authoring, here are what need to be done to get on board. __Any PRs not following rules here will be rejected.__ For the existing `CLIError` in command groups, command group owners should schedule to replace them with the new error types.
1. [__Mandatory__] Use the new designed error types instead of CLIError, detail section [here](#Error-Type)
2. [__Mandatory__] Follow the error message authoring guidelines, detail section [here](#Error-Message)
3. [__Recommendation__] Provide recommendations for users to take action, detail section [here](#Error-Recommendation)


## Error Type

### Available Error Types

The new designed error types are provided in [azure/cli/core/azclierror.py](https://github.com/Azure/azure-cli/blob/dev/src/azure-cli-core/azure/cli/core/azclierror.py), where the error types are defined in three layers with their structures below. `AzCLIError` is the base layer for all the new defined error types. The second layer includes the main categories (`UserFault`, `ClientError`, `ServiceError`), which can be shown to users and also can be used for Telemetry analysis. __The third layer includes the specific error types, which are the ones command group authors can use when raising errors.__

```
| -- AzCLIError                                 # [Base Layer]: DO NOT use it in command groups
|    | -- UserFault                             # [Second Layer]: DO NOT use it in command groups
|    |    | -- CommandNotFoundError             # [Third Layer]: Can be used in command groups
|    |    | -- UnrecognizedArgumentError
|    |    | -- RequiredArgumentMissingError
|    |    | -- MutuallyExclusiveArgumentError
|    |    | -- InvalidArgumentValueError
|    |    | -- ArgumentParseError               # fallback of argument related errors
|    |    | -- BadRequestError
|    |    | -- UnauthorizedError
|    |    | -- ForbiddenError
|    |    | -- ResourceNotFoundError
|    |    | -- AzureResponseError               # fallback of response related errors
|    |    | -- AzureConnectionError
|    |    | -- ClientRequestError               # fallback of request related errors
|    |    | -- ValidationError                  # fallback of validation related errors
|    |    | -- ManualInterrupt
|    |    | -- ... More ...
|    | -- ClientError
|    |    | -- CLIInternalError
|    | -- ServiceError
|    |    | -- AzureInternalError
```

To summarize, here is a list of rules for command group authors to select a proper error type.
- __DO NOT__ use the error types defined in the base layer and the second layer
- Consider defining a new error type if you can not find a proper one when it is a general error
- Avoid using the fallback error types unless you can not find a proper one and the error is not general enough for a new error type

### Apply the Error Type

Applying the new error types is just as easy as using CLIError. Wherever an CLIError could appear, you can use the new error types to replace it.

For example, previously, you may raise CLIError in this way.
```
err_msg = 'the specified resource group ... not exist'
raise CLIError(err_msg)
```

Now, you could use the new error type in this way.
```
from azure.cli.core.azclierror import ResourceNotFoundError

err_msg = 'the specified resource group ... not exist'
raise ResourceNotFoundError(err_msg)
```

The new error types are all with the same init function which has the signature below. When an error happens, you are highly recommended to provide some recommendations for users to take action if the error message if not clear enough for users to know what to do next.
```
__init__(self, error_msg, recommendation=None):
```
- `error_msg`: _string_, _required_. A clear message shown to users what the error is.
- `recommendation`: _string_ or _list_, _optional_. Recommendations telling users what action to take.

### Add A New Error Type

If there is not a proper error type for your case and the error is general enough, consider defining a new error type in [azure/cli/core/azclierror.py](https://github.com/Azure/azure-cli/blob/dev/src/azure-cli-core/azure/cli/core/azclierror.py). The defined error type should be inherited from one of the errors define in the second layer (`UserFault`, `ClientError`, `ServiceError`).

For example, a new error type can be defined in this way.
```
class NewErrorTypeName(UserFault):
    """ A description of new error type. """
    pass
```


## Error Message

A clear and actionable error message is very important when raising an error, so make sure your error message describe clearly what the error is and provide users what they need to do if possible.

A general pattern is provide here, keep it in mind when you write an error message.

1. __What the error is.__
2. __Why it happens.__
3. __What users need to do to fix it.__

Below are the specific DOs and DON'Ts when writing the error messages. PRs violates rules here will be rejected.

__DOs__
- Use the capital letter ahead of an error message.

__DON'Ts__
- Do not control the style of an error message. (e.g, the unnecessary `'\n'` and the colorization.)
- Do not include the error type info in an error message. (e.g, _usage error: --ids | --name [--resource-group]_)
- Do not use a formula-like or a programming expression in the error message. (e.g, _Parameter 'resource_group_name' must conform to the following pattern: '^[-\\w\\._\\(\\)]+$'_)
- Do not use ambiguous expressions which mean nothing to users. (e.g, _Something unexpected happens._)


## Error Recommendation

When necessary, it is highly suggested for command group authors to provide recommendations for users to resolve the errors they are encountering. It is also suggested that we split the error message itself from the recommendations, which can be done either by specifying a recommendation property when initiating an error type or using the `set_recommendation` function after an error is initiated. The recommendations you provide will be printed right below the error message, one recommendation in a new line.


```
from azure.cli.core.azclierror import MutuallyExclusiveArgumentError

error_msg = 'Please specify all of (--publisher, --offer, --sku, --version), or --urn'
recommendation = 'Try to use --urn publisher:offer:sku:version only'
raise MutuallyExclusiveArgumentError(err_msg, recommendation)
```

```
from azure.cli.core.azclierror import MutuallyExclusiveArgumentError

error_msg = 'Please specify all of (--publisher, --offer, --sku, --version), or --urn'
recommendation = 'Try to use --urn publisher:offer:sku:version only'

az_error = MutuallyExclusiveArgumentError(err_msg)
az_error.set_recommendation(recommendation)
raise az_error
```