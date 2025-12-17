@echo off
echo Atualizando Balanco Out-25...
cd /d "%~dp0"
.venv\Scripts\python.exe update_balance_sheet.py
echo.
echo Concluido! Pressione qualquer tecla para sair.
pause
