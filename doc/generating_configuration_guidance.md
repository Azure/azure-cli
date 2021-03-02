# Generating Configuration Guidance

[Azdev](https://github.com/Azure/azure-cli-dev-tools) supports to generate a snapshot of command interfaces for a specified module since version 0.2.0.

## Output

### Folder structure
After generation, there will be a folder named `configuration` under the module dir. The subdirectories of `configuration` are named by profiles, such as `latest`, `2020-09-01-hybrid` and `2019-03-01-hybrid`.
Each profile named folder contains two json files named `commands.json` and `examples.json` respectively.

```
- <module dir>
    - ...
    - configuration
        - latest
            - commands.json
            - examples.json
        - 2020-09-01-hybrid
            - commands.json
            - examples.json
        - <other profile name>
            - commands.json
            - examples.json
```

### Schema of `commands.json`

```json

```

### Schema of `examples.json`

```json


```

