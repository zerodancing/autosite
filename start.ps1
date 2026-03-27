Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectDir

$venvPython = $null
if (Test-Path ".\venv\Scripts\python.exe") {
  $venvPython = ".\venv\Scripts\python.exe"
} elseif (Test-Path ".\.venv\Scripts\python.exe") {
  $venvPython = ".\.venv\Scripts\python.exe"
}

if (-not $venvPython) {
  throw "Не найдено виртуальное окружение: venv\Scripts\python.exe или .venv\Scripts\python.exe"
}

if (-not (Test-Path ".\.deps_ready")) {
  & $venvPython -m pip install -r requirements.txt
  New-Item -ItemType File -Path ".\.deps_ready" -Force | Out-Null
}

& $venvPython manage.py migrate
Start-Process powershell -ArgumentList '-NoProfile','-WindowStyle','Hidden','-Command','Start-Sleep -Seconds 3; Start-Process "http://127.0.0.1:8000/"'
& $venvPython manage.py runserver 127.0.0.1:8000
