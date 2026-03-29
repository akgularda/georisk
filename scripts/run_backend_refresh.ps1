$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$pythonExe = @(
    (Get-Command python -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue),
    "C:\Python314\python.exe"
) | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1

if (-not $pythonExe) {
    throw "Python executable not found."
}

$arguments = @("scripts/run_backend_refresh.py", "--python-executable", $pythonExe) + $args
& $pythonExe @arguments
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
