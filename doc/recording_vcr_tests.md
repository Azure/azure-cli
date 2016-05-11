Recording Command Tests with VCR.py
========================================

Azure CLI uses the VCR.py library to record the HTTP messages exchanged during a program run and play them back at a later time, making it useful for creating command level tests. These tests can be replayed at a later time without any network activity, allowing us to detect regressions in the handling of parameters and in the compatability between AzureCLI and the PythonSDK.

##Overview

Each command module has a `tests` folder with the following files: `command_specs.py` and `test_commands.py`. The second is largely boilerplate; you will add your test definitions to `command_specs.py`. These files contain two important definitions: `TEST_DEF` which lists the commands you want to test and gives them each a name, and `ENV_VAR` where you can set any environment variables you might need when replaying on TravisCI.

The structure of `TEST_DEF` is straightforward:

```
TEST_DEF = [
  {
    'test_name': 'name1',
    'command': 'command1'
  },
  {
    'test_name': 'name2',
    'script': script_class()
  }
]
```

Simply add your new entries and run all tests. The test driver will automatically detect the new tests and run the commands, show you the output, and query if it is correct. If so, it will save the HTTP recording into a YAML file, as well as the raw output into a dictionary called `expected_results.res`. When the test is replayed, as long as the test has an entry in `expected_results.res` and a corresponding .yaml file, the test will proceed automatically. If either the entry or the .yaml file are missing, the test will be re-recorded.

If the tests are run on TravisCI, any tests which cannot be replayed will automatically fail. 

##Types of Tests

The system currently accepts individual commands and script test objects. Individual commands will always display the output and query the user if the results are correct. These are the "old" style tests.

To allow for more complex testing scenarios involving creating and deleting resources, long-running operations, or automated verification, use the script object method. To do so, simply create a class in the `command_specs.py` file with the following structure:

```Python
class MyScenarioTest(CommandTestScript):
  def __init__(self):
    super(MyScenarioTest, self).__init__(self.set_up, self.test_body, self.tear_down)
  
  def set_up(self):
    # Setup logic here
    pass
    
  def test_body(self):
    # Main test logic
    pass
    
  def tear_down(self):
    # clean up logic here
    pass
```

The `set_up` and `tear_down` methods are optional and can be omitted. A number of helper methods are available for structuring your script tests.

####run(command_string)

This method executes a given command and returns the output. The results are not sent to the display or to expected results. Use this for:

- running commands that produce no output (the next statement will usually be a test)
- running commands that are needed for conditional logic or in setup/cleanup logic

####rec(command_string)

This method runs a given command and records its output to the display for manual verification. Using this command will force the user to verify the output via a Y/N prompt. If the user accepts the output, it will be saved to `expected_results.res`.

####test(command_string, checks)

This method runs a given command and automatically validates the output. The results are saved to `expected_results.res` if valid, but nothing is display on the screen. Valid checks include: `bool`, `str`, `dict` and JMESPath checks (see below). A check with a `dict` can be used to check for multiple matching parameters (and logic). Child `dict` objects can be used as values to verify properties within nested objects.

#####JMESPath Comparator

You can use the JMESPathComparator object to validate the result from a command.
This is useful for checking that the JSON result has fields you were expecting, arrays of certain lengths etc.

######Usage
```
JMESPathComparator(query, expected_result)
```
- `query` - JMESPath query as a string.
- `expected_result` - The expected result from the JMESPath query (see [jmespath.search()](https://github.com/jmespath/jmespath.py#api))

######Example

The example below shows how you can use a JMESPath query to validate the values from a command.
When calling `test(command_string, checks)` you can pass in just one JMESPathComparator or a list of JMESPathComparators.

```
from azure.cli.utils.command_test_script import JMESPathComparator

self.test('vm list-ip-addresses --resource-group myResourceGroup',
    [
        JMESPathComparator('length(@)', 1),
        JMESPathComparator('[0].virtualMachine.name', 'myVMName')])
```


####set_env(variable_name, value)

This method is a wrapper around `os.environ` and simply sets an environment variable to the specified value.

####pop_env(variable_name)

Another wrapper around `os.environ` this pops the value of the indicated environment variable.

####print_(string)

This method allows you to write to the display output, but does not add to the `expected_results.res` file. One application of this would be to print information ahead of a `rec` statement so the person validating the output knows what to look for.

##Long Running Operations (LRO)

The system now allows the testing of long running operations. Regardless of the time required to record the test, playback will truncate the long running operation to finish very quickly. However, because re-recording these actions can take a very long time, it is recommended that each LRO scenario be individually tested (possibly in tandem with a delete operation) rather than as part of a larger scenario.

##Limitations

The current system saves time, but has some limitations.

+ You can't test for things like 'this input results in an exception'. It simply tests that the response equals an expected response.
