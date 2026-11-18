' Launch a scheduler batch file with no console window; preserve its exit code.
' Task Scheduler runs .bat files through a visible cmd.exe under an interactive
' token, which flashes a window at the user on every run -- CLV-Capture fires
' every 5 minutes, so that is 288 flashes a day. Point the task at:
'   wscript.exe "<this file>" "<full path to the .bat>" [args...]
Option Explicit
Dim shell, cmd, i, rc
If WScript.Arguments.Count = 0 Then WScript.Quit(2)
Set shell = CreateObject("WScript.Shell")
' Guard: run-hidden-guard.ps1 in this folder kills the command's process tree if Task
' Scheduler stops this wscript (a stop, time limit included, never reaches the child
' otherwise -- 2026-09-23 consolidation audit #17). Skipped if the file is missing.
Dim fso, guard
Set fso = CreateObject("Scripting.FileSystemObject")
guard = fso.BuildPath(fso.GetParentFolderName(WScript.ScriptFullName), "run-hidden-guard.ps1")
If fso.FileExists(guard) Then shell.Run "powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File " & Chr(34) & guard & Chr(34), 0, False
cmd = Chr(34) & WScript.Arguments(0) & Chr(34)
For i = 1 To WScript.Arguments.Count - 1
  cmd = cmd & " " & Chr(34) & WScript.Arguments(i) & Chr(34)
Next
rc = shell.Run(cmd, 0, True)
WScript.Quit(rc)
