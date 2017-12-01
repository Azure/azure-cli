Setting up your development environment
========================================
The Azure Python CLI projects sources are located on GitHub (https://github.com/Azure/azure-cli/). In order to contribute to the project, you are expected to:
-    Have a GitHub account. For Microsoft contributors, follow the guidelines on https://opensourcehub.microsoft.com/ to create, configure and link your account
-    Fork the  https://github.com/Azure/azure-cli/ repository into your private GitHub account
-    Create pull requests against the https://github.com/azure/azure-cli repository to get your code changes merged into the project repository.

## Preparing your machine
1.    Install Python 3.5.x from http://python.org. Please note that the version of Python that comes preinstalled on OSX is 2.7.
2.    Clone your repository and check out the master branch.
3.    Create a new virtual environment “env” for Python 3.5 in the root of your clone. You can do this by running:

  #### Windows
  ```BatchFile
  python -m venv <clone root>\env
  ```
  #### OSX/Ubuntu (bash)
  ```Shell
  python –m venv <clone root>/env
  ```
4.  Activate the env virtual environment by running:

  #### Windows
  ```BatchFile
  <clone root>\env\scripts\activate.bat
  ```
  #### OSX/Ubuntu (bash)
  ```Shell
  . <clone root>/env/bin/activate
  ```

5.    Install the dependencies and load the command modules as local packages using pip.
  ```Shell
  python scripts/dev_setup.py
  ```
6.  Add `<clone root>\src` to your PYTHONPATH environment variable:

  #### Windows
  ```BatchFile
  set PYTHONPATH=<clone root>\src;%PYTHONPATH%
  ```
  #### OSX/Ubuntu (bash)
  ```Shell
  export PYTHONPATH=<clone root>/src:${PYTHONPATH}
  ```
7.  Setup tab completion (OSX/Ubuntu ONLY).

  Open Bash or zsh window and run:

  ```Shell
  source <clone root>/src/azure-cli/az.completion.sh
  ```

## Configuring your IDE
#### Visual Studio (Windows only)
1.    Install Python Tools for Visual Studio. As of 2/18/2016, the current version (PTVS 2.2) can be found at http://microsoft.github.io/PTVS/.
2.    Open the azure-cli.pyproj project
You should now be able to launch your project by pressing F5/start debugging

#### Visual Studio Code (Any platform)
Experimental steps – still haven’t been able to get virtual environments to work well with VSCode

1.    Install VS Code
2.    Install (one of) the python extension(s) (https://marketplace.visualstudio.com/items?itemName=donjayamanne.python)
Debugging should now work (including stepping and setting breakpoints).

The repo has a launch.json file that will launch the version of Python that is first on your path.

## Running CLI
#### Command line
1.  Activate your virtual environment if not already done

  #### OSX/Ubuntu (bash):
  ```Shell
  . <clone root>/env/bin/activate
  ```

  #### Windows:
  ```BatchFile
  <clone root>\env\scripts\activate.bat
  ```

2.  Invoke the CLI using:

  #### Windows/OSX/Ubuntu:
  ```
  az
  ```

## Running Tests:
#### Command line
  Running the `dev_setup.py` file installed the test and style check scripts into the `tools` directory under your
  `<clone root>` directory and added them into the current virtualenv.

##### Windows/OSX/Ubuntu:

  To run the CLI tests:
  ```
  run_tests [-h] [--module MODULES [MODULES ...]] [--parallel] [--live] [--test TESTS]
  ```

  To check the CLI and command modules for style errors:
  ```
  check_style [-h] [--ci] [--pep8] [--pylint] [--module MODULES]
  ```

#### VS Code
  Under construction...

#### Visual Studio
  Select `Test > Windows > Test Explorer` and click `Run All` in the Test Explorer pane.
