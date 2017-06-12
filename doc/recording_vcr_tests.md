Automating tests for Azure CLI
========================================

## Overview

There are two types of automated tests you can add for Azure CLI. They are the [unit tests](https://en.wikipedia.org/wiki/Unit_testing) and the [integration tests](https://en.wikipedia.org/wiki/Integration_testing). 

For unit tests, we support unit tests written in the forms of both standard [unittest](https://docs.python.org/3/library/unittest.html) and [nosetest](http://nose.readthedocs.io/en/latest/writing_tests.html).

For integration tests, we provide [ScenarioTest](scenario_base_tests.md) to support [VCR.py](https://vcrpy.readthedocs.io/en/latest/) based replayable tests.

## About replayable tests

The Azure CLI translates user inputs into Azure Python SDK call. And Azure Python SDK will communicate with [Azure REST API](https://docs.microsoft.com/en-us/rest/api/). Therefore if the HTTP communicate is captured and recorded, the integration tests can be replay in automation without a live testing environment.

The Azure CLI relies on [VCR.py](https://vcrpy.readthedocs.io/en/latest/) to record and replay HTTP communications. On top of the VCR.py, we build [ScenarioTest](scenario_base_test.md) to facilitate authoring tests.

## Authoring Tests

https://github.com/Azure/azure-cli/blob/master/doc/scenario_base_tests.md

### Tips

* Make the tests delete the Azure resources after execution.
* Name the test method in following format: `test_<module>_<feature>`.

## Recording Tests

### Preparing

1. Set up your [development environment](configuring_your_machine.md)
2. Log in your Azure account using `az login` command.
3. Select the API profile you want to test. (Optional)
4. Select the subscription you want to use for recording tests. The replaying does not rely on the knowledge of the subscription. And the credentials will be removed from the recordings.

### Record test for the first time

After the test is executed, a recording file will be generated at `recording/<api_profile_name>/<test_name>.yaml`. The recording file will be created no matter the test pass or not. The behavior makes it easy for you to find issues when a test fails. If you make changes to the test, delete the recording and rerun the test, a new recording file will be regenerated.

It is a good practice to add recording file to the local git cache, which makes it easy to diff the different versions of recording to detect issues or changes.

Once the recording file is generated, execute the test again. This time the test will run in playback mode. The execution is offline, and will not act on the Azure subscription.

If the replay passes, you can commit the tests as well as recordings.

### Run test live

When recording file is missing, the test framework will execute the test in live mode. You can force tests to be run live by set following environment variable:
```
export AZURE_CLI_TEST_RUN_LIVE='True'
```

Also, you can author tests which are for live test only. Just derive the test class from [LiveTest].

### Rebase recordings

The tests are run on TravisCI as part of the pull request validation. Therefore it is important to keep the recordings up-to-date. Rebase recordings can be done by force live test or deleting existing recording locally and submit new recordings.

## Legacy integration tests.

Before `ScenarioTest` was added, the integration tests all derive from [vcr_test_base](https://github.com/Azure/azure-cli/blob/013b96e702a4eb054f67e8a563a7b050eac4f036/src/azure-cli-testsdk/azure/cli/testsdk/vcr_test_base.py). However, it is now obsoleted. All new integration tests should derive from `ScenarioTest`.

## Test Issues

Here are some common issues that occur when authoring tests that you should be aware of.

- **Non-deterministic results**: If you find that a test will pass on some playbacks but fail on others, there are a couple possible things to check:
  1. check if your command makes use of concurrency.
  2. check your parameter aliasing (particularly if it complains that a required parameter is missing that you know is there)
- **Paths**: When including paths in your tests as parameter values, always wrap them in double quotes. While this isn't necessary when running from the command line (depending on your shell environment), it will likely cause issues with the test framework.
