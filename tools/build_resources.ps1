$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$inputFile = Join-Path $repoRoot "resources\icons.qrc"
$outputFile = Join-Path $repoRoot "sim-spr-lmr-simulator\icons_.py"

if (Get-Command pyrcc5 -ErrorAction SilentlyContinue) {
    & pyrcc5 $inputFile -o $outputFile
}
else {
    & python -m PyQt5.pyrcc_main $inputFile -o $outputFile
}

if ($LASTEXITCODE -ne 0) {
    throw "Resource compilation failed with exit code $LASTEXITCODE"
}

Write-Host "Generated $outputFile"
