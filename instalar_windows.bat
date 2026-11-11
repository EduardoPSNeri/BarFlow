@echo off
setlocal
cd /d "%~dp0"
title BarFlow - Instalador Windows
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\instalar_windows.ps1"
set "RESULTADO=%ERRORLEVEL%"
echo.
if not "%RESULTADO%"=="0" (
  echo [ERRO] Instalacao nao concluida. Codigo: %RESULTADO%
) else (
  echo [OK] Instalacao finalizada. Use iniciar_windows.bat para abrir o BarFlow.
)
pause
exit /b %RESULTADO%
