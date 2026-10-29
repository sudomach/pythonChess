$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $repoRoot

& (Join-Path $repoRoot "build_exe.ps1")
if ($LASTEXITCODE -ne 0) {
    throw "The executable build failed with exit code $LASTEXITCODE."
}

$compilerCandidates = @(
    (Join-Path ${env:ProgramFiles(x86)} "Inno Setup 6\ISCC.exe"),
    (Join-Path $env:ProgramFiles "Inno Setup 6\ISCC.exe"),
    (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe")
)
$compilerCommand = Get-Command ISCC.exe -ErrorAction SilentlyContinue
$compiler = if ($compilerCommand) { $compilerCommand.Source } else {
    $compilerCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
}

if (-not $compiler) {
    throw "Inno Setup 6 was not found. Install it from https://jrsoftware.org/isinfo.php, then run this script again."
}

& $compiler (Join-Path $repoRoot "PythonChess.iss")
if ($LASTEXITCODE -ne 0) {
    throw "Inno Setup failed with exit code $LASTEXITCODE."
}

Write-Host "Installer created: $repoRoot\installer\PythonChessSetup.exe"
