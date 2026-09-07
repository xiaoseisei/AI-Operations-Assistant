[CmdletBinding()]
param(
    [string]$Destination = ''
)

$ErrorActionPreference = 'Stop'
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..')
if (-not $Destination) { $Destination = Join-Path $repoRoot '.runtime\tools\node20' }
$version = '20.20.2'
$archiveName = "node-v$version-win-x64.zip"
$baseUrl = "https://nodejs.org/dist/v$version"
$archive = Join-Path $env:TEMP $archiveName
$expectedHash = 'DC3700FDD57A63EEDB8FD7E3C7BAAA32E6A740A1B904167FF4204BC68ED8BF77'

Invoke-WebRequest -Uri "$baseUrl/$archiveName" -OutFile $archive -TimeoutSec 120
$actualHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $archive).Hash
if ($actualHash -ne $expectedHash) {
    Remove-Item -LiteralPath $archive -Force -ErrorAction SilentlyContinue
    throw "Node.js archive SHA-256 mismatch: $actualHash"
}

$parent = Split-Path -Parent $Destination
$expanded = Join-Path $parent "node-v$version-win-x64"
New-Item -ItemType Directory -Force -Path $parent | Out-Null
if (Test-Path -LiteralPath $expanded) { Remove-Item -LiteralPath $expanded -Recurse -Force }
if (Test-Path -LiteralPath $Destination) { Remove-Item -LiteralPath $Destination -Recurse -Force }
Expand-Archive -LiteralPath $archive -DestinationPath $parent -Force
Move-Item -LiteralPath $expanded -Destination $Destination
Remove-Item -LiteralPath $archive -Force

$node = Join-Path $Destination 'node.exe'
if (-not (Test-Path -LiteralPath $node)) { throw "Node.js executable missing: $node" }
& $node --version
Write-Output "NODE20_READY $Destination"
