$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

$releaseRoot = $env:SMOKE_TEST_RELEASE_ROOT
if (-not $releaseRoot) {
    $releaseRoot = Get-ChildItem -Path $projectRoot -Directory -Filter "Sinkronisasi-Excel-Tools-v*" |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1 -ExpandProperty FullName
}

if (-not $releaseRoot) {
    throw "Folder rilis tidak ditemukan. Jalankan package_release.ps1 terlebih dahulu."
}

$syncExe = Join-Path $releaseRoot "Sinkronisasi-Excel-Gambar.exe"
$converterExe = Join-Path $releaseRoot "Converter-HEIC-ke-JPG.exe"
$excelPath = Join-Path $projectRoot "Form RC Calon Pelanggan AM 2026 Prov. Malut (1).xlsx"
$testRoot = Join-Path $projectRoot "smoke_test_outputs"
$logPath = Join-Path $testRoot "smoke_test.log"
$summaryPath = Join-Path $testRoot "smoke_test_summary.json"
$syncOutput = Join-Path $testRoot "sinkronisasi_release_all.xlsx"
$syncReport = Join-Path $testRoot "sinkronisasi_release_all.json"
$converterOutput = Join-Path $testRoot "converter_release"
$converterReport = Join-Path $converterOutput "report_release.json"
$syncTimeoutSec = 180
$converterTimeoutSec = 600

function Stop-TestProcesses {
    Get-Process |
        Where-Object {
            $_.Path -like "*Sinkronisasi-Excel-Gambar.exe" -or
            $_.Path -like "*importos.exe" -or
            $_.Path -like "*Converter-HEIC-ke-JPG.exe" -or
            $_.Path -like "*heic_converter_app.exe"
        } |
        Stop-Process -Force -ErrorAction SilentlyContinue
}

function Write-LogLine {
    param(
        [string]$Message
    )

    if ($null -eq $Message) {
        $Message = ""
    }

    $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
    Write-Host $Message
    Add-Content -Path $logPath -Value $line
}

function Wait-ForAutomationReport {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ReportPath,

        [Parameter(Mandatory = $true)]
        [string]$Label,

        [int]$TimeoutSec = 180
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        if (Test-Path $ReportPath) {
            return
        }

        Start-Sleep -Milliseconds 500
    }

    throw "Timeout menunggu report ${Label}: $ReportPath"
}

if (-not (Test-Path $syncExe)) {
    throw "File tidak ditemukan: $syncExe"
}

if (-not (Test-Path $converterExe)) {
    throw "File tidak ditemukan: $converterExe"
}

if (-not (Test-Path $excelPath)) {
    throw "File Excel tidak ditemukan: $excelPath"
}

Stop-TestProcesses

if (Test-Path $testRoot) {
    Remove-Item $testRoot -Recurse -Force
}

New-Item -ItemType Directory -Force -Path $testRoot | Out-Null
New-Item -ItemType Directory -Force -Path $converterOutput | Out-Null
Set-Content -Path $logPath -Value ""
$summary = [ordered]@{
    release_root = $releaseRoot
    sync = $null
    converter = $null
}

Write-LogLine "Menjalankan smoke test Sinkronisasi-Excel-Gambar.exe..."
$env:SYNC_APP_AUTOMATION = "1"
$env:SYNC_APP_AUTOMATION_EXCEL = $excelPath
$env:SYNC_APP_AUTOMATION_MODE = "all"
$env:SYNC_APP_AUTOMATION_USE_DEFAULT_FOLDERS = "1"
$env:SYNC_APP_AUTOMATION_OUTPUT = $syncOutput
$env:SYNC_APP_AUTOMATION_REPORT = $syncReport
$env:SYNC_APP_AUTOMATION_CLOSE = "1"

$syncProcess = Start-Process -FilePath $syncExe -PassThru
Wait-ForAutomationReport -ReportPath $syncReport -Label "sinkronisasi" -TimeoutSec $syncTimeoutSec

if (-not (Test-Path $syncReport)) {
    throw "Report sinkronisasi tidak terbentuk: $syncReport"
}

$syncResult = Get-Content $syncReport -Raw | ConvertFrom-Json
Stop-TestProcesses
$summary.sync = [ordered]@{
    status = $syncResult.status
    processed_sheets = $syncResult.processed_sheets
    total_matches = $syncResult.total_matches
    mismatch_count = $syncResult.mismatch_count
    output_workbook = $syncResult.last_saved_path
}
Write-LogLine "Sinkronisasi selesai:"
Write-LogLine "  Status          : $($syncResult.status)"
Write-LogLine "  Sheet valid      : $($syncResult.processed_sheets)"
Write-LogLine "  Total match      : $($syncResult.total_matches)"
Write-LogLine "  Mismatch         : $($syncResult.mismatch_count)"
Write-LogLine "  Output workbook  : $($syncResult.last_saved_path)"

Write-LogLine ""
Write-LogLine "Menjalankan smoke test Converter-HEIC-ke-JPG.exe..."
$env:HEIC_CONVERTER_AUTOMATION = "1"
$env:HEIC_CONVERTER_AUTOMATION_USE_DEFAULT_FOLDERS = "1"
$env:HEIC_CONVERTER_AUTOMATION_OUTPUT = $converterOutput
$env:HEIC_CONVERTER_AUTOMATION_REPORT = $converterReport
$env:HEIC_CONVERTER_AUTOMATION_CLOSE = "1"

$converterProcess = Start-Process -FilePath $converterExe -PassThru
Wait-ForAutomationReport -ReportPath $converterReport -Label "converter" -TimeoutSec $converterTimeoutSec

if (-not (Test-Path $converterReport)) {
    throw "Report converter tidak terbentuk: $converterReport"
}

$converterResult = Get-Content $converterReport -Raw | ConvertFrom-Json
$convertedFiles = Get-ChildItem $converterOutput -Filter *.jpg -Recurse | Measure-Object | Select-Object -ExpandProperty Count
Stop-TestProcesses
$summary.converter = [ordered]@{
    status = $converterResult.status
    total_candidates = $converterResult.total_candidates
    converted_count = $converterResult.converted_count
    actual_jpg_count = $convertedFiles
    output_dir = $converterResult.output_dir
}
Write-LogLine "Converter selesai:"
Write-LogLine "  Status          : $($converterResult.status)"
Write-LogLine "  Kandidat         : $($converterResult.total_candidates)"
Write-LogLine "  Converted        : $($converterResult.converted_count)"
Write-LogLine "  File JPG aktual  : $convertedFiles"
Write-LogLine "  Output folder    : $($converterResult.output_dir)"

Set-Content -Path $summaryPath -Value ($summary | ConvertTo-Json -Depth 5)
Write-LogLine ""
Write-LogLine "Smoke test release selesai."
Write-LogLine "Folder hasil: $testRoot"
Write-LogLine "Summary JSON: $summaryPath"
