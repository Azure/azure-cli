Extension Metadata
==================

Additional metadata can be added to your extension.

This is useful if you want to:
- Specify a version contract for your extension and the CLI.
- etc.


How To
------

Create the file `azext_metadata.json` under your extension.

For example `azext_*/azext_metadata.json`.

In your `setup.py`, include the following:
``` python
package_data={'azext_*': ['azext_metadata.json']}
```

Now, the CLI will be able to read your extension metadata.

Note: Replace `*` with your module name.

Python documentation - [Installing Package Data](https://docs.python.org/2/distutils/setupscript.html#installing-package-data)


Metadata Format
---------------

This documents the known metadata entries.

Note: You can optionally extend this with your own metadata by adding your own namespace. We use the `azext` namespace.

### azext.minCliCoreVersion
Description: The minimum CLI core version required (inclusive).
Exclude to not specify a minimum.

Type: `string`

Example: `"azext.minCliCoreVersion": "2.0.10"`

### azext.maxCliCoreVersion
Description: The maximum CLI core version required (inclusive).
Exclude to not specify a maximum.

Type: `string`

Example: `"azext.maxCliCoreVersion": "2.0.15"`

### azext.isPreview
Description: Indicate that the extension is in preview.

### azext.isExperimental
Description: Indicate that the extension is experimental and not covered by customer support.

Type: `boolean`

Example: `"azext.isPreview": true`
