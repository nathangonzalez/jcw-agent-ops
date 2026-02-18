@echo off
setlocal

powershell -ExecutionPolicy Bypass -File "%~dp0stats.ps1"

endlocal
