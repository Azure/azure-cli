Install Troubleshooting
=======================

Before posting an issue, please review our list of [common issues](https://github.com/Azure/azure-cli/issues?q=label%3AFAQ+is%3Aclosed).

These are issues we have closed because we cannot address them within the CLI due to platform or language limitations.


Upgrade from 0.1.0b10 causes 'KeyError: Azure' error
----------------------------------------------------

On Python 2, it's recommended to upgrade with the `--ignore-installed` flag:
`pip install --upgrade --ignore-installed azure-cli`.

Alternatively, use the interactive install script.

See [#1540](https://github.com/Azure/azure-cli/issues/1540#issue-195125878)


Error: 'Could not find a version that satisfies the requirement azure-cli'
--------------------------------------------------------------------------

The error message from pip usually means a very old version of pip is installed.
Run `pip --version` to confirm. [Latest pip version](https://pip.pypa.io/en/stable/news/)

Upgrade `pip` with ``$ pip install --upgrade pip`` or install with the ``--pre`` flag.

See [#1308](https://github.com/Azure/azure-cli/issues/1308#issuecomment-260413613)


'X509' object has no attribute '_x509'
--------------------------------------

If you run into an ``AttributeError: 'X509' object has no attribute '_x509'`` error, downgrade your version of the requests library from 2.12.1 to 2.11.1.

See [#1360](https://github.com/Azure/azure-cli/issues/1360)


Windows - 'FileNotFoundError' error on install
----------------------------------------------

Verify that the file path quoted in the error has more than 260 characters.

If so, the installation files exceed the 260 character limit for file paths on Windows.

This can be resolved by installing the CLI in a higher directory to prevent reaching the Windows max filepath length.

See [#1221](https://github.com/Azure/azure-cli/issues/1221#issuecomment-258290204)


Ubuntu 12.04 LTS - Known warning
--------------------------------

You may see the following warning message during install and execution of `az`.
```
/usr/local/az/envs/default/local/lib/python2.7/site-packages/pip/pep425tags.py:30: RuntimeWarning: invalid Python installation: unable to open /usr/az/envs/default/lib/python2.7/config/Makefile (No such file or directory)
  warnings.warn("{0}".format(e), RuntimeWarning)
```

See [#348](https://github.com/Azure/azure-cli/issues/348)

See also [pypa/pip#1074](https://github.com/pypa/pip/issues/1074)


Errors with curl redirection
----------------------------

If you get an error with the curl command regarding the `-L` parameter or an error saying `Object Moved`, try using the full url instead of the aka.ms url:
```shell
# If you see this:
$ curl -L https://aka.ms/InstallAzureCli | bash
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100   175  100   175    0     0    562      0 --:--:-- --:--:-- --:--:--   560
bash: line 1: syntax error near unexpected token `<'
'ash: line 1: `<html><head><title>Object moved</title></head><body>

# Try this instead:
$ curl https://azurecliprod.blob.core.windows.net/install | bash
```


Errors on install with cffi or cryptography
-------------------------------------------

If you get errors on install on **OS X**, upgrade pip by typing:

```shell
    pip install --upgrade --force-reinstall pip
```

If you get errors on install on **Debian or Ubuntu** such as the examples below,
install libssl-dev and libffi-dev by typing:

```shell
    sudo apt-get update && sudo apt-get install -y libssl-dev libffi-dev
```

Also install Python Dev for your version of Python.

Python 2:

```shell
    sudo apt-get install -y python-dev
```

Python 3:

```shell
    sudo apt-get install -y python3-dev
```

Ubuntu 15 may require `build-essential` also:

```shell
    sudo apt-get install -y build-essential
```

**Example Errors**

```shell

    Downloading cffi-1.5.2.tar.gz (388kB)
      100% |################################| 389kB 3.9MB/s
      Complete output from command python setup.py egg_info:

          No working compiler found, or bogus compiler options
          passed to the compiler from Python's distutils module.
          See the error messages above.
          (If they are about -mno-fused-madd and you are on OS/X 10.8,
          see http://stackoverflow.com/questions/22313407/ .)

      ----------------------------------------
    Command "python setup.py egg_info" failed with error code 1 in /tmp/pip-build-77i2fido/cffi/
```

```shell
    #include <openssl/e_os2.h>
                             ^
    compilation terminated.
    error: command 'x86_64-linux-gnu-gcc' failed with exit status 1

    Failed building wheel for cryptography
```

See Stack Overflow question - [Failed to install Python Cryptography package with PIP and setup.py](http://stackoverflow.com/questions/22073516/failed-to-install-python-cryptography-package-with-pip-and-setup-py)
