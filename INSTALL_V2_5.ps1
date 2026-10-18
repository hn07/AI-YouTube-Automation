# V2.5 safe installer for an existing Windows project.
# Copies only the new V2.5 files. It does not delete or replace existing files.
$ErrorActionPreference = "Stop"
$Project = "D:\MyWorkSpace\AI_YouTube_Automation_V1_1"
$Branch = "feature/v2.5-one-click-auto-production"
$Base = "https://raw.githubusercontent.com/hn07/AI-YouTube-Automation/$Branch"
$Files = @(
  @{ Remote = "src/one_click_production_v2_5.py"; Local = "src\one_click_production_v2_5.py" },
  @{ Remote = "RUN_V2_5_ONE_CLICK.bat"; Local = "RUN_V2_5_ONE_CLICK.bat" },
  @{ Remote = "TEST_V2_5.bat"; Local = "TEST_V2_5.bat" },
  @{ Remote = "V2_5_GUIDE.md"; Local = "V2_5_GUIDE.md" }
)

if (-not (Test-Path -LiteralPath $Project -PathType Container)) {
  throw "Project folder not found: $Project. No files were changed."
}

$Missing = @()
foreach ($Item in $Files) {
  $Destination = Join-Path $Project $Item.Local
  if (Test-Path -LiteralPath $Destination) {
    throw "Destination already exists; refusing to overwrite: $Destination. No files were changed. Rename/back up that file and rerun only if you intend to replace it."
  }
  $Missing += $Item
}

$Temp = Join-Path $env:TEMP ("AIYT_V25_" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $Temp | Out-Null
try {
  foreach ($Item in $Files) {
    $Download = Join-Path $Temp ($Item.Remote -replace "/", "_")
    $Uri = "$Base/$($Item.Remote)"
    Invoke-WebRequest -Uri $Uri -OutFile $Download
    if ((Get-Item -LiteralPath $Download).Length -lt 20) {
      throw "Downloaded file appears empty: $Uri"
    }
    $Item | Add-Member -NotePropertyName TempPath -NotePropertyValue $Download
  }

  # All downloads succeeded before the first project file is written.
  foreach ($Item in $Files) {
    $Destination = Join-Path $Project $Item.Local
    $Parent = Split-Path -Parent $Destination
    New-Item -ItemType Directory -Force -Path $Parent | Out-Null
    Copy-Item -LiteralPath $Item.TempPath -Destination $Destination
    Write-Host "Installed: $Destination"
  }
}
finally {
  if (Test-Path -LiteralPath $Temp) {
    Remove-Item -LiteralPath $Temp -Recurse -Force
  }
}

Write-Host ""
Write-Host "V2.5 files copied. Existing project data/output files were not intentionally changed."
Write-Host "Next: run TEST_V2_5.bat, then RUN_V2_5_ONE_CLICK.bat."
Write-Host "Note: this preview does not auto-verify claims or simulate human approval."
