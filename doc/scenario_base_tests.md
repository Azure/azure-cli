# How to write ScenarioTest based VCR test

The `ScenarioTest` class is introduced in pull request [#2393](https://github.com/Azure/azure-cli/pull/2393). It is the preferred base class for and VCR based test cases from now on. The `ScenarioTest` class is designed to be a better and easier test harness for authoring scenario based VCR test.

### Sample 1. Basic fixture
```Python
from azure.cli.testsdk import ScenarioTest

class StorageAccountTests(ScenarioTest):
    def test_list_storage_account(self):
        self.cmd('az storage account list')
```
Note:

1. When the test is run without recording file, the test will be run under live mode. A recording file will be created at `recording/<test_method_name>.yaml`
2. Wrap the command in `self.cmd` method. It will assert the exit code of the command to be zero.
3. All the functions and classes your need for writing tests are included in `azure.cli.testsdk` namespace. It is recommanded __not__ to refrenced to the sub-namespace to avoid breaking changes.

### Sample 2. Validate the return value in JSON
``` Python
class StorageAccountTests(ScenarioTest):
    def test_list_storage_account(self):
        accounts_list = self.cmd('az storage account list').get_output_in_json()
        assert len(accounts_list) > 0
```
Note:

1. The return value of `self.cmd` is an instance of class `ExecutionResult`. It has the exit code and stdout as its properties.
2. `get_output_in_json` deserialize the output to a JSON object

Tip:

1. Don't make any rigid assertions based on any assumptions which may not stand in a live test environment.


### Sample 3. Validate the return JSON value using JMESPath
``` Python
from azure.cli.testsdk import ScenarioTest, JMESPathCheck

class StorageAccountTests(ScenarioTest):
    def test_list_storage_account(self):
        self.cmd('az account list-locations',
        checks=[JMESPathCheck("[?name=='westus'].displayName | [0]", 'West US')])
```
Note: 

1. What is JMESPath? [JMESPath is a query language for JSON](http://jmespath.org/)
2. If a command is return value in JSON, multiple JMESPath based check can be added to the checks list to validate the result.
3. In addition to the `JMESPatchCheck`, there are other checks list `NoneCheck` which validate the output is `None`. The check mechanism is extensible. Any callable accept `ExecutionResult` can act as a check.


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
Note:

1. The preparers are executed in before each test in the test class when `setUp` is executed. The resource will be cleaned up after testing.
2. The resource group name is injected to the test method as a parameter. By default 'ResourceGroupPreparer' set the value to 'resource_group' parameter. The target parameter can be customized (see following samples).
3. The resource group will be deleted in async for performance reason.


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
Note:

1. In addition to the name, the location of the resource group can be also injected into the test method.
2. Both parameters' names can be customized.
3. The test method parameter accepting the location value is optional. The test harness will inspect the method signature and decide if the value will be added to the keyworded arguments.


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

One of the most important features of `ScenarioTest` is names managements. For the tests to be able to run in a live environment and avoid name collision a strong name randomization is required. On the other hand, for the tests to be recorded and replay, the naming mechanism must be repeatable during playback mode. The `self.create_randome_name` assist the test to achieve the goal.

The method will create a random name during recording, and when it is called during playback, it returns a name (internally it is called moniker) based on the sequence of the name request. The order won't change once the test is written. Peak into the recording file, you find no random name. For example, note the names like 'clitest.rg000001', they aren't the names of the resources which are actually created in Azure. They're placed before the requests are persisted.
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

In short, for the names of any Azure resources used in the tests, always use the `self.create_random_name` to generate its value. Also make sure the correct length is given to the method because different resource have different limitation of the name length. The method will always try to create the longest name possible to fully randomize the name. 


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

1. Like `ResourceGroupPreparer` you can use `StorageAccountPreparer` to prepare a disposable storage account for the test. The account is deleted along with the resource group.
2. To create a storage account a resource group is required. Therefore `ResourceGroupPrepare` is needed to place above the `StorageAccountPreparer`. The preparers designed to be executed from top to bottom. (The core implementaiton of preparer is in the[AbstractPreparer](https://github.com/Azure/azure-cli/blob/master/src/azure-cli-testsdk/azure/cli/testsdk/preparers.py#L25))
3. The preparers communicate among them by adding values to the `kwargs` of the decorated methods. Therefore the `StorageAccountPreparer` uses the resource group created in preceding `ResourceGroupPreparer`.
4. The `StorageAccountPreparer` can be further customized:
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
2. The resource group name is not required in test so the function doesn't have to declare a parameter to accept the name. However it doesn't mean that the resource group is not created. Its name is in the keyworded parameter dictionary for all the preparer to consume. It is removed before the test function is actually invoked. 
