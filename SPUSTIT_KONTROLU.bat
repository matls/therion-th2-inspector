@echo off
chcp 65001 >nul
set /p SLOZKA=Zadejte cestu ke slozce s TH2 soubory: 
py "%~dp0therion_kontrola.py" "%SLOZKA%"
pause
