Examples of use
===============
NOTE:
Wheel and Twine are required.
Use the command below to install them if not installed.
pip install --upgrade wheel twine

Show help
---------
```
$ python -m automation.release.run -h
```

Build azure-cli-core
--------------------
```
$ python -m automation.release.run -c azure-cli-core
```

Build azure-cli-core without patching the version number
--------------------------------------------------------
```
$ python -m automation.release.run -c azure-cli-core --no-version-patch
```

Build & Publish azure-cli-core to test PyPI
-------------------------------------------
```
$ export TWINE_USERNAME=<user>
$ export TWINE_PASSWORD=<pass>
$ python -m automation.release.run -c azure-cli-core -r https://testpypi.python.org/pypi
```

Build & Publish azure-cli-core to public PyPI
---------------------------------------------
```
$ export TWINE_USERNAME=<user>
$ export TWINE_PASSWORD=<pass>
$ python -m automation.release.run -c azure-cli-core -r https://pypi.python.org/pypi
```
