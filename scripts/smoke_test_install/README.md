Automated Install Testing
=========================

The scripts in this directory allow automated testing of the install.


Set Up
------

[Nose](http://nose.readthedocs.io/en/latest/) and [Sh](https://amoffat.github.io/sh/) are required to run these tests as well as [six](https://pypi.python.org/pypi/six).

```
pip install nose sh six
```

`az` also needs to be installed on the machine you will run the tests from.  
- You need to be logged in to `az` as the tests use `az` to create the VMs.
- You need to have an SSH key on the machine also (i.e. ~/.ssh/id_rsa.pub). Your public key is used so you can log into the VMs for debugging.

Run Tests
---------

### Resource groups
Resource group creation and deletion is done outside of running the tests.  
This is so that the resource group will remain after the tests have executed.  
With this, you can ssh into the VMs and do any required debugging then delete the resource group afterwards.

```
az group create -l <LOCATION> -n <NAME>
az group delete -n <NAME>
```

NOTE: Keep resource group names short and the test names short.
Otherwise, you may get 'deployment name too long' errors when the VMs are being created.

### Environment Variables
The following environment variables are required:
- `AZ_TEST_RG`  (e.g. cli-test-1)
- `AZ_TEST_CLI_VERSION_PREV` (e.g. 2016.06.14.nightly)
- `AZ_TEST_CLI_VERSION` (e.g. 2016.06.15.nightly)
- `AZ_TEST_LOGIN_USERNAME`  
    The Azure subscription username when you run az login. The will be used in the tests to test `az login`.
- `AZ_TEST_LOGIN_PASSWORD`  
This environment variables may need to be escaped if they contain quotes (e.g. for passwords).

The following are optional and have defaults:
- AZ_TEST_INSTALL_URL  (e.g. http://azure-cli-nightly.westus.cloudapp.azure.com/install-dev-latest)
- AZ_TEST_VM_USERNAME  (e.g. myuser)  
    The username of the Linux vms that are created by the tests.

### Test Execution

#### Recommended commands
Collect the number of tests that exist.
```
nosetests --collect-only
```

Now you know how many tests there are, run them all in parallel.
```
nosetests --nologcapture -v --processes=<NUM_TESTS> --process-timeout=<NUM_SECONDS>
```

At the time of writing, `nosetests --nologcapture -v --processes=22 --process-timeout=1800` works well as there were 22 tests.

#### Other test execution commands that may be useful for debugging
```
# Run tests in serial and show results as tests finish
nosetests -v

# Run tests in serial and don't show logs
nosetests --nologcapture

# Run test in serial and show results as tests finish and don't show logs
nosetests --nologcapture -v
```

#### Run specific tests
See https://nose.readthedocs.io/en/latest/usage.html#selecting-tests

For example
```
nosetests test_install_linux:TestUbuntu1404_global
```

Debugging Tests
---------------

`Nose` and `sh` show outputs for the failed tests, broken down with the command executed, exit code, stdout and stderr.

The test log should show you the command that failed. You can then SSH into the machine and debug.

However, if you want to debug the test itself, modify the test and only run that specific test.  
Here are the steps:
1. Find the class that belongs to the test.
2. Modify the `setUpClass()` function so that instead of creating a VM, we use the one that we want to debug with.  
    a. Remove the call to `create_vm()`.  
    b. `import sh` and then use `sh.ssh.bake('-oStrictHostKeyChecking=no', '-tt', "{}@{}".format('<USERNAME>', '<IP_ADDRESS_OF_VM>'))`.  
e.g.
```
@classmethod
def setUpClass(cls):
    import sh
    cls.vm = sh.ssh.bake('-oStrictHostKeyChecking=no', '-tt', "{}@{}".format('myuser', '138.91.197.83'))
```

