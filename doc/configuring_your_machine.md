Setting up your development environment
========================================
The Azure Python CLI projects sources are located on GitHub (https://github.com/Azure/azure-cli/). In order to contribute to the project, you are expected to:
-    Have a GitHub account. For Microsoft contributors, follow the guidelines on https://opensourcehub.microsoft.com/ to create, configure and link your account
-    Fork the  https://github.com/Azure/azure-cli/ repository into your private GitHub account
-    Create pull requests against the https://github.com/azure/azure-cli repository to get your code changes merged into the project repository.

## Preparing your machine
1. Install Python 3.5.x or higher from http://python.org. Please note that the version of Python that comes preinstalled on OSX is 2.7.
2. Clone your repository and check out the [`dev`](https://github.com/Azure/azure-cli/tree/dev) branch.
3. Create a new virtual environment “env” for Python in the root of your clone. You can do this by running:

  #### Windows
  ```BatchFile
  python -m venv <clone root>\env
  ```
  #### OSX/Ubuntu (bash)
  ```Shell
  python -m venv <clone root>/env
  ```
4. Activate the env virtual environment by running:

  #### Windows
  ```BatchFile
  <clone root>\env\scripts\activate.bat
  ```
  #### OSX/Ubuntu (bash)
  ```Shell
  . <clone root>/env/bin/activate
  ```

5. Install the dependencies and load the command modules as local packages using pip.
  ```Shell
  python scripts/dev_setup.py
  ```
6. Add `<clone root>\src` to your PYTHONPATH environment variable:

  #### Windows
  ```BatchFile
  set PYTHONPATH=<clone root>\src;%PYTHONPATH%
  ```
  #### OSX/Ubuntu (bash)
  ```Shell
  export PYTHONPATH=<clone root>/src:${PYTHONPATH}
  ```
7. Setup tab completion (OSX/Ubuntu ONLY).

  Open Bash or zsh window and run:

  ```Shell
  source <clone root>/src/azure-cli/az.completion.sh
  ```

## Configuring your IDE
#### Visual Studio (Windows only)
1. Install Python Tools for Visual Studio. As of 2/18/2016, the current version (PTVS 2.2) can be found at http://microsoft.github.io/PTVS/.
2. Open the `azure-cli.pyproj` project
You should now be able to launch your project by pressing F5/start debugging

#### Visual Studio Code (Any platform)
Experimental steps – still haven’t been able to get virtual environments to work well with VSCode

1. Install VS Code
2. Install (one of) the python extension(s) (https://marketplace.visualstudio.com/items?itemName=donjayamanne.python)
3. Put [breakpoints](https://code.visualstudio.com/docs/editor/debugging#_breakpoints) in your code, then click on the Debug icon in the Activity Bar on the side of Visual Studio Code, and select `Azure CLI Debug` from the drop down menu. After that, press the play button to start debugging.
4. To add custom arguments to the command that you want to debug, press the gear icon beside the drop down menu and modify the `args` field in `launch.json`

The repo has a `launch.json` file that will launch the version of Python that is first on your path.

## Running CLI
#### Command line
1. Activate your virtual environment if not already done:

  #### OSX/Ubuntu (bash):
  ```Shell
  . <clone root>/env/bin/activate
  ```

  #### Windows:
  ```BatchFile
  <clone root>\env\scripts\activate.bat
  ```

2. Invoke the CLI using:

  #### Windows/OSX/Ubuntu:
  ```
  az
  ```

## Running Tests and Checking Code Style
#### Command line
  Running the `dev_setup.py` file will install `azdev`, a CLI that performs useful tasks for Azure CLI developers such as executing  CLI tests, CLI linter, and style checking.

##### Windows/OSX/Ubuntu:

  For a list of available `azdev` commands:
  ```
  azdev --help
  ```

  To run the CLI tests:
  ```
  azdev test [-h] [--series] [--live] [--src-file SRC_FILE]
                  [--dest-file DEST_FILE] [--ci] [--discover]
                  [--profile PROFILE]
                  [tests [tests ...]]
  ```

  To check the CLI and command modules for style errors:
  ```
  azdev style [-h] [--ci] [--pep8] [--pylint] [--module MODULES]
  ```

#### Visual Studio Code
  Click on the Debug icon in the Activity Bar on the side of Visual Studio Code, and select `Azdev Scripts` from the drop down menu. To execute `azdev` commands via Visual Studio Code, you will need to press the gear icon beside the drop down menu and modify the `args` field in `launch.json`. Make sure that any modification of `launch.json` is not included in your pull requests.

#### Visual Studio
  Select `Test > Windows > Test Explorer` and click `Run All` in the Test Explorer pane.
