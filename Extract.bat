@echo off
REM Set the folder paths
set "ORIGINAL_FILES_FOLDER=F:\SteamLibrary\steamapps\common\AI The Somnium Files"
set "MODIFIED_FILES_FOLDER=C:\Users\Volca\source\repos\Rayquaza\Rayquaza\x64\Debug\mod"
set "OUT_XDELTA_FILES_FOLDER=out"

REM Check if the original and modified folders exist
if not exist "%ORIGINAL_FILES_FOLDER%" (
    echo Original files folder does not exist: %ORIGINAL_FILES_FOLDER%
    pause
    exit /b 1
)

if not exist "%MODIFIED_FILES_FOLDER%" (
    echo Modified files folder does not exist: %MODIFIED_FILES_FOLDER%
    pause
    exit /b 1
)

REM Run the Python script to extract patches
call Rayquaza.exe --og "%ORIGINAL_FILES_FOLDER%" --mod "%MODIFIED_FILES_FOLDER%" --out "%OUT_XDELTA_FILES_FOLDER%"
pause
