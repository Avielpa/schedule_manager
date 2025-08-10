# PowerShell script to find and eliminate auto venv activation

Write-Host "=== FINDING AND ELIMINATING AUTO VENV ACTIVATION ===" -ForegroundColor Red
Write-Host ""

# 1. Check PowerShell profiles
Write-Host "1. Checking PowerShell profiles..." -ForegroundColor Yellow

$profiles = @(
    $PROFILE.AllUsersAllHosts,
    $PROFILE.AllUsersCurrentHost, 
    $PROFILE.CurrentUserAllHosts,
    $PROFILE.CurrentUserCurrentHost
)

foreach ($profile in $profiles) {
    if ($profile -and (Test-Path $profile)) {
        Write-Host "   Found profile: $profile" -ForegroundColor Red
        $content = Get-Content $profile
        if ($content -match "Activate\.ps1|venv|virtual") {
            Write-Host "   *** PROBLEM: This profile contains venv activation!" -ForegroundColor Red
            Write-Host "   Content:" -ForegroundColor White
            $content | ForEach-Object { Write-Host "     $_" -ForegroundColor Gray }
            Write-Host "   Backing up and clearing..." -ForegroundColor Yellow
            Copy-Item $profile "$profile.backup.$(Get-Date -Format 'yyyyMMdd_HHmmss')"
            "" | Out-File $profile -Encoding UTF8
            Write-Host "   Profile cleared and backed up!" -ForegroundColor Green
        } else {
            Write-Host "   Profile is clean" -ForegroundColor Green
        }
    } else {
        Write-Host "   No profile at: $profile" -ForegroundColor Green
    }
}

# 2. Check environment variables
Write-Host ""
Write-Host "2. Checking environment variables..." -ForegroundColor Yellow

$envVars = @("VIRTUAL_ENV", "PYTHONPATH", "PYTHON_PATH", "CONDA_DEFAULT_ENV")
foreach ($var in $envVars) {
    $value = [Environment]::GetEnvironmentVariable($var, "User")
    if ($value) {
        Write-Host "   Found USER env var: $var = $value" -ForegroundColor Red
        [Environment]::SetEnvironmentVariable($var, $null, "User")
        Write-Host "   Cleared USER env var: $var" -ForegroundColor Green
    }
    
    $value = [Environment]::GetEnvironmentVariable($var, "Machine") 
    if ($value) {
        Write-Host "   Found MACHINE env var: $var = $value" -ForegroundColor Red
        Write-Host "   You may need admin rights to clear machine-level env vars" -ForegroundColor Yellow
    }
}

# Clear current session
$env:VIRTUAL_ENV = ""
$env:PYTHONPATH = ""
$env:PYTHON_PATH = ""
$env:CONDA_DEFAULT_ENV = ""

# 3. Check VSCode settings
Write-Host ""
Write-Host "3. Checking VSCode settings..." -ForegroundColor Yellow

$vscodeSettings = @(
    "$env:APPDATA\Code\User\settings.json",
    "C:\Users\Aviel\vsprojects\autoLearning\.vscode\settings.json"
)

foreach ($settingsFile in $vscodeSettings) {
    if (Test-Path $settingsFile) {
        Write-Host "   Checking: $settingsFile" -ForegroundColor White
        $content = Get-Content $settingsFile -Raw
        if ($content -match '"python\.terminal\.activateEnvironment":\s*true|"python\.pythonPath"|"python\.defaultInterpreterPath":\s*"[^"]*venv') {
            Write-Host "   *** PROBLEM: VSCode settings may have venv activation!" -ForegroundColor Red
        } else {
            Write-Host "   VSCode settings look clean" -ForegroundColor Green
        }
    }
}

# 4. Check Windows Terminal settings
Write-Host ""
Write-Host "4. Checking Windows Terminal settings..." -ForegroundColor Yellow

$wtSettings = "$env:LOCALAPPDATA\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json"
if (Test-Path $wtSettings) {
    Write-Host "   Found Windows Terminal settings" -ForegroundColor White
    $content = Get-Content $wtSettings -Raw
    if ($content -match "Activate\.ps1|venv") {
        Write-Host "   *** PROBLEM: Windows Terminal may have venv activation!" -ForegroundColor Red
    } else {
        Write-Host "   Windows Terminal settings look clean" -ForegroundColor Green
    }
}

# 5. Kill all Python processes
Write-Host ""
Write-Host "5. Killing Python processes..." -ForegroundColor Yellow
Get-Process python* -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Write-Host "   Python processes stopped" -ForegroundColor Green

# 6. Clear PowerShell history
Write-Host ""
Write-Host "6. Clearing PowerShell history..." -ForegroundColor Yellow
Clear-History
Remove-Item (Get-PSReadlineOption).HistorySavePath -ErrorAction SilentlyContinue
Write-Host "   PowerShell history cleared" -ForegroundColor Green

Write-Host ""
Write-Host "=== COMPLETE SOLUTION ===" -ForegroundColor Green
Write-Host "Now close ALL terminals and VSCode completely, then:" -ForegroundColor White
Write-Host "1. Wait 10 seconds" -ForegroundColor Cyan
Write-Host "2. Open VSCode" -ForegroundColor Cyan  
Write-Host "3. Open terminal" -ForegroundColor Cyan
Write-Host "4. Should see clean: PS C:\Users\Aviel\vsprojects\autoLearning>" -ForegroundColor Cyan
Write-Host ""
Write-Host "If it STILL activates, run this script AS ADMINISTRATOR" -ForegroundColor Red