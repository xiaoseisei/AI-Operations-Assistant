[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$root = Resolve-Path (Join-Path $PSScriptRoot '..')
docker compose -f (Join-Path $root 'compose.yaml') -f (Join-Path $root 'compose.dev.yaml') config *> $null
if ($LASTEXITCODE -ne 0) { throw 'Docker Compose configuration is invalid.' }
Write-Output 'INFRA_CHECK_PASS compose_config=valid'
