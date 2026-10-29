$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $repoRoot

$pythonExe = Join-Path $repoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

& $pythonExe -m pip install -r requirements.txt

& $pythonExe -m PyInstaller --noconsole --windowed --name "PythonChess" `
    --onedir --noconfirm `
    --add-data "assets;assets" `
    --add-data "data;data" `
    --add-binary "engines\stockfish-windows-x86-64-universal.exe;engines" `
    main.py

if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller failed with exit code $LASTEXITCODE."
}

Write-Host "Build complete. EXE is here: $repoRoot\dist\PythonChess\PythonChess.exe"
