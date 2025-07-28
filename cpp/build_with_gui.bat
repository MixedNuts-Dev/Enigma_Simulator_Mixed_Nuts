@echo off
echo Building Enigma Simulator C++ with GUI support...
echo.

REM Check for Qt6
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

if %QT6_FOUND%==0 (
    echo ERROR: Qt6 not found!
    echo Please install Qt6 from https://www.qt.io/download
    echo Or use build.bat for console-only version.
    pause
    exit /b 1
)

echo Qt6 found at: %QT6_PATH%
echo.

REM Clean build directory
echo Cleaning previous build...
if exist build_gui (
    rmdir /s /q build_gui
    echo Previous build directory removed.
)

echo Creating fresh build directory...
mkdir build_gui
cd build_gui

echo.
echo Configuring with CMake (Qt6 enabled)...
cmake -G "Visual Studio 17 2022" -A x64 ^
    -DCMAKE_PREFIX_PATH="%QT6_PATH%" ^
    -DQt6_DIR="%QT6_PATH%\lib\cmake\Qt6" ..

if errorlevel 1 (
    echo ERROR: CMake configuration failed!
    cd ..
    pause
    exit /b 1
)

echo.
echo Building Release version...
cmake --build . --config Release

if errorlevel 1 (
    echo ERROR: Build failed!
    cd ..
    pause
    exit /b 1
)

echo.
echo Deploying Qt dependencies...
"%QT6_PATH%\bin\windeployqt.exe" Release\EnigmaSimulatorCppGUI.exe

echo.
echo Build successful!
echo Console executable: build_gui\Release\EnigmaSimulatorCpp.exe
echo GUI executable: build_gui\Release\EnigmaSimulatorCppGUI.exe
echo.
echo To create an installer with GUI, run: build_gui_installer.bat
echo.
cd ..
pause