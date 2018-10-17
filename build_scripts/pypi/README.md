Python Package Builds (.whl & .tar.gz)
======================================

For example:
```
artifacts_dir=$(mktemp -d)
python build_scripts/pypi/build.py $artifacts_dir .
ls -la $artifacts_dir
```
