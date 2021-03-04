# Quoting issues with PowerShell

This issue is being tracked at [#15529](https://github.com/Azure/azure-cli/issues/15529).

## Symptom

On Windows, there is a known issue of PowerShell when calling native `.exe` executables or `.bat`, `.cmd` Command Prompt scripts: https://github.com/PowerShell/PowerShell/issues/1995.

In short, **Windows native command invoked from PowerShell will be parsed by Command Prompt again**. This behavior contradicts the doc [About Quoting Rules](https://docs.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_quoting_rules).

As `az` is a Command Prompt script (at `C:\Program Files (x86)\Microsoft SDKs\Azure\CLI2\wbin\az.cmd`), it will have issues when invoked from PowerShell. These issues don't happen when invoking a PowerShell cmdlet:

```powershell
# Double quotes are preserved
> Write-Host '"some quoted text"'
"some quoted text"

# Double quotes are lost
> python.exe -c "import sys; print(sys.argv[1])" '"some quoted text"'
some quoted text
```

In order for a symbol to be received by Azure CLI, you will have to take both PowerShell and Command Prompt's parsing into consideration. If a symbol still exists after 2 rounds of parsing, Azure CLI will receive it. 

## Workaround: the stop-parsing symbol
To prevent this, you may use [stop-parsing symbol](https://docs.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_parsing) `--%` between `az` and arguments.

> The stop-parsing symbol (--%), introduced in PowerShell 3.0, directs PowerShell to refrain from interpreting input as PowerShell commands or expressions.
> When it encounters a stop-parsing symbol, PowerShell treats the remaining characters in the line as a literal.

For instance,

```powershell
az --% vm create --name xxx
```

But keep in mind that **the command still needs to be escaped following the Command Prompt syntax**.

```powershell
# Use --% to stop PowerShell from parsing the argument and escape double quotes
# following the Command Prompt syntax
> python.exe --% -c "import sys; print(sys.argv[1])" "\"some quoted text\""
"some quoted text"
```

## Typical issues

### Ampersand `&` is interpreted by Command Prompt

 This causes the argument to be parsed again by Command Prompt and breaks the argument. This typically happens when passing a URL with query string to `az`:

```powershell
> az 'https://graph.microsoft.com/v1.0/me/events?$orderby=createdDateTime&$skip=20' --debug
az: 'https://graph.microsoft.com/v1.0/me/events?$orderby=createdDateTime' is not in the 'az' command group.
'$skip' is not recognized as an internal or external command,
operable program or batch file.
```

In general, when running `az "a&b"` in PowerShell,

1. Since there is no whitespace in the argument, PowerShell will strip the quotes and pass the argument to Command Prompt
2. The ampersand `&` is parsed again by Command Prompt as a [command separator](https://docs.microsoft.com/en-us/previous-versions/windows/it-pro/windows-xp/bb490954(v=technet.10)#using-multiple-commands-and-conditional-processing-symbols)
3. `b` is treated as a separate command by Command Prompt, instead of part of the argument

```powershell
> az "a&b" --debug
az: 'a' is not in the 'az' command group.
'b' is not recognized as an internal or external command,
operable program or batch file.
```

This is what `cmd.exe` or Windows system sees:

```cmd
>az a&b --debug
az: 'a' is not in the 'az' command group. 
'b' is not recognized as an internal or external command,
operable program or batch file.
```

To solve it:

```powershell
# When quoted by single quotes ('), double quotes (") are preserved by PowerShell and sent 
# to Command Prompt, so that ampersand (&) is treated as a literal character
> az '"a&b"' --debug
Command arguments: ['a&b', '--debug']

# Escape double quotes (") with backticks (`) as required by PowerShell
> az "`"a&b`"" --debug
Command arguments: ['a&b', '--debug']

# Escape double quotes (") by repeating them
> az """a&b""" --debug
Command arguments: ['a&b', '--debug']

# With a whitespace in the argument, double quotes (") are preserved by PowerShell and
# sent to Command Prompt
> az "a&b " --debug
Command arguments: ['a&b ', '--debug']

# Use --% to stop PowerShell from parsing the argument
> az --% "a&b" --debug
Command arguments: ['a&b', '--debug']
```

This issue is tracked at https://github.com/PowerShell/PowerShell/issues/1995#issuecomment-539822061

### Double quotes `"` are lost

This typically happens when passing a JSON to `az`. This is because double quotes within the JSON string are lost when calling a native `.exe` file within PowerShell.

```powershell
# Wrong! Note that the double quotes (") are lost
> python.exe -c "import sys; print(sys.argv)" '{"key": "value"}'
['-c', '{key: value}']
```

This is what `cmd.exe` or Windows system sees:

```cmd
>python.exe -c "import sys; print(sys.argv)" "{"key": "value"}"
['-c', '{key: value}']
```

To solve it:

```powershell
# Escape double quotes (") with backward-slashes (\) as required by Command Prompt,
# then quote the string with single quotes (') as required by PowerShell
> python.exe -c "import sys; print(sys.argv)" '{\"key\": \"value\"}'
['-c', '{"key": "value"}']

# First escape double quotes with backticks (`) as required by PowerShell,
# then escape double quotes with backward-slash (\) as required by Command Prompt,
# then quote the string with double quotes (") as required by PowerShell
> python.exe -c "import sys; print(sys.argv)" "{\`"key\`": \`"value\`"}"
['-c', '{"key": "value"}']

# First escape double quotes by repeating it as required by PowerShell,
# then escape double quotes with backward-slash (\) as required by Command Prompt,
# then quote the string with double quotes (") as required by PowerShell
> python.exe -c "import sys; print(sys.argv)" "{\""key\"": \""value\""}"
['-c', '{"key": "value"}']

# Stop PowerShell parsing
> python.exe --% -c "import sys; print(sys.argv)" "{\"key\": \"value\"}"
['-c', '{"key": "value"}']
```

The same applies to `az`:

```powershell
# Wrong!
> az '{"key": "value"}' --debug
Command arguments: ['{key: value}', '--debug']

# Correct
> az '{\"key\": \"value\"}' --debug
Command arguments: ['{"key": "value"}', '--debug']

> az "{\`"key\`": \`"value\`"}" --debug
Command arguments: ['{"key": "value"}', '--debug']

> az "{\""key\"": \""value\""}" --debug
Command arguments: ['{"key": "value"}', '--debug']

> az --% "{\"key\": \"value\"}" --debug
Command arguments: ['{"key": "value"}', '--debug']
```

## Best practice: use file input for JSON

For complex arguments like JSON string, the best practice is to use Azure CLI's `@<file>` convention to load from a file to bypass the shell's interpretation.

Note that At symbol (`@`) is [splatting operator](https://docs.microsoft.com/powershell/module/microsoft.powershell.core/about/about_splatting) in PowerShell, so it should be quoted.

```powershell
az ad app create ... --required-resource-accesses "@manifest.json"
```

You may also use `@-` to read from `stdin`:

```powershell
Get-Content -Path manifest.json | az ad app create ... --required-resource-accesses "@-"
```
