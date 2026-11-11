@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
 echo [ERRO] Ambiente virtual nao encontrado. Execute instalar_windows.bat.
 pause
 exit /b 1
)
".venv\Scripts\python.exe" -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
echo.
echo Servidor encerrou com codigo %ERRORLEVEL%
pause
