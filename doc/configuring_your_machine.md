Setting up your development environment
========================================
The Azure Python CLI projects sources are located on GitHub (https://github.com/Azure/azure-cli/). In order to contribute to the project, you are expected to: 
-	Have a GitHub account. For Microsoft contributors, follow the guidelines on https://opensourcehub.microsoft.com/ to create, configure and link your account
-	Fork the  https://github.com/Azure/azure-cli/ repository into your private GitHub account
-	Create pull requests against the httips://github.com/azure/azure-cli repository to get your code changes merged into the project repository.

##Preparing your machine
+	Install Python 3.5.x from http://python.org. Please note that the version of Python that comes preinstalled on OSX is 2.7. 
+	Clone your repository and check out the master branch
+	Create a new virtual environment “env” for Python 3.5 in the root of your clone. You can do this by running:

Windows
```BatchFile
python.exe -m venv <clone root>\env
```
OSX/Ubuntu
```Shell 
python –m venv <clone root>/env
```

+	Activate the env virtual environment by running:

Windows:
```BatchFile
<clone root>\env\scripts\activate.bat
```
OSX/Ubuntu (bash):
```Shell
. <clone root>/env/bin/activate
```

+	Install the latest autorest generated azure sdk.
```Shell
python –m pip install azure==2.0.0a1
```
+	Add <clone root>\src to your PYTHONPATH environment variable:

Windows:
```BatchFile
set PYTHONPATH=<clone root>\src;%PYTHONPATH%
```
OSX/Ubuntu (bash):
```Shell
export PYTHONPATH=<clone root>/src:${PYTHONPATH}
```

##Configuring your IDE
###Visual Studio (Windows only)
+	Install Python Tools for Visual Studio. As of 2/18/2016, the current version (PTVS 2.2) can be found here.
+	Open the azure-cli.pyproj project
You should now be able to launch your project by pressing F5/start debugging

###Visual Studio Code (Any platform)
Experimental steps – still haven’t been able to get virtual environments to work well with VSCode
+	Install VS Code
+	Install (one of) the python extension(s) (https://marketplace.visualstudio.com/items?itemName=donjayamanne.python)
Debugging should now work (including stepping and setting breakpoints). 

The repo has a launch.json file that will launch the version of Python that is first on your path. 

##Running unit tests:

###Command line:
If you have configured your PYTHONPATH correctly (see above), you should be able to run all unit tests by executing python -m unittest from your <clone root>/src directory. 

###VS Code:
<Working on it>

###Visual Studio
<Working on it>

