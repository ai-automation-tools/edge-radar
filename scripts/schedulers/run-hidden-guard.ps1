# run-hidden-guard.ps1 -- kill a hidden task's command if Task Scheduler stops the task.
#
# Started hidden by run-hidden.vbs just before it runs the task's real command.
# Its PARENT is therefore that wscript.exe, which is the only process Task Scheduler
# knows about. A task stop -- including the task's own ExecutionTimeLimit -- kills
# wscript.exe and nothing else, so without this the command wscript was waiting on
# keeps running (reproduced 2026-09-23; consolidation audit #17).
#
# While wscript is alive this remembers wscript's children (each PID with its creation
# time). When wscript goes, any remembered child STILL running is killed with its whole
# tree. After a normal finish the child has already exited, so nothing is killed. A
# detached service a script started and left behind is never touched either: only
# wscript's own direct children, and whatever is still under them, are killed.
# Creation times are checked, so a reused PID can never be hit.
#
# Launched with window style 0, it never shows a window. Copies of this file sit next
# to each waiting run-hidden.vbs (routines\bin, Edge-Radar scripts\schedulers,
# Edge-Radar-Agy scripts\automation); keep them identical.

$ErrorActionPreference = 'SilentlyContinue'
$me = Get-CimInstance Win32_Process -Filter "ProcessId=$PID"
$parentId = [int]$me.ParentProcessId
$parent = Get-CimInstance Win32_Process -Filter "ProcessId=$parentId"
if (-not $parent -or $parent.Name -ne 'wscript.exe') { exit 0 }
$parentBorn = $parent.CreationDate
$known = @{}

while ($true) {
    $p = Get-CimInstance Win32_Process -Filter "ProcessId=$parentId"
    if ($p -and $p.CreationDate -eq $parentBorn) {
        foreach ($c in @(Get-CimInstance Win32_Process -Filter "ParentProcessId=$parentId")) {
            if ($c.ProcessId -ne $PID -and $c.CreationDate -ge $parentBorn) { $known[[int]$c.ProcessId] = $c.CreationDate }
        }
        Start-Sleep -Seconds 5
        continue
    }
    foreach ($id in @($known.Keys)) {
        $c = Get-CimInstance Win32_Process -Filter "ProcessId=$id"
        if ($c -and $c.CreationDate -eq $known[$id]) { & taskkill.exe /PID $id /T /F *> $null }
    }
    exit 0
}
