@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
 echo [ERRO] Ambiente virtual nao encontrado. Execute instalar_windows.bat.
 pause
 exit /b 1
)
".venv\Scripts\python.exe" "scripts\iniciar_barflow.py"
if errorlevel 1 (
 echo.
 echo Consulte data\inicializacao.log e execute iniciar_diagnostico.bat.
 pause
 exit /b 1
)
exit /b 0
