# Build packages in Jenkins server.
# The script expects a virtualenv created under ./env folder as prerequisite

python -m virtualenv --clear env
. ./env/bin/activate

echo 'Build Azure CLI and its command modules '

if [ -d ./artifacts ]; then
    rm -rf ./artifacts
fi

mkdir -p ./artifacts/build
artifacts=$(cd ./artifacts/build && pwd)

working_dir=$(pwd)
for setup_file in $(find src -name 'setup.py'); do
    cd $(dirname $setup_file)
    echo ""
    echo "Components at $(pwd) is being built ..."
    python setup.py sdist -d $artifacts bdist_wheel -d $artifacts
    cd $working_dir
done

echo 'Build completed.'