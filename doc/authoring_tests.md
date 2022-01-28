# Automating tests for Azure CLI

## Overview

There are two types of automated tests you can add for Azure CLI: [unit tests](https://en.wikipedia.org/wiki/Unit_testing) and  [integration tests](https://en.wikipedia.org/wiki/Integration_testing).

For unit tests, we support unit tests written in the forms standard [unittest](https://docs.python.org/3/library/unittest.html).

For integration tests, we provide the `ScenarioTest` and `LiveScenarioTest` classes to support replayable tests via [VCR.py](https://vcrpy.readthedocs.io/en/latest/).

### About replayable tests

Azure CLI translates user inputs into Azure Python SDK calls which communicate with [Azure REST API](https://docs.microsoft.com/rest/api/). These HTTP communications are captured and recorded so the integration tests can be replayed in an automation environment without making actual HTTP calls. This ensures that the commands actually work against the service when they are recorded (and then can be re-run live to verify) and provides protection against regressions or breaking changes when they are played back.

### Nightly live test run

The scenario tests are run in replayable mode in the Travis CI during pull request verification and branch merge. However, the tests will be run in live mode nightly in internal test infrastructure. See [Test Policies](#test-policies) for more details.

The rationale behind the nightly live test:

1) The live scenario tests actually verify the end to end scenario.
2) The live scenario tests ensure the credibility of the tested scenario.
3) The test recording tends to go stale. The sample it captures will eventually deviate from the actual traffic samples.
4) The tests in playback mode does not verify the request body and it doesn't ensure the correct requests sequence.
5) The unhealthy set of live tests prevent the Azure CLI team from rebaselining tests rapidly.
6) Neglecting the live tests will reduce the quality and the credibility of the test bed.

It is a requirement for the command owner to maintain their test in live mode.

## Authoring Tests

### Test Policies

* __DO NOT USE__ hard-coded or otherwise persistent resources. This makes it difficult or impossible to re-record tests or run them live. In general, all resources needed to support the test should be created as part of the test and torn down after the test finishes. The use of `ResourceGroupPreparer` helps to facilitate this.
* Tests __MUST__ be included for all new command modules and any new commands to existing test modules. PRs will be rejected outright if they do not include tests.
* Name test methods in the following format: `test_<module>_<feature>`.
* The scenario test must be able to run repeatedly in live mode. The feature owner is responsible of maintaining their scenario tests.

## Recording Tests

### Preparation

1. Set up your [development environment](configuring_your_machine.md)
2. Select the API profile you want to test. (Optional)
3. Select the cloud you want to test. (Optional) You may need to register a cloud first (for example, if targeting a staging or test environment).
4. Log in your Azure account using `az login` command.
5. Select the subscription you want to use for recording tests. The replaying does not rely on the knowledge of the subscription and the credentials will be removed from the recordings.

### Recording tests for the first time

