# Debug in Visual Studio Code

## Prerequisite

* Visual Studio Code [Link](http://code.visualstudio.com/)
* Visual Studio Code Python Extension [Link](https://marketplace.visualstudio.com/items?itemName=donjayamanne.python)
* Python 3.6+
* Set up development environment [Link](https://github.com/Azure/azure-cli/blob/master/doc/configuring_your_machine.md)

## Quick start

1. Start VS Code at the root of the `azure-cli` source code folder.
2. Switch to [debug panel](https://code.visualstudio.com/Docs/editor/debugging). (CMD + Shift + D)
3. Select one of the debug configuration in the dropdown on top of the debug panel.
4. Start debugging (Press F5 or click the play button)

## Configuration

The `launch.json` under `.vscode` folder has already been pre-configured to enable execute `az --help` and break in to debug immediately. You can update it to execute the scenario you need.

1. Set `false` to `stopOnEntry` property to break at the first break point you specified.
2. Update the `args` array to run specified command. You need to make sure the arguments are split by space. 
3. Choose between external terminal and integrated terminal. The latter can be toggle by Ctrl + `

## Reference
- `launch.json` schema: https://code.visualstudio.com/Docs/editor/debugging
