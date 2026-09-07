[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..')
$output = Join-Path $repoRoot 'sbom\cyclonedx-python.json'
New-Item -ItemType Directory -Force (Split-Path -Parent $output) | Out-Null

$uv = Get-Command uv -ErrorAction SilentlyContinue
if (-not $uv) {
    $candidate = Join-Path $env:USERPROFILE '.local\bin\uv.exe'
    if (Test-Path -LiteralPath $candidate) { $uv = Get-Command $candidate }
}
if (-not $uv) { throw 'uv is required to generate the SBOM.' }

Push-Location $repoRoot
try {
    & $uv.Source run --locked --with cyclonedx-bom cyclonedx-py environment --pyproject pyproject.toml --output-reproducible --output-format JSON --output-file $output .venv
    if ($LASTEXITCODE -ne 0) { throw 'CycloneDX SBOM generation failed.' }
}
finally { Pop-Location }

if (-not (Test-Path -LiteralPath $output)) { throw "SBOM was not created: $output" }
if ((Get-Item -LiteralPath $output).Length -eq 0) { throw 'SBOM output is empty.' }
Write-Output "SBOM_GENERATED $output"
