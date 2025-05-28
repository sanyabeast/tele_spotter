@echo off
title Image Captioning — Drag a JPG onto this .bat or run manually

:: Activate venv
call venv\Scripts\activate.bat

:: Check if a file was dragged onto the .bat
if "%~1"=="" goto manual_input

set "imgpath=%~1"
goto run

:manual_input
echo.
echo Drag a .jpg file into this window and press [Enter]
set /p "imgpath=Path: "

if "%imgpath%"=="" goto manual_input
if not exist "%imgpath%" (
    echo File not found.
    goto manual_input
)

:run
echo.
echo Running captioner on: %imgpath%
echo ---------------------------------------
python interrogate.py "%imgpath%"
echo ---------------------------------------
echo.
pause
goto manual_input
