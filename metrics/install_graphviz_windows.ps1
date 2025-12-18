Param(
    [switch]$UseWinget,
    [switch]$UseChocolatey,
    [switch]$UseScoop
)

$ErrorActionPreference = 'Stop'

function Test-Cmd($name) {
    return [bool](Get-Command $name -ErrorAction SilentlyContinue)
}

Write-Host "[metrics] Attempting to install Graphviz (dot)..."

if (-not $UseWinget -and -not $UseChocolatey -and -not $UseScoop) {
    if (Test-Cmd winget) { $UseWinget = $true }
    elseif (Test-Cmd choco) { $UseChocolatey = $true }
    elseif (Test-Cmd scoop) { $UseScoop = $true }
}

if ($UseWinget) {
    if (-not (Test-Cmd winget)) { throw "winget not found" }
    Write-Host "[metrics] Using winget..."
    try {
        winget install -e --id Graphviz.Graphviz
    }
    catch {
        Write-Host "[metrics] winget install by id failed; trying by name..." -ForegroundColor Yellow
        winget install -e --name graphviz
    }
}
elseif ($UseChocolatey) {
    if (-not (Test-Cmd choco)) { throw "choco not found" }
    Write-Host "[metrics] Using Chocolatey..."
    choco install graphviz -y
}
elseif ($UseScoop) {
    if (-not (Test-Cmd scoop)) { throw "scoop not found" }
    Write-Host "[metrics] Using scoop..."
    scoop install graphviz
}
else {
    Write-Host "[metrics] No package manager detected (winget/choco/scoop)." -ForegroundColor Yellow
    Write-Host "[metrics] Install Graphviz manually and ensure 'dot' is on PATH." -ForegroundColor Yellow
}

Write-Host "[metrics] Verifying dot..."
if (Test-Cmd dot) {
    dot -V
    Write-Host "[metrics] OK: dot is available on PATH." -ForegroundColor Green
    exit 0
}

# winget installs may not update PATH; detect package location.
$pkgRoot = Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Packages'
if (Test-Path $pkgRoot) {
    $pkg = Get-ChildItem $pkgRoot -Directory -ErrorAction SilentlyContinue | Where-Object Name -match 'Graphviz\.Graphviz' | Select-Object -First 1
    if ($pkg) {
        $dot = Get-ChildItem -Recurse $pkg.FullName -Filter 'dot.exe' -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($dot) {
            Write-Host "[metrics] Graphviz is installed but dot is not on PATH." -ForegroundColor Yellow
            Write-Host "[metrics] Found: $($dot.FullName)" -ForegroundColor Yellow
            Write-Host "[metrics] NOTE: metrics/run_metrics.py can still use this automatically." -ForegroundColor Yellow
            exit 0
        }
    }
}

Write-Host "[metrics] dot not found." -ForegroundColor Yellow
exit 1
