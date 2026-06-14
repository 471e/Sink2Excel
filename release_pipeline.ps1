$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

$logPath = Join-Path $projectRoot "release_pipeline.log"

function Write-Step {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Message
    )

    $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
    Write-Host $line
}

function Assert-PathExists {
    param(
        [Parameter(Mandatory = $true)]
        [string]$PathValue,

        [Parameter(Mandatory = $true)]
        [string]$Label
    )

    if (-not (Test-Path $PathValue)) {
        throw "$Label tidak ditemukan: $PathValue"
    }
}

try {
    Start-Transcript -Path $logPath -Force | Out-Null

    Write-Step "Memulai pipeline rilis v1.0.1"

    Write-Step "Menjalankan build_apps.ps1"
    & (Join-Path $projectRoot "build_apps.ps1")

    Write-Step "Menjalankan package_release.ps1"
    & (Join-Path $projectRoot "package_release.ps1")

    Write-Step "Menjalankan smoke_test_release.ps1"
    & (Join-Path $projectRoot "smoke_test_release.ps1")

    $distRoot = Join-Path $projectRoot "dist_apps"
    $releaseRoot = Join-Path $projectRoot "Sinkronisasi-Excel-Tools-v1.0.1"
    $zipPath = Join-Path $projectRoot "Sinkronisasi-Excel-Tools-v1.0.1.zip"
    $summaryPath = Join-Path $projectRoot "smoke_test_outputs\smoke_test_summary.json"

    Assert-PathExists -PathValue (Join-Path $distRoot "importos.exe") -Label "Executable sinkronisasi"
    Assert-PathExists -PathValue (Join-Path $distRoot "heic_converter_app.exe") -Label "Executable converter"
    Assert-PathExists -PathValue $releaseRoot -Label "Folder rilis"
    Assert-PathExists -PathValue $zipPath -Label "Zip rilis"
    Assert-PathExists -PathValue $summaryPath -Label "Ringkasan smoke test"

    Write-Step "Pipeline selesai dengan sukses"
    Write-Step "Folder rilis : $releaseRoot"
    Write-Step "Zip rilis    : $zipPath"
    Write-Step "Smoke summary: $summaryPath"
}
catch {
    Write-Error $_
    exit 1
}
finally {
    try {
        Stop-Transcript | Out-Null
    }
    catch {
    }
}
