# Mesa de Servicios — puerto 8010 por defecto (evita conflicto con otras APIs en 8000).
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$env:PYTHONPATH = "."
& ".\.venv\Scripts\python.exe" -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8010
