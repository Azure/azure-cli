Recording Command Tests with VCR.py
========================================

Azure CLI uses the VCR.py library to record the HTTP messages exchanged during a program run and play them back at a later time, making it useful for creating command level scenario tests. These tests can be replayed at a later time without any network activity, allowing us to detect regressions in the handling of parameters and in the compatability between AzureCLI and the PythonSDK.

##Overview

Each command module has a `tests` folder with a file called: `test_<module>_commands.py`. This is where you will define tests. 

Tests all derive from the `VCRBTestBase` class found in `azure.cli.utils.vcr_test_base`. This class exposes the VCR tests using the standard Python `unittest` framework and allows the tests to be discovered by and debugged in Visual Studio.

After adding your test, run it. The test driver will automatically detect the test is unrecorded and record the HTTP requests and responses in a cassette .yaml file. If the test succeeds, the cassette will be preserved and future playthroughs of the test will come from the cassette.

If the tests are run on TravisCI, any tests which cannot be replayed will automatically fail. 

##Authoring Tests

To create a new test, simply create a class in the `test_<module>_commands.py` file with the following structure:

```Python

class MyTestClass(VCRTestBase):

  def __init__(self, test_method):
    # TODO: replace MyTestClass with your class name
    super(MyTestClass, self).__init__(__file__, test_method, debug=False, run_live=False)
      
  def test_my_test_class(self): # TODO: rename to 'test_<your name here>'
    self.execute()

  def body(self):
    # TODO: insert your test logic here
    
  def set_up(self):
    # TODO: Optional setup logic here (will not be replayed on playback)
    
  def tear_down(self):
    # TODO: Optional tear down logic here (will not be replayed on playback)
```

The `debug` and `run_live` parameters in the `__init__` method are shown with their defaults and can be omitted. `debug` is the equivalent of specifying `debug=True` for all calls to `cmd` in the test (see below). Specifying `run_live=True` will cause the test to always be run with actual HTTP requests, ignoring VCR entirely.

The `set_up` and `tear_down` methods are optional and can be omitted. A number of helper methods are available for structuring your script tests.

####cmd(command_string, checks=None, allowed_exceptions=None, debug=False)

This method executes a given command and returns the output. If the output is in JSON format, the method will return the results as a JSON object for easier manuipulation.

The `debug` parameter can be specified as `True` on a single call to `cmd` or in the init of the test class. Turning this on will print the command string, the results and, if a failure occurred, the failure.

The `allowed_exceptions` parameter allows you to specify one or more (as a list) exception messages that will allow the test to still pass. Exception types are not used because the CLI wraps many types of errors in a `CLIError`. There are some tests where a specific exception is intended. Add the exception message to this list to allow the test to continue successfully in the presence of this message.

The `checks` parameter allows you to specify one or more (as a list) checks to automatically validate the output. A number of Check objects exist for this purpose. You can create your own as long as they implement the compare method (see existing checks for examples):

#####JMESPathCheck(query, expected_result)

Use the JMESPathCheck object to validate the result using any valid JMESPath query. This is useful for checking that the JSON result has fields you were expecting, arrays of certain lengths etc. See www.jmespath.org for guidance on writing JMESPath queries.

######Usage
```
JMESPathCheck(query, expected_result)
```
- `query` - JMESPath query as a string.
- `expected_result` - The expected result from the JMESPath query (see [jmespath.search()](https://github.com/jmespath/jmespath.py#api))

######Example

The example below shows how you can use a JMESPath query to validate the values from a command.
When calling `test(command_string, checks)` you can pass in just one JMESPathComparator or a list of JMESPathComparators.

```Python
self.cmd('vm list-ip-addresses --resource-group myResourceGroup', checks=[
  JMESPathCheck('length(@)', 1),
  JMESPathCheck('[0].virtualMachine.name', 'myVMName')
])
```

#####NoneCheck()

Use this to verify that the output contains nothing. Note that this is different from `checks=None` which will skip any validation.

#####StringCheck(expected_result)

Matches string output to expected.

#####BooleanCheck(expected_result)

Compares truthy responses (True, 'true', 1, etc.) to a Boolean True or False.

####set_env(variable_name, value)

This method is a wrapper around `os.environ` and simply sets an environment variable to the specified value.

####pop_env(variable_name)

Another wrapper around `os.environ` this pops the value of the indicated environment variable.

##Test Issues

Here are some common issues that occur when authoring tests that you should be aware of.

- **deployment_name**: Commands (typically smart creates) which utilize ARM templates accept a hidden `deployment_name` parameter. During normal use, this value is generated automatically, but when authoring a test, this value must be specified or a match request will not be found on playback. Azure keeps deployment names reserved for a time--if you try to re-record a test while the deployment name is still reserved, your test will fail. The symptom will usually be an empty result. If this happens, try changing the deployment name and re-recording.
- **Non-deterministic results**: If you find that a test will pass on some playbacks but fail on others, there are a couple possible things to check:
  1. check if your command makes use of concurrency.
  2. check your parameter aliasing (particularly if it complains that a required parameter is missing that you know is there)
- **Paths**: When including paths in your tests as parameter values, always wrap them in double quotes. While this isn't necessary when running from the command line (depending on your shell environment) it will likely cause issues with the test framework.
