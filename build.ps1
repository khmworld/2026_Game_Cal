$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

function Get-PythonExe {
    $candidate = Join-Path $env:LocalAppData "Programs\Python\Python311\python.exe"
    if (Test-Path $candidate) { return $candidate }
    return "python"
}

function Stop-GameCalendarProcesses {
    Write-Host "[1/4] Running process cleanup..."

    $names = @(
        "GameCalendar",
        "GameCalendar_fixed",
        "GameCalendar_onedir",
        "GameCalendar_onedir_v2"
    )

    foreach ($name in $names) {
        Get-Process -Name $name -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    }

    cmd /c "taskkill /F /T /IM GameCalendar.exe >nul 2>&1"
    cmd /c "taskkill /F /T /IM GameCalendar_fixed.exe >nul 2>&1"
    cmd /c "taskkill /F /T /IM GameCalendar_onedir.exe >nul 2>&1"
    cmd /c "taskkill /F /T /IM GameCalendar_onedir_v2.exe >nul 2>&1"

    Start-Sleep -Milliseconds 700

    $left = Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -like "GameCalendar*" }
    if ($left) {
        Write-Host "남아있는 프로세스(PID):" -ForegroundColor Yellow
        $left | Select-Object ProcessName, Id | Format-Table -AutoSize
        throw "프로세스 잠금 해제 실패. 관리자 권한 PowerShell에서 build.ps1을 다시 실행하거나 재부팅 후 재시도하세요."
    }
}

function Clear-BuildOutput {
    Write-Host "[2/4] Cleaning build output..."
    Remove-Item ".\build" -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item ".\dist\GameCalendar_onedir" -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item ".\startup_trace.log" -Force -ErrorAction SilentlyContinue
}

function Build-App {
    Write-Host "[3/4] Building with PyInstaller (one-dir)..."
    $pythonExe = Get-PythonExe
    & $pythonExe -m PyInstaller GameCalendar.spec --clean -y
}

function Show-Result {
    Write-Host "[4/4] Build result check..."
    $exePath = ".\dist\GameCalendar_onedir\GameCalendar_onedir.exe"
    if (-not (Test-Path $exePath)) {
        throw "빌드 결과 exe를 찾을 수 없습니다: $exePath"
    }
    Get-Item $exePath | Select-Object FullName, Length, LastWriteTime | Format-List
    Write-Host "`n완료: dist\GameCalendar_onedir 폴더째로 배포하세요." -ForegroundColor Green
}

Stop-GameCalendarProcesses
Clear-BuildOutput
Build-App
Show-Result
