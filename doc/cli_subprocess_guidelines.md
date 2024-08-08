# Azure CLI Subprocess Guidelines

In certain cli modules, there are scenarios that need to call a subsystem to run commands outside cli, like getting kubectl info in aks, or deployment setup in mysql using `git` and `gh`, through python built-in [subprocess](https://docs.python.org/3/library/subprocess.html) module. Despite its simplicity and versatility, ensuring the security of applying it can be challenging in different platforms under different circumstance, and it is error-prone for developers to neglect security best practices during development.


## Insecure Use Of Subsystem Commands Under Subprocess Module


### Dynamic Command Construction Under Risk

Assume a script that needs to read in `user_input` from users to execute a `git` related command and runs it through subprocess using shell. In regular cases, users would add a valid git command, like `git --version` or something else, but if undesired input gets logged into this system, like `--version;echo aa`, the appended `;echo aa` would be executed by the subsystem too, like below: 

```commandline
import subprocess
user_input = input("input a git command to run: ")
cmd = f"git {user_input}"
subprocess.run(cmd, shell=True)
```

```commandline
input a git command to run: --version;echo aa
git version 2.34.1
aa
```

This is a simple example for demonstrating the side effects in python's subsystem improper usage. And it's common for cli developers to build and execute commands dynamically from users' input in a more complicated way. When constructing and executing commands in subprocess through `shell=True`, it exposes a big security vulnerability to potential malicious users outside. 


## Mitigating Security Vulnerability When Calling Subsystem Commands

There are several aspects of security practices that developers need to have in mindset to safeguard their cli modules from command injection attacks.

TL;DR

### Cli Subprocess

If users don't have the time or knowledge to figure out how to adapt necessary secure practices, azure cli provides `cli_subprocess` which inherited all official subprocess functionalities, with necessary security checks and illegal input blocking and masking enforced. 

What developers need to do is:
1) `import cli_subprocess`
2) replace `subprocess.run` (or Popen or check_call or check_output or call) with `cli_subprocess.run` or etc.
3) construct cmd args as array like: [executable, arg0, arg1, arg2, ...]

`cli_subporcess` will add necessary security checks and process the input and output the same way as `subprocess`, and block all potential risks from commands constructed from user input.
Below is an example for `cli_subprocess` use case:

```commandline
# code before:
cmd = f"git commit -m {user_message}"
import subprocess
output = subprocess.run(cmd, shell=True, check=False, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
if output.returncode != 0:
      raise CLIInternalError('Command execution failed, command is: '{}', error message is: {}'.format(cmd, output.stderr))
return output.stdout
```

If `cli_subporcess` is applied, it would be like:
```commandline
# code after:
cmd = ["git","commit", "-m", user_message]
import subprocess
import cli_subprocess
output = cli_subprocess.run(cmd, shell=True, check=False, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
if output.returncode != 0:
      raise CLIInternalError('Command execution failed, command is: '{}', error message is: {}'.format(cmd, output.stderr))
return output.stdout
```

All various kinds of `subprocess` Popen calling use cases can be easily adjusted into `cli_subprocess` with security risks processed and eliminated in this centralized module.

Besides that, users might need to know some parts of the accessibility in both `cli_subprocess` and `subprocess`
1) when calling shell built-in cmds, like `dir` or `az`, using `shell=True` **in windows platform**, `subprocess` implicitly uses `cmd.exe`, while `cli_subprocess` asks developers to provide the `cmd.exe` as executable file specifically in the arg list's first item, like `["cmd.exe", "/c", "az", "--version"]`
2) if developers want to find an easy way to split their current cmd string into list, **for unix-like platforms**, developers can apply [`shlex.split`](https://docs.python.org/3/library/shlex.html#shlex.split) for quick access. But a prepared cmd statement is still more recommended (for more info about prepared cmd statement, please read below sections).
3) it might be not that obvious to find target command's executable file **in windows platform**, a tool developer can use is `shutil.which` that gives the executable file path in windows system, like `shutil.which(git)`. The cmd `git --version` can be adjusted as `[shutil.which(git), "--version"]`. Please provide the corresponding executable path in target platforms.

### Best Practices In Subprocess Use Cases


The following sections discuss some secure coding conventions that, when implemented, can help protect cli applications from command injection vulnerabilities when calling subsystems through `subprocess`.

#### Proper input validation and sanitization

Input from users or external sources should never be trusted when appending them into subsystem's cmd. Developers better provide expected patterns to validate and sanitize user input before adding that into subsystem's cmd. 
Below is an example input sanitizer that only allows alphanumeric characters from the input string.  

```commandline
import re
def sanitize_input(user_input):
    return re.sub(r'[^a-zA-Z0-9]', '', user_input)
```
In a real cli module scenario, developers better use their corresponding sanitization pattern for reducing the chaining commands risks.

#### Use parameterized cmd statement

A parameterized cmd statement is a way to structure a command starting from defining the command structure first and then provide the parameters that should be inserted into the command separately. 
In this way, the system will treat the first item as the executable file and the left item as args of that executable application.
```
# instead of
cmd = f"git {user_input}"
# using 
cmd = ["git", user_input]
```

#### Avoid use `shell=True` with user_inputs

When using subprocess module, avoid `shell=True` argument when it comes with cmd containing user inputs. When python executes a command with `shell=True`, the system shell will interpret any string passed in and if this string contains user input without proper sanitization, an attacker can inject malicious commands, as demonstrated in the very beginning of this doc.


## Summary
Ensuring the safety of cli from command injection under subprocess calling requires an in-depth understanding of these vulnerabilities and also proactive measures to counteract potential exploits. Cli developers can either apply the three security practices, if applicable, when using builtin `subprocess`, or use a more centralized module `cli_subprocess` cli provided, to safeguard cli modules from command injection attack and for future more accessible security enforcements.
