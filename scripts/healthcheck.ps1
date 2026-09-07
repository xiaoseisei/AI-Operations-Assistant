[CmdletBinding()]
param(
    [switch]$RequireDocker
)

$ErrorActionPreference = 'Stop'
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$fixturePath = Join-Path $scriptRoot 'healthcheck-fixture.json'

function Get-ToolVersion([string]$Command, [string[]]$Arguments) {
    $tool = Get-Command $Command -ErrorAction SilentlyContinue
    if (-not $tool) { return $null }
    try { return (& $tool.Source @Arguments 2>&1 | Out-String).Trim() } catch { return $null }
}

$pythonCommand = 'python'
$pythonVersion = Get-ToolVersion $pythonCommand @('--version')
if (-not $pythonVersion -or $pythonVersion -notmatch 'Python 3\.12\.') {
    $launcher = Get-Command 'py' -ErrorAction SilentlyContinue
    if ($launcher) {
        $pythonCommand = 'py'
        $pythonVersion = Get-ToolVersion $pythonCommand @('-3.12', '--version')
    }
}
if (-not $pythonVersion -or $pythonVersion -notmatch 'Python 3\.12\.') {
    throw 'Python 3.12.x is required. Install it before running the health check.'
}

$uvCommand = 'uv'
$uvVersion = Get-ToolVersion $uvCommand @('--version')
if (-not $uvVersion) {
    $userUv = Join-Path $env:USERPROFILE '.local\bin\uv.exe'
    if (Test-Path -LiteralPath $userUv) {
        $uvCommand = $userUv
        $uvVersion = Get-ToolVersion $uvCommand @('--version')
    }
}
if (-not $uvVersion) {
    throw 'uv is required. Install uv before running the health check.'
}

if (-not (Test-Path -LiteralPath $fixturePath)) { throw "Missing fixture: $fixturePath" }
$fixture = Get-Content -Raw -LiteralPath $fixturePath | ConvertFrom-Json
if ($fixture.mode -ne 'offline' -or $fixture.database -ne 'sqlite' -or $fixture.adapter -ne 'mock') {
    throw 'Health fixture must define offline + sqlite + mock.'
}

Write-Output "PASS python=$pythonVersion command=$pythonCommand"
Write-Output "PASS uv=$uvVersion"

$nodeCommand = 'node'
$localNode = Join-Path $scriptRoot '..\.runtime\tools\node20\node.exe'
if (Test-Path -LiteralPath $localNode) { $nodeCommand = $localNode }
$nodeVersion = Get-ToolVersion $nodeCommand @('--version')
if ($nodeVersion -and $nodeVersion -match '^v20\.') { Write-Output "PASS node=$nodeVersion" }
else { Write-Warning 'Node.js 20 LTS is not available; continuing in offline mode.' }

$dockerVersion = Get-ToolVersion 'docker' @('--version')
$composeVersion = if ($dockerVersion) { Get-ToolVersion 'docker' @('compose', 'version') } else { $null }
$dockerReady = $dockerVersion -and $composeVersion
if ($dockerReady) { Write-Output "PASS docker=$dockerVersion"; Write-Output "PASS compose=$composeVersion" }
else {
    if ($RequireDocker) { throw 'Docker Engine 24+ and Docker Compose v2 are required in strict mode.' }
    Write-Warning 'Docker/Compose is not available; continuing with SQLite + Mock offline mode.'
}

Write-Output 'HEALTHCHECK_PASS mode=offline database=sqlite adapter=mock'
