param(
  [switch]$RunTests
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$VenvPath = Join-Path $Root ".venv"
if (-not (Test-Path $VenvPath)) {
  python -m venv $VenvPath
}

$Activate = Join-Path $VenvPath "Scripts\\Activate.ps1"
. $Activate

python -m pip install --upgrade pip
pip install -r requirements.txt

if (-not (Test-Path "config.yaml")) {
  Copy-Item "config.yaml.example" "config.yaml"
}

if ($RunTests) {
  python -m pytest
}

Write-Output "Installation complete. Run: python -m app.webapp"
