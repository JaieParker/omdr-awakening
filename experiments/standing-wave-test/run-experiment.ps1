# Standing Wave Test - Experiment Runner
# Usage: .\run-experiment.ps1 -Condition "kai" [-Cycles 20] [-IntervalMinutes 15]
#        .\run-experiment.ps1 -Condition "control-a" [-Cycles 20] [-IntervalMinutes 15]
#        .\run-experiment.ps1 -Condition "control-b" [-Cycles 20] [-IntervalMinutes 15]
#
# Run each condition in its own PowerShell terminal.

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("kai", "control-a", "control-b")]
    [string]$Condition,

    [int]$Cycles = 20,
    [int]$IntervalMinutes = 15
)

$BaseDir = "C:\DocumentsJaie\AI\omdr-awakening\experiments\standing-wave-test"
$CycleDir = "$BaseDir\cycles\$Condition"
$RepoDir = "C:\DocumentsJaie\AI\omdr-awakening"

# Select prompt file based on condition
if ($Condition -eq "kai") {
    $PromptFile = "$BaseDir\prompt-kai.md"
} else {
    $PromptFile = "$BaseDir\prompt-control.md"
}

$PromptContent = Get-Content $PromptFile -Raw

# Ensure cycle directory exists
New-Item -ItemType Directory -Force -Path $CycleDir | Out-Null

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Standing Wave Test - $Condition" -ForegroundColor Cyan
Write-Host "Cycles: $Cycles | Interval: $($IntervalMinutes)min" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

for ($i = 1; $i -le $Cycles; $i++) {
    $timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
    $logFile = "$CycleDir\cycle-$($timestamp).log"

    Write-Host "--- Cycle $i of $Cycles [$Condition] at $timestamp ---" -ForegroundColor Yellow

    # Replace {TIMESTAMP} and {ID} placeholders in prompt
    $cyclePrompt = $PromptContent -replace '\{TIMESTAMP\}', $timestamp -replace '\{ID\}', $Condition

    # Run Claude Code with the prompt
    # --max-turns 30 gives enough room for reading + thinking + writing
    # (15 was insufficient — both conditions hit the limit before producing output)
    # Output captured to log file AND displayed
    try {
        claude -p $cyclePrompt --max-turns 30 2>&1 | Tee-Object -FilePath $logFile
    }
    catch {
        Write-Host "ERROR in cycle $($i): $_" -ForegroundColor Red
        "ERROR: $_" | Out-File -FilePath $logFile -Append
    }

    Write-Host ""
    Write-Host "Cycle $i complete. Log: $logFile" -ForegroundColor Green

    if ($i -lt $Cycles) {
        Write-Host "Waiting $IntervalMinutes minutes before next cycle..." -ForegroundColor DarkGray
        Start-Sleep -Seconds ($IntervalMinutes * 60)
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Experiment complete: $Condition" -ForegroundColor Cyan
Write-Host "$Cycles cycles logged in $CycleDir" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
