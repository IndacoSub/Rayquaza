@echo off
REM Set the folder paths
set "FILES_FOLDER=F:\SteamLibrary\steamapps\common\AI The Somnium Files"
set "XDELTA_FILES_FOLDER=out"

REM Check if the files and xdelta folders exist
if not exist "%FILES_FOLDER%" (
    echo Files folder does not exist: %FILES_FOLDER%
    pause
    exit /b 1
)

if not exist "%XDELTA_FILES_FOLDER%" (
    echo Xdelta files folder does not exist: %XDELTA_FILES_FOLDER%
    pause
    exit /b 1
)

REM Run the Python script to apply patches
python Rayquaza.py --og "%FILES_FOLDER%" --xdelta "%XDELTA_FILES_FOLDER%" --mod "%FILES_FOLDER%" -a
pause