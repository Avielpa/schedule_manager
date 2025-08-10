# NUCLEAR OPTION: Complete VSCode Python settings reset

Write-Host "=== NUCLEAR VSCODE PYTHON RESET ===" -ForegroundColor Red
Write-Host "This will reset ALL VSCode Python settings!" -ForegroundColor Yellow
Write-Host ""

$confirm = Read-Host "Continue? (type YES to proceed)"
if ($confirm -ne "YES") {
    Write-Host "Cancelled by user" -ForegroundColor Yellow
    exit
}

# 1. Close VSCode processes
Write-Host "1. Closing VSCode processes..." -ForegroundColor Yellow
Get-Process Code* -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 3

# 2. Backup and reset global VSCode settings
Write-Host "2. Resetting global VSCode settings..." -ForegroundColor Yellow
$globalSettings = "$env:APPDATA\Code\User\settings.json"
if (Test-Path $globalSettings) {
    Copy-Item $globalSettings "$globalSettings.backup.$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    
    # Create clean settings
    $cleanSettings = @"
{
    "python.terminal.activateEnvironment": false,
    "python.terminal.activateEnvInCurrentTerminal": false,
    "python.defaultInterpreterPath": "",
    "python.pythonPath": "",
    "python.venvPath": "",
    "python.condaPath": "",
    "terminal.integrated.inheritEnv": false,
    "terminal.integrated.shellIntegration.enabled": false,
    "python.analysis.autoImportCompletions": false,
    "python.terminal.executeInFileDir": false
}
"@
    $cleanSettings | Out-File $globalSettings -Encoding UTF8
    Write-Host "   Global settings reset!" -ForegroundColor Green
}

# 3. Reset workspace settings
Write-Host "3. Resetting workspace settings..." -ForegroundColor Yellow
$workspaceSettings = "C:\Users\Aviel\vsprojects\autoLearning\.vscode\settings.json"
$cleanWorkspaceSettings = @"
{
    "python.terminal.activateEnvironment": false,
    "python.terminal.activateEnvInCurrentTerminal": false,
    "python.defaultInterpreterPath": "",
    "python.pythonPath": "",
    "python.venvPath": "",
    "python.condaPath": "",
    "terminal.integrated.inheritEnv": false,
    "terminal.integrated.shellIntegration.enabled": false,
    "terminal.integrated.automationProfile.windows": null,
    "terminal.integrated.defaultProfile.windows": "PowerShell",
    "terminal.integrated.env.windows": {
        "VIRTUAL_ENV": "",
        "PYTHONPATH": "",
        "PYTHON_PATH": ""
    }
}
"@
$cleanWorkspaceSettings | Out-File $workspaceSettings -Encoding UTF8 -Force
Write-Host "   Workspace settings reset!" -ForegroundColor Green

# 4. Clear VSCode extension data
Write-Host "4. Clearing Python extension data..." -ForegroundColor Yellow
$extensionDir = "$env:USERPROFILE\.vscode\extensions"
if (Test-Path $extensionDir) {
    Get-ChildItem $extensionDir -Directory | Where-Object { $_.Name -like "*python*" } | ForEach-Object {
        $cacheDir = Join-Path $_.FullName "cache"
        if (Test-Path $cacheDir) {
            Remove-Item $cacheDir -Recurse -Force -ErrorAction SilentlyContinue
            Write-Host "   Cleared cache for: $($_.Name)" -ForegroundColor Green
        }
    }
}

# 5. Clear Windows Registry entries (if any)
Write-Host "5. Clearing registry entries..." -ForegroundColor Yellow
try {
    Remove-ItemProperty -Path "HKCU:\Environment" -Name "VIRTUAL_ENV" -ErrorAction SilentlyContinue
    Remove-ItemProperty -Path "HKCU:\Environment" -Name "PYTHONPATH" -ErrorAction SilentlyContinue
    Write-Host "   Registry entries cleared" -ForegroundColor Green
} catch {
    Write-Host "   Registry access limited (normal)" -ForegroundColor Yellow
}

# 6. Create a test script
Write-Host "6. Creating test script..." -ForegroundColor Yellow
$testScript = @"
# Test script - run this to verify fix
Write-Host "Testing terminal activation..." -ForegroundColor Green

if (`$env:VIRTUAL_ENV) {
    Write-Host "ERROR: VIRTUAL_ENV is still set to: `$env:VIRTUAL_ENV" -ForegroundColor Red
} else {
    Write-Host "GOOD: VIRTUAL_ENV is not set" -ForegroundColor Green  
}

Write-Host ""
Write-Host "To manually activate venv:" -ForegroundColor Cyan
Write-Host "cd schedule_manage" 
Write-Host ".\venv\Scripts\activate"
Write-Host ""
Write-Host "Current directory: `$PWD" -ForegroundColor White
Write-Host "Python path: " -NoNewline -ForegroundColor White
try { Write-Host (Get-Command python).Source -ForegroundColor Yellow } catch { Write-Host "Python not found" -ForegroundColor Red }
"@

$testScript | Out-File "C:\Users\Aviel\vsprojects\autoLearning\test_clean_terminal.ps1" -Encoding UTF8
Write-Host "   Test script created!" -ForegroundColor Green

Write-Host ""
Write-Host "=== NUCLEAR RESET COMPLETE ===" -ForegroundColor Green
Write-Host "NOW DO THIS:" -ForegroundColor White
Write-Host "1. Close this PowerShell window" -ForegroundColor Cyan
Write-Host "2. Wait 10 seconds" -ForegroundColor Cyan
Write-Host "3. Open NEW PowerShell window" -ForegroundColor Cyan
Write-Host "4. cd C:\Users\Aviel\vsprojects\autoLearning" -ForegroundColor Cyan
Write-Host "5. .\test_clean_terminal.ps1" -ForegroundColor Cyan
Write-Host ""
Write-Host "Terminal should be COMPLETELY CLEAN!" -ForegroundColor Green