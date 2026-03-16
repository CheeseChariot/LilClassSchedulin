# Setup on Windows PowerShell

## Goal

Get the app running on a fresh Windows machine where Python might not be installed.

## 1. Verify installed commands

```powershell
Get-Command python, py, pip, git -ErrorAction SilentlyContinue |
  Select-Object Name, Source
```

If `python --version` says Python was not found and suggests Microsoft Store, Python is not actually installed yet.

## 2. Install Python

Recommended install methods:

1. Python.org installer (recommended)
2. Winget package manager

Winget example:

```powershell
winget install --id Python.Python.3.12 -e
```

After install, close PowerShell and open a new window, then verify:

```powershell
python --version
```

## 3. Clone repository

```powershell
git clone https://github.com/CheeseChariot/LilClassSchedulin.git
Set-Location .\LilClassSchedulin
```

## 4. Create virtual environment

```powershell
python -m venv .venv
```

## 5. Activate virtual environment

```powershell
.\.venv\Scripts\Activate.ps1
```

If script execution is blocked:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 6. Install dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 7. Start app

```powershell
python app.py
```

Open `http://127.0.0.1:5000` in your browser.

## 8. Optional debug mode

```powershell
$env:FLASK_DEBUG = "1"
python app.py
```

Use `Ctrl+C` in the terminal to stop the server.
