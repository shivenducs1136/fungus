<#
.SYNOPSIS
    Builds fungus-mcp.exe - a self-contained MCP server executable.
.EXAMPLE
    .\build\build_exe.ps1
    .\build\build_exe.ps1 -Clean
#>
param([switch]$Clean)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path $PSScriptRoot -Parent

Push-Location $RepoRoot
try {
    $venvActivate = Join-Path $RepoRoot ".venv\Scripts\Activate.ps1"
    if (Test-Path $venvActivate) {
        Write-Host "Activating venv..." -ForegroundColor Cyan
        & $venvActivate
    }

    if ($Clean) {
        Write-Host "Cleaning previous build artifacts..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force -ErrorAction SilentlyContinue dist, build\__pycache__
    }

    $pyinstaller = Get-Command pyinstaller -ErrorAction SilentlyContinue
    if (-not $pyinstaller) {
        Write-Host "PyInstaller not found - installing..." -ForegroundColor Yellow
        pip install pyinstaller --quiet
    }

    Write-Host "Building fungus-mcp.exe..." -ForegroundColor Cyan
    pyinstaller build\fungus_mcp.spec --noconfirm

    $exe = Join-Path $RepoRoot "dist\fungus-mcp.exe"
    if (Test-Path $exe) {
        $size = [math]::Round((Get-Item $exe).Length / 1MB, 1)
        Write-Host "Build succeeded: dist\fungus-mcp.exe ($($size) MB)" -ForegroundColor Green
        Write-Host ""
        Write-Host "Ship to users:" -ForegroundColor Green
        Write-Host "  dist\fungus-mcp.exe" -ForegroundColor White
        Write-Host "  build\mcp_distribution.json (rename to mcp.json)" -ForegroundColor White
    } else {
        Write-Error "Build failed - exe not found."
    }
} finally {
    Pop-Location
}
