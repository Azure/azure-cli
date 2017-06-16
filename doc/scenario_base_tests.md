# How to write ScenarioTest based VCR test

The `ScenarioTest` class was introduced in pull request
[#2393](https://github.com/Azure/azure-cli/pull/2393).
It is the preferred base class for all VCR based test cases from now on.
The `ScenarioTest` class is designed to be a better and easier test harness
for authoring scenario based VCR tests.

### Sample 1. Basic fixture
```Python
from azure.cli.testsdk import ScenarioTest

class StorageAccountTests(ScenarioTest):
    def test_list_storage_account(self):
        self.cmd('az storage account list')
```
Notes:

1. When the test is run and no recording file is available,
the test will be run in live mode.
A recording file will be created at `recording/<test_method_name>.yaml`.
2. Wrap the command in the `self.cmd` method.
It will assert that the exit code of the command is zero.
3. All the functions and classes you need for writing tests
are included in the `azure.cli.testsdk` namespace.
It is recommended __not__ to import from a sub-namespace to avoid breaking changes.

### Sample 2. Validate the return value in JSON
``` Python
class StorageAccountTests(ScenarioTest):
    def test_list_storage_account(self):
        accounts_list = self.cmd('az storage account list').get_output_in_json()
        assert len(accounts_list) > 0
```
Notes:

1. The return value of `self.cmd` is an instance of the class `ExecutionResult`.
It has the exit code and stdout as its properties.
2. `get_output_in_json` deserializes the output to a JSON object.

Tip: Don't make any rigid assertions based on assumptions
which may not stand in a live test environment.


### Sample 3. Validate the return JSON value using JMESPath
``` Python
from azure.cli.testsdk import ScenarioTest, JMESPathCheck

class StorageAccountTests(ScenarioTest):
    def test_list_storage_account(self):
        self.cmd('az account list-locations',
        checks=[JMESPathCheck("[?name=='westus'].displayName | [0]", 'West US')])
```
Notes: 

1. What is JMESPath?
[JMESPath is a query language for JSON](http://jmespath.org/).
2. If a command returns JSON,
multiple JMESPath based checks can be added to the checks list to validate the result.
3. In addition to the `JMESPatchCheck`,
there are other checks like `NoneCheck` which validate the output is `None`.
The check mechanism is extensible.
Any callable accepting a single `ExecutionResult` argument can act as a check.


### Sample 4. Prepare a resource group for a test
``` Python
from azure.cli.testsdk import ScenarioTest, JMESPathCheck, ResourceGroupPreparer

class StorageAccountTests(ScenarioTest):
    @ResourceGroupPreparer()
    def test_create_storage_account(self, resource_group):
        self.cmd('az group show -n {}'.format(resource_group), checks=[
            JMESPathCheck('name', resource_group),
            JMESPathCheck('properties.provisioningState', 'Succeeded')
        ])
```
Notes:

1. The preparers are executed before each test in the test class when `setUp` is executed.
Any resources created in this way will be cleaned up after testing.
2. The resource group name is injected into the test method as a parameter.
By default `ResourceGroupPreparer` passes the value as the `resource_group` parameter.
The target parameter can be customized (see following samples).
3. The resource group will be deleted asynchronously for performance reason.


### Sample 5. Get more from ResourceGroupPreparer
``` Python
class StorageAccountTests(ScenarioTest):
    @ResourceGroupPreparer(parameter_name='group_name', parameter_name_for_location='group_location')
    def test_create_storage_account(self, group_name, group_location):
        self.cmd('az group show -n {}'.format(group_name), checks=[
            JMESPathCheck('name', group_name),
            JMESPathCheck('location', group_location),
            JMESPathCheck('properties.provisioningState', 'Succeeded')
        ])
```
Notes:

1. In addition to the name,
the location of the resource group can be also injected into the test method.
2. Both parameters' names can be customized.
3. The test method parameter accepting the location value is optional.
The test harness will inspect the method signature
and decide if the value will be added to the keyword arguments.


### Sample 6. Random name and name mapping
``` Python
class StorageAccountTests(ScenarioTest):
    @ResourceGroupPreparer(parameter_name_for_location='location')
    def test_create_storage_account(self, resource_group, location):
        name = self.create_random_name(prefix='cli', length=24)
        self.cmd('az storage account create -n {} -g {} --sku {} -l {}'.format(
            name, resource_group, 'Standard_LRS', location))
        self.cmd('az storage account show -n {} -g {}'.format(name, resource_group), checks=[
            JMESPathCheck('name', name),
            JMESPathCheck('location', location),
            JMESPathCheck('sku.name', 'Standard_LRS'),
            JMESPathCheck('kind', 'Storage')
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
For example, note names like 'clitest.rg000001' in the below example:
they aren't the names of the resources which are actually created in Azure.
They're replaced before the requests are recorded.

``` Yaml
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

In short, for the name of any Azure resources used in the tests,
always use `self.create_random_name` to generate its value.
Also, make sure the correct length is given to the method
because different resources have different limitations on the name length.
The method will always try to create the longest name possible
to fully randomize the name. 


### Sample 7. Prepare storage account for tests
``` Python
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

1. Like `ResourceGroupPreparer`, you can use `StorageAccountPreparer`
to prepare a disposable storage account for the test.
The account is deleted along with the resource group during test teardown.
2. Creation of a storage account requires a resource group.
Therefore `ResourceGroupPrepare` must be placed above `StorageAccountPreparer`,
since preparers are designed to be executed from top to bottom.
(The core preparer implementation is in the
[AbstractPreparer](https://github.com/Azure/azure-python-devtools/blob/master/src/azure_devtools/scenario_tests/preparers.py)
class in the [azure-devtools](https://pypi.python.org/pypi/azure-devtools) package.)
3. The preparers communicate among themselves
by adding values to the `kwargs` of the decorated methods.
Therefore the `StorageAccountPreparer` uses the resource group created in the preceding `ResourceGroupPreparer`.
4. The `StorageAccountPreparer` can be further customized
to modify the parameters of the created storage account:
``` Python
@StorageAccountPreparer(sku='Standard_LRS', location='southcentralus', parameter_name='storage')
```

### Sampel 8. Prepare multiple storage accounts for tests
``` Python
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

1. Two storage accounts name should be assigned to different function parameters.
2. The resource group name is not required in test
so the function doesn't have to declare a parameter to accept the name.
However it doesn't mean that the resource group is not created.
Its name is in the keyworded parameter dictionary for all the preparer to consume.
It is removed before the test function is actually invoked. 
