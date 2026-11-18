#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Recreate the .claude/skills junctions that point at the canonical /skills source.

.DESCRIPTION
    The Edge-Radar Claude Code skills live once, under /skills at the repo root
    (every folder there with a SKILL.md is linked; there is no list to keep). Claude Code only discovers skills under
    .claude/skills/, so each is wired up as a Windows directory *junction*
    pointing back to /skills.

    Real symlinks can't be committed here (git core.symlinks=false on Windows),
    so the junctions are git-ignored and the content is tracked exactly once under
    /skills. That means a fresh clone has no junctions yet — run this script once
    after cloning (or after deleting/recreating the skill dirs) to wire them up.

    Idempotent: a junction that already points at the right target is left alone.

.EXAMPLE
    pwsh -File scripts/setup/link_skills.ps1
#>
$ErrorActionPreference = 'Stop'

# Repo root = two levels up from this script (scripts/setup/ -> repo).
$repo   = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$skills = Get-ChildItem -LiteralPath (Join-Path $repo 'skills') -Directory |
    Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName 'SKILL.md') } |
    Select-Object -ExpandProperty Name
New-Item -ItemType Directory -Force -Path (Join-Path $repo '.claude\skills') | Out-Null

foreach ($name in $skills) {
    $link   = Join-Path $repo ".claude\skills\$name"
    $target = Join-Path $repo "skills\$name"

    if (Test-Path -LiteralPath $link) {
        $item = Get-Item -LiteralPath $link -Force
        if ($item.LinkType -eq 'Junction' -and ($item.Target -ccontains $target)) {
            Write-Host "ok      .claude/skills/$name already linked"
            continue
        }
        if ($item.LinkType) {
            # Remove the link itself. Remove-Item -Recurse can follow a junction
            # and empty the real skill folder it points at.
            $item.Delete()
        } else {
            Remove-Item -LiteralPath $link -Recurse -Force  # a stray copy, not a link
        }
    }

    New-Item -ItemType Junction -Path $link -Target $target | Out-Null
    Write-Host "linked  .claude/skills/$name -> skills/$name"
}

Write-Host "Done. Claude Code will discover the skills under .claude/skills/ via the junctions."
