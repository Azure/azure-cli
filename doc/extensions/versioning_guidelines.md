# Versioning of Azure Cli Extension

To keep a unified versioning strategy across azure cli extension modules, azure cli extension set up a simple list of rules and requirements on how cli extension version assigned and incremented, based on [Semantic Versioning] (https://semver.org/#semantic-versioning-200) 

## Versioning Scheme

The published cli extension modules MUST comply with the following version scheme:

```
MAJOR.MINOR.PATCH[{a|b}[0-9]*]
```
Extension version identifiers are separated into up to four segments:

- MAJOR: version major number, numeric identifier
- MINOR: version minor number, numeric identifier
- PATCH: version patch number, numeric identifier
- pre: pre-release or preview indicator, started with `a` or `b` and ended with numer