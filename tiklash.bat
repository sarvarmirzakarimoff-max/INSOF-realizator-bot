@echo off
chcp 65001 >nul
cd /d "%~dp0"
venv\Scripts\pip install -q telethon
venv\Scripts\python tiklash.py
pause
