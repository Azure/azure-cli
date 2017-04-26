# Azure CLI Interactive Shell
[![Travis](https://travis-ci.org/Azure/azure-cli-shell.svg?branch=master)](https://travis-ci.org/Azure/azure-cli-shell)

## The interactive shell for Microsoft Azure CLI (Command Line Interface)

- Interactive Tutorials
- Lightweight Drop Down Completions 
- Auto Cached Suggestions 
- Dynamic parameter completion 
- Defaulting scopes of commands
- On the fly descriptions of the commands AND parameters 
- On the fly examples of how to utilize each command 
- Query the previous command
- Navigation of example pane 
- Optional layout configurations 
- Optional "az" component 
- Fun Colors 

![Overview](docs/shell_tutorial.gif)

## Installation

```bash
   $ pip install --user azure-cli-shell
```

A list of common install issues and their resolutions are available at [install troubleshooting](https://github.com/azure/azure-cli-shell/blob/master/docs/install_troubleshooting.md).


## Running

To start the application

```bash
   $ az-shell
```

Then type your commands and hit [Enter]

To use commands outside the application

```bash
   $ #[command]
```

To Search through the last command as json
jmespath format for querying

```bash
   $ ? [param]
```

*Note: Only if the previous command dumps out json, e.g. vm list*

To only see the commands for a command

```bash
   $ %% [top-level command] [sub-level command] etc
```

To undefault a value

```bash
   $ %% ..
```

## Use Examples

Type a command, for example:

```bash
   $ vm create
```

Look at the examples

*Scroll through the pane with Control Y for up and Control N for down #*

Pick the example you want with:

```bash
   $ vm create :: [Example Number]
```

## Clear History

```bash
   $ clear
```

Only clears the appended suggestion when you restart the shell


## Dev Setup

Fork and clone repository

```bash
   $ . dev_setup.py
```

To get the Exit Code of the previous command:

```
   $ $
```

## Docker Image


There is a docker image on docker hub

```bash
   $ docker pull azuresdk/azure-cli-shell:latest
   $ docker run -it azuresdk/azure-cli-shell:latest
   root#: az-shell
```


## License

```
Azure CLI Shell

Copyright (c) Microsoft Corporation

All rights reserved. 

MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the ""Software""), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED *AS IS*, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
```
