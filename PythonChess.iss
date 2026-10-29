#define AppName "Python Chess"
#define AppVersion "1.0.0"
#define AppPublisher "Python Chess"

[Setup]
AppId={{E17867E0-A035-4B24-BCA7-80B121169D94}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\PythonChess
DefaultGroupName={#AppName}
UninstallDisplayIcon={app}\PythonChess.exe
OutputDir=installer
OutputBaseFilename=PythonChessSetup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "dist\PythonChess\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Python Chess"; Filename: "{app}\PythonChess.exe"
Name: "{autodesktop}\Python Chess"; Filename: "{app}\PythonChess.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\PythonChess.exe"; Description: "Launch Python Chess"; Flags: nowait postinstall skipifsilent
