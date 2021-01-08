Setting up your development environment
========================================
The Azure Python CLI projects sources are located on GitHub (https://github.com/Azure/azure-cli/). In order to contribute to the project, you are expected to:
-    Have a GitHub account. For Microsoft contributors, follow the guidelines on https://opensource.microsoft.com/ to create, configure and link your account
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
1. Both VS 2015 and 2017 support Python development, but VS 2015 is more reliable, particular on the intellisense and "Test Explorer". VS 2019's Python support is being actively improved, and we will recommend it here once the evaluation result is promising.  
2. Steps to setup VS 2015:

   - You can install VS 2015 from https://visualstudio.microsoft.com/vs/older-downloads/#visual-studio-2015-family
   - Click menu "View->Other Windows->Python Environment" and create a new one by pointing to a local installed Python like 3.7.0.
   - Click menu "File->New Project", and in the dialog select "Python->From Existing Python Code". This will create a project from your local clone.
   - Go through the wizard
   - Once the project gets populated in the solution explorer, for better IDE performance, exclude folders not interested such as "bin", "build_scripts", "doc", etc. For the same performance reason, under \<root\>\src\azure-cli\azure\cli\command_modules exclude all unrelated command modules.
   - In solution explorer, right click "Python Environments", and invoke "Add Virtual Environment".
   - Save the new project and solution.
   - Back to the command prompt, activate the virtual environment by running "env\scripts\activate".
   - Run "pip install azdev"
   - Run "azdev setup -c"
   - Run "pip install ptvsd==2.2.0". This is to enable unit test executing & debugging through "Test Explorer"
   - Back to the VS IDE, you are all set


#### Visual Studio Code (Any platform)


1. Install [VS Code](https://code.visualstudio.com/)
2. Install (one of) the [python extension(s)](https://marketplace.visualstudio.com/items?itemName=ms-python.python) for VS Code
3. Create a new [virtual environment](https://docs.python.org/3/library/venv.html)
    - The location for the environment does not matter, but it's recommended to create it as close to the root folder as possible
    - If there is an existing virtual environment you wish to use, skip this step 
4.  Open the folder containing the clone of this repository in VS Code
5. Set the [Python Interpreter](https://code.visualstudio.com/docs/python/environments#_select-and-activate-an-environment) to use as the python.exe located in your virtual environment
    - If your virtual environment's Python Interpreter is not shown, you may need to add the root folder it's located in to the extension's venv path. This will be under File -> Preferences -> Settings -> Python: Venv Path.
    - You can also use your workspace or user `settings.json`, or `launch.json` file to specify the interpreter's path. Details can be found in the Environments section of the Python VS Code extension [documentation](https://code.visualstudio.com/docs/python/environments#_choose-a-debugging-environment). An example in `settings.json`:
        ```
        {
            "python.pythonPath": "C:\\repo\\env\\Scripts\\python.exe"
        }
        ```
        or in `launch.json`:
        ```
        {
            "pythonPath": "C:\\repo\\env\\Scripts\\python.exe"
        }
        ```
    
6. Activate your environment and execute the following commands
   1. pip install azdev
   2. azdev setup -c

Your setup is now complete. For further documentation on debugging this project in VS Code please refer to [Debugging Az Cli in VS Code](./debug/debug_in_vs_code.md)

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
