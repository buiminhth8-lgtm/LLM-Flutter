; Inno Setup scaffold for LLM-Studio.
; Build only after the portable directory has been verified on a clean Windows user profile.

[Setup]
AppName=LLM-Studio
AppVersion=1.0.0
DefaultDirName={localappdata}\Programs\LLM-Studio
DefaultGroupName=LLM-Studio
DisableProgramGroupPage=yes
OutputBaseFilename=LLM-Studio-Setup

[Files]
Source: "..\..\dist\LLM-Studio\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\LLM-Studio Web"; Filename: "{app}\scripts\start_web.ps1"

[UninstallDelete]
; User data is intentionally preserved by default.
