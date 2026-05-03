@echo off
echo ================================================
echo  AstroSignature Tool — Auto Installer v2
echo ================================================
echo.

:: ── Use the folder where this bat file lives as the source ───────────────────
SET SRCDIR=%~dp0
SET TXTFILE=%SRCDIR%AstroSignature.txt
SET PYFILE=%SRCDIR%AstroSignature.py
SET DEST=

:: ── Step 1 — Locate the source file ─────────────────────────────────────────
IF EXIST "%TXTFILE%" (
    echo Found AstroSignature.txt in Downloads — renaming to .py...
    IF EXIST "%PYFILE%" del "%PYFILE%"
    ren "%TXTFILE%" "AstroSignature.py"
    echo   Renamed successfully.
    echo.
) ELSE IF EXIST "%PYFILE%" (
    echo Found AstroSignature.py in Downloads — ready to install.
    echo.
) ELSE (
    echo ERROR: AstroSignature.txt or AstroSignature.py not found in:
    echo   %SRCDIR%
    echo.
    echo Please make sure AstroSignature.py (or .txt) is in the
    echo same folder as this installer, then run it again.
    echo.
    pause
    exit /b 1
)

:: ── Step 2 — Auto-detect Siril scripts directory ─────────────────────────────
echo Searching for Siril scripts directory...
echo.

:: Check all known valid Siril script locations on Windows
:: Location 1 — Most common: Roaming\siril\scripts (Siril default)
IF EXIST "%APPDATA%\siril\scripts\" (
    SET DEST=%APPDATA%\siril\scripts\
    echo   Found: %APPDATA%\siril\scripts\
    GOTO FOUND
)

:: Location 2 — Roaming\Siril\scripts (capitalised)
IF EXIST "%APPDATA%\Siril\scripts\" (
    SET DEST=%APPDATA%\Siril\scripts\
    echo   Found: %APPDATA%\Siril\scripts\
    GOTO FOUND
)

:: Location 3 — Local\siril-scripts\utility (reported by DaveNF2G, Issue #6)
IF EXIST "%LOCALAPPDATA%\siril-scripts\utility\" (
    SET DEST=%LOCALAPPDATA%\siril-scripts\utility\
    echo   Found: %LOCALAPPDATA%\siril-scripts\utility\
    GOTO FOUND
)

:: Location 4 — Local\siril\scripts
IF EXIST "%LOCALAPPDATA%\siril\scripts\" (
    SET DEST=%LOCALAPPDATA%\siril\scripts\
    echo   Found: %LOCALAPPDATA%\siril\scripts\
    GOTO FOUND
)

:: Location 5 — Local\Siril\scripts (capitalised)
IF EXIST "%LOCALAPPDATA%\Siril\scripts\" (
    SET DEST=%LOCALAPPDATA%\Siril\scripts\
    echo   Found: %LOCALAPPDATA%\Siril\scripts\
    GOTO FOUND
)

:: Location 6 — Program Files installation (system-wide)
IF EXIST "%PROGRAMFILES%\Siril\scripts\" (
    SET DEST=%PROGRAMFILES%\Siril\scripts\
    echo   Found: %PROGRAMFILES%\Siril\scripts\
    GOTO FOUND
)

:: Location 7 — Program Files x86
IF EXIST "%PROGRAMFILES(X86)%\Siril\scripts\" (
    SET DEST=%PROGRAMFILES(X86)%\Siril\scripts\
    echo   Found: %PROGRAMFILES(X86)%\Siril\scripts\
    GOTO FOUND
)

:: ── No known location found — create the default and warn user ───────────────
echo   No existing Siril scripts directory found.
echo   Creating default location: %APPDATA%\siril\scripts\
echo.
echo   NOTE: If Siril does not find the script after installation,
echo   open Siril and check:
echo   Preferences ^> Scripts — to see which folder Siril is using,
echo   then manually copy AstroSignature.py to that folder.
echo.
SET DEST=%APPDATA%\siril\scripts\

:FOUND
:: ── Step 3 — Create destination if needed and copy file ─────────────────────
echo.
echo Installing to: %DEST%
IF NOT EXIST "%DEST%" mkdir "%DEST%"
copy /Y "%PYFILE%" "%DEST%" >nul
IF %ERRORLEVEL%==0 (
    echo   SUCCESS
) ELSE (
    echo   FAILED — check folder permissions
    echo.
    echo   Try running this installer as Administrator:
    echo   Right-click AstroSignature_Install.bat ^> Run as administrator
    pause
    exit /b 1
)

:: ── Step 4 — Clean up source folder ─────────────────────────────────────────
echo.
echo Cleaning up source folder...
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
