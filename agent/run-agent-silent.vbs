' Launches the print agent silently — no console window on boot
Set WshShell = CreateObject("WScript.Shell")
scriptDir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
WshShell.Run "cmd /c """ & scriptDir & "\run-agent.bat""", 0, False
