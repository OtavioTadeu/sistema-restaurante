@echo off
chcp 65001 > nul
cd /d "%~dp0"
python iniciar.py
if errorlevel 1 pause
