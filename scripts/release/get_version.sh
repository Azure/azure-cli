# Extract the version of the CLI from azure-cli package's __init__.py file.

: "${BUILD_STAGINGDIRECTORY:?BUILD_STAGINGDIRECTORY environment variable not set}"

ver=`cat src/azure-cli/azure/cli/__init__.py | grep __version__ | sed s/' '//g | sed s/'__version__='// |  sed s/\"//g`
echo $ver > $BUILD_STAGINGDIRECTORY/version
echo $ver > $BUILD_STAGINGDIRECTORY/azure-cli-${ver}.txt