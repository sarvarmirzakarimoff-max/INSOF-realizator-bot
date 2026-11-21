@echo off
chcp 65001 >nul
cd /d "%~dp0"
venv\Scripts\python korish_yasash.py
if exist tiklash\korish.html start "" "tiklash\korish.html"
pause
