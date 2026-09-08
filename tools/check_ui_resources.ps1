$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$uiRoot = Join-Path $repoRoot "ui"
$pythonUiFile = Join-Path $repoRoot "sim-spr-lmr-simulator\Sim_LMR_interface.py"
$qrcFile = Join-Path $repoRoot "resources\icons.qrc"

[xml]$qrc = Get-Content -LiteralPath $qrcFile -Encoding UTF8
$available = New-Object 'System.Collections.Generic.HashSet[string]'

foreach ($node in $qrc.RCC.qresource.file) {
    if ($node -is [string]) {
        $alias = $node
    }
    elseif ($node.alias) {
        $alias = [string]$node.alias
    }
    else {
        $alias = [string]$node.InnerText
    }

    [void]$available.Add(":/icons/$alias")
}

$pattern = ':/icons/[^"<;\r\n]+?\.(?:png|jpg|jpeg|ico|svg)'
$referenced = New-Object 'System.Collections.Generic.HashSet[string]'

foreach ($file in Get-ChildItem -LiteralPath $uiRoot -Filter *.ui) {
    $content = Get-Content -LiteralPath $file.FullName -Raw -Encoding UTF8
    $decodedContent = [System.Net.WebUtility]::HtmlDecode($content)
    $matches = [regex]::Matches($decodedContent, $pattern)
    foreach ($match in $matches) {
        [void]$referenced.Add($match.Value.Trim())
    }
}

# Some resource paths are assigned directly in the generated Python interface
# and therefore do not occur in the .ui files.
if (Test-Path -LiteralPath $pythonUiFile) {
    $content = Get-Content -LiteralPath $pythonUiFile -Raw -Encoding UTF8
    $matches = [regex]::Matches($content, $pattern)
    foreach ($match in $matches) {
        [void]$referenced.Add($match.Value.Trim())
    }
}

$missing = $referenced | Where-Object { -not $available.Contains($_) } | Sort-Object

if ($missing) {
    Write-Host "Missing resource aliases:"
    $missing | ForEach-Object { Write-Host "  $_" }
    exit 1
}

Write-Host "All referenced UI resources are covered by $qrcFile"
