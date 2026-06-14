$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

$distRoot = Join-Path $projectRoot "dist_apps"
$buildRoot = Join-Path $projectRoot "build_apps"
$specRoot = Join-Path $projectRoot "build_specs"
$importosWork = Join-Path $buildRoot "importos"
$heicWork = Join-Path $buildRoot "heic_converter_app"

if (Test-Path $distRoot) {
    Remove-Item $distRoot -Recurse -Force
}

if (Test-Path $buildRoot) {
    Remove-Item $buildRoot -Recurse -Force
}

if (Test-Path $specRoot) {
    Remove-Item $specRoot -Recurse -Force
}

New-Item -ItemType Directory -Force -Path $distRoot | Out-Null
New-Item -ItemType Directory -Force -Path $buildRoot | Out-Null
New-Item -ItemType Directory -Force -Path $specRoot | Out-Null
New-Item -ItemType Directory -Force -Path $importosWork | Out-Null
New-Item -ItemType Directory -Force -Path $heicWork | Out-Null

Write-Host "Build importos.exe..."
pyinstaller `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name importos `
    --distpath $distRoot `
    --workpath $importosWork `
    --specpath $specRoot `
    importos.py

Write-Host "Build heic_converter_app.exe..."
Start-Sleep -Seconds 2
pyinstaller `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name heic_converter_app `
    --distpath $distRoot `
    --workpath $heicWork `
    --specpath $specRoot `
    --hidden-import pillow_heif `
    --collect-all pillow_heif `
    heic_converter_app.py

Write-Host ""
Write-Host "Build selesai."
Write-Host "Output:"
Get-ChildItem $distRoot | Select-Object Name, Length, LastWriteTime
