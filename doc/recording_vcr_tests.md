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
    'command': 'command2'
  }
]
```

Simply add your new entries and run all tests. The test driver will automatically detect the new tests and run the command, show you the output, and query if it is correct. If so, it will save the HTTP recording into a YAML file, as well as the raw output into a dictionary called `expected_results.res`. When the test is replayed, as long at the test has an entry in `expected_results.res` and a corresponding .yaml file, the test will proceed automatically. If either the entry or the .yaml file are missing, the test will be re-recorded.

If the tests are run on TravisCI, any tests which cannot be replayed will automatically fail. 

##Recording Tests

Many tests, for example those which simply retrieve information, can simply be played back, verified and recorded.

Other tests, such as create and delete scenarios, may require additional commands to set up for recording, or may require additional commands to verify the proper operation of a command. For example, several create commands output nothing on success. Thus, you'll find yourself staring at nothing with a propmpt asking if that is the expected response.

For these scenarios, I recommend having a second shell open, from which you can run any setup commands and then run any commands you need to verify the proper operation of the command in order to answer the prompt.

I don't recommend trying to structure your tests so that one test sets up for another, because in general you cannot guarantee the order in which the tests will run. Also, I don't recommend attempting to record large batches of tests at once. I generally add one to three tests at a time and leave the remaining new tests commented out. Running `testall.bat` will let me record these. Then I uncomment a few more and so on, until they are all recorded.

##Limitations

The current system saves time, but has some limitations.

+ Certain commands require manual steps to setup or verify
+ You can't test for things like 'this input results in an exception'. It simply tests that the response equals an expected response.
+ This system does not work with long running operations. While it technically does, the resulting recording takes as long as the original call, which negates some of the key benefits of automated testing.
