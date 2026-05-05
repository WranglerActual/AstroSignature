@echo off
echo ================================================
echo  AstroSignature Tool -- Auto Installer v2.1
echo ================================================
echo.
SET SRCDIR=%~dp0
SET TXTFILE=%SRCDIR%AstroSignature.txt
SET PYFILE=%SRCDIR%AstroSignature.py
SET DEST=
SET CFGDEST=
echo Source folder: %SRCDIR%
echo.
:: Step 1 -- Locate the source file
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
:: Step 2 -- Try to read Siril config file for script path
echo Checking Siril configuration file...
SET CFGDIR=%LOCALAPPDATA%\siril
IF NOT EXIST "%CFGDIR%" GOTO SKIPCFG
:: Search for config.1.x file (handles future Siril versions)
FOR %%F IN ("%CFGDIR%\config.1.*") DO SET CFGFILE=%%F
IF NOT DEFINED CFGFILE GOTO SKIPCFG
IF NOT EXIST "%CFGFILE%" GOTO SKIPCFG
echo   Found config file: %CFGFILE%
:: Extract script_path= line from config
FOR /F "tokens=2 delims==" %%A IN ('findstr /B "script_path=" "%CFGFILE%"') DO SET RAWPATH=%%A
IF NOT DEFINED RAWPATH GOTO SKIPCFG
:: Take only the first path (before the semicolon)
FOR /F "tokens=1 delims=;" %%B IN ("%RAWPATH%") DO SET CFGDEST=%%B
IF NOT DEFINED CFGDEST GOTO SKIPCFG
:: Clean up double backslashes from config file format
SET CFGDEST=%CFGDEST:\\=\%
echo   Siril script path from config: %CFGDEST%
SET DEST=%CFGDEST%
GOTO INSTALL
:SKIPCFG
echo   Config file not found or unreadable -- using path detection.
echo.
:: Step 3 -- Fallback: auto-detect Siril scripts directory
echo Searching for Siril scripts directory...
echo.
IF EXIST "%APPDATA%\siril\scripts\" GOTO LOC1
IF EXIST "%APPDATA%\Siril\scripts\" GOTO LOC2
IF EXIST "%LOCALAPPDATA%\siril\scripts\" GOTO LOC3
IF EXIST "%LOCALAPPDATA%\Siril\scripts\" GOTO LOC4
IF EXIST "%PROGRAMFILES%\Siril\scripts\" GOTO LOC5
IF EXIST "%PROGRAMFILES(X86)%\Siril\scripts\" GOTO LOC6
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
SET DEST=%LOCALAPPDATA%\siril\scripts\
echo   Found: %LOCALAPPDATA%\siril\scripts\
GOTO INSTALL
:LOC4
SET DEST=%LOCALAPPDATA%\Siril\scripts\
echo   Found: %LOCALAPPDATA%\Siril\scripts\
GOTO INSTALL
:LOC5
SET DEST=%PROGRAMFILES%\Siril\scripts\
echo   Found: %PROGRAMFILES%\Siril\scripts\
GOTO INSTALL
:LOC6
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
