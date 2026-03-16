# Troubleshooting

## Python not found in PowerShell

Symptom:
- `python --version` says Python was not found and mentions Microsoft Store.

Fix:
1. Install Python from python.org or use `winget install --id Python.Python.3.12 -e`.
2. Reopen PowerShell.
3. Run `python --version` again.

## Cannot activate virtual environment

Symptom:
- PowerShell blocks `Activate.ps1` due to execution policy.

Fix:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## `pip` command not found

Use module form instead:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Port 5000 already in use

Symptom:
- Flask fails to bind port.

Fix option 1:
- Stop the other process using port 5000.

Fix option 2:

```powershell
python -c "from app import app; app.run(debug=True, port=5001)"
```

## JSON decode errors or broken pages from malformed data

The app now tolerates many malformed structures by normalizing loaded JSON.
If a specific file is severely corrupted, replace it with a known valid structure from `doc/03-data-model.md`.

## Missing badges or progression file

On startup, the app recreates missing or invalid root structure for:
- `data/badges.json`
- `data/progression.json`

## Git line endings warning

Windows may show line ending warnings. This is typically harmless.
If needed:

```powershell
git config core.autocrlf true
```
