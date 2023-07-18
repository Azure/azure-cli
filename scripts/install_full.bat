Rem This script is the windows counter-part to ./install_full.sh

pushd %~dp0..

set cmd="dir .\src\ /b | findstr /v azure-cli-testsdk"
for /f "tokens=*" %%e in (' %cmd% ') do (
    pip install --no-deps .\src\%%e
)

set cmd="python .\scripts\get-python-version.py"
for /f "tokens=*" %%v in (' %cmd% ') do set SHORT_PY_VER=%%v
pip install -r .\src\azure-cli\requirements.%SHORT_PY_VER%.Windows.txt

popd