@echo off
chcp 65001 >nul
cd /d "%~dp0"
venv\Scripts\python telefon_arxiv.py
start "" "tiklash\telefon"
pause
