' Local Lab - AI Voice Generator
' This launches the app without showing command window

Set WshShell = CreateObject("WScript.Shell")
WshShell.Run chr(34) & CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName) & "\START_HERE.bat" & chr(34), 0
Set WshShell = Nothing
