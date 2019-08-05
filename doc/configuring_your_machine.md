Setting up your development environment
========================================
The Azure Python CLI projects sources are located on GitHub (https://github.com/Azure/azure-cli/). In order to contribute to the project, you are expected to:
-    Have a GitHub account. For Microsoft contributors, follow the guidelines on https://opensourcehub.microsoft.com/ to create, configure and link your account
-    Fork the  https://github.com/Azure/azure-cli/ repository into your private GitHub account
-    Create pull requests against the https://github.com/azure/azure-cli repository to get your code changes merged into the project repository.

## Preparing your machine
1. Azdev is a tool to simplify the process of developing for CLI command modules and extensions. Follow the steps here: https://github.com/Azure/azure-cli-dev-tools#setting-up-your-development-environment
2. Setup tab completion (OSX/Ubuntu ONLY).

    Open Bash or zsh window and run:

    ```Shell
    source <clone root>/src/azure-cli/az.completion.sh
    ```

## Configuring your IDE
#### Visual Studio (Windows only)
1. Both VS 2015 and 2017 support Python development, but VS 2015 is more relible, particular on the intellisense and "Test Explorer". VS 2019's Python support is being actively improved, and we will recommend it here once the evalution result is promising.  
2. Steps to setup VS 2015:

   - You can install VS 2015 from https://visualstudio.microsoft.com/vs/older-downloads/
   - Click menu "View->Other Windows->Python Environment" and create a new one by pointing to a local installed Python like 3.7.0.
   - Click menu "File->New Project", and in the dialog select "Python->From Existing Python Code". This will create a project from your local clone.
   - Go through the wizard
   - Once the project gets populated in the solution explorer, for better IDE performance, exlude folders not interested such as "bin", "build_scripts", "doc", etc. For ther same performance reason, under \<root\>\src\azure-cli\azure\cli\command_modules exlude all unrelated command modules.
   - In solution explorer, right click "Python Environments", and invoke "Add Virtual Environment".
   - Save the new project and solution.
   - Back to the command prompt, activate the virtual environment by running "env\scripts\activate".
   - Run "pip install azdev"
   - Run "azdev setup -c"
   - Run "pip install ptvsd==2.2.0". This is to enable unit test executing & debugging through "Test Explorer"
   - Back to the VS IDE, you are all set


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

#### Azdev CLI
To run tests or check style from the command line, use the `azdev` tool. For more information, visit: https://github.com/Azure/azure-cli-dev-tools

Tests: `azdev test mymodule`

Style checkers: `azdev style mymodule` and `azdev linter mymodule`

#### Visual Studio Code
  Click on the Debug icon in the Activity Bar on the side of Visual Studio Code, and select `Azdev Scripts` from the drop down menu. To execute `azdev` commands via Visual Studio Code, you will need to press the gear icon beside the drop down menu and modify the `args` field in `launch.json`. Make sure that any modification of `launch.json` is not included in your pull requests.

#### Visual Studio
  Select `Test > Windows > Test Explorer` and click `Run All` in the Test Explorer pane.
