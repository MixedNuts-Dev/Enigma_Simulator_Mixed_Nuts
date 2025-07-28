@echo off
echo Creating Enigma Simulator C++ Installer...
echo.

REM Check if build exists
if not exist build\Release\EnigmaSimulatorCpp.exe (
    echo ERROR: Build not found! Please run build.bat first.
    pause
    exit /b 1
)

REM Check for Qt6 (optional for GUI)
echo Checking for Qt6 installation...
set QT6_FOUND=0
if exist "C:\Qt\6.5.0\msvc2019_64" (
    set QT6_PATH=C:\Qt\6.5.0\msvc2019_64
    set QT6_FOUND=1
) else if exist "C:\Qt\6.4.0\msvc2019_64" (
    set QT6_PATH=C:\Qt\6.4.0\msvc2019_64
    set QT6_FOUND=1
) else if exist "C:\Qt\6.3.0\msvc2019_64" (
    set QT6_PATH=C:\Qt\6.3.0\msvc2019_64
    set QT6_FOUND=1
)

if %QT6_FOUND%==1 (
    echo Qt6 found at: %QT6_PATH%
    echo Building with GUI support...
) else (
    echo Qt6 not found. Building console-only installer.
)

echo.
echo Creating installer with CPack...
cd build

REM Create installer using CPack (NSIS)
cpack -G NSIS -C Release

if errorlevel 1 (
    echo.
    echo ERROR: CPack failed! 
    echo Make sure NSIS is installed: https://nsis.sourceforge.io/Download
    cd ..
    pause
    exit /b 1
)

echo.
echo Installer created successfully!
echo Location: build\Enigma Simulator Cpp-1.0.0-win64.exe
echo.
cd ..
pause