# Azure CLI Subprocess Guidelines

In certain CLI modules, there are scenarios that need to call a subprocess to run commands outside CLI, like getting kubectl info in aks, or deployment setup in mysql using `git` and `gh`, through python built-in [subprocess](https://docs.python.org/3/library/subprocess.html) module. Despite its simplicity and versatility, ensuring the security of applying it can be challenging in different platforms under different circumstance, and it is error-prone for developers to neglect security best practices during development.


## Insecure Use Of Commands Under Subprocess Module


### Dynamic command construction under risk

Assume a script that needs to read in `user_input` from users to execute a `git` related command and runs it through subprocess using shell. In regular cases, users would add a valid git command, like `git --version` or something else, but if undesired input gets logged into this system, like `--version;echo aa`, the appended `;echo aa` would be executed by `subprocess` too, like below: 

```python
import subprocess
user_input = input("input a git command to run: ")
cmd = f"git {user_input}"
subprocess.run(cmd, shell=True)
```

```console
input a git command to run: --version;echo aa
git version 2.34.1
aa
```

This is a simple example for demonstrating the side effects in python's `subprocess` improper usage. And it's common for CLI developers to build and execute commands dynamically from users' input in a more complicated way. When constructing and executing commands in subprocess through `shell=True`, it exposes a big security vulnerability to potential malicious users outside. 


## Mitigating Security Vulnerability When Calling Subprocess Commands

There are several aspects of security practices that developers need to have in mindset to safeguard their CLI modules from command injection attacks.

### CLI centralized subprocess executing

Azure CLI provides a centralized function `run_cmd` adapted from official `subprocess.run`, with necessary argument covered and illegal input blocking enforced. 

What developers need to do is:
1. `from azure.cli.core.util import run_cmd`
2. replace `subprocess.run` (or `Popen` or `check_call` or `check_output` or `call`) with `run_cmd`.
3. construct cmd `args` as array, like `[executable, arg0, arg1, arg2, ...]`

`run_cmd` add necessary argument type checks and process the input and output the same way as `subprocess.run`, and block potential risks from commands constructed from user input.
Below is an example for `run_cmd` use case:

```python
# code before:
cmd = f"git commit -m {user_message}"
import subprocess
output = subprocess.run(cmd, shell=True, check=False, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
if output.returncode != 0:
      raise CLIInternalError('Command execution failed, command is: '{}', error message is: {}'.format(cmd, output.stderr))
return output.stdout
```

If `run_cmd` is applied, it would be like:
```python
# code after:
cmd = ["git","commit", "-m", user_message]
import subprocess
from azure.cli.core.util import run_cmd
output = run_cmd(cmd, check=False, capture_output=True)
if output.returncode != 0:
      raise CLIInternalError('Command execution failed, command is: '{}', error message is: {}'.format(cmd, output.stderr))
return output.stdout
```

All various kinds of `subprocess` Popen calling use cases can be easily adjusted into `run_cmd` with security risks processed and eliminated in this centralized function.

#### Notes
Besides that, developers might need to know some parts of the accessibility in both `run_cmd` and `subprocess`
1. when calling shell built-in cmds, like `dir` or `echo`, using `shell=True` **in windows platform**, `subprocess` implicitly uses `cmd.exe`, while `run_cmd` asks developers to provide the `cmd.exe` as executable file specifically in the arg list's first item, like `["cmd.exe", "/c", "echo", "abc"]`
2. if developers want to find an easy way to split their current cmd string into list, **for unix-like platforms**, developers can apply [`shlex.split`](https://docs.python.org/3/library/shlex.html#shlex.split) for quick access. But a prepared cmd statement is still more recommended (for more info about prepared cmd statement, please read below sections). 
3. if developers want to locate the target command's executable file, a tool developers can use is `shutil.which` that gives the full executable file path in system, like `shutil.which(git)` returns the full `git.exe` path in windows platform `C:\\Program Files\\Git\\cmd\\git.EXE`. 
4. if the target cmd is `az`-related, like `az group show --name xxxx`, please see the following "`az`-related cmd execution" section.

### `az`-related command execution

If the target cmd is `az`-related, like `az group show --name xxxx`, instead of using `subprocess`, CLI recommends using internal function call to get the target information, as the following three options (if applicable):
 
1. SDK operation. If target cmd is an operation from SDK, developers can apply corresponding method from SDK directly. For example:
```python
# code before:
cmd = "az group show --name {}".format(resource_group_name)
import json
import subprocess
output = subprocess.run(cmd, shell=True, check=False, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
resourceGroup = json.loads(output.stdout)
location = resourceGroup['location']

# code after:
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.profiles import ResourceType
resource_client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES)
location = resource_client.resource_groups.get(resource_group_name).location
```

2. Atomic cmd from codegen. If this cmd has been migrated through codegenV2, developers can call its atomic cmd. For example:
```python
# code before:
cmd = "az monitor autoscale show --name {} --resource-group {}".format(autoscale_name, resource_group_name)
import json
import subprocess
output = subprocess.run(cmd, shell=True, check=False, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
autoscale_settings = json.loads(output.stdout)

# code after:
from .aaz.latest.monitor.autoscale import Show as AutoScaleShow
autoscale_settings = AutoScaleShow(cli_ctx=instance.cli_ctx)(command_args={
    "resource_group": resource_group_name, 
    "autoscale_name": autoscale_name
})
```

3. if neither of the two methods above is applicable, developers can apply the central function `run_az_cmd` CLI provided to execute `az`-related cmds. For example:
```python
# code before:
cmd = "az group show --name {}".format(resource_group_name)
import json
import subprocess
output = subprocess.run(cmd, shell=True, check=False, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
resourceGroup = json.loads(output.stdout)
location = resourceGroup['location']

# code after:
cmd = ["az", "group", "show", "--name", resource_group_name]
from azure.cli.core.util import run_az_cmd
resourceGroup = run_az_cmd(cmd).result
location = resourceGroup['location']
```

### Best practices in subprocess use cases


The following sections discuss some secure coding conventions that, when implemented, can help protect CLI applications from command injection vulnerabilities when using `subprocess` module.

#### Proper input validation and sanitization

Input from users or external sources should never be trusted when appending them into `subprocess` cmd. Developers better provide expected patterns to validate and sanitize user input before adding that into subprocess' cmd. 
Below is an example input sanitizer that only allows alphanumeric characters from the input string.  

```python
import re
def sanitize_input(user_input):
    return re.sub(r'[^a-zA-Z0-9]', '', user_input)
```
In a real CLI module scenario, developers better use their corresponding sanitization pattern for reducing the chaining commands risks.

#### Use parameterized cmd statement

A parameterized cmd statement is a way to structure a command starting from defining the command structure first and then provide the parameters that should be inserted into the command separately. 
In this way, the system will treat the first item as the executable file and the left item as args of that executable application.

```python
# instead of
cmd = f"git {user_input}"
# using 
cmd = ["git", user_input]
```

#### Avoid use `shell=True` with user_inputs

When using subprocess module, avoid `shell=True` argument when it comes with cmd containing user inputs. When python executes a command with `shell=True`, the system shell will interpret any string passed in and if this string contains user input without proper sanitization, an attacker can inject malicious commands, as demonstrated in the very beginning of this doc.


## Summary
Ensuring the safety of Azure CLI from command injection under subprocess calling requires an in-depth understanding of these vulnerabilities and also proactive measures to counteract potential exploits. CLI developers should apply the security practices before using builtin `subprocess`, and it's recommended to use the centralized function `run_cmd` CLI provided (or the applicable three methods for `az`-related cmds) , to safeguard CLI modules from command injection attack and for future more accessible security enforcements.
