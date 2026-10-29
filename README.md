# Python Chess

A desktop chess game built with Python, Pygame, and `python-chess`. Play locally
with two players or challenge the Stockfish computer opponent.

## Features

- Local two-player chess and play against Stockfish
- Four computer difficulty settings
- Optional game clocks
- Player profiles with saved settings, match history, and statistics
- Move undo, sound controls, and a chess rules help screen
- Windows installer with a Start Menu shortcut and an optional desktop shortcut

Profiles are stored locally on the computer; they are not online accounts and
are not synchronized between devices.

## Install on Windows

Run `installer\PythonChessSetup.exe` and follow the setup prompts. The installer
can create an optional desktop shortcut. After installation, launch **Python
Chess** from the Windows Start Menu.

The installer is built for 64-bit Windows. It includes the game, its assets,
and the bundled Stockfish engine.

## Run from source

You need Python 3.10 or later and Windows to use the included Stockfish binary.
From PowerShell in the project directory:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

`requirements.txt` includes the application dependencies as well as PyInstaller
and pytest, which are used to build and test the project.

## Build the Windows application

The build scripts use the existing `.venv` if available, or `python` from your
PATH otherwise.

To build the application bundle:

```powershell
.\build_exe.ps1
```

The executable and its supporting files are written to
`dist\PythonChess\`. This is a folder-based application bundle; keep the
supporting files alongside `PythonChess.exe`.

To create the installer, first install [Inno Setup 6](https://jrsoftware.org/isinfo.php), then run:

```powershell
.\build_installer.ps1
```

The installer is written to `installer\PythonChessSetup.exe`. The scripts expect
the Stockfish Windows executable at
`engines\stockfish-windows-x86-64-universal.exe`. The `engines\` folder is
excluded from version control, so provide that file before building. Get
Stockfish from its [official download page](https://stockfishchess.org/download/).

## Run the tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## Saved data and assets

- On Windows, player profiles are saved to `%APPDATA%\PythonChess\players.json`.
- The chess piece images are in `assets\pieces\vector-chess-pieces\`; their
  included `License.txt` identifies them as CC0.
- Sound effects are in `assets\sound\`.
- The Stockfish engine is a separate executable bundled with Windows builds.
