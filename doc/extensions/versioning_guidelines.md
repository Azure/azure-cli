# Versioning of Azure CLI Extension

To keep a unified versioning strategy across Azure CLI extension modules, Azure CLI set up a simple list of rules and requirements on how CLI extension version numbers are assigned and incremented, based on [Semantic Versioning](https://semver.org/#semantic-versioning-200) 

## Versioning Scheme

The published CLI extension modules MUST comply with the following version scheme:

```
MAJOR.MINOR.PATCH[pre]
```
Extension version identifiers are separated into up to four segments:

- MAJOR: version major number, numeric identifier, non-negative integers, no leading zeroes
- MINOR: version minor number, numeric identifier, non-negative integers, no leading zeroes
- PATCH: version patch number, numeric identifier, non-negative integers, no leading zeroes
- pre: preview (or pre-release) indicator, `b[1-9][0-9]*`, started with `b` and ended with numeric identifier, positive integers, no leading zeroes

#### Notes
- Azure CLI extension only holds two kinds of public releases: stable and preview
- Each segment MUST increase numerically. If MAJOR number is incremented, MINOR and PATCH number should be reset to 0. And PATCH number should be reset to 0 if MINOR number is incremented
- Precedence is determined by the first difference when comparing each of these segments from left to right as follows: Major, minor, and patch versions numerically. And, preview-release version is smaller than corresponding stable-release version. For instance: 1.9.0 < 2.0.0b1 < 2.0.0b2 < 2.0.0 < 2.1.0

## Versioning Practice

### Initialization

Extension modules released as stable version should use version scheme: MAJOR.MINOR.PATCH and version number should start with 1.0.0. While modules released as preview version use scheme: MAJOR.MINOR.PATCHb[0-9]+ and initialization starts with 1.0.0b1. Existing modules should comply with this scheme in future releases, and those already did need to increase their version as following increment rule.

### CLI Extension Version Increment Rules
CLI extension holds the following rules:
1. if next version is stable,
   - if last version is stable as x.x.x (>= 1.0.0):
     - if breaking change introduced, next version will be x+1.x.x
     - if new features added but no breaking change, next version will be x.x+1.x
     - if only bug fixes made, next version will be x.x.x+1
   - if no last version (or last version < 1.0.0), next version will be the first stable version 1.0.0
2. if next version is preview,
   - if last version is stable as x.x.x (>= 1.0.0):
     - if breaking change introduced, next version will be x+1.x.xb1
     - if new features added but no breaking change, next version will be x.x+1.xb1
     - if only bug fixes made, next version will be x.x.x+1b1
   - if last version is preview as x.x.xbx (>= 1.0.0b1):
     - if breaking change added, next version will be x+1.x.xb1
     - if new features added but no breaking change, next version will be x.x.xbx+1
     - if only bug fixes, next version will be x.x.xbx+1
   - if last version is stable as x.x.x (<1.0.0) or preview as x.x.xbx (< 1.0.0b1), next preview version should be 1.0.0b1

### CLI Extension Version Transition Table

Considering version increment rules above, version transition table can be summarized as table below:

<table>
    <tr>
        <td rowspan="2">Next version tag</td>
        <td rowspan="2">Last version</td>
        <td colspan="3">Changes</td>
        <td rowspan="2">Next version</td>
    </tr>
    <tr>
        <td>Breaking change</td>
        <td>Feature</td>
        <td>Bug fix</td>
    </tr>
    <tr>
        <td rowspan="4">Stable</td>
        <td rowspan="3">2.0.0</td>
        <td>&#10004</td>
        <td>-</td>
        <td>-</td>
        <td>3.0.0</td>
    </tr>
    <tr>
        <td>&#10006</td>
        <td>&#10004</td>
        <td>-</td>
        <td>2.1.0</td>
    </tr>
    <tr>
        <td>&#10006</td>
        <td>&#10006</td>
        <td>&#10004</td>
        <td>2.0.1</td>
    </tr>
    <tr>
        <td>No stable version</td>
        <td>-</td>
        <td>-</td>
        <td>-</td>
        <td>1.0.0</td>
    </tr>
    <tr>
        <td rowspan="6">Preview</td>
        <td rowspan="3">2.0.0</td>
        <td>&#10004</td>
        <td>-</td>
        <td>-</td>
        <td>3.0.0b1</td>
    </tr>
    <tr>
        <td>&#10006</td>
        <td>&#10004</td>
        <td>-</td>
        <td>2.1.0b1</td>
    </tr>
    <tr>
        <td>&#10006</td>
        <td>&#10006</td>
        <td>&#10004</td>
        <td>2.0.1b1</td>
    </tr>
    <tr>
        <td rowspan="3">2.0.0b1</td>
        <td>&#10004</td>
        <td>-</td>
        <td>-</td>
        <td>3.0.0b1</td>
    </tr>
    <tr>
        <td>&#10006</td>
        <td>&#10004</td>
        <td>-</td>
        <td>2.0.0b2</td>
    </tr>
    <tr>
        <td>&#10006</td>
        <td>&#10006</td>
        <td>&#10004</td>
        <td>2.0.0b2</td>
    </tr>
</table>

#### Notes
- &#10004; means yes
- &#10006; means no
- \- means skip check
- The major version number of preview can increase by at most one compared to the last stable version. For example, the last stable version is 2.0.0, if there are breaking changes for next preview release, the version will be 3.0.0b1. Then another breaking changes for the next preview release, the version will be 3.0.0b2
- Minimum preview version is 1.0.0b1 and minimum stable version is 1.0.0

## Backward Compatibility of Extension Version Tags

Current extension module has a combination of semantic scheme and extra metadata tags (`azext.isExperimental` and `azext.isPreview`) to mark module release version. To keep backward compatibility:
- `azext.isPreview` is reserved for all preview extension releases.
- `azext.isExperimental` is deprecated and will be replaced by `azext.isPreview` for version tag simplicity, since CLI extension only supports two types of public releases now: stable and preview
- For all stable extension releases, neither `azext.isPreview` nor `azext.isExperimental` can be added into module metadata.

## Extension Installation Upgrade

To distinguish `stable-only` extension installation with `preview-included` extension installation, `--allow-preview` is added into `az extension add/update` and `az upgrade` and the `stable/preview` justification is made based on this extension versioning specification from CLI version `2.56.0`. Default value for `--allow-preview` is `True` for user compatibility and will be reset to `False` in future breaking change window.