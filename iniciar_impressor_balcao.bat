@echo off
chcp 65001 > nul
title Dogão do Castelo - Agente de Impressão da Cozinha
color 0B

echo ========================================================
echo   DOGÃO DO CASTELO - VIGIA DE IMPRESSÃO DE COMANDAS
echo ========================================================
echo.
echo Iniciando o agente de impressão...
echo Mantenha esta janela aberta durante todo o expediente!
echo.

if exist "venv\Scripts\python.exe" (
    "venv\Scripts\python.exe" agente_impressao.py
) else (
    python agente_impressao.py
)

pause