After the test is executed, a recording file will be generated at `recording/<api_profile_name>/<test_name>.yaml`. The recording file will be created no matter the test pass or not. The behavior makes it easy for you to find issues when a test fails. To re-record the test, you can either delete the existing recording and re-run the test, or simply re-run the test using the `--live` flag (ex: `azdev test example_test --live`.

It is a good practice to add recording file to the local git cache, which makes it easy to diff the different versions of recording to detect issues or changes.

Once the recording file is generated, execute the test again. This time the test will run in playback mode. The execution is offline, and will not act on the Azure subscription.

If the replay passes, you can commit the tests as well as recordings and submit them as part of your PR.

### Running tests live

When a recording file is missing, the test framework will execute the test in live mode. You can also force tests to run live either by setting the environment variable `AZURE_TEST_RUN_LIVE` or by using the `--live` flag with the `azdev test` command. 

Also, you can author tests which are for live test only by deriving the test class from `LiveScenarioTest`. Since these tests will not be run as part of the CI, you lose much of the automatic regression protection by doing this. However, for certain tests that cannot be re-recorded, cannot be replayed, or fail due to service issues, this is a viable approach.

### Test Run Frequency

Recorded tests are run on TravisCI as part of all pull request validations. Therefore it is important to keep the recordings up-to-date, and to ensure that they can be re-recorded.

Live tests run nightly in a separate system and are not tied to pull requests.

## Troubleshooting Test Issues

Here are some issues that may occur when authoring tests that you should be aware of.

* **Non-deterministic results**: If you find that a test will pass on some playbacks but fail on others, there are a couple possible things to check:
  1. check if your command makes use of concurrency.
  2. check your parameter aliasing (particularly if it complains that a required parameter is missing that you know is there)
 If your command makes use of concurrency, consider using unit tests, LiveScenarioTest, or, if practical, forcing the test to operate on a single thread for recording and playback.
* **Paths**: When including paths in your tests as parameter values, always wrap them in double quotes. While this isn't necessary when running from the command line (depending on your shell environment), it will likely cause issues with the test framework.
* **Defaults**: Ensure you don't have any defaults configured with `az configure` prior to running tests. Defaults can interfere with the expected test flow.

## Sample Scenario Tests

### Sample 1. Basic fixture

```python
from azure.cli.testsdk import ScenarioTest

class StorageAccountTests(ScenarioTest):
    def test_list_storage_account(self):
        self.cmd('az storage account list')
```

Notes:

1. When the test is run and no recording file is available, the test will be run in live mode. A recording file will be created at `recording/<test_method_name>.yaml`.
2. Wrap the command in the `self.cmd` method. It will assert that the exit code of the command is zero.
3. All the functions and classes you need for writing tests are included in the `azure.cli.testsdk` namespace. It is recommended __not__ to import from a sub-namespace to avoid breaking changes.

### Sample 2. Validate the return value in JSON

```python
class StorageAccountTests(ScenarioTest):
    def test_list_storage_account(self):
        accounts_list = self.cmd('az storage account list').get_output_in_json()
        assert len(accounts_list) > 0
```

Notes:

1. The return value of `self.cmd` is an instance of the class `ExecutionResult`. It has the exit code and stdout as its properties.
2. `get_output_in_json` deserializes the output to a JSON object.

Tip: Don't make any rigid assertions based on assumptions
which may not stand in a live test environment.

### Sample 3. Validate the return JSON value using JMESPath

```python
from azure.cli.testsdk import ScenarioTest

class StorageAccountTests(ScenarioTest):
    def test_list_storage_account(self):
        self.cmd('az account list-locations', checks=[
            self.check("[?name=='westus'].displayName | [0]", 'West US')
        ])
```

Notes:

1. The first argument in the `check` method is a JMESPath query. [JMESPath is a query language for JSON](http://jmespath.org/).
2. If a command returns JSON, multiple JMESPath based checks can be added to the checks list to validate the result.
3. In addition to the `check` method, there are other checks like `is_empty` which validate the output is `None`. The check mechanism is extensible. Any callable accepting a single `ExecutionResult` argument can act as a check: see [checkers.py](https://github.com/Azure/azure-cli/blob/dev/src/azure-cli-testsdk/azure/cli/testsdk/checkers.py).

### Sample 4. Prepare a resource group for a test

```python
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer

class StorageAccountTests(ScenarioTest):
    @ResourceGroupPreparer()
    def test_create_storage_account(self, resource_group):
        self.cmd('az group show -n {rg}', checks=[
            self.check('name', '{rg}'),
            self.check('properties.provisioningState', 'Succeeded')
        ])
```

Notes:

1. The preparers are executed before each test in the test class when `setUp` is executed. Any resources created in this way will be cleaned up after testing. Unless you specify that a preparer use an existing resource via its associated environment variable. See [Test-Related Environment Variables](#test-related-environment-variables).
2. The resource group name is injected into the test method as a parameter. By default `ResourceGroupPreparer` passes the value as the `resource_group` parameter. The target parameter can be customized (see following samples).
3. The resource group will be deleted asynchronously for performance reason.
4. The resource group will automatically be registered into the tests keyword arguments (`self.kwargs`) with the key default key of `rg`. This can then be directly plugged into the command string in `cmd` and into the verification step of the `check` method. The test infrastructure will automatically replace the values.

### Sample 5. Get more from ResourceGroupPreparer

```python
class StorageAccountTests(ScenarioTest):
    @ResourceGroupPreparer(parameter_name='group_name', parameter_name_for_location='group_location')
    def test_create_storage_account(self, group_name, group_location):
        self.kwargs.update({
          'loc': group_location
        })
        self.cmd('az group show -n {rg}', checks=[
            self.check('name', '{rg}'),
            self.check('location', '{loc}'),
            self.check('properties.provisioningState', 'Succeeded')
        ])
```

Notes:

1. In addition to the name, the location of the resource group can be also injected into the test method.
2. Both parameters' names can be customized.
3. You can add the location to the test's kwargs using the `self.kwargs.update` method. This allows you to take advantage of the automatic kwarg replacement in your command strings and checks.

### Sample 6. Random name and name mapping

```python
class StorageAccountTests(ScenarioTest):
    @ResourceGroupPreparer(parameter_name_for_location='location')
    def test_create_storage_account(self, resource_group, location):
        self.kwargs.update({
          'name': self.create_random_name(prefix='cli', length=24),
          'loc': location,
          'sku': 'Standard_LRS',
          'kind': 'Storage'
        })
        self.cmd('az storage account create -n {name} -g {rg} --sku {sku} -l {loc}')
        self.cmd('az storage account show -n {name} -g {rg}', checks=[
            self.check('name', '{name}'),
            self.check('location', '{loc}'),
            self.check('sku.name', '{sku}'),
            self.check('kind', '{kind}')
        ])
```

Note:

One of the most important features of `ScenarioTest` is name management.
For the tests to be able to run in a live environment and avoid name collision
a strong name randomization is required.
On the other hand, for the tests to be recorded and replayed,
the naming mechanism must be repeatable during playback mode.
The `self.create_random_name` method helps the test achieve both goals.

The method will create a random name during recording,
and when it is called during playback,
it returns a name (internally it is called moniker)
based on the sequence of the name request.
The order won't change once the test is written.
Peek into the recording file, and you will find no random name.
For example, note names like 'clitest.rg000001' in the sample recording below:
they aren't the names of the resources which are actually created in Azure.
They're replaced before the requests are recorded.

```Yaml
- request:
    body: '{"location": "westus", "tags": {"use": "az-test"}}'
    headers:
      Accept: [application/json]
      Accept-Encoding: ['gzip, deflate']
      CommandName: [group create]
      Connection: [keep-alive]
      Content-Length: ['50']
      Content-Type: [application/json; charset=utf-8]
      User-Agent: [python/3.5.2 (Darwin-16.4.0-x86_64-i386-64bit) requests/2.9.1 msrest/0.4.6
                   msrest_azure/0.4.7 resourcemanagementclient/0.30.2 Azure-SDK-For-Python
                   AZURECLI/2.0.0+dev]
      accept-language: [en-US]
    method: PUT
    uri: https://management.azure.com/subscriptions/00000000-0000-0000-0000-000000000000/resourcegroups/clitest.rg000001?api-version=2016-09-01
  response:
    body: {string: '{"id":"/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/clitest.rg000001","name":"clitest.rg000001","location":"westus","tags":{"use":"az-test"},"properties":{"provisioningState":"Succeeded"}}'}
    headers:
      cache-control: [no-cache]
      content-length: ['326']
      content-type: [application/json; charset=utf-8]
      date: ['Fri, 10 Mar 2017 17:59:58 GMT']
      expires: ['-1']
      pragma: [no-cache]
      strict-transport-security: [max-age=31536000; includeSubDomains]
      x-ms-ratelimit-remaining-subscription-writes: ['1199']
    status: {code: 201, message: Created}
```

In short, always use `self.create_random_name` to generate
the name of any Azure resource used in a test.
Also, make sure the correct length is given to the method
because different resources have different limitations on the name length.
The method will always try to create the longest name possible
to fully randomize the name.

### Sample 7. Prepare a storage account for tests

```python
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer

class StorageAccountTests(ScenarioTest):
    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_list_storage_accounts(self, storage_account):
        accounts = self.cmd('az storage account list').get_output_in_json()
        search = [account for account in accounts if account['name'] == storage_account]
        assert len(search) == 1
```

Note:

1. Like `ResourceGroupPreparer`, you can use `StorageAccountPreparer` to prepare a disposable storage account for the test. The account is deleted along with the resource group during test teardown.
2. Creation of a storage account requires a resource group. Therefore `ResourceGroupPrepare` must be placed above `StorageAccountPreparer`, since preparers are designed to be executed from top to bottom. (The core preparer implementation is in the `azure.cli.testsdk.scenario_tests.preparers.AbstractPreparer`.)
3. The preparers communicate among themselves by adding values to the `kwargs` of the decorated methods. Therefore the `StorageAccountPreparer` uses the resource group created in the preceding `ResourceGroupPreparer`.
4. The `StorageAccountPreparer` can be further customized to modify the parameters of the created storage account:

```python
@StorageAccountPreparer(sku='Standard_LRS', location='southcentralus', parameter_name='storage')
```

### Sample 8. Prepare multiple storage accounts for tests

```python
class StorageAccountTests(ScenarioTest):
    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='account_1')
    @StorageAccountPreparer(parameter_name='account_2')
    def test_list_storage_accounts(self, account_1, account_2):
        accounts_list = self.cmd('az storage account list').get_output_in_json()
        assert len(accounts_list) >= 2
        assert next(acc for acc in accounts_list if acc['name'] == account_1)
        assert next(acc for acc in accounts_list if acc['name'] == account_2)
```

Note:

1. Two storage account names will be assigned to different function parameters.
2. The resource group name is not needed for the test so the function doesn't have to declare a parameter to accept the name. However it doesn't mean that the resource group is not created. Its name is in the keyword parameter dictionary for any other preparer to consume, but it is removed before the test function is actually invoked.

<!--
Note: This document's source uses
[semantic linefeeds](http://rhodesmill.org/brandon/2012/one-sentence-per-line/)
to make diffs and updates clearer.
-->

### Sample 9. Assert Specific Error Occurs

```python
with self.assertRaisesRegexp(CLIError, "usage error: --vnet NAME --subnet NAME | --vnet ID --subnet NAME | --subnet ID"):
            self.cmd('container create -g {rg} -n {container_group_name} --image nginx --vnet {vnet_name}')
```

The above syntax is the recommended way to test that a specific error occurs. You must pass the type of the error as well as a string used to match the error message. If the error is encountered, the text will be validated and, if matching, the command will be deemed a success (for testing purposes) and execution will continue. If the command does not yield the expected error, the test will fail.



## Test-Related Environment Variables

There are a few environment variables that modify the behaviour of the CLI's test infrastructure.

As mentioned previously, **AZURE_TEST_RUN_LIVE** runs tests live, if it is set to a truthy value (e.g. "True"). It is preferable to use --live

However there are other environment variables that alter the behavior of resource preparers such as the `ResourceGroupPreparer`, such as:
1. **`AZURE_CLI_TEST_DEV_RESOURCE_GROUP_NAME` and `AZURE_CLI_TEST_DEV_RESOURCE_GROUP_LOCATION`** : If set, the first environment variable specifies an existing resource group to be returned by the `ResourceGroupPreparer`. The specified resource group will not be deleted after the test. The second specifies the existing resource group's location, defaults to the location passed when calling `ResourceGroupPreparer`.
2. **`AZURE_CLI_TEST_DEV_STORAGE_ACCOUNT_NAME`** : Specifies an existing storage account. Associated with the `StorageAccountPreparer`.
3. **`AZURE_CLI_TEST_DEV_KEY_VAULT_NAME`** : Specifies an existing key vault name. Associated with the `KeyVaultPreparer`.
5. **`AZURE_CLI_TEST_DEV_SP_NAME` and `AZURE_CLI_TEST_DEV_SP_PASSWORD`** : Specifies the name of an existing service principal and its password. Associated with the `RoleBasedServicePrincipalPreparer`.
4. **`AZURE_CLI_TEST_DEV_APP_NAME`and `AZURE_CLI_TEST_DEV_APP_SECRET`** : Specifies an existing managed app and its secret (secret defaults to `None`). Associated with the `ManagedApplicationPreparer`.

Setting these variables can reduce the time taken to run live tests new resource as the preparers don't have to create and delete new resources.

> To learn more about these environment variables, please see the preparers' source code in [`/src/azure-cli-testsdk/azure/cli/testsdk/preparers.py`](https://github.com/Azure/azure-cli/blob/dev/src/azure-cli-testsdk/azure/cli/testsdk/preparers.py).
