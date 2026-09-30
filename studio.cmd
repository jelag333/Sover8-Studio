@echo off
rem Lanceur du Studio Tesseract : studio ajouter | liste | fiche | modifier | auto | monter | apercus | page | verifier
setlocal
set "STUDIO=%~dp0"
if not exist "%STUDIO%.venv\Scripts\python.exe" (
  echo Studio non installe : lance installer.ps1
  exit /b 1
)
set PYTHONUTF8=1
"%STUDIO%.venv\Scripts\python.exe" "%STUDIO%outils\studio.py" %*
