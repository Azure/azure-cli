if (Test-Path "$PSScriptRoot\..\python.exe") {
  $env:AZ_INSTALLER="ZIP"
  & "$PSScriptRoot\..\python.exe" -IBm azure.cli @args
  exit $LASTEXITCODE
} else {
  Write-Error "Failed to load python executable."
  exit 1
}
