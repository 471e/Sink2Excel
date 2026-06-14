$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

. (Join-Path $projectRoot "release_config.ps1")

$distRoot = Join-Path $projectRoot "dist_apps"
$releaseRoot = Join-Path $projectRoot $releaseName
$zipPath = Join-Path $projectRoot "$releaseName.zip"
$syncAppTargetName = "Sinkronisasi-Excel-Gambar.exe"
$converterTargetName = "Converter-HEIC-ke-JPG.exe"

if (-not (Test-Path (Join-Path $distRoot "importos.exe"))) {
    throw "File importos.exe belum ada di dist_apps."
}

if (-not (Test-Path (Join-Path $distRoot "heic_converter_app.exe"))) {
    throw "File heic_converter_app.exe belum ada di dist_apps."
}

if (Test-Path $releaseRoot) {
    Remove-Item $releaseRoot -Recurse -Force
}

if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}

New-Item -ItemType Directory -Force -Path $releaseRoot | Out-Null

Copy-Item (Join-Path $distRoot "importos.exe") (Join-Path $releaseRoot $syncAppTargetName)
Copy-Item (Join-Path $distRoot "heic_converter_app.exe") (Join-Path $releaseRoot $converterTargetName)
Copy-Item (Join-Path $projectRoot "PANDUAN-EXE.txt") $releaseRoot
Copy-Item (Join-Path $projectRoot "README.md") $releaseRoot

Compress-Archive -Path (Join-Path $releaseRoot "*") -DestinationPath $zipPath

Write-Host "Paket rilis selesai dibuat."
Write-Host "Versi  : $releaseVersion"
Write-Host "Folder : $releaseRoot"
Write-Host "Zip    : $zipPath"
