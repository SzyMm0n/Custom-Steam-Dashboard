Param(
    [switch]$UseWinget,
    [switch]$UseChocolatey,
    [switch]$UseScoop
)

$ErrorActionPreference = 'Stop'

function Test-Cmd($name) {
    return [bool](Get-Command $name -ErrorAction SilentlyContinue)
}

Write-Host "[metrics] Attempting to install 'cloc'..."

if (-not $UseWinget -and -not $UseChocolatey -and -not $UseScoop) {
    # Auto-pick first available
    if (Test-Cmd winget) { $UseWinget = $true }
    elseif (Test-Cmd choco) { $UseChocolatey = $true }
    elseif (Test-Cmd scoop) { $UseScoop = $true }
}

if ($UseWinget) {
    if (-not (Test-Cmd winget)) { throw "winget not found" }
    Write-Host "[metrics] Using winget..."
    try {
        winget install -e --id AlDanial.Cloc
    }
    catch {
        Write-Host "[metrics] winget install by id failed; trying by name..." -ForegroundColor Yellow
        winget install -e --name cloc
    }
}
elseif ($UseChocolatey) {
    if (-not (Test-Cmd choco)) { throw "choco not found" }
    Write-Host "[metrics] Using Chocolatey..."
    choco install cloc -y
}
elseif ($UseScoop) {
    if (-not (Test-Cmd scoop)) { throw "scoop not found" }
    Write-Host "[metrics] Using scoop..."
    scoop install cloc
}
else {
    Write-Host "[metrics] No package manager detected (winget/choco/scoop)." -ForegroundColor Yellow
    Write-Host "[metrics] Install cloc manually and ensure 'cloc' is on PATH." -ForegroundColor Yellow
    Write-Host "[metrics] After install run: cloc --version" -ForegroundColor Yellow
}

Write-Host "[metrics] Verifying cloc..."
if (Test-Cmd cloc) {
    cloc --version
    Write-Host "[metrics] OK: cloc is available on PATH." -ForegroundColor Green
    exit 0
}

# winget installs may not update PATH; detect package location.
$pkgRoot = Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Packages'
if (Test-Path $pkgRoot) {
    $pkg = Get-ChildItem $pkgRoot -Directory -ErrorAction SilentlyContinue | Where-Object Name -match 'AlDanial\.Cloc' | Select-Object -First 1
    if ($pkg) {
        $exe = Join-Path $pkg.FullName 'cloc.exe'
        if (Test-Path $exe) {
            Write-Host "[metrics] cloc is installed but not on PATH." -ForegroundColor Yellow
            Write-Host "[metrics] Found: $exe" -ForegroundColor Yellow
            Write-Host "[metrics] NOTE: metrics/run_metrics.py can still use this automatically." -ForegroundColor Yellow
            exit 0
        }
    }
}

Write-Host "[metrics] cloc not found." -ForegroundColor Yellow
exit 1
