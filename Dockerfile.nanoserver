FROM mcr.microsoft.com/windows/servercore:1709 AS base

ARG CLI_VERSION

# Metadata as defined at http://label-schema.org
ARG BUILD_DATE
LABEL maintainer="Microsoft" \
      org.label-schema.schema-version="1.0" \
      org.label-schema.vendor="Microsoft" \
      org.label-schema.name="Azure CLI 2.0" \
      org.label-schema.version=$CLI_VERSION \
      org.label-schema.license="MIT" \
      org.label-schema.description="The Azure CLI 2.0 is the new Azure CLI and is applicable when you use the Resource Manager deployment model." \
      org.label-schema.url="https://docs.microsoft.com/cli/azure/overview" \
      org.label-schema.usage="https://docs.microsoft.com/cli/azure/install-az-cli2#docker" \
      org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.vcs-url="https://github.com/Azure/azure-cli.git" \
      org.label-schema.docker.cmd="docker run -v $HOME\.azure:C:\Users\ContainerUser\.azure -it mcr.microsoft.com/azure-cli:$CLI_VERSION"

SHELL ["powershell", "-Command", "$ErrorActionPreference = 'Stop'; $ProgressPreference = 'SilentlyContinue';"]

ENV PYTHON_VERSION 3.6.5
ENV PYTHON_HASH 9e96c934f5d16399f860812b4ac7002b
ENV DESTINATION_FOLDER C:\\tools

RUN $python_url = ('https://www.python.org/ftp/python/{0}/python-{0}-amd64.exe' -f $env:PYTHON_VERSION); \
    Write-Host ('Downloading {0}...' -f $python_url); \
    mkdir tmp > $null; \
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; \
    (New-Object System.Net.WebClient).DownloadFile($python_url, 'c:\tmp\python-installer.exe'); \
    Write-Host ('Checking hash...' -f $python_url); \
    if ((Get-FileHash c:\tmp\python-installer.exe -Algorithm md5).Hash -ne $env:PYTHON_HASH) { Write-Host 'Python installer checksum verification failed!'; exit 1; }; \
    $install_folder = Join-Path -Path $env:DESTINATION_FOLDER -ChildPath 'python'; \
    Write-Host ('Installing into {0}...' -f $install_folder); \
    Start-Process c:\tmp\python-installer.exe -Wait -ArgumentList @('/quiet', 'InstallAllUsers=1', 'TargetDir={0}' -f $install_folder, 'PrependPath=1', 'Shortcuts=0', 'Include_doc=0','Include_pip=1', 'Include_test=0'); \
    Remove-Item tmp -Recurse -Force;

FROM mcr.microsoft.com/powershell:6.0.2-nanoserver

COPY --from=base ["tools", "tools"]

USER ContainerAdministrator

RUN setx /M PATH %PATH%;c:\tools\python\;c:\tools\python\Scripts\;

COPY . /azure-cli

WORKDIR azure-cli

USER ContainerUser

RUN python -m pip install --upgrade pip
RUN pip install wheel

SHELL ["pwsh.exe", "-Command", "$ErrorActionPreference = 'Stop'; $ProgressPreference = 'SilentlyContinue';"]

RUN $folder = @(); \
foreach($i in Get-ChildItem 'src\\' -Exclude 'azure-cli-testsdk') \
{ \
    $folder += Join-Path 'src\\' $i.Name \
} \
$wheels = Join-Path $pwd 'wheels'; \
Write-Host 'Building python packages...'; \
foreach($f in $folder) \
{ \
    try { \
        Push-Location $f; \
        & python.exe setup.py bdist_wheel -d $wheels; \
    } \
    finally { \
        Pop-Location \
    } \
}\ 
Write-Host 'Installing python packages...'; \
Push-Location $wheels; \
$modules = (Get-ChildItem *.whl -Name); \
foreach($m in $modules) \
{ \
    & pip install --no-cache-dir $m; \
}\
Pop-Location; \
Write-Host 'Done'; 

WORKDIR /

CMD pwsh.exe
