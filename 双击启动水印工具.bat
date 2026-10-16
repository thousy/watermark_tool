@echo off
chcp 65001 >nul
cd /d "%~dp0"
start "" "C:\Users\admin\AppData\Local\Programs\Python\Python314\pythonw.exe" "%~dp0watermark_gui.py"
exit
