@echo off
echo ================================================
echo  AstroSignature Tool -- Auto Installer v2
echo ================================================
echo.
SET SRCDIR=%~dp0
SET TXTFILE=%SRCDIR%AstroSignature.txt
SET PYFILE=%SRCDIR%AstroSignature.py
echo Source folder: %SRCDIR%
echo.
IF EXIST "%TXTFILE%" GOTO DOTXT
IF EXIST "%PYFILE%" GOTO DOPY
echo ERROR: AstroSignature.py or .txt not found in:
echo   %SRCDIR%
echo.
echo Please make sure AstroSignature.py is in the same folder
echo as this installer, then run it again.
echo.
pause
exit /b 1
:DOTXT
echo Found AstroSignature.txt -- renaming to .py...
IF EXIST "%PYFILE%" del "%PYFILE%"
ren "%TXTFILE%" "AstroSignature.py"
echo   Renamed successfully.
echo.
:DOPY
echo Found AstroSignature.py -- ready to install.
echo.
echo Searching for Siril scripts directory...
echo.
IF EXIST "%APPDATA%\siril\scripts\" GOTO LOC1
IF EXIST "%APPDATA%\Siril\scripts\" GOTO LOC2
IF EXIST "%LOCALAPPDATA%\siril-scripts\utility\" GOTO LOC3
IF EXIST "%LOCALAPPDATA%\siril\scripts\" GOTO LOC4
IF EXIST "%LOCALAPPDATA%\Siril\scripts\" GOTO LOC5
IF EXIST "%PROGRAMFILES%\Siril\scripts\" GOTO LOC6
IF EXIST "%PROGRAMFILES(X86)%\Siril\scripts\" GOTO LOC7
GOTO NOTFOUND
:LOC1
SET DEST=%APPDATA%\siril\scripts\
echo   Found: %APPDATA%\siril\scripts\
GOTO INSTALL
:LOC2
SET DEST=%APPDATA%\Siril\scripts\
echo   Found: %APPDATA%\Siril\scripts\
GOTO INSTALL
:LOC3
SET DEST=%LOCALAPPDATA%\siril-scripts\utility\
echo   Found: %LOCALAPPDATA%\siril-scripts\utility\
GOTO INSTALL
:LOC4
SET DEST=%LOCALAPPDATA%\siril\scripts\
echo   Found: %LOCALAPPDATA%\siril\scripts\
GOTO INSTALL
:LOC5
SET DEST=%LOCALAPPDATA%\Siril\scripts\
echo   Found: %LOCALAPPDATA%\Siril\scripts\
GOTO INSTALL
:LOC6
SET DEST=%PROGRAMFILES%\Siril\scripts\
echo   Found: %PROGRAMFILES%\Siril\scripts\
GOTO INSTALL
:LOC7
SET DEST=%PROGRAMFILES(X86)%\Siril\scripts\
echo   Found: %PROGRAMFILES(X86)%\Siril\scripts\
GOTO INSTALL
:NOTFOUND
echo   No Siril scripts directory found.
echo   Creating default: %APPDATA%\siril\scripts\
echo.
echo   NOTE: After installation check Siril under
echo   Preferences ^> Scripts to confirm the correct path.
echo.
SET DEST=%APPDATA%\siril\scripts\
:INSTALL
echo.
echo Installing to: %DEST%
IF NOT EXIST "%DEST%" mkdir "%DEST%"
copy /Y "%PYFILE%" "%DEST%" >nul
IF ERRORLEVEL 1 GOTO FAILED
echo   SUCCESS
echo.
echo Cleaning up...
del "%PYFILE%"
echo   AstroSignature.py removed from source folder.
echo.
echo ================================================
echo  Installation complete!
echo  Installed to: %DEST%
echo.
echo  Refresh scripts in Siril:
echo  Preferences ^> Scripts ^> refresh button ^> Apply
echo ================================================
echo.
pause
exit /b 0
:FAILED
echo   FAILED -- check folder permissions.
echo.
echo   Try right-clicking AstroSignature_Install.bat
echo   and selecting Run as administrator.
echo.
pause
exit /b 1
